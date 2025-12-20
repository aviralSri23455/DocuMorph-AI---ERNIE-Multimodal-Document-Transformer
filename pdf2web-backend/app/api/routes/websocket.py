"""WebSocket endpoints for real-time updates."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from loguru import logger
from typing import Optional

from app.services.websocket_service import websocket_service

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    document_id: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time updates.
    
    Query params:
        document_id: Optional document ID to subscribe to
        client_id: Optional client identifier
    
    Messages:
        - Subscribe to document: {"action": "subscribe", "document_id": "..."}
        - Ping: {"action": "ping"}
    
    Events received:
        - processing_started, processing_progress, processing_completed
        - ocr_page_started, ocr_page_completed, ocr_completed
        - pii_scan_started, pii_detected, pii_scan_completed
        - block_updated, theme_analyzed, suggestions_ready
        - html_generation_started, html_generation_completed
        - export_started, export_completed
        - deploy_started, deploy_completed
        - processing_error
    """
    await websocket_service.connect(websocket, document_id, client_id)
    
    try:
        while True:
            # Receive and handle messages
            data = await websocket.receive_text()
            await websocket_service.handle_message(websocket, data)
            
    except WebSocketDisconnect:
        websocket_service.disconnect(websocket)
        logger.info(f"WebSocket disconnected: doc={document_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_service.disconnect(websocket)


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status."""
    return {
        "enabled": websocket_service._enabled,
        "total_connections": websocket_service.manager.get_connection_count()
    }


@router.get("/ws/connections/{document_id}")
async def document_connections(document_id: str):
    """Get number of connections watching a document."""
    count = websocket_service.manager.get_connection_count(document_id)
    return {
        "document_id": document_id,
        "connections": count,
        "connection_count": count  # Alias for compatibility
    }
