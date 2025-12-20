"""Document Store Service for managing document state."""
import uuid
from datetime import datetime
from typing import Dict, Optional, List
from loguru import logger

from app.models.schemas import (
    ExtractedDocument, ContentBlock, PIIRedaction,
    ProcessingMode, SemanticSuggestion, ThemeAnalysis
)


class DocumentStore:
    """In-memory document store for managing processing state."""
    
    def __init__(self):
        self._documents: Dict[str, ExtractedDocument] = {}
        self._markdown: Dict[str, str] = {}
        self._suggestions: Dict[str, List[SemanticSuggestion]] = {}
        self._theme_analysis: Dict[str, ThemeAnalysis] = {}
        self._html: Dict[str, str] = {}
        self._original_blocks: Dict[str, List[ContentBlock]] = {}
        self._original_pii: Dict[str, List[PIIRedaction]] = {}
        self._page_images: Dict[str, Dict[int, str]] = {}  # For vision analysis
        self._knowledge_graphs: Dict[str, dict] = {}  # For knowledge graph navigation
    
    def create_document(
        self,
        filename: str,
        total_pages: int,
        blocks: List[ContentBlock],
        images: List[str],
        pii_redactions: List[PIIRedaction],
        processing_mode: ProcessingMode
    ) -> ExtractedDocument:
        """Create and store a new document."""
        document_id = str(uuid.uuid4())
        
        document = ExtractedDocument(
            document_id=document_id,
            filename=filename,
            total_pages=total_pages,
            blocks=blocks,
            images=images,
            pii_redactions=pii_redactions,
            processing_mode=processing_mode,
            created_at=datetime.now()
        )
        
        self._documents[document_id] = document
        self._original_blocks[document_id] = [b.model_copy() for b in blocks]
        self._original_pii[document_id] = [p.model_copy() for p in pii_redactions]
        
        logger.info(f"Created document: {document_id}")
        return document
    
    def get_document(self, document_id: str) -> Optional[ExtractedDocument]:
        """Retrieve a document by ID."""
        return self._documents.get(document_id)
    
    def update_document(
        self,
        document_id: str,
        blocks: List[ContentBlock] = None,
        pii_redactions: List[PIIRedaction] = None
    ) -> Optional[ExtractedDocument]:
        """Update document content."""
        document = self._documents.get(document_id)
        if not document:
            return None
        
        if blocks is not None:
            document.blocks = blocks
        if pii_redactions is not None:
            document.pii_redactions = pii_redactions
        
        return document
    
    def store_markdown(self, document_id: str, markdown: str):
        """Store generated Markdown."""
        self._markdown[document_id] = markdown
    
    def get_markdown(self, document_id: str) -> Optional[str]:
        """Retrieve stored Markdown."""
        return self._markdown.get(document_id)
    
    def store_suggestions(self, document_id: str, suggestions: List[SemanticSuggestion]):
        """Store semantic suggestions."""
        self._suggestions[document_id] = suggestions
    
    def get_suggestions(self, document_id: str) -> List[SemanticSuggestion]:
        """Retrieve semantic suggestions."""
        return self._suggestions.get(document_id, [])
    
    def store_theme_analysis(self, document_id: str, analysis: ThemeAnalysis):
        """Store theme analysis."""
        self._theme_analysis[document_id] = analysis
    
    def get_theme_analysis(self, document_id: str) -> Optional[ThemeAnalysis]:
        """Retrieve theme analysis."""
        return self._theme_analysis.get(document_id)
    
    def store_html(self, document_id: str, html: str):
        """Store generated HTML."""
        self._html[document_id] = html
    
    def get_html(self, document_id: str) -> Optional[str]:
        """Retrieve generated HTML."""
        return self._html.get(document_id)
    
    def get_original_blocks(self, document_id: str) -> List[ContentBlock]:
        """Get original blocks before edits."""
        return self._original_blocks.get(document_id, [])
    
    def get_original_pii(self, document_id: str) -> List[PIIRedaction]:
        """Get original PII redactions."""
        return self._original_pii.get(document_id, [])
    
    def store_page_images(self, document_id: str, page_images: Dict[int, str]):
        """Store page image paths for vision analysis."""
        self._page_images[document_id] = page_images
    
    def get_page_images(self, document_id: str) -> Optional[Dict[int, str]]:
        """Retrieve page image paths for vision analysis."""
        return self._page_images.get(document_id)
    
    def set_knowledge_graph(self, document_id: str, graph: dict):
        """Store knowledge graph for a document."""
        self._knowledge_graphs[document_id] = graph
    
    def get_knowledge_graph(self, document_id: str) -> Optional[dict]:
        """Retrieve knowledge graph for a document."""
        return self._knowledge_graphs.get(document_id)
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document and all associated data."""
        if document_id not in self._documents:
            return False
        
        del self._documents[document_id]
        self._markdown.pop(document_id, None)
        self._suggestions.pop(document_id, None)
        self._theme_analysis.pop(document_id, None)
        self._html.pop(document_id, None)
        self._original_blocks.pop(document_id, None)
        self._original_pii.pop(document_id, None)
        self._page_images.pop(document_id, None)
        self._knowledge_graphs.pop(document_id, None)
        
        logger.info(f"Deleted document: {document_id}")
        return True
    
    def list_documents(self) -> List[ExtractedDocument]:
        """List all documents."""
        return list(self._documents.values())
    
    def cleanup_old_documents(self, max_age_hours: int = 24):
        """Remove documents older than specified age."""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        
        to_delete = []
        for doc_id, doc in self._documents.items():
            if doc.created_at.timestamp() < cutoff:
                to_delete.append(doc_id)
        
        for doc_id in to_delete:
            self.delete_document(doc_id)
        
        if to_delete:
            logger.info(f"Cleaned up {len(to_delete)} old documents")


# Singleton instance
document_store = DocumentStore()
