"""Co-Design Layer endpoints for human-in-the-loop interaction."""
from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel
from typing import List, Optional
from app.models.schemas import (
    CoDesignSubmission, CoDesignEdit, PIIRedactionAction,
    ContentBlock, ContentType, HTMLGenerationResponse, ThemeType
)
from app.services.document_store import document_store
from app.services.markdown_service import markdown_service
from app.services.pii_service import pii_service
from app.services.ernie_service import ernie_service
from app.services.html_generator import html_generator
from app.services.audit_service import audit_service, AuditAction
from app.services.websocket_service import websocket_service

# Import ContentType for chart suggestion endpoint
from app.models.schemas import ContentType

router = APIRouter()


@router.get("/{document_id}/preview")
async def get_preview(document_id: str):
    """
    Get Co-Design preview data for a document.
    
    Returns all data needed for the Co-Design UI:
    - Content blocks with confidence scores
    - PII redactions for review
    - Theme suggestions
    - Semantic component suggestions
    """
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    markdown = document_store.get_markdown(document_id)
    theme_analysis = document_store.get_theme_analysis(document_id)
    suggestions = document_store.get_suggestions(document_id)
    
    # Generate theme analysis if not exists
    if not theme_analysis and markdown:
        try:
            theme_analysis = await ernie_service.analyze_theme(markdown)
            document_store.store_theme_analysis(document_id, theme_analysis)
            logger.info(f"Generated theme analysis for {document_id}")
        except Exception as e:
            logger.warning(f"Theme analysis failed: {e}")
    
    # Generate semantic suggestions if not exists
    if not suggestions:
        try:
            from app.config import settings
            page_images = document_store.get_page_images(document_id)
            suggestions = await ernie_service.analyze_semantics(
                document.blocks,
                page_images=page_images if settings.enable_vision_analysis else None
            )
            document_store.store_suggestions(document_id, suggestions)
            logger.info(f"Generated {len(suggestions)} semantic suggestions for {document_id}")
        except Exception as e:
            logger.warning(f"Semantic analysis failed: {e}")
            suggestions = []
    
    # Identify low-confidence blocks
    low_confidence_blocks = [
        b for b in document.blocks if b.confidence < 0.8
    ]
    
    return {
        "document_id": document_id,
        "filename": document.filename,
        "processing_mode": document.processing_mode,
        "blocks": [b.model_dump() for b in document.blocks],
        "markdown": markdown,
        "pii_redactions": [r.model_dump() for r in document.pii_redactions],
        "theme_analysis": theme_analysis.model_dump() if theme_analysis else None,
        "semantic_suggestions": [s.model_dump() for s in suggestions],
        "low_confidence_blocks": [b.model_dump() for b in low_confidence_blocks],
        "stats": {
            "total_blocks": len(document.blocks),
            "low_confidence_count": len(low_confidence_blocks),
            "pii_count": len(document.pii_redactions),
            "suggestion_count": len(suggestions)
        }
    }


@router.post("/{document_id}/edit-block")
async def edit_block(document_id: str, edit: CoDesignEdit):
    """
    Edit a single content block.
    
    Allows users to:
    - Correct OCR errors
    - Change block type
    - Approve/reject blocks
    """
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Find and update block
    block_found = False
    updated_blocks = []
    
    for block in document.blocks:
        if block.id == edit.block_id:
            block_found = True
            if edit.new_content is not None:
                block.content = edit.new_content
                block.confidence = 1.0  # User-verified
            if edit.new_type is not None:
                block.type = edit.new_type
            block.metadata["user_edited"] = True
        updated_blocks.append(block)
    
    if not block_found:
        raise HTTPException(status_code=404, detail="Block not found")
    
    # Update document
    document_store.update_document(document_id, blocks=updated_blocks)
    
    # Regenerate markdown
    new_markdown = await markdown_service.build_markdown(updated_blocks, include_metadata=True)
    document_store.store_markdown(document_id, new_markdown)
    
    logger.info(f"Edited block {edit.block_id} in document {document_id}")
    
    # Audit log
    await audit_service.log_block_edit(
        document_id=document_id,
        block_id=edit.block_id,
        edit_type="content" if edit.new_content else "type"
    )
    
    # WebSocket notification
    await websocket_service.emit_block_updated(document_id, edit.block_id, "edited")
    
    return {"message": "Block updated successfully", "block_id": edit.block_id}


@router.post("/{document_id}/pii-action")
async def handle_pii_action(document_id: str, action: PIIRedactionAction):
    """
    Handle PII redaction actions.
    
    Actions:
    - approve: Keep the redaction
    - undo: Restore original text
    - modify: Change the redacted value
    """
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Find the redaction
    redaction = None
    for r in document.pii_redactions:
        if r.id == action.redaction_id:
            redaction = r
            break
    
    if not redaction:
        raise HTTPException(status_code=404, detail="Redaction not found")
    
    if action.action == "undo":
        # Restore original text in the block
        for block in document.blocks:
            if block.id == redaction.block_id:
                block.content = await pii_service.undo_redaction(
                    block.content, redaction
                )
                break
        
        # Remove redaction from list
        document.pii_redactions = [
            r for r in document.pii_redactions if r.id != action.redaction_id
        ]
        
    elif action.action == "modify" and action.new_value:
        # Update redaction placeholder
        for block in document.blocks:
            if block.id == redaction.block_id:
                block.content = block.content.replace(
                    redaction.redacted, action.new_value
                )
                break
        redaction.redacted = action.new_value
    
    # Update document
    document_store.update_document(
        document_id, 
        blocks=document.blocks,
        pii_redactions=document.pii_redactions
    )
    
    # Regenerate markdown
    new_markdown = await markdown_service.build_markdown(document.blocks, include_metadata=True)
    document_store.store_markdown(document_id, new_markdown)
    
    logger.info(f"PII action '{action.action}' on redaction {action.redaction_id}")
    
    # Audit log
    await audit_service.log_pii_action(
        document_id=document_id,
        action_type=action.action,
        redaction_id=action.redaction_id,
        pii_type=redaction.pii_type,
        new_value=action.new_value
    )
    
    return {"message": f"PII action '{action.action}' completed"}


@router.post("/{document_id}/submit", response_model=HTMLGenerationResponse)
async def submit_codesign(document_id: str, submission: CoDesignSubmission):
    """
    Submit Co-Design edits and generate final HTML.
    
    This is the main endpoint for finalizing the Co-Design process:
    1. Apply all pending edits
    2. Process PII actions
    3. Apply theme selection
    4. Generate HTML with approved components
    5. Apply chart conversions (table → chart/hybrid)
    6. Enable quiz widgets for selected lists
    7. Enable code execution for selected code blocks
    """
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Apply block edits
    for edit in submission.edits:
        for block in document.blocks:
            if block.id == edit.block_id:
                if edit.new_content is not None:
                    block.content = edit.new_content
                if edit.new_type is not None:
                    block.type = edit.new_type
                break
    
    # Apply PII actions
    for pii_action in submission.pii_actions:
        await handle_pii_action(document_id, pii_action)
    
    # Update document
    document_store.update_document(document_id, blocks=document.blocks)
    
    # Regenerate markdown
    markdown = await markdown_service.build_markdown(document.blocks)
    document_store.store_markdown(document_id, markdown)
    
    # Get suggestions
    suggestions = document_store.get_suggestions(document_id)
    
    # Determine theme
    theme = submission.theme
    if not submission.theme_override:
        theme_analysis = document_store.get_theme_analysis(document_id)
        if theme_analysis and theme_analysis.confidence > 0.7:
            theme = theme_analysis.suggested_theme
    
    # Generate HTML with all interactive features
    try:
        html = await html_generator.generate(
            blocks=document.blocks,
            theme=theme,
            suggestions=suggestions,
            approved_components=submission.approved_components,
            images=document.images,
            chart_conversions=submission.chart_conversions,
            quiz_enabled_blocks=submission.quiz_enabled_blocks,
            code_execution_blocks=submission.code_execution_blocks,
            timeline_blocks=submission.timeline_blocks,
            map_blocks=submission.map_blocks
        )
        
        document_store.store_html(document_id, html)
        
        # Determine which components were injected
        injected = [
            s.suggestion.value for s in suggestions 
            if s.block_id in submission.approved_components
        ]
        
        # Add chart conversion info
        for block_id, option in submission.chart_conversions.items():
            if option != "keep_table":
                injected.append(f"chart_{option}")
        
        # Add quiz/code execution info
        if submission.quiz_enabled_blocks:
            injected.append(f"quiz_widgets:{len(submission.quiz_enabled_blocks)}")
        if submission.code_execution_blocks:
            injected.append(f"code_execution:{len(submission.code_execution_blocks)}")
        
        # Add timeline/map widget info
        if submission.timeline_blocks:
            injected.append(f"timeline_widgets:{len(submission.timeline_blocks)}")
        if submission.map_blocks:
            injected.append(f"map_widgets:{len(submission.map_blocks)}")
        
        logger.info(f"Generated HTML for document {document_id} with theme {theme}")
        
        # Audit log
        await audit_service.log(
            action=AuditAction.HTML_GENERATED,
            document_id=document_id,
            details={
                "theme": theme.value,
                "components_count": len(injected)
            }
        )
        
        # Audit theme change
        theme_analysis = document_store.get_theme_analysis(document_id)
        if theme_analysis:
            await audit_service.log_theme_change(
                document_id=document_id,
                suggested_theme=theme_analysis.suggested_theme.value,
                applied_theme=theme.value,
                was_override=submission.theme_override
            )
        
        # WebSocket notification
        await websocket_service.emit_html_generated(document_id, theme.value, len(injected))
        
        return HTMLGenerationResponse(
            document_id=document_id,
            html=html,
            assets=document.images,
            theme=theme,
            components_injected=injected
        )
        
    except Exception as e:
        logger.error(f"HTML generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"HTML generation failed: {str(e)}")


@router.post("/{document_id}/regenerate-suggestions")
async def regenerate_suggestions(document_id: str):
    """Regenerate semantic suggestions after edits."""
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    suggestions = await ernie_service.analyze_semantics(document.blocks)
    document_store.store_suggestions(document_id, suggestions)
    
    return {
        "suggestions": [s.model_dump() for s in suggestions],
        "total": len(suggestions)
    }


@router.post("/{document_id}/reset")
async def reset_to_original(document_id: str):
    """Reset document to original extracted state."""
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    original_blocks = document_store.get_original_blocks(document_id)
    original_pii = document_store.get_original_pii(document_id)
    
    document_store.update_document(
        document_id,
        blocks=original_blocks,
        pii_redactions=original_pii
    )
    
    # Regenerate markdown
    markdown = await markdown_service.build_markdown(original_blocks, include_metadata=True)
    document_store.store_markdown(document_id, markdown)
    
    logger.info(f"Reset document {document_id} to original state")
    
    return {"message": "Document reset to original state"}


@router.get("/{document_id}/low-confidence")
async def get_low_confidence_blocks(document_id: str, threshold: float = 0.8):
    """
    Get blocks with low OCR confidence for review.
    
    Lightweight Review feature: highlights blocks that need user attention.
    """
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    low_confidence = []
    for block in document.blocks:
        if block.confidence < threshold:
            low_confidence.append({
                "block_id": block.id,
                "content": block.content,
                "type": block.type.value,
                "confidence": block.confidence,
                "page": block.page,
                "needs_review": True
            })
    
    return {
        "document_id": document_id,
        "threshold": threshold,
        "low_confidence_blocks": low_confidence,
        "total_blocks": len(document.blocks),
        "blocks_needing_review": len(low_confidence)
    }


class BulkApproveRequest(BaseModel):
    block_ids: List[str] = None
    approve_all: bool = False


@router.post("/{document_id}/bulk-approve")
async def bulk_approve_blocks(document_id: str, request: BulkApproveRequest):
    """
    Bulk approve blocks (Accept All feature for Lightweight Review).
    
    - approve_all: Approve all blocks regardless of confidence
    - block_ids: Approve specific blocks
    """
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    approved_count = 0
    for block in document.blocks:
        if request.approve_all or (request.block_ids and block.id in request.block_ids):
            block.confidence = 1.0  # Mark as user-verified
            block.metadata["user_approved"] = True
            approved_count += 1
    
    document_store.update_document(document_id, blocks=document.blocks)
    
    return {
        "message": f"Approved {approved_count} blocks",
        "approved_count": approved_count
    }


@router.post("/{document_id}/chart-suggestion/{block_id}")
async def get_chart_suggestion(document_id: str, block_id: str):
    """
    Get chart type suggestion for a specific table block.
    
    Returns suggested chart type (bar, line, pie) based on table content.
    """
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    block = None
    for b in document.blocks:
        if b.id == block_id:
            block = b
            break
    
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    
    if block.type != ContentType.TABLE:
        raise HTTPException(status_code=400, detail="Block is not a table")
    
    # Analyze table for best chart type
    suggestion = await ernie_service.analyze_semantics([block])
    
    if suggestion:
        return {
            "block_id": block_id,
            "suggested_chart": suggestion[0].suggestion.value,
            "confidence": suggestion[0].confidence,
            "options": ["keep_table", "convert_to_chart", "hybrid"]
        }
    
    return {
        "block_id": block_id,
        "suggested_chart": "chart_bar",
        "confidence": 0.5,
        "options": ["keep_table", "convert_to_chart", "hybrid"]
    }


@router.get("/{document_id}/data-sent-to-cloud")
async def get_data_sent_to_cloud(document_id: str):
    """
    Show what data will be sent to ERNIE (transparency feature).
    
    In Secure Mode, shows sanitized content only.
    In Standard Mode, shows full content.
    """
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    markdown = document_store.get_markdown(document_id)
    
    # Calculate what's redacted
    redaction_summary = {}
    for r in document.pii_redactions:
        pii_type = r.pii_type
        if pii_type not in redaction_summary:
            redaction_summary[pii_type] = 0
        redaction_summary[pii_type] += 1
    
    return {
        "document_id": document_id,
        "processing_mode": document.processing_mode.value,
        "is_secure_mode": document.processing_mode.value == "secure",
        "content_to_send": markdown if markdown else "",
        "pii_redacted": redaction_summary,
        "total_redactions": len(document.pii_redactions),
        "images_sent": False,  # Images never sent to cloud
        "raw_pdf_sent": False,  # Raw PDF never sent
        "note": "Only sanitized text structure is sent to ERNIE. Images and raw PDF data remain local."
    }


class AutoConvertRequest(BaseModel):
    """Request for AI Auto-Convert (MCP-style automated processing)."""
    theme: Optional[ThemeType] = None  # None = let AI decide
    auto_charts: bool = True  # Auto-convert tables to charts
    auto_quizzes: bool = True  # Auto-enable quizzes for Q&A lists
    auto_code_execution: bool = False  # Auto-enable code execution
    auto_timeline: bool = True  # Auto-enable timeline widgets
    auto_map: bool = True  # Auto-enable map widgets


@router.post("/{document_id}/auto-convert", response_model=HTMLGenerationResponse)
async def auto_convert(document_id: str, request: AutoConvertRequest = None):
    """
    🤖 AI Auto-Convert Mode (MCP-style processing for Frontend)
    
    This endpoint provides automated processing similar to how an AI assistant
    would use MCP tools. It skips the Co-Design review and automatically:
    
    1. Accepts all OCR results (no manual review)
    2. Keeps all PII redactions (no undo)
    3. Uses AI-suggested theme (or specified theme)
    4. Auto-converts tables to charts based on AI suggestions
    5. Auto-enables quizzes for detected Q&A lists
    6. Auto-enables timeline/map widgets where detected
    
    Use this for:
    - "Quick Convert" button in frontend
    - Batch processing
    - When users want instant results without review
    
    For human-in-the-loop review, use the normal Co-Design flow instead.
    """
    if request is None:
        request = AutoConvertRequest()
    
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    markdown = document_store.get_markdown(document_id)
    if not markdown:
        raise HTTPException(status_code=400, detail="Document not processed yet")
    
    # Get or generate theme analysis
    theme_analysis = document_store.get_theme_analysis(document_id)
    if not theme_analysis:
        theme_analysis = await ernie_service.analyze_theme(markdown)
        document_store.store_theme_analysis(document_id, theme_analysis)
    
    # Determine theme
    theme = request.theme if request.theme else theme_analysis.suggested_theme
    
    # Get or generate semantic suggestions
    suggestions = document_store.get_suggestions(document_id)
    if not suggestions:
        page_images = document_store.get_page_images(document_id)
        suggestions = await ernie_service.analyze_semantics(
            document.blocks,
            page_images=page_images
        )
        document_store.store_suggestions(document_id, suggestions)
    
    # Auto-approve all components based on suggestions
    approved_components = []
    chart_conversions = {}
    quiz_enabled_blocks = []
    code_execution_blocks = []
    timeline_blocks = []
    map_blocks = []
    
    for suggestion in suggestions:
        approved_components.append(suggestion.block_id)
        
        # Auto chart conversion
        if request.auto_charts and suggestion.suggestion.value.startswith("chart_"):
            chart_conversions[suggestion.block_id] = "convert_to_chart"
        
        # Auto quiz
        if request.auto_quizzes and suggestion.suggestion.value == "quiz":
            quiz_enabled_blocks.append(suggestion.block_id)
        
        # Auto code execution
        if request.auto_code_execution and suggestion.suggestion.value in ["code_block", "code_executable"]:
            code_execution_blocks.append(suggestion.block_id)
        
        # Auto timeline
        if request.auto_timeline and suggestion.suggestion.value == "timeline":
            timeline_blocks.append(suggestion.block_id)
        
        # Auto map
        if request.auto_map and suggestion.suggestion.value == "map":
            map_blocks.append(suggestion.block_id)
    
    # Generate HTML
    try:
        html = await html_generator.generate(
            blocks=document.blocks,
            theme=theme,
            suggestions=suggestions,
            approved_components=approved_components,
            images=document.images,
            chart_conversions=chart_conversions,
            quiz_enabled_blocks=quiz_enabled_blocks,
            code_execution_blocks=code_execution_blocks,
            timeline_blocks=timeline_blocks,
            map_blocks=map_blocks
        )
        
        document_store.store_html(document_id, html)
        
        # Build injected components list
        injected = [s.suggestion.value for s in suggestions]
        
        logger.info(f"Auto-converted document {document_id} with theme {theme}")
        
        # Audit log
        await audit_service.log(
            action=AuditAction.HTML_GENERATED,
            document_id=document_id,
            details={
                "mode": "auto_convert",
                "theme": theme.value,
                "components_count": len(injected)
            }
        )
        
        # WebSocket notification
        await websocket_service.emit_html_generated(document_id, theme.value, len(injected))
        
        return HTMLGenerationResponse(
            document_id=document_id,
            html=html,
            assets=document.images,
            theme=theme,
            components_injected=injected
        )
        
    except Exception as e:
        logger.error(f"Auto-convert failed: {e}")
        raise HTTPException(status_code=500, detail=f"Auto-convert failed: {str(e)}")
