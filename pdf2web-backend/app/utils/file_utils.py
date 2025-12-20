"""File handling utilities."""
import hashlib
from pathlib import Path
from typing import Optional
import aiofiles


async def save_upload_file(content: bytes, filename: str, upload_dir: Path) -> Path:
    """Save uploaded file content to disk."""
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_hash = hashlib.md5(content[:1024]).hexdigest()[:8]
    safe_filename = f"{file_hash}_{filename}"
    file_path = upload_dir / safe_filename
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    return file_path


def get_file_extension(filename: str) -> str:
    """Get file extension in lowercase."""
    return Path(filename).suffix.lower()


def is_valid_pdf(content: bytes) -> bool:
    """Check if content is a valid PDF."""
    return content[:4] == b'%PDF'


def get_file_size_mb(content: bytes) -> float:
    """Get file size in megabytes."""
    return len(content) / (1024 * 1024)


async def read_file_content(file_path: Path) -> Optional[bytes]:
    """Read file content asynchronously."""
    if not file_path.exists():
        return None
    
    async with aiofiles.open(file_path, 'rb') as f:
        return await f.read()


def cleanup_temp_files(directory: Path, pattern: str = "*"):
    """Clean up temporary files matching pattern."""
    for file_path in directory.glob(pattern):
        if file_path.is_file():
            file_path.unlink()
