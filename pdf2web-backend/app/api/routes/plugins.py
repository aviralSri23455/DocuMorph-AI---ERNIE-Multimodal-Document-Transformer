"""Plugin system endpoints."""
from fastapi import APIRouter, HTTPException, Body
from loguru import logger
from typing import Optional, Dict, Any

from app.services.plugin_service import plugin_service, PluginStatus
from app.config import settings

router = APIRouter()


@router.get("/")
async def list_plugins():
    """
    List all discovered plugins.
    
    Returns plugin information including:
    - name, version, type, description
    - status (active, disabled, error)
    - path
    """
    if not settings.enable_plugins:
        raise HTTPException(status_code=400, detail="Plugin system is disabled")
    
    plugins = plugin_service.list_plugins()
    
    return {
        "plugins": [
            {
                "name": p.manifest.name,
                "version": p.manifest.version,
                "type": p.manifest.type.value,
                "description": p.manifest.description,
                "author": p.manifest.author,
                "status": p.status.value,
                "path": p.path,
                "error": p.error_message
            }
            for p in plugins
        ],
        "total": len(plugins),
        "active": len([p for p in plugins if p.status == PluginStatus.ACTIVE])
    }


@router.get("/active")
async def list_active_plugins():
    """List only active plugins."""
    if not settings.enable_plugins:
        raise HTTPException(status_code=400, detail="Plugin system is disabled")
    
    active = plugin_service.get_active_plugins()
    
    return {
        "plugins": active,
        "total": len(active)
    }


@router.get("/{plugin_name}")
async def get_plugin_info(plugin_name: str):
    """Get detailed information about a specific plugin."""
    if not settings.enable_plugins:
        raise HTTPException(status_code=400, detail="Plugin system is disabled")
    
    plugins = plugin_service.list_plugins()
    plugin = next((p for p in plugins if p.manifest.name == plugin_name), None)
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_name}")
    
    return {
        "name": plugin.manifest.name,
        "version": plugin.manifest.version,
        "type": plugin.manifest.type.value,
        "description": plugin.manifest.description,
        "author": plugin.manifest.author,
        "status": plugin.status.value,
        "path": plugin.path,
        "entry_point": plugin.manifest.entry_point,
        "dependencies": plugin.manifest.dependencies,
        "config_schema": plugin.manifest.config_schema,
        "assets": plugin.manifest.assets,
        "error": plugin.error_message
    }


@router.post("/{plugin_name}/enable")
async def enable_plugin(plugin_name: str):
    """Enable a disabled plugin."""
    if not settings.enable_plugins:
        raise HTTPException(status_code=400, detail="Plugin system is disabled")
    
    # Check if plugin exists first
    plugins = plugin_service.list_plugins()
    plugin = next((p for p in plugins if p.manifest.name == plugin_name), None)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_name}")
    
    # If already active, just return success
    if plugin.status == PluginStatus.ACTIVE:
        return {"message": f"Plugin '{plugin_name}' is already enabled"}
    
    success = plugin_service.enable_plugin(plugin_name)
    
    if not success:
        raise HTTPException(status_code=400, detail=f"Could not enable plugin: {plugin_name}")
    
    logger.info(f"Enabled plugin: {plugin_name}")
    
    return {"message": f"Plugin '{plugin_name}' enabled successfully"}


@router.post("/{plugin_name}/disable")
async def disable_plugin(plugin_name: str):
    """Disable an active plugin."""
    if not settings.enable_plugins:
        raise HTTPException(status_code=400, detail="Plugin system is disabled")
    
    # Check if plugin exists first
    plugins = plugin_service.list_plugins()
    plugin = next((p for p in plugins if p.manifest.name == plugin_name), None)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_name}")
    
    success = plugin_service.disable_plugin(plugin_name)
    
    if not success:
        raise HTTPException(status_code=400, detail=f"Could not disable plugin: {plugin_name}")
    
    logger.info(f"Disabled plugin: {plugin_name}")
    
    return {"message": f"Plugin '{plugin_name}' disabled successfully"}


@router.post("/{plugin_name}/render")
async def render_with_plugin(
    plugin_name: str,
    content: str = Body(..., embed=True),
    block_id: str = Body("test-block", embed=True),
    options: Optional[Dict[str, Any]] = Body(None, embed=True)
):
    """
    Render content using a specific plugin.
    
    Args:
        plugin_name: Name of the plugin to use
        content: Content to render
        block_id: Block ID for the rendered element
        options: Additional rendering options
    """
    if not settings.enable_plugins:
        raise HTTPException(status_code=400, detail="Plugin system is disabled")
    
    result = plugin_service.render_widget(
        plugin_name,
        content,
        block_id,
        **(options or {})
    )
    
    if result is None:
        raise HTTPException(status_code=400, detail=f"Plugin render failed: {plugin_name}")
    
    return {
        "plugin": plugin_name,
        "html": result
    }


@router.get("/assets/all")
async def get_all_plugin_assets():
    """Get all CSS and JS assets from active plugins."""
    if not settings.enable_plugins:
        raise HTTPException(status_code=400, detail="Plugin system is disabled")
    
    assets = plugin_service.get_all_assets()
    
    return {
        "css": assets.get("css", []),
        "js": assets.get("js", [])
    }


@router.get("/types")
async def list_plugin_types():
    """List available plugin types."""
    from app.services.plugin_service import PluginType
    
    return {
        "types": [
            {"value": t.value, "name": t.name}
            for t in PluginType
        ]
    }
