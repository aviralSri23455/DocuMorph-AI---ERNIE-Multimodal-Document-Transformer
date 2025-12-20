"""Accessibility validation and enhancement endpoints."""
from fastapi import APIRouter, HTTPException, Body, Query
from loguru import logger
from typing import Optional

from app.services.accessibility_service import accessibility_service, WCAGLevel
from app.services.document_store import document_store
from app.config import settings

router = APIRouter()


@router.post("/validate")
async def validate_html(
    html: str = Body(..., embed=True),
    wcag_level: str = Query("AA", regex="^(A|AA|AAA)$")
):
    """
    Validate HTML for WCAG accessibility compliance.
    
    Args:
        html: HTML content to validate
        wcag_level: WCAG compliance level (A, AA, or AAA)
    
    Returns:
        Accessibility report with issues and score
    """
    if not settings.enable_accessibility_checks:
        raise HTTPException(status_code=400, detail="Accessibility checks are disabled")
    
    # Temporarily set WCAG level
    original_level = accessibility_service.wcag_level
    accessibility_service.wcag_level = WCAGLevel(wcag_level)
    
    try:
        report = await accessibility_service.validate_html(html)
        
        return {
            "passed": report.passed,
            "wcag_level": report.wcag_level.value,
            "score": report.score,
            "summary": report.summary,
            "issues": [
                {
                    "rule_id": i.rule_id,
                    "severity": i.severity,
                    "message": i.message,
                    "element": i.element,
                    "suggestion": i.suggestion,
                    "wcag_criteria": i.wcag_criteria
                }
                for i in report.issues
            ]
        }
    finally:
        accessibility_service.wcag_level = original_level


@router.post("/validate/{document_id}")
async def validate_document(
    document_id: str,
    wcag_level: str = Query("AA", regex="^(A|AA|AAA)$")
):
    """
    Validate a document's generated HTML for accessibility.
    
    Args:
        document_id: Document ID
        wcag_level: WCAG compliance level
    """
    if not settings.enable_accessibility_checks:
        raise HTTPException(status_code=400, detail="Accessibility checks are disabled")
    
    html = document_store.get_html(document_id)
    if not html:
        raise HTTPException(
            status_code=404,
            detail="HTML not found. Generate HTML first."
        )
    
    original_level = accessibility_service.wcag_level
    accessibility_service.wcag_level = WCAGLevel(wcag_level)
    
    try:
        report = await accessibility_service.validate_html(html)
        
        return {
            "document_id": document_id,
            "passed": report.passed,
            "wcag_level": report.wcag_level.value,
            "score": report.score,
            "summary": report.summary,
            "issues": [i.model_dump() for i in report.issues]
        }
    finally:
        accessibility_service.wcag_level = original_level


@router.post("/enhance")
async def enhance_html(
    html: str = Body(..., embed=True)
):
    """
    Enhance HTML with accessibility features.
    
    Adds:
    - Skip links
    - ARIA labels
    - Focus indicators
    - High contrast support
    - Keyboard navigation styles
    
    Args:
        html: HTML content to enhance
    
    Returns:
        Enhanced HTML
    """
    enhanced = await accessibility_service.enhance_html(html)
    
    return {
        "html": enhanced,
        "enhancements_applied": [
            "skip_links" if settings.enable_skip_links else None,
            "aria_labels" if settings.auto_aria_labels else None,
            "keyboard_navigation" if settings.keyboard_navigation else None,
            "high_contrast" if settings.support_high_contrast else None
        ]
    }


@router.post("/enhance/{document_id}")
async def enhance_document(document_id: str):
    """
    Enhance a document's HTML with accessibility features.
    
    Args:
        document_id: Document ID
    """
    html = document_store.get_html(document_id)
    if not html:
        raise HTTPException(
            status_code=404,
            detail="HTML not found. Generate HTML first."
        )
    
    enhanced = await accessibility_service.enhance_html(html)
    
    # Store enhanced HTML
    document_store.store_html(document_id, enhanced)
    
    logger.info(f"Enhanced accessibility for document {document_id}")
    
    return {
        "document_id": document_id,
        "message": "HTML enhanced with accessibility features",
        "enhancements_applied": [
            "skip_links" if settings.enable_skip_links else None,
            "aria_labels" if settings.auto_aria_labels else None,
            "keyboard_navigation" if settings.keyboard_navigation else None,
            "high_contrast" if settings.support_high_contrast else None
        ]
    }


@router.get("/rules")
async def list_accessibility_rules():
    """List all accessibility validation rules."""
    rules = accessibility_service._rules
    
    return {
        "rules": [
            {
                "id": rule_id,
                "level": rule_data["level"].value,
                "severity": rule_data["severity"],
                "message": rule_data["message"],
                "wcag": rule_data.get("wcag")
            }
            for rule_id, rule_data in rules.items()
        ],
        "total": len(rules)
    }


@router.get("/settings")
async def get_accessibility_settings():
    """Get current accessibility settings."""
    return {
        "enabled": settings.enable_accessibility_checks,
        "wcag_level": settings.wcag_level,
        "auto_aria_labels": settings.auto_aria_labels,
        "support_high_contrast": settings.support_high_contrast,
        "screen_reader_optimized": settings.screen_reader_optimized,
        "keyboard_navigation": settings.keyboard_navigation,
        "enable_skip_links": settings.enable_skip_links
    }


@router.get("/wcag-levels")
async def list_wcag_levels():
    """List available WCAG compliance levels."""
    return {
        "levels": ["A", "AA", "AAA"]
    }
