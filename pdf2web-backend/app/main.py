"""Main FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.api.routes import pdf, codesign, export, health, deploy, websocket, audit, plugins, accessibility, mcp, knowledge_graph, ui


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Convert PDFs to interactive HTML with AI-powered semantic injection",
        version="1.0.0",
        debug=settings.debug
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    # Health routes at both /api and root level for compatibility
    app.include_router(health.router, prefix="/api", tags=["Health"])
    app.include_router(health.router, tags=["Health"])
    app.include_router(pdf.router, prefix="/api/pdf", tags=["PDF Processing"])
    app.include_router(codesign.router, prefix="/api/codesign", tags=["Co-Design"])
    app.include_router(export.router, prefix="/api/export", tags=["Export"])
    app.include_router(deploy.router, prefix="/api/deploy", tags=["Deployment"])
    app.include_router(websocket.router, prefix="/api/realtime", tags=["WebSocket"])
    app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
    app.include_router(plugins.router, prefix="/api/plugins", tags=["Plugins"])
    app.include_router(accessibility.router, prefix="/api/accessibility", tags=["Accessibility"])
    app.include_router(mcp.router, prefix="/api/mcp", tags=["MCP"])
    app.include_router(knowledge_graph.router, prefix="/api", tags=["Knowledge Graph"])
    app.include_router(ui.router, tags=["Web UI"])
    
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Starting {settings.app_name}")
        logger.info(f"Environment: {settings.app_env}")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"MCP Server: {'enabled' if settings.enable_mcp_server else 'disabled'}")
        logger.info(f"WebSocket: {'enabled' if settings.enable_websocket else 'disabled'}")
        logger.info(f"Plugins: {'enabled' if settings.enable_plugins else 'disabled'}")
        logger.info(f"Audit Logging: {'enabled' if settings.enable_audit_log else 'disabled'}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down application")
        # Cleanup services
        from app.services.deploy_service import deploy_service
        await deploy_service.close()
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)
