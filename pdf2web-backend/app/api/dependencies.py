"""API dependencies and utilities."""
from fastapi import HTTPException, Header
from typing import Optional

from app.config import settings


async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key for protected endpoints."""
    if settings.app_env == "development":
        return True
    
    if not x_api_key or x_api_key != settings.secret_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return True


async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user from authorization header (placeholder)."""
    # In production, implement proper authentication
    return {"user_id": "anonymous", "role": "user"}
