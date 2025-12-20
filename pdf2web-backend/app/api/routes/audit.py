"""Audit logging endpoints."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from loguru import logger
from typing import Optional, List

from app.services.audit_service import audit_service, AuditAction, AuditEntry
from app.config import settings

router = APIRouter()


@router.get("/")
async def get_audit_entries(
    limit: int = Query(50, ge=1, le=500),
    action: Optional[str] = Query(None, description="Filter by action type")
):
    """
    Get recent audit log entries.
    
    Args:
        limit: Maximum number of entries to return
        action: Optional action type filter
    """
    if not settings.enable_audit_log:
        raise HTTPException(status_code=400, detail="Audit logging is disabled")
    
    action_filter = None
    if action:
        try:
            action_filter = AuditAction(action)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid action type: {action}")
    
    entries = await audit_service.get_recent_entries(limit, action_filter)
    
    return {
        "entries": [e.model_dump() for e in entries],
        "total": len(entries),
        "limit": limit
    }


@router.get("/document/{document_id}")
async def get_document_audit_trail(
    document_id: str,
    limit: int = Query(100, ge=1, le=500)
):
    """
    Get audit trail for a specific document.
    
    Args:
        document_id: Document ID
        limit: Maximum number of entries to return
    """
    if not settings.enable_audit_log:
        raise HTTPException(status_code=400, detail="Audit logging is disabled")
    
    entries = await audit_service.get_document_audit_trail(document_id, limit)
    
    return {
        "document_id": document_id,
        "entries": [e.model_dump() for e in entries],
        "total": len(entries)
    }


@router.get("/export")
async def export_audit_log(
    document_id: Optional[str] = Query(None),
    format: str = Query("json", regex="^(json|csv)$")
):
    """
    Export audit log as JSON or CSV.
    
    Args:
        document_id: Optional document ID filter
        format: Export format (json or csv)
    """
    if not settings.enable_audit_log:
        raise HTTPException(status_code=400, detail="Audit logging is disabled")
    
    json_export = await audit_service.export_audit_log(document_id)
    
    if format == "csv":
        import json
        entries = json.loads(json_export)
        
        if not entries:
            return PlainTextResponse("No entries found", media_type="text/csv")
        
        # Build CSV
        headers = ["id", "timestamp", "action", "document_id", "user_id"]
        csv_lines = [",".join(headers)]
        
        for entry in entries:
            row = [
                entry.get("id", ""),
                entry.get("timestamp", ""),
                entry.get("action", ""),
                entry.get("document_id", ""),
                entry.get("user_id", "")
            ]
            csv_lines.append(",".join(str(v) for v in row))
        
        return PlainTextResponse("\n".join(csv_lines), media_type="text/csv")
    
    return PlainTextResponse(json_export, media_type="application/json")


@router.get("/actions")
async def list_audit_actions():
    """List all available audit action types."""
    return {
        "actions": [a.value for a in AuditAction]
    }


@router.post("/cleanup")
async def cleanup_old_logs():
    """Clean up old audit logs based on retention policy."""
    if not settings.enable_audit_log:
        raise HTTPException(status_code=400, detail="Audit logging is disabled")
    
    await audit_service.cleanup_old_logs()
    
    return {
        "message": f"Cleaned up logs older than {settings.audit_log_retention_days} days"
    }


@router.get("/stats")
async def get_audit_stats():
    """Get audit log statistics."""
    if not settings.enable_audit_log:
        raise HTTPException(status_code=400, detail="Audit logging is disabled")
    
    entries = await audit_service.get_recent_entries(1000)
    
    # Count by action type
    action_counts = {}
    for entry in entries:
        action = entry.action.value
        action_counts[action] = action_counts.get(action, 0) + 1
    
    # Count by document
    doc_counts = {}
    for entry in entries:
        if entry.document_id:
            doc_counts[entry.document_id] = doc_counts.get(entry.document_id, 0) + 1
    
    return {
        "total_entries": len(entries),
        "by_action": action_counts,
        "documents_tracked": len(doc_counts),
        "retention_days": settings.audit_log_retention_days
    }
