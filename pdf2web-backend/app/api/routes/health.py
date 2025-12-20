"""Health check endpoints."""
from fastapi import APIRouter
from loguru import logger

from app.models.schemas import HealthResponse
from app.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check application health and service availability."""
    services = {
        "ocr": _check_ocr_service(),
        "pii": _check_pii_service(),
        "ernie": _check_ernie_service()
    }
    
    return HealthResponse(
        status="healthy" if all(services.values()) else "degraded",
        version="1.0.0",
        services=services
    )


def _check_ocr_service() -> bool:
    """Check if OCR service is available."""
    try:
        from paddleocr import PaddleOCR
        return True
    except ImportError:
        return False


def _check_pii_service() -> bool:
    """Check if PII service is available."""
    try:
        from presidio_analyzer import AnalyzerEngine
        return True
    except ImportError:
        return False


def _check_ernie_service() -> bool:
    """Check if ERNIE API is configured (Novita AI or Baidu)."""
    return bool(settings.ernie_api_key or settings.ernie_access_token)


@router.get("/health/ernie")
async def ernie_health_check():
    """Check ERNIE/LLM API connectivity and configuration."""
    try:
        configured = _check_ernie_service()
        
        # Safely get settings values
        model = None
        api_url = None
        vision_enabled = False
        vision_model = None
        
        if configured:
            try:
                model = settings.ernie_model
                api_url = settings.ernie_api_url
                vision_enabled = settings.enable_vision_analysis
                vision_model = settings.ernie_vision_model
            except Exception as e:
                logger.warning(f"Error reading ERNIE settings: {e}")
        
        return {
            "service": "ernie",
            "configured": configured,
            "model": model,
            "api_url": api_url,
            "vision_enabled": vision_enabled and configured,
            "vision_model": vision_model,
            "status": "ready" if configured else "not_configured",
            "message": "LLM API configured" + (" with vision support" if vision_enabled else "") if configured else "API key or access token not set"
        }
    except Exception as e:
        logger.error(f"ERNIE health check error: {e}")
        return {
            "service": "ernie",
            "configured": False,
            "model": None,
            "api_url": None,
            "vision_enabled": False,
            "vision_model": None,
            "status": "error",
            "message": f"Health check error: {str(e)}"
        }


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs"
    }
