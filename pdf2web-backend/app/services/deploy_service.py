"""Deployment Service for Netlify, S3, and Vercel."""
import httpx
import base64
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from loguru import logger

from app.config import settings


class DeployService:
    """Service for deploying HTML to various platforms."""
    
    def __init__(self):
        self._client = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    # ==================== NETLIFY ====================
    async def deploy_to_netlify(
        self,
        document_id: str,
        html_content: str,
        images: List[str] = None,
        netlify_token: str = None,
        site_name: str = None
    ) -> Optional[Dict[str, str]]:
        """
        Deploy HTML to Netlify.
        
        Args:
            document_id: Document identifier
            html_content: HTML content to deploy
            images: Image paths to include
            netlify_token: Netlify personal access token
            site_name: Optional site name (auto-generated if not provided)
            
        Returns:
            Dict with deploy_url, site_id, admin_url or None if failed
        """
        if not netlify_token:
            logger.error("Netlify token not provided")
            return None
        
        headers = {
            "Authorization": f"Bearer {netlify_token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Step 1: Create or get site
            site_id = await self._get_or_create_netlify_site(headers, site_name)
            if not site_id:
                return None
            
            # Step 2: Prepare files for deployment
            files = {"index.html": html_content}
            
            # Add images
            if images:
                for img_path in images:
                    src = Path(img_path)
                    if src.exists():
                        with open(src, "rb") as f:
                            files[f"images/{src.name}"] = base64.b64encode(f.read()).decode()
            
            # Step 3: Create deploy
            deploy_url = f"https://api.netlify.com/api/v1/sites/{site_id}/deploys"
            
            # Calculate file digests for Netlify
            import hashlib
            file_digests = {}
            for path, content in files.items():
                if isinstance(content, str) and not path.startswith("images/"):
                    digest = hashlib.sha1(content.encode()).hexdigest()
                else:
                    digest = hashlib.sha1(base64.b64decode(content) if path.startswith("images/") else content.encode()).hexdigest()
                file_digests[f"/{path}"] = digest
            
            # Create deploy with file list
            deploy_data = {"files": file_digests}
            response = await self.client.post(deploy_url, json=deploy_data, headers=headers)
            
            if response.status_code not in [200, 201]:
                logger.error(f"Netlify deploy creation failed: {response.text}")
                return None
            
            deploy_info = response.json()
            deploy_id = deploy_info["id"]
            required_files = deploy_info.get("required", [])
            
            # Step 4: Upload required files
            for file_path, content in files.items():
                file_hash = file_digests[f"/{file_path}"]
                if file_hash in required_files:
                    upload_url = f"https://api.netlify.com/api/v1/deploys/{deploy_id}/files/{file_path}"
                    file_content = content.encode() if isinstance(content, str) and not file_path.startswith("images/") else base64.b64decode(content) if file_path.startswith("images/") else content.encode()
                    
                    upload_headers = {**headers, "Content-Type": "application/octet-stream"}
                    await self.client.put(upload_url, content=file_content, headers=upload_headers)
            
            logger.info(f"Deployed to Netlify: {deploy_info.get('ssl_url', deploy_info.get('url'))}")
            
            return {
                "deploy_url": deploy_info.get("ssl_url") or deploy_info.get("url"),
                "site_id": site_id,
                "admin_url": deploy_info.get("admin_url"),
                "deploy_id": deploy_id
            }
            
        except Exception as e:
            logger.error(f"Netlify deployment failed: {e}")
            return None
    
    async def _get_or_create_netlify_site(self, headers: dict, site_name: str = None) -> Optional[str]:
        """Get existing site or create new one."""
        try:
            if site_name:
                # Try to find existing site
                sites_url = "https://api.netlify.com/api/v1/sites"
                response = await self.client.get(sites_url, headers=headers)
                if response.status_code == 200:
                    sites = response.json()
                    for site in sites:
                        if site.get("name") == site_name:
                            return site["id"]
            
            # Create new site
            create_url = "https://api.netlify.com/api/v1/sites"
            site_data = {}
            if site_name:
                site_data["name"] = site_name
            
            response = await self.client.post(create_url, json=site_data, headers=headers)
            if response.status_code in [200, 201]:
                return response.json()["id"]
            
            return None
        except Exception as e:
            logger.error(f"Failed to get/create Netlify site: {e}")
            return None
    
    # ==================== AWS S3 ====================
    async def deploy_to_s3(
        self,
        document_id: str,
        html_content: str,
        images: List[str] = None,
        aws_access_key: str = None,
        aws_secret_key: str = None,
        bucket_name: str = None,
        region: str = "us-east-1"
    ) -> Optional[Dict[str, str]]:
        """
        Deploy HTML to AWS S3 with static website hosting.
        
        Args:
            document_id: Document identifier
            html_content: HTML content to deploy
            images: Image paths to include
            aws_access_key: AWS access key ID
            aws_secret_key: AWS secret access key
            bucket_name: S3 bucket name
            region: AWS region
            
        Returns:
            Dict with website_url, bucket_name or None if failed
        """
        if not all([aws_access_key, aws_secret_key, bucket_name]):
            logger.error("AWS credentials or bucket name not provided")
            return None
        
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Create S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=region
            )
            
            # Check if bucket exists, create if not
            try:
                s3_client.head_bucket(Bucket=bucket_name)
            except ClientError:
                # Create bucket
                if region == "us-east-1":
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': region}
                    )
                
                # Enable static website hosting
                s3_client.put_bucket_website(
                    Bucket=bucket_name,
                    WebsiteConfiguration={
                        'IndexDocument': {'Suffix': 'index.html'},
                        'ErrorDocument': {'Key': 'error.html'}
                    }
                )
                
                # Set bucket policy for public access
                bucket_policy = {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{bucket_name}/*"
                    }]
                }
                s3_client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=json.dumps(bucket_policy)
                )
            
            # Upload index.html
            s3_client.put_object(
                Bucket=bucket_name,
                Key="index.html",
                Body=html_content.encode(),
                ContentType="text/html"
            )
            
            # Upload images
            if images:
                for img_path in images:
                    src = Path(img_path)
                    if src.exists():
                        content_type = self._get_content_type(src.suffix)
                        with open(src, "rb") as f:
                            s3_client.put_object(
                                Bucket=bucket_name,
                                Key=f"images/{src.name}",
                                Body=f.read(),
                                ContentType=content_type
                            )
            
            # Get website URL
            website_url = f"http://{bucket_name}.s3-website-{region}.amazonaws.com"
            
            logger.info(f"Deployed to S3: {website_url}")
            
            return {
                "website_url": website_url,
                "bucket_name": bucket_name,
                "region": region
            }
            
        except ImportError:
            logger.error("boto3 not installed. Run: pip install boto3")
            return None
        except Exception as e:
            logger.error(f"S3 deployment failed: {e}")
            return None
    
    # ==================== VERCEL ====================
    async def deploy_to_vercel(
        self,
        document_id: str,
        html_content: str,
        images: List[str] = None,
        vercel_token: str = None,
        project_name: str = None
    ) -> Optional[Dict[str, str]]:
        """
        Deploy HTML to Vercel.
        
        Args:
            document_id: Document identifier
            html_content: HTML content to deploy
            images: Image paths to include
            vercel_token: Vercel access token
            project_name: Optional project name
            
        Returns:
            Dict with deploy_url, project_id or None if failed
        """
        if not vercel_token:
            logger.error("Vercel token not provided")
            return None
        
        headers = {
            "Authorization": f"Bearer {vercel_token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Prepare files
            files = [
                {
                    "file": "index.html",
                    "data": base64.b64encode(html_content.encode()).decode()
                }
            ]
            
            # Add images
            if images:
                for img_path in images:
                    src = Path(img_path)
                    if src.exists():
                        with open(src, "rb") as f:
                            files.append({
                                "file": f"images/{src.name}",
                                "data": base64.b64encode(f.read()).decode()
                            })
            
            # Create deployment
            deploy_url = "https://api.vercel.com/v13/deployments"
            deploy_data = {
                "name": project_name or f"pdf2web-{document_id[:8]}",
                "files": files,
                "projectSettings": {
                    "framework": None
                }
            }
            
            response = await self.client.post(deploy_url, json=deploy_data, headers=headers)
            
            if response.status_code not in [200, 201]:
                logger.error(f"Vercel deployment failed: {response.text}")
                return None
            
            deploy_info = response.json()
            
            logger.info(f"Deployed to Vercel: https://{deploy_info.get('url')}")
            
            return {
                "deploy_url": f"https://{deploy_info.get('url')}",
                "project_id": deploy_info.get("projectId"),
                "deployment_id": deploy_info.get("id"),
                "ready_state": deploy_info.get("readyState")
            }
            
        except Exception as e:
            logger.error(f"Vercel deployment failed: {e}")
            return None
    
    def _get_content_type(self, extension: str) -> str:
        """Get MIME type for file extension."""
        types = {
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".webp": "image/webp"
        }
        return types.get(extension.lower(), "application/octet-stream")


# Singleton instance
deploy_service = DeployService()
