"""WebSocket Service for real-time updates."""
import json
import asyncio
from typing import Dict, Set, Optional, Any
from datetime import datetime
from enum import Enum
from loguru import logger
from fastapi import WebSocket, WebSocketDisconnect

from app.config import settings


class WSEventType(str, Enum):
    """WebSocket event types."""
    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    
    # Processing events
    PROCESSING_STARTED = "processing_started"
    PROCESSING_PROGRESS = "processing_progress"
    PROCESSING_COMPLETED = "processing_completed"
    PROCESSING_ERROR = "processing_error"
    
    # OCR events
    OCR_PAGE_STARTED = "ocr_page_started"
    OCR_PAGE_COMPLETED = "ocr_page_completed"
    OCR_COMPLETED = "ocr_completed"
    
    # PII events
    PII_SCAN_STARTED = "pii_scan_started"
    PII_DETECTED = "pii_detected"
    PII_SCAN_COMPLETED = "pii_scan_completed"
    
    # Co-Design events
    BLOCK_UPDATED = "block_updated"
    THEME_ANALYZED = "theme_analyzed"
    SUGGESTIONS_READY = "suggestions_ready"
    
    # Generation events
    HTML_GENERATION_STARTED = "html_generation_started"
    HTML_GENERATION_PROGRESS = "html_generation_progress"
    HTML_GENERATION_COMPLETED = "html_generation_completed"
    
    # Export events
    EXPORT_STARTED = "export_started"
    EXPORT_COMPLETED = "export_completed"
    DEPLOY_STARTED = "deploy_started"
    DEPLOY_COMPLETED = "deploy_completed"


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        # document_id -> set of websockets
        self._document_connections: Dict[str, Set[WebSocket]] = {}
        # All active connections
        self._active_connections: Set[WebSocket] = set()
        # Connection metadata
        self._connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        document_id: str = None,
        client_id: str = None
    ):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        self._active_connections.add(websocket)
        
        # Store connection info
        self._connection_info[websocket] = {
            "document_id": document_id,
            "client_id": client_id,
            "connected_at": datetime.now().isoformat()
        }
        
        # Register for document updates
        if document_id:
            if document_id not in self._document_connections:
                self._document_connections[document_id] = set()
            self._document_connections[document_id].add(websocket)
        
        logger.info(f"WebSocket connected: client={client_id}, doc={document_id}")
        
        # Send connection confirmation
        await self.send_personal(websocket, WSEventType.CONNECTED, {
            "message": "Connected to PDF2Web real-time updates",
            "document_id": document_id
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self._active_connections.discard(websocket)
        
        # Remove from document connections
        info = self._connection_info.pop(websocket, {})
        document_id = info.get("document_id")
        
        if document_id and document_id in self._document_connections:
            self._document_connections[document_id].discard(websocket)
            if not self._document_connections[document_id]:
                del self._document_connections[document_id]
        
        logger.info(f"WebSocket disconnected: doc={document_id}")
    
    async def send_personal(
        self,
        websocket: WebSocket,
        event_type: WSEventType,
        data: Dict[str, Any]
    ):
        """Send message to a specific connection."""
        try:
            message = {
                "event": event_type.value,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
    
    async def broadcast_to_document(
        self,
        document_id: str,
        event_type: WSEventType,
        data: Dict[str, Any]
    ):
        """Broadcast message to all connections watching a document."""
        connections = self._document_connections.get(document_id, set())
        
        message = {
            "event": event_type.value,
            "timestamp": datetime.now().isoformat(),
            "document_id": document_id,
            "data": data
        }
        
        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        # Clean up disconnected
        for ws in disconnected:
            self.disconnect(ws)
    
    async def broadcast_all(
        self,
        event_type: WSEventType,
        data: Dict[str, Any]
    ):
        """Broadcast message to all connections."""
        message = {
            "event": event_type.value,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        disconnected = []
        for websocket in self._active_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        for ws in disconnected:
            self.disconnect(ws)
    
    def get_connection_count(self, document_id: str = None) -> int:
        """Get number of active connections."""
        if document_id:
            return len(self._document_connections.get(document_id, set()))
        return len(self._active_connections)


class WebSocketService:
    """Service for managing real-time WebSocket updates."""
    
    def __init__(self):
        self.manager = ConnectionManager()
        self._enabled = settings.enable_websocket
    
    async def connect(
        self,
        websocket: WebSocket,
        document_id: str = None,
        client_id: str = None
    ):
        """Handle new WebSocket connection."""
        if not self._enabled:
            await websocket.close(code=1000, reason="WebSocket disabled")
            return
        
        await self.manager.connect(websocket, document_id, client_id)
    
    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection."""
        self.manager.disconnect(websocket)
    
    async def handle_message(
        self,
        websocket: WebSocket,
        message: str
    ):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            action = data.get("action")
            
            if action == "subscribe":
                # Subscribe to document updates
                document_id = data.get("document_id")
                if document_id:
                    info = self.manager._connection_info.get(websocket, {})
                    old_doc = info.get("document_id")
                    
                    # Unsubscribe from old document
                    if old_doc and old_doc in self.manager._document_connections:
                        self.manager._document_connections[old_doc].discard(websocket)
                    
                    # Subscribe to new document
                    if document_id not in self.manager._document_connections:
                        self.manager._document_connections[document_id] = set()
                    self.manager._document_connections[document_id].add(websocket)
                    info["document_id"] = document_id
                    
                    await self.manager.send_personal(websocket, WSEventType.CONNECTED, {
                        "message": f"Subscribed to document {document_id}"
                    })
            
            elif action == "ping":
                await self.manager.send_personal(websocket, WSEventType.CONNECTED, {
                    "message": "pong"
                })
                
        except json.JSONDecodeError:
            logger.warning("Invalid WebSocket message format")
    
    # ==================== Event Emitters ====================
    
    async def emit_processing_started(self, document_id: str, filename: str):
        """Emit processing started event."""
        await self.manager.broadcast_to_document(
            document_id,
            WSEventType.PROCESSING_STARTED,
            {"filename": filename, "status": "started"}
        )
    
    async def emit_processing_progress(
        self,
        document_id: str,
        stage: str,
        progress: float,
        message: str = None
    ):
        """Emit processing progress event."""
        await self.manager.broadcast_to_document(
            document_id,
            WSEventType.PROCESSING_PROGRESS,
            {
                "stage": stage,
                "progress": progress,
                "message": message
            }
        )
    
    async def emit_ocr_progress(
        self,
        document_id: str,
        current_page: int,
        total_pages: int,
        blocks_found: int = 0
    ):
        """Emit OCR progress event."""
        await self.manager.broadcast_to_document(
            document_id,
            WSEventType.OCR_PAGE_COMPLETED,
            {
                "current_page": current_page,
                "total_pages": total_pages,
                "progress": current_page / total_pages,
                "blocks_found": blocks_found
            }
        )
    
    async def emit_pii_detected(
        self,
        document_id: str,
        pii_count: int,
        pii_types: Dict[str, int]
    ):
        """Emit PII detection event."""
        await self.manager.broadcast_to_document(
            document_id,
            WSEventType.PII_DETECTED,
            {
                "total_count": pii_count,
                "by_type": pii_types
            }
        )
    
    async def emit_suggestions_ready(
        self,
        document_id: str,
        suggestion_count: int,
        suggestions_summary: Dict[str, int]
    ):
        """Emit suggestions ready event."""
        await self.manager.broadcast_to_document(
            document_id,
            WSEventType.SUGGESTIONS_READY,
            {
                "count": suggestion_count,
                "summary": suggestions_summary
            }
        )
    
    async def emit_block_updated(
        self,
        document_id: str,
        block_id: str,
        update_type: str
    ):
        """Emit block updated event."""
        await self.manager.broadcast_to_document(
            document_id,
            WSEventType.BLOCK_UPDATED,
            {
                "block_id": block_id,
                "update_type": update_type
            }
        )
    
    async def emit_html_generated(
        self,
        document_id: str,
        theme: str,
        components_count: int
    ):
        """Emit HTML generation completed event."""
        await self.manager.broadcast_to_document(
            document_id,
            WSEventType.HTML_GENERATION_COMPLETED,
            {
                "theme": theme,
                "components_injected": components_count,
                "status": "completed"
            }
        )
    
    async def emit_deploy_completed(
        self,
        document_id: str,
        platform: str,
        deploy_url: str
    ):
        """Emit deployment completed event."""
        await self.manager.broadcast_to_document(
            document_id,
            WSEventType.DEPLOY_COMPLETED,
            {
                "platform": platform,
                "deploy_url": deploy_url,
                "status": "completed"
            }
        )
    
    async def emit_error(
        self,
        document_id: str,
        error_message: str,
        stage: str = None
    ):
        """Emit error event."""
        await self.manager.broadcast_to_document(
            document_id,
            WSEventType.PROCESSING_ERROR,
            {
                "error": error_message,
                "stage": stage
            }
        )


# Singleton instance
websocket_service = WebSocketService()
