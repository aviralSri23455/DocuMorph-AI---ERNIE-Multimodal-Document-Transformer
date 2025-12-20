"""MCP (Model Context Protocol) Server endpoints."""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from typing import Dict, Any
import json
import asyncio

from app.services.mcp_service import mcp_service
from app.config import settings

router = APIRouter()


@router.get("/info")
async def get_server_info():
    """Get MCP server information."""
    if not settings.enable_mcp_server:
        raise HTTPException(status_code=400, detail="MCP server is disabled")
    
    return mcp_service.get_server_info()


@router.get("/tools")
async def list_tools():
    """
    List all available MCP tools.
    
    Returns tool definitions with:
    - name
    - description
    - inputSchema (parameters)
    """
    if not settings.enable_mcp_server:
        raise HTTPException(status_code=400, detail="MCP server is disabled")
    
    tools = mcp_service.get_tools()
    
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.inputSchema.model_dump()
            }
            for t in tools
        ],
        "total": len(tools)
    }


@router.get("/tools/{tool_name}")
async def get_tool(tool_name: str):
    """Get information about a specific tool."""
    if not settings.enable_mcp_server:
        raise HTTPException(status_code=400, detail="MCP server is disabled")
    
    tool = mcp_service.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
    
    return {
        "name": tool.name,
        "description": tool.description,
        "inputSchema": tool.inputSchema.model_dump()
    }


@router.post("/tools/{tool_name}/call")
async def call_tool(tool_name: str, request: Request):
    """
    Call an MCP tool.
    
    Args:
        tool_name: Name of the tool to call
        request body: Tool arguments as JSON
    
    Returns:
        Tool execution result
    """
    if not settings.enable_mcp_server:
        raise HTTPException(status_code=400, detail="MCP server is disabled")
    
    # Check authentication if enabled
    if settings.mcp_auth_enabled:
        auth_header = request.headers.get("Authorization")
        if not auth_header or auth_header != f"Bearer {settings.mcp_auth_token}":
            raise HTTPException(status_code=401, detail="Invalid MCP authentication")
    
    try:
        arguments = await request.json()
    except:
        arguments = {}
    
    result = await mcp_service.call_tool(tool_name, arguments)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/rpc")
async def handle_rpc(request: Request):
    """
    Handle MCP JSON-RPC requests.
    
    Supports:
    - initialize
    - tools/list
    - tools/call
    - resources/list
    """
    if not settings.enable_mcp_server:
        raise HTTPException(status_code=400, detail="MCP server is disabled")
    
    # Check authentication if enabled
    if settings.mcp_auth_enabled:
        auth_header = request.headers.get("Authorization")
        if not auth_header or auth_header != f"Bearer {settings.mcp_auth_token}":
            raise HTTPException(status_code=401, detail="Invalid MCP authentication")
    
    try:
        rpc_request = await request.json()
    except:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Parse error"},
            "id": None
        }
    
    response = await mcp_service.handle_request(rpc_request)
    return response


@router.get("/sse")
async def sse_endpoint(request: Request):
    """
    Server-Sent Events endpoint for MCP transport.
    
    Provides real-time updates for MCP clients.
    """
    if not settings.enable_mcp_server:
        raise HTTPException(status_code=400, detail="MCP server is disabled")
    
    if settings.mcp_transport != "sse":
        raise HTTPException(status_code=400, detail="SSE transport not enabled")
    
    async def event_generator():
        # Send initial connection event
        yield f"event: connected\ndata: {json.dumps({'status': 'connected'})}\n\n"
        
        # Send server info
        server_info = mcp_service.get_server_info()
        yield f"event: server_info\ndata: {json.dumps(server_info)}\n\n"
        
        # Send tools list
        tools_response = mcp_service.list_tools_response()
        yield f"event: tools\ndata: {json.dumps(tools_response)}\n\n"
        
        # Keep connection alive with heartbeat
        while True:
            if await request.is_disconnected():
                break
            yield f"event: heartbeat\ndata: {json.dumps({'status': 'alive'})}\n\n"
            await asyncio.sleep(30)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/settings")
async def get_mcp_settings():
    """Get MCP server settings."""
    return {
        "enabled": settings.enable_mcp_server,
        "host": settings.mcp_server_host,
        "port": settings.mcp_server_port,
        "transport": settings.mcp_transport,
        "auth_enabled": settings.mcp_auth_enabled,
        "enabled_tools": settings.mcp_enabled_tools_list
    }


# ==================== Convenience Tool Endpoints ====================

@router.post("/extract-pdf")
async def extract_pdf_endpoint(request: Request):
    """
    Convenience endpoint for PDF extraction.
    
    Body: {"pdf_path": "path/to/file.pdf", "language": "en"}
    """
    if not settings.enable_mcp_server:
        raise HTTPException(status_code=400, detail="MCP server is disabled")
    
    args = await request.json()
    result = await mcp_service.call_tool("pdf_extract", args)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/detect-pii")
async def detect_pii_endpoint(request: Request):
    """
    Convenience endpoint for PII detection.
    
    Body: {"text": "text to scan", "redact": true}
    """
    if not settings.enable_mcp_server:
        raise HTTPException(status_code=400, detail="MCP server is disabled")
    
    args = await request.json()
    result = await mcp_service.call_tool("pii_detect", args)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/build-markdown")
async def build_markdown_endpoint(request: Request):
    """
    Convenience endpoint for Markdown building.
    
    Body: {"blocks": [...], "include_metadata": false}
    """
    if not settings.enable_mcp_server:
        raise HTTPException(status_code=400, detail="MCP server is disabled")
    
    args = await request.json()
    result = await mcp_service.call_tool("markdown_build", args)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/generate-html")
async def generate_html_endpoint(request: Request):
    """
    Convenience endpoint for HTML generation.
    
    Body: {"markdown": "...", "theme": "light"}
    """
    if not settings.enable_mcp_server:
        raise HTTPException(status_code=400, detail="MCP server is disabled")
    
    args = await request.json()
    result = await mcp_service.call_tool("html_generate", args)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result
