"""Markdown Builder Service for converting extracted content to Markdown."""
from typing import List, Optional
from loguru import logger

from app.models.schemas import ContentBlock, ContentType


class MarkdownService:
    """Service for building structured Markdown from content blocks."""
    
    def __init__(self):
        self.heading_levels = {
            "h1": "#",
            "h2": "##", 
            "h3": "###",
            "h4": "####"
        }
    
    async def build_markdown(
        self, 
        blocks: List[ContentBlock],
        include_metadata: bool = False
    ) -> str:
        """
        Convert content blocks to structured Markdown.
        
        Args:
            blocks: List of content blocks
            include_metadata: Include block metadata as comments
            
        Returns:
            Markdown string
        """
        markdown_parts = []
        current_page = -1
        
        for block in blocks:
            # Add page separator if new page
            if block.page != current_page:
                if current_page >= 0:
                    markdown_parts.append("\n---\n")
                current_page = block.page
                if include_metadata:
                    markdown_parts.append(f"<!-- Page {block.page + 1} -->\n")
            
            # Convert block to markdown
            md_content = self._block_to_markdown(block, include_metadata)
            if md_content:
                markdown_parts.append(md_content)
        
        return "\n".join(markdown_parts)
    
    def _block_to_markdown(self, block: ContentBlock, include_metadata: bool) -> str:
        """Convert a single block to Markdown."""
        content = block.content.strip()
        if not content:
            return ""
        
        # Add metadata comment if requested
        metadata_comment = ""
        if include_metadata:
            metadata_comment = f"<!-- block:{block.id} confidence:{block.confidence:.2f} -->\n"
        
        # Convert based on content type
        converters = {
            ContentType.HEADING: self._convert_heading,
            ContentType.PARAGRAPH: self._convert_paragraph,
            ContentType.TABLE: self._convert_table,
            ContentType.LIST: self._convert_list,
            ContentType.CODE: self._convert_code,
            ContentType.IMAGE: self._convert_image,
            ContentType.QUOTE: self._convert_quote
        }
        
        converter = converters.get(block.type, self._convert_paragraph)
        md_content = converter(block)
        
        return metadata_comment + md_content + "\n"
    
    def _convert_heading(self, block: ContentBlock) -> str:
        """Convert heading block to Markdown."""
        content = block.content.strip()
        
        # Determine heading level based on font size
        font_size = block.metadata.get("font_size", 12)
        if font_size >= 24:
            prefix = "#"
        elif font_size >= 18:
            prefix = "##"
        elif font_size >= 14:
            prefix = "###"
        else:
            prefix = "####"
        
        return f"{prefix} {content}"
    
    def _convert_paragraph(self, block: ContentBlock) -> str:
        """Convert paragraph block to Markdown."""
        return block.content.strip()
    
    def _convert_table(self, block: ContentBlock) -> str:
        """Convert table block to Markdown table."""
        content = block.content.strip()
        
        # If already contains pipe characters, assume it's table-like
        if "|" in content:
            lines = content.split("\n")
            md_lines = []
            
            for i, line in enumerate(lines):
                cells = [c.strip() for c in line.split("|") if c.strip()]
                if cells:
                    md_line = "| " + " | ".join(cells) + " |"
                    md_lines.append(md_line)
                    
                    # Add header separator after first row
                    if i == 0:
                        separator = "| " + " | ".join(["---"] * len(cells)) + " |"
                        md_lines.append(separator)
            
            return "\n".join(md_lines)
        
        # Otherwise, try to parse as structured data
        return self._parse_table_content(content)
    
    def _parse_table_content(self, content: str) -> str:
        """Parse unstructured table content into Markdown table."""
        lines = content.strip().split("\n")
        if len(lines) < 2:
            return content
        
        # Try to detect columns by consistent spacing
        md_lines = []
        for i, line in enumerate(lines):
            # Split by multiple spaces or tabs
            import re
            cells = re.split(r'\s{2,}|\t', line.strip())
            cells = [c.strip() for c in cells if c.strip()]
            
            if cells:
                md_line = "| " + " | ".join(cells) + " |"
                md_lines.append(md_line)
                
                if i == 0:
                    separator = "| " + " | ".join(["---"] * len(cells)) + " |"
                    md_lines.append(separator)
        
        return "\n".join(md_lines) if md_lines else content
    
    def _convert_list(self, block: ContentBlock) -> str:
        """Convert list block to Markdown list."""
        content = block.content.strip()
        lines = content.split("\n")
        md_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if already has list marker
            if line.startswith(("-", "*", "•")):
                # Normalize to dash
                md_lines.append("- " + line.lstrip("-*• "))
            elif line[0].isdigit() and ("." in line[:3] or ")" in line[:3]):
                # Numbered list
                md_lines.append(line)
            else:
                md_lines.append("- " + line)
        
        return "\n".join(md_lines)
    
    def _convert_code(self, block: ContentBlock) -> str:
        """Convert code block to Markdown code block."""
        content = block.content.strip()
        
        # Detect language if possible
        language = self._detect_code_language(content)
        
        # Remove existing code fences if present
        if content.startswith("```"):
            return content
        
        return f"```{language}\n{content}\n```"
    
    def _detect_code_language(self, content: str) -> str:
        """Detect programming language from code content."""
        content_lower = content.lower()
        
        if "def " in content or "import " in content or "class " in content:
            return "python"
        elif "function " in content or "const " in content or "let " in content:
            return "javascript"
        elif "<html" in content_lower or "<div" in content_lower:
            return "html"
        elif "{" in content and "}" in content and ":" in content:
            return "json"
        elif "SELECT " in content.upper() or "FROM " in content.upper():
            return "sql"
        
        return ""
    
    def _convert_image(self, block: ContentBlock) -> str:
        """Convert image reference to Markdown."""
        image_path = block.metadata.get("image_path", "")
        alt_text = block.metadata.get("alt_text", "Image")
        return f"![{alt_text}]({image_path})"
    
    def _convert_quote(self, block: ContentBlock) -> str:
        """Convert quote block to Markdown blockquote."""
        lines = block.content.strip().split("\n")
        return "\n".join([f"> {line}" for line in lines])
    
    async def parse_markdown(self, markdown: str) -> List[ContentBlock]:
        """Parse Markdown back into content blocks (for editing)."""
        import uuid
        blocks = []
        lines = markdown.split("\n")
        current_block = []
        current_type = ContentType.PARAGRAPH
        
        for line in lines:
            stripped = line.strip()
            
            # Detect block type
            if stripped.startswith("#"):
                # Save previous block
                if current_block:
                    blocks.append(self._create_block(current_block, current_type))
                    current_block = []
                
                current_type = ContentType.HEADING
                current_block.append(stripped.lstrip("# "))
                
            elif stripped.startswith("```"):
                if current_type == ContentType.CODE:
                    # End of code block
                    blocks.append(self._create_block(current_block, current_type))
                    current_block = []
                    current_type = ContentType.PARAGRAPH
                else:
                    # Start of code block
                    if current_block:
                        blocks.append(self._create_block(current_block, current_type))
                    current_block = []
                    current_type = ContentType.CODE
                    
            elif stripped.startswith("|"):
                if current_type != ContentType.TABLE:
                    if current_block:
                        blocks.append(self._create_block(current_block, current_type))
                    current_block = []
                    current_type = ContentType.TABLE
                current_block.append(stripped)
                
            elif stripped.startswith(("-", "*", "•")) or (stripped and stripped[0].isdigit()):
                if current_type != ContentType.LIST:
                    if current_block:
                        blocks.append(self._create_block(current_block, current_type))
                    current_block = []
                    current_type = ContentType.LIST
                current_block.append(stripped)
                
            elif stripped:
                if current_type not in [ContentType.CODE, ContentType.TABLE, ContentType.LIST]:
                    current_type = ContentType.PARAGRAPH
                current_block.append(stripped)
        
        # Save last block
        if current_block:
            blocks.append(self._create_block(current_block, current_type))
        
        return blocks
    
    def _create_block(self, lines: List[str], content_type: ContentType) -> ContentBlock:
        """Create a content block from lines."""
        import uuid
        return ContentBlock(
            id=str(uuid.uuid4()),
            type=content_type,
            content="\n".join(lines),
            page=0,
            confidence=1.0
        )


# Singleton instance
markdown_service = MarkdownService()
