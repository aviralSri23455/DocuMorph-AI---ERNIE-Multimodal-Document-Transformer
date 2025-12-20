"""MCP (Model Context Protocol) Server Service."""
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from loguru import logger
from pydantic import BaseModel

from app.config import settings


class MCPToolSchema(BaseModel):
    """MCP Tool input schema."""
    type: str = "object"
    properties: Dict[str, Any] = {}
    required: List[str] = []


class MCPTool(BaseModel):
    """MCP Tool definition."""
    name: str
    description: str
    inputSchema: MCPToolSchema


class MCPResource(BaseModel):
    """MCP Resource definition."""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None


class MCPService:
    """Service for MCP Server functionality."""
    
    def __init__(self):
        self._tools: Dict[str, MCPTool] = {}
        self._tool_handlers: Dict[str, Callable] = {}
        self._resources: Dict[str, MCPResource] = {}
        self._enabled = settings.enable_mcp_server
        
        if self._enabled:
            self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """Register built-in PDF2Web tools."""
        
        # PDF Extract Tool
        self.register_tool(
            MCPTool(
                name="pdf_extract",
                description="Extract text and structure from a PDF file using PaddleOCR",
                inputSchema=MCPToolSchema(
                    properties={
                        "pdf_path": {"type": "string", "description": "Path to PDF file"},
                        "language": {"type": "string", "description": "OCR language code", "default": "en"},
                        "max_pages": {"type": "integer", "description": "Maximum pages to process"}
                    },
                    required=["pdf_path"]
                )
            ),
            self._handle_pdf_extract
        )
        
        # PII Detect Tool
        self.register_tool(
            MCPTool(
                name="pii_detect",
                description="Detect and redact PII (Personal Identifiable Information) from text",
                inputSchema=MCPToolSchema(
                    properties={
                        "text": {"type": "string", "description": "Text to scan for PII"},
                        "redact": {"type": "boolean", "description": "Whether to redact detected PII", "default": True},
                        "pii_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "PII types to detect (EMAIL, PHONE, NAME, SSN, etc.)"
                        }
                    },
                    required=["text"]
                )
            ),
            self._handle_pii_detect
        )
        
        # Markdown Build Tool
        self.register_tool(
            MCPTool(
                name="markdown_build",
                description="Convert extracted content blocks to structured Markdown",
                inputSchema=MCPToolSchema(
                    properties={
                        "blocks": {
                            "type": "array",
                            "description": "Content blocks to convert",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "content": {"type": "string"}
                                }
                            }
                        },
                        "include_metadata": {"type": "boolean", "default": False}
                    },
                    required=["blocks"]
                )
            ),
            self._handle_markdown_build
        )
        
        # Semantic Analyze Tool
        self.register_tool(
            MCPTool(
                name="semantic_analyze",
                description="Analyze content for semantic component suggestions (charts, quizzes, etc.)",
                inputSchema=MCPToolSchema(
                    properties={
                        "content": {"type": "string", "description": "Content to analyze"},
                        "content_type": {"type": "string", "description": "Type of content (table, list, code)"}
                    },
                    required=["content"]
                )
            ),
            self._handle_semantic_analyze
        )
        
        # HTML Generate Tool
        self.register_tool(
            MCPTool(
                name="html_generate",
                description="Generate responsive HTML from Markdown with interactive components",
                inputSchema=MCPToolSchema(
                    properties={
                        "markdown": {"type": "string", "description": "Markdown content"},
                        "theme": {
                            "type": "string",
                            "enum": ["light", "dark", "professional", "academic", "minimal"],
                            "default": "light"
                        },
                        "components": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Interactive components to inject"
                        }
                    },
                    required=["markdown"]
                )
            ),
            self._handle_html_generate
        )
        
        # Theme Analyze Tool
        self.register_tool(
            MCPTool(
                name="theme_analyze",
                description="Analyze document content to suggest appropriate visual theme",
                inputSchema=MCPToolSchema(
                    properties={
                        "content": {"type": "string", "description": "Document content to analyze"}
                    },
                    required=["content"]
                )
            ),
            self._handle_theme_analyze
        )
        
        # Accessibility Check Tool
        self.register_tool(
            MCPTool(
                name="accessibility_check",
                description="Validate HTML for WCAG accessibility compliance",
                inputSchema=MCPToolSchema(
                    properties={
                        "html": {"type": "string", "description": "HTML content to validate"},
                        "wcag_level": {
                            "type": "string",
                            "enum": ["A", "AA", "AAA"],
                            "default": "AA"
                        }
                    },
                    required=["html"]
                )
            ),
            self._handle_accessibility_check
        )
    
    def register_tool(self, tool: MCPTool, handler: Callable):
        """Register an MCP tool."""
        self._tools[tool.name] = tool
        self._tool_handlers[tool.name] = handler
        logger.debug(f"Registered MCP tool: {tool.name}")
    
    def get_tools(self) -> List[MCPTool]:
        """Get all registered tools."""
        enabled_tools = settings.mcp_enabled_tools_list
        return [t for t in self._tools.values() if t.name in enabled_tools]
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get a specific tool by name."""
        return self._tools.get(name)
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        if name not in self._tool_handlers:
            return {"error": f"Tool not found: {name}"}
        
        if name not in settings.mcp_enabled_tools_list:
            return {"error": f"Tool not enabled: {name}"}
        
        try:
            handler = self._tool_handlers[name]
            result = await handler(arguments)
            return {"content": result}
        except Exception as e:
            logger.error(f"MCP tool error ({name}): {e}")
            return {"error": str(e)}
    
    # ==================== Tool Handlers ====================
    
    async def _handle_pdf_extract(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pdf_extract tool call."""
        from app.services.ocr_service import ocr_service
        from pathlib import Path
        
        pdf_path = Path(args["pdf_path"])
        if not pdf_path.exists():
            return {"error": "PDF file not found"}
        
        blocks, images = await ocr_service.extract_from_pdf(pdf_path)
        
        return {
            "blocks": [
                {
                    "id": b.id,
                    "type": b.type.value,
                    "content": b.content,
                    "page": b.page,
                    "confidence": b.confidence
                }
                for b in blocks
            ],
            "images": images,
            "total_blocks": len(blocks),
            "total_images": len(images)
        }
    
    async def _handle_pii_detect(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pii_detect tool call."""
        from app.services.pii_service import pii_service
        from app.models.schemas import ContentBlock, ContentType
        import uuid
        
        text = args["text"]
        redact = args.get("redact", True)
        
        # Create a temporary block
        block = ContentBlock(
            id=str(uuid.uuid4()),
            type=ContentType.PARAGRAPH,
            content=text,
            page=0,
            confidence=1.0
        )
        
        blocks, redactions = await pii_service.scan_and_redact([block])
        
        return {
            "original_text": text,
            "redacted_text": blocks[0].content if redact else text,
            "pii_found": [
                {
                    "type": r.pii_type,
                    "original": r.original,
                    "redacted": r.redacted,
                    "confidence": r.confidence
                }
                for r in redactions
            ],
            "total_pii": len(redactions)
        }
    
    async def _handle_markdown_build(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle markdown_build tool call."""
        from app.services.markdown_service import markdown_service
        from app.models.schemas import ContentBlock, ContentType
        import uuid
        
        blocks_data = args["blocks"]
        include_metadata = args.get("include_metadata", False)
        
        blocks = []
        for b in blocks_data:
            blocks.append(ContentBlock(
                id=str(uuid.uuid4()),
                type=ContentType(b.get("type", "paragraph")),
                content=b["content"],
                page=b.get("page", 0),
                confidence=b.get("confidence", 1.0)
            ))
        
        markdown = await markdown_service.build_markdown(blocks, include_metadata)
        
        return {
            "markdown": markdown,
            "blocks_processed": len(blocks)
        }
    
    async def _handle_semantic_analyze(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle semantic_analyze tool call."""
        from app.services.ernie_service import ernie_service
        from app.models.schemas import ContentBlock, ContentType
        import uuid
        
        content = args["content"]
        content_type = args.get("content_type", "paragraph")
        
        block = ContentBlock(
            id=str(uuid.uuid4()),
            type=ContentType(content_type),
            content=content,
            page=0,
            confidence=1.0
        )
        
        suggestions = await ernie_service.analyze_semantics([block])
        
        return {
            "suggestions": [
                {
                    "block_id": s.block_id,
                    "suggestion": s.suggestion.value,
                    "confidence": s.confidence,
                    "config": s.config
                }
                for s in suggestions
            ]
        }
    
    async def _handle_html_generate(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle html_generate tool call."""
        from app.services.html_generator import html_generator
        from app.services.markdown_service import markdown_service
        from app.models.schemas import ThemeType
        
        markdown = args["markdown"]
        theme = ThemeType(args.get("theme", "light"))
        
        # Parse markdown to blocks
        blocks = await markdown_service.parse_markdown(markdown)
        
        # Generate HTML
        html = await html_generator.generate(
            blocks=blocks,
            theme=theme,
            suggestions=[],
            approved_components=[]
        )
        
        return {
            "html": html,
            "theme": theme.value,
            "blocks_processed": len(blocks)
        }
    
    async def _handle_theme_analyze(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle theme_analyze tool call."""
        from app.services.ernie_service import ernie_service
        
        content = args["content"]
        analysis = await ernie_service.analyze_theme(content)
        
        return {
            "suggested_theme": analysis.suggested_theme.value,
            "confidence": analysis.confidence,
            "reasoning": analysis.reasoning
        }
    
    async def _handle_accessibility_check(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle accessibility_check tool call."""
        from app.services.accessibility_service import accessibility_service, WCAGLevel
        
        html = args["html"]
        wcag_level = args.get("wcag_level", "AA")
        
        # Temporarily set WCAG level
        original_level = accessibility_service.wcag_level
        accessibility_service.wcag_level = WCAGLevel(wcag_level)
        
        report = await accessibility_service.validate_html(html)
        
        # Restore original level
        accessibility_service.wcag_level = original_level
        
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
                    "suggestion": i.suggestion
                }
                for i in report.issues
            ]
        }
    
    # ==================== MCP Protocol Methods ====================
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get MCP server information."""
        return {
            "name": "pdf2web-mcp-server",
            "version": "1.0.0",
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": False, "listChanged": False}
            }
        }
    
    def list_tools_response(self) -> Dict[str, Any]:
        """Get tools list in MCP format."""
        return {
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.inputSchema.model_dump()
                }
                for t in self.get_tools()
            ]
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MCP JSON-RPC request.
        
        Args:
            request: MCP request object
            
        Returns:
            MCP response object
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        result = None
        error = None
        
        try:
            if method == "initialize":
                result = self.get_server_info()
            elif method == "tools/list":
                result = self.list_tools_response()
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = await self.call_tool(tool_name, arguments)
            elif method == "resources/list":
                result = {"resources": list(self._resources.values())}
            else:
                error = {"code": -32601, "message": f"Method not found: {method}"}
        except Exception as e:
            error = {"code": -32603, "message": str(e)}
        
        response = {"jsonrpc": "2.0", "id": request_id}
        if error:
            response["error"] = error
        else:
            response["result"] = result
        
        return response


# Singleton instance
mcp_service = MCPService()
