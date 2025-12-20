"""Input validation utilities."""
import re
from typing import Optional


def validate_document_id(document_id: str) -> bool:
    """Validate document ID format (UUID)."""
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(document_id))


def validate_github_repo(repo_name: str) -> bool:
    """Validate GitHub repository name format."""
    # Format: username/repo-name
    pattern = re.compile(r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+$')
    return bool(pattern.match(repo_name))


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove path separators and special characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(sanitized) > 200:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        sanitized = name[:195] + ('.' + ext if ext else '')
    return sanitized


def validate_language_code(code: str) -> bool:
    """Validate language code."""
    valid_codes = ['en', 'ch', 'french', 'german', 'korean', 'japan', 'chinese_cht']
    return code.lower() in valid_codes


def validate_theme(theme: str) -> bool:
    """Validate theme name."""
    valid_themes = ['light', 'dark', 'professional', 'academic', 'minimal']
    return theme.lower() in valid_themes
