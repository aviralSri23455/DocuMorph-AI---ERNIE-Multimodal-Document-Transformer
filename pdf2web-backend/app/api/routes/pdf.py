"""PDF processing endpoints."""
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from loguru import logger

from app.models.schemas import (
    ProcessingMode, UploadResponse, ExtractionResponse
)
from app.services.ocr_service import ocr_service
from app.services.pii_service import pii_service
from app.services.markdown_service import markdown_service
from app.services.ernie_service import ernie_service
from app.services.document_store import document_store
from app.services.websocket_service import websocket_service
from app.config import settings

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    mode: ProcessingMode = Form(ProcessingMode.SECURE),
    language: str = Form("en"),
    redact_emails: bool = Form(True),
    redact_phones: bool = Form(True),
    redact_names: bool = Form(True),
    redact_ssn: bool = Form(True),
    redact_credit_cards: bool = Form(True)
):
    """
    Upload a PDF file for processing.
    
    - **file**: PDF file to upload
    - **mode**: Processing mode (secure/standard)
    - **language**: OCR language code
    - **redact_***: Secure Mode PII redaction options
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # Check file size
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    
    if file_size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB"
        )
    
    # Save file temporarily
    file_id = str(uuid.uuid4())
    pdf_path = settings.upload_dir / f"{file_id}.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(pdf_path, "wb") as f:
        f.write(content)
    
    logger.info(f"Uploaded PDF: {file.filename} ({file_size_mb:.2f}MB) - Mode: {mode}")
    
    try:
        logger.info(f"Starting processing for file_id: {file_id}")
        
        # Emit processing started event
        await websocket_service.emit_processing_started(file_id, file.filename)
        
        # Extract content using OCR (local processing)
        # Also saves page images for optional vision analysis
        logger.info("Starting OCR extraction...")
        await websocket_service.emit_processing_progress(file_id, "ocr", 0.1, "Starting OCR extraction...")
        
        try:
            blocks, images, page_images = await ocr_service.extract_from_pdf(
                pdf_path, 
                save_page_images=settings.enable_vision_analysis
            )
            logger.info(f"OCR extraction complete: {len(blocks)} blocks, {len(images)} images")
            await websocket_service.emit_processing_progress(file_id, "ocr", 0.4, f"Extracted {len(blocks)} content blocks")
        except Exception as ocr_error:
            import traceback
            logger.error(f"OCR extraction failed: {ocr_error}")
            logger.error(f"OCR Traceback: {traceback.format_exc()}")
            await websocket_service.emit_error(file_id, str(ocr_error), "ocr")
            raise HTTPException(status_code=500, detail=f"OCR extraction failed: {str(ocr_error)}")
        
        total_pages = len(set(b.page for b in blocks)) or 1
        logger.info(f"Total pages: {total_pages}")
        
        # Apply PII redaction in Secure Mode
        pii_redactions = []
        if mode == ProcessingMode.SECURE:
            logger.info("Starting PII redaction (Secure Mode)...")
            await websocket_service.emit_processing_progress(file_id, "pii", 0.5, "Scanning for PII...")
            
            # Build Secure Mode config from form parameters
            secure_config = {
                "redact_emails": redact_emails,
                "redact_phones": redact_phones,
                "redact_names": redact_names,
                "redact_ssn": redact_ssn,
                "redact_credit_cards": redact_credit_cards
            }
            try:
                blocks, pii_redactions = await pii_service.scan_and_redact(blocks, config=secure_config)
                logger.info(f"Secure Mode: Redacted {len(pii_redactions)} PII instances")
                
                # Emit PII detection event
                if pii_redactions:
                    pii_types = {}
                    for r in pii_redactions:
                        pii_types[r.pii_type] = pii_types.get(r.pii_type, 0) + 1
                    await websocket_service.emit_pii_detected(file_id, len(pii_redactions), pii_types)
                
                await websocket_service.emit_processing_progress(file_id, "pii", 0.6, f"Redacted {len(pii_redactions)} PII items")
            except Exception as pii_error:
                import traceback
                logger.warning(f"PII redaction failed, continuing without redaction: {pii_error}")
                logger.warning(f"PII Traceback: {traceback.format_exc()}")
                # Continue without PII redaction rather than failing completely
        
        logger.info("Creating document in store...")
        await websocket_service.emit_processing_progress(file_id, "store", 0.7, "Storing document...")
        
        # Create document in store
        document = document_store.create_document(
            filename=file.filename,
            total_pages=total_pages,
            blocks=blocks,
            images=images,
            pii_redactions=pii_redactions,
            processing_mode=mode
        )
        logger.info(f"Document created: {document.document_id}")
        
        # Store page images for vision analysis
        if page_images:
            document_store.store_page_images(document.document_id, page_images)
            logger.info(f"Stored {len(page_images)} page images")
        
        # Generate Markdown (sanitized in Secure Mode)
        logger.info("Generating markdown...")
        await websocket_service.emit_processing_progress(file_id, "markdown", 0.85, "Generating markdown...")
        
        markdown_content = await markdown_service.build_markdown(blocks, include_metadata=True)
        document_store.store_markdown(document.document_id, markdown_content)
        logger.info("Markdown generated and stored")
        
        # Cleanup temp PDF (never sent to cloud)
        pdf_path.unlink(missing_ok=True)
        
        # Emit completion event
        await websocket_service.emit_processing_progress(document.document_id, "complete", 1.0, "Processing complete!")
        
        return UploadResponse(
            document_id=document.document_id,
            filename=file.filename,
            total_pages=total_pages,
            processing_mode=mode,
            message=f"Successfully extracted {len(blocks)} content blocks" + 
                    (f" ({len(pii_redactions)} PII redacted)" if pii_redactions else "")
        )
        
    except HTTPException:
        pdf_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        pdf_path.unlink(missing_ok=True)
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"PDF processing failed: {e}")
        logger.error(f"Traceback: {error_trace}")
        # Return more detailed error in debug mode
        if settings.debug:
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/{document_id}", response_model=ExtractionResponse)
async def get_extraction(document_id: str):
    """
    Get extracted content for a document.
    
    Returns the extracted content blocks, markdown, and analysis results
    for use in the Co-Design layer.
    """
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    markdown = document_store.get_markdown(document_id)
    theme_analysis = document_store.get_theme_analysis(document_id)
    suggestions = document_store.get_suggestions(document_id)
    
    # If no theme analysis yet, perform it
    if not theme_analysis and markdown:
        theme_analysis = await ernie_service.analyze_theme(markdown)
        document_store.store_theme_analysis(document_id, theme_analysis)
    
    # If no suggestions yet, analyze semantics (with optional vision analysis)
    if not suggestions:
        page_images = document_store.get_page_images(document_id)
        suggestions = await ernie_service.analyze_semantics(
            document.blocks,
            page_images=page_images if settings.enable_vision_analysis else None
        )
        document_store.store_suggestions(document_id, suggestions)
    
    return ExtractionResponse(
        document=document,
        markdown=markdown or "",
        theme_analysis=theme_analysis,
        semantic_suggestions=suggestions
    )


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all associated data."""
    if not document_store.delete_document(document_id):
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully"}


@router.get("/{document_id}/blocks")
async def get_blocks(document_id: str):
    """Get content blocks for a document."""
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "blocks": [b.model_dump() for b in document.blocks],
        "total": len(document.blocks)
    }


@router.get("/{document_id}/pii")
async def get_pii_redactions(document_id: str):
    """Get PII redactions for a document."""
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    summary = await pii_service.get_pii_summary(document.pii_redactions)
    
    return {
        "redactions": [r.model_dump() for r in document.pii_redactions],
        "summary": summary,
        "total": len(document.pii_redactions)
    }
