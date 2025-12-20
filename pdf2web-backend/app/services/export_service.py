"""Export Service for packaging and deploying generated HTML."""
import zipfile
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from loguru import logger

from app.config import settings


class ExportService:
    """Service for exporting and deploying HTML packages."""
    
    def __init__(self):
        self.output_dir = settings.output_dir
    
    async def create_html_package(
        self,
        document_id: str,
        html_content: str,
        images: List[str] = None,
        assets: List[str] = None
    ) -> Path:
        """
        Create a downloadable HTML package (zip).
        
        Args:
            document_id: Unique document identifier
            html_content: Generated HTML content
            images: List of image paths to include
            assets: Additional asset paths
            
        Returns:
            Path to the created zip file
        """
        # Create package directory
        package_dir = self.output_dir / document_id
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Write HTML file
        html_path = package_dir / "index.html"
        html_path.write_text(html_content, encoding="utf-8")
        
        # Copy images
        if images:
            images_dir = package_dir / "images"
            images_dir.mkdir(exist_ok=True)
            
            for img_path in images:
                src = Path(img_path)
                if src.exists():
                    dst = images_dir / src.name
                    shutil.copy2(src, dst)
                    
                    # Update image references in HTML
                    html_content = html_content.replace(
                        str(img_path), 
                        f"images/{src.name}"
                    )
            
            # Rewrite HTML with updated paths
            html_path.write_text(html_content, encoding="utf-8")
        
        # Copy additional assets
        if assets:
            assets_dir = package_dir / "assets"
            assets_dir.mkdir(exist_ok=True)
            
            for asset_path in assets:
                src = Path(asset_path)
                if src.exists():
                    shutil.copy2(src, assets_dir / src.name)
        
        # Create zip file
        zip_path = self.output_dir / f"{document_id}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in package_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(package_dir)
                    zipf.write(file_path, arcname)
        
        # Cleanup package directory
        shutil.rmtree(package_dir)
        
        logger.info(f"Created HTML package: {zip_path}")
        return zip_path
    
    async def export_markdown(
        self,
        document_id: str,
        markdown_content: str,
        images: List[str] = None
    ) -> Path:
        """Export sanitized Markdown with images."""
        # Create export directory
        export_dir = self.output_dir / f"{document_id}_markdown"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Write markdown file
        md_path = export_dir / "document.md"
        md_path.write_text(markdown_content, encoding="utf-8")
        
        # Copy images
        if images:
            images_dir = export_dir / "images"
            images_dir.mkdir(exist_ok=True)
            
            for img_path in images:
                src = Path(img_path)
                if src.exists():
                    shutil.copy2(src, images_dir / src.name)
        
        # Create zip
        zip_path = self.output_dir / f"{document_id}_markdown.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in export_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(export_dir)
                    zipf.write(file_path, arcname)
        
        shutil.rmtree(export_dir)
        
        logger.info(f"Exported Markdown: {zip_path}")
        return zip_path
    
    async def deploy_to_github_pages(
        self,
        document_id: str,
        html_content: str,
        repo_name: str,
        github_token: str,
        images: List[str] = None
    ) -> Optional[str]:
        """
        Deploy HTML to GitHub Pages.
        
        Args:
            document_id: Document identifier
            html_content: HTML content to deploy
            repo_name: GitHub repository name
            github_token: GitHub personal access token
            images: Image paths to include
            
        Returns:
            Deployed URL or None if failed
        """
        import httpx
        
        try:
            # Create temporary package
            package_path = await self.create_html_package(
                document_id, html_content, images
            )
            
            # GitHub API setup
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with httpx.AsyncClient() as client:
                # Check if repo exists, create if not
                repo_url = f"https://api.github.com/repos/{repo_name}"
                response = await client.get(repo_url, headers=headers)
                
                if response.status_code == 404:
                    # Create repository
                    create_url = "https://api.github.com/user/repos"
                    repo_data = {
                        "name": repo_name.split("/")[-1],
                        "auto_init": True,
                        "private": False
                    }
                    await client.post(create_url, json=repo_data, headers=headers)
                
                # Read and encode package contents
                import base64
                
                with zipfile.ZipFile(package_path, 'r') as zipf:
                    for file_info in zipf.filelist:
                        content = zipf.read(file_info.filename)
                        encoded = base64.b64encode(content).decode()
                        
                        # Create/update file in repo
                        file_url = f"https://api.github.com/repos/{repo_name}/contents/{file_info.filename}"
                        
                        # Check if file exists
                        existing = await client.get(file_url, headers=headers)
                        sha = existing.json().get("sha") if existing.status_code == 200 else None
                        
                        file_data = {
                            "message": f"Deploy {file_info.filename}",
                            "content": encoded,
                            "branch": "gh-pages"
                        }
                        if sha:
                            file_data["sha"] = sha
                        
                        await client.put(file_url, json=file_data, headers=headers)
                
                # Enable GitHub Pages
                pages_url = f"https://api.github.com/repos/{repo_name}/pages"
                pages_data = {"source": {"branch": "gh-pages", "path": "/"}}
                await client.post(pages_url, json=pages_data, headers=headers)
            
            # Cleanup
            package_path.unlink(missing_ok=True)
            
            # Return deployed URL
            username = repo_name.split("/")[0]
            repo = repo_name.split("/")[-1]
            deployed_url = f"https://{username}.github.io/{repo}/"
            
            logger.info(f"Deployed to GitHub Pages: {deployed_url}")
            return deployed_url
            
        except Exception as e:
            logger.error(f"GitHub Pages deployment failed: {e}")
            return None
    
    async def get_download_url(self, document_id: str, export_type: str) -> Optional[str]:
        """Get download URL for exported file."""
        if export_type == "html":
            file_path = self.output_dir / f"{document_id}.zip"
        elif export_type == "markdown":
            file_path = self.output_dir / f"{document_id}_markdown.zip"
        else:
            return None
        
        if file_path.exists():
            # In production, this would return a proper URL
            return f"/api/export/download/{document_id}/{export_type}"
        
        return None
    
    async def cleanup_old_exports(self, max_age_hours: int = 24):
        """Clean up old export files."""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        
        for file_path in self.output_dir.glob("*.zip"):
            if file_path.stat().st_mtime < cutoff:
                file_path.unlink()
                logger.info(f"Cleaned up old export: {file_path}")


# Singleton instance
export_service = ExportService()
