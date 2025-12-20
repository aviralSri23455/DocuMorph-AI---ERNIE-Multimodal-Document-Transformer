"""Audit Logging Service for Co-Design actions."""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum
from loguru import logger
from pydantic import BaseModel

from app.config import settings


class AuditAction(str, Enum):
    """Types of auditable actions."""
    # Document actions
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DELETE = "document_delete"
    
    # PII actions
    PII_DETECTED = "pii_detected"
    PII_REDACTION_APPROVED = "pii_redaction_approved"
    PII_REDACTION_UNDONE = "pii_redaction_undone"
    PII_REDACTION_MODIFIED = "pii_redaction_modified"
    
    # Block edit actions
    BLOCK_CONTENT_EDITED = "block_content_edited"
    BLOCK_TYPE_CHANGED = "block_type_changed"
    BLOCK_APPROVED = "block_approved"
    BLOCKS_BULK_APPROVED = "blocks_bulk_approved"
    
    # Theme actions
    THEME_SUGGESTED = "theme_suggested"
    THEME_OVERRIDDEN = "theme_overridden"
    THEME_APPLIED = "theme_applied"
    
    # Component actions
    COMPONENT_SUGGESTED = "component_suggested"
    COMPONENT_APPROVED = "component_approved"
    CHART_CONVERSION = "chart_conversion"
    QUIZ_ENABLED = "quiz_enabled"
    CODE_EXECUTION_ENABLED = "code_execution_enabled"
    
    # Export actions
    HTML_GENERATED = "html_generated"
    EXPORT_CREATED = "export_created"
    DEPLOYED = "deployed"
    
    # Session actions
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"


class AuditEntry(BaseModel):
    """Single audit log entry."""
    id: str
    timestamp: str
    action: AuditAction
    document_id: Optional[str] = None
    user_id: Optional[str] = None
    details: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class AuditService:
    """Service for audit logging with local storage."""
    
    def __init__(self):
        self.log_dir = settings.audit_log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._memory_log: List[AuditEntry] = []
        self._max_memory_entries = 1000
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp based on settings."""
        now = datetime.now()
        if settings.timestamp_format == "unix":
            return str(int(now.timestamp()))
        elif settings.timestamp_format == "human":
            return now.strftime("%Y-%m-%d %H:%M:%S")
        else:  # iso
            return now.isoformat()
    
    def _generate_id(self) -> str:
        """Generate unique audit entry ID."""
        import uuid
        return str(uuid.uuid4())
    
    async def log(
        self,
        action: AuditAction,
        document_id: str = None,
        user_id: str = None,
        details: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> AuditEntry:
        """
        Log an audit entry.
        
        Args:
            action: Type of action being logged
            document_id: Associated document ID
            user_id: User performing the action
            details: Action-specific details
            metadata: Additional metadata
            
        Returns:
            Created AuditEntry
        """
        if not settings.enable_audit_log:
            return None
        
        entry = AuditEntry(
            id=self._generate_id(),
            timestamp=self._get_timestamp(),
            action=action,
            document_id=document_id,
            user_id=user_id,
            details=details or {},
            metadata=metadata or {}
        )
        
        # Store in memory
        self._memory_log.append(entry)
        if len(self._memory_log) > self._max_memory_entries:
            self._memory_log = self._memory_log[-self._max_memory_entries:]
        
        # Write to file (append mode)
        await self._write_to_file(entry)
        
        logger.debug(f"Audit: {action.value} - doc:{document_id}")
        return entry
    
    async def _write_to_file(self, entry: AuditEntry):
        """Write audit entry to daily log file."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"audit_{date_str}.jsonl"
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    async def log_pii_action(
        self,
        document_id: str,
        action_type: str,
        redaction_id: str,
        pii_type: str,
        original_value: str = None,
        new_value: str = None
    ):
        """Log PII-related action."""
        if not settings.track_pii_actions:
            return
        
        action_map = {
            "approve": AuditAction.PII_REDACTION_APPROVED,
            "undo": AuditAction.PII_REDACTION_UNDONE,
            "modify": AuditAction.PII_REDACTION_MODIFIED
        }
        
        await self.log(
            action=action_map.get(action_type, AuditAction.PII_REDACTION_APPROVED),
            document_id=document_id,
            details={
                "redaction_id": redaction_id,
                "pii_type": pii_type,
                "original_masked": original_value[:3] + "***" if original_value else None,
                "new_value_set": new_value is not None
            }
        )
    
    async def log_block_edit(
        self,
        document_id: str,
        block_id: str,
        edit_type: str,
        old_value: str = None,
        new_value: str = None
    ):
        """Log block edit action."""
        if not settings.track_block_edits:
            return
        
        action = AuditAction.BLOCK_CONTENT_EDITED if edit_type == "content" else AuditAction.BLOCK_TYPE_CHANGED
        
        await self.log(
            action=action,
            document_id=document_id,
            details={
                "block_id": block_id,
                "edit_type": edit_type,
                "old_value_length": len(old_value) if old_value else 0,
                "new_value_length": len(new_value) if new_value else 0
            }
        )
    
    async def log_theme_change(
        self,
        document_id: str,
        suggested_theme: str,
        applied_theme: str,
        was_override: bool
    ):
        """Log theme-related action."""
        if not settings.track_theme_changes:
            return
        
        action = AuditAction.THEME_OVERRIDDEN if was_override else AuditAction.THEME_APPLIED
        
        await self.log(
            action=action,
            document_id=document_id,
            details={
                "suggested_theme": suggested_theme,
                "applied_theme": applied_theme,
                "was_override": was_override
            }
        )
    
    async def get_document_audit_trail(
        self,
        document_id: str,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Get audit trail for a specific document."""
        entries = [e for e in self._memory_log if e.document_id == document_id]
        return entries[-limit:]
    
    async def get_recent_entries(
        self,
        limit: int = 50,
        action_filter: AuditAction = None
    ) -> List[AuditEntry]:
        """Get recent audit entries."""
        entries = self._memory_log
        if action_filter:
            entries = [e for e in entries if e.action == action_filter]
        return entries[-limit:]
    
    async def export_audit_log(
        self,
        document_id: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> str:
        """Export audit log as JSON."""
        entries = self._memory_log
        
        if document_id:
            entries = [e for e in entries if e.document_id == document_id]
        
        return json.dumps([e.model_dump() for e in entries], indent=2)
    
    async def cleanup_old_logs(self):
        """Remove audit logs older than retention period."""
        retention_days = settings.audit_log_retention_days
        cutoff = datetime.now().timestamp() - (retention_days * 24 * 3600)
        
        for log_file in self.log_dir.glob("audit_*.jsonl"):
            if log_file.stat().st_mtime < cutoff:
                log_file.unlink()
                logger.info(f"Cleaned up old audit log: {log_file}")


# Singleton instance
audit_service = AuditService()
