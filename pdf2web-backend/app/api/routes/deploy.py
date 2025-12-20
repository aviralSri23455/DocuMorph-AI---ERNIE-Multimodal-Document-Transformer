"""Deployment endpoints for Netlify, S3, and Vercel."""
from fastapi import APIRouter, HTTPException
from loguru import logger
from typing import Optional
from pydantic import BaseModel

from app.models.schemas import ExportResponse
from app.services.document_store import document_store
from app.services.deploy_service import deploy_service

router = APIRouter()

class NetlifyDeployRequest(BaseModel):
    netlify_token: str
    site_name: Optional[str] = None

class S3DeployRequest(BaseModel):
    aws_access_key: str
    aws_secret_key: str
    bucket_name: str
    region: str = "us-east-1"

class VercelDeployRequest(BaseModel):
    vercel_token: str
    project_name: Optional[str] = None


@router.post("/{document_id}/netlify", response_model=ExportResponse)
async def deploy_to_netlify(
    document_id: str,
    request: NetlifyDeployRequest
):
    """
    Deploy HTML to Netlify.
    
    Args:
        document_id: Document ID
        netlify_token: Netlify personal access token
        site_name: Optional site name (auto-generated if not provided)
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
        result = await deploy_service.deploy_to_netlify(
            document_id=document_id,
            html_content=html,
            images=document.images,
            netlify_token=request.netlify_token,
            site_name=request.site_name
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Netlify deployment failed")
        
        logger.info(f"Deployed document {document_id} to Netlify: {result['deploy_url']}")
        
        return ExportResponse(
            document_id=document_id,
            export_type="netlify",
            deploy_url=result["deploy_url"],
            message=f"Successfully deployed to Netlify. Site ID: {result['site_id']}"
        )
        
    except Exception as e:
        logger.error(f"Netlify deployment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


@router.post("/{document_id}/s3", response_model=ExportResponse)
async def deploy_to_s3(
    document_id: str,
    request: S3DeployRequest
):
    """
    Deploy HTML to AWS S3 with static website hosting.
    
    Args:
        document_id: Document ID
        aws_access_key: AWS access key ID
        aws_secret_key: AWS secret access key
        bucket_name: S3 bucket name
        region: AWS region (default: us-east-1)
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
        result = await deploy_service.deploy_to_s3(
            document_id=document_id,
            html_content=html,
            images=document.images,
            aws_access_key=request.aws_access_key,
            aws_secret_key=request.aws_secret_key,
            bucket_name=request.bucket_name,
            region=request.region
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="S3 deployment failed")
        
        logger.info(f"Deployed document {document_id} to S3: {result['website_url']}")
        
        return ExportResponse(
            document_id=document_id,
            export_type="s3",
            deploy_url=result["website_url"],
            message=f"Successfully deployed to S3. Bucket: {result['bucket_name']}"
        )
        
    except Exception as e:
        logger.error(f"S3 deployment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


@router.post("/{document_id}/vercel", response_model=ExportResponse)
async def deploy_to_vercel(
    document_id: str,
    request: VercelDeployRequest
):
    """
    Deploy HTML to Vercel.
    
    Args:
        document_id: Document ID
        vercel_token: Vercel access token
        project_name: Optional project name
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
        result = await deploy_service.deploy_to_vercel(
            document_id=document_id,
            html_content=html,
            images=document.images,
            vercel_token=request.vercel_token,
            project_name=request.project_name
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Vercel deployment failed")
        
        logger.info(f"Deployed document {document_id} to Vercel: {result['deploy_url']}")
        
        return ExportResponse(
            document_id=document_id,
            export_type="vercel",
            deploy_url=result["deploy_url"],
            message=f"Successfully deployed to Vercel. Project ID: {result['project_id']}"
        )
        
    except Exception as e:
        logger.error(f"Vercel deployment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")
