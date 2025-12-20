"""Export endpoints for downloading and deploying generated content."""
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel

from app.models.schemas import ExportResponse
from app.services.document_store import document_store
from app.services.export_service import export_service
from app.config import settings

router = APIRouter()


class GitHubPagesDeployRequest(BaseModel):
    repo_name: str
    github_token: str


@router.post("/{document_id}/html", response_model=ExportResponse)
async def export_html(document_id: str):
    """
    Export document as HTML package (zip).
    
    Creates a downloadable zip containing:
    - index.html
    - images/ folder
    - assets/ folder (if any)
    """
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    html = document_store.get_html(document_id)
    if not html:
        raise HTTPException(
            status_code=400, 
            detail="HTML not generated. Please complete Co-Design first."
        )
    
    try:
        zip_path = await export_service.create_html_package(
            document_id=document_id,
            html_content=html,
            images=document.images
        )
        
        download_url = f"/api/export/download/{document_id}/html"
        
        logger.info(f"Created HTML export for document {document_id}")
        
        return ExportResponse(
            document_id=document_id,
            export_type="html",
            download_url=download_url,
            message="HTML package created successfully"
        )
        
    except Exception as e:
        logger.error(f"HTML export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/{document_id}/markdown", response_model=ExportResponse)
async def export_markdown(document_id: str):
    """
    Export sanitized Markdown with images.
    
    Creates a downloadable zip containing:
    - document.md
    - images/ folder
    """
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    markdown = document_store.get_markdown(document_id)
    if not markdown:
        raise HTTPException(status_code=400, detail="Markdown not available")
    
    try:
        zip_path = await export_service.export_markdown(
            document_id=document_id,
            markdown_content=markdown,
            images=document.images
        )
        
        download_url = f"/api/export/download/{document_id}/markdown"
        
        logger.info(f"Created Markdown export for document {document_id}")
        
        return ExportResponse(
            document_id=document_id,
            export_type="markdown",
            download_url=download_url,
            message="Markdown package created successfully"
        )
        
    except Exception as e:
        logger.error(f"Markdown export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/download/{document_id}/{export_type}")
async def download_export(document_id: str, export_type: str):
    """Download an exported file."""
    if export_type == "html":
        file_path = settings.output_dir / f"{document_id}.zip"
    elif export_type == "markdown":
        file_path = settings.output_dir / f"{document_id}_markdown.zip"
    else:
        raise HTTPException(status_code=400, detail="Invalid export type")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export file not found")
    
    document = document_store.get_document(document_id)
    filename = document.filename.replace(".pdf", "") if document else document_id
    
    return FileResponse(
        path=file_path,
        filename=f"{filename}_{export_type}.zip",
        media_type="application/zip"
    )


@router.post("/{document_id}/github-pages", response_model=ExportResponse)
async def deploy_to_github(
    document_id: str,
    request: GitHubPagesDeployRequest
):
    """
    Deploy HTML to GitHub Pages.
    
    Requires:
    - repo_name: GitHub repository (username/repo)
    - github_token: Personal access token with repo permissions
    """
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    html = document_store.get_html(document_id)
    if not html:
        raise HTTPException(
            status_code=400,
            detail="HTML not generated. Please complete Co-Design first."
        )
    
    try:
        deploy_url = await export_service.deploy_to_github_pages(
            document_id=document_id,
            html_content=html,
            repo_name=request.repo_name,
            github_token=request.github_token,
            images=document.images
        )
        
        if not deploy_url:
            raise HTTPException(status_code=500, detail="Deployment failed")
        
        logger.info(f"Deployed document {document_id} to GitHub Pages: {deploy_url}")
        
        return ExportResponse(
            document_id=document_id,
            export_type="github_pages",
            deploy_url=deploy_url,
            message="Successfully deployed to GitHub Pages"
        )
        
    except Exception as e:
        logger.error(f"GitHub Pages deployment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


@router.get("/{document_id}/preview-html")
async def preview_html(document_id: str):
    """Get raw HTML for preview (without downloading)."""
    html = document_store.get_html(document_id)
    if not html:
        raise HTTPException(
            status_code=404,
            detail="HTML not generated. Please complete Co-Design first."
        )
    
    return {"html": html}


@router.delete("/{document_id}/cleanup")
async def cleanup_exports(document_id: str):
    """Clean up exported files for a document."""
    html_zip = settings.output_dir / f"{document_id}.zip"
    md_zip = settings.output_dir / f"{document_id}_markdown.zip"
    
    deleted = []
    if html_zip.exists():
        html_zip.unlink()
        deleted.append("html")
    if md_zip.exists():
        md_zip.unlink()
        deleted.append("markdown")
    
    return {"message": f"Cleaned up exports: {deleted}" if deleted else "No exports to clean"}
