"""Pydantic schemas for request/response models."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class ProcessingMode(str, Enum):
    """Processing mode for PDF conversion."""
    SECURE = "secure"  # Local processing, PII redaction
    STANDARD = "standard"  # Hybrid local + cloud


class ContentType(str, Enum):
    """Types of content detected in PDF."""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    LIST = "list"
    CODE = "code"
    IMAGE = "image"
    QUOTE = "quote"


class ComponentSuggestion(str, Enum):
    """Interactive component suggestions."""
    CHART_BAR = "chart_bar"
    CHART_LINE = "chart_line"
    CHART_PIE = "chart_pie"
    CHART_HYBRID = "chart_hybrid"  # Table + Chart combined
    QUIZ = "quiz"
    CODE_BLOCK = "code_block"
    CODE_EXECUTABLE = "code_executable"  # Interactive code execution
    TIMELINE = "timeline"
    MAP = "map"
    NONE = "none"


class ChartConversionOption(str, Enum):
    """Options for table to chart conversion."""
    KEEP_TABLE = "keep_table"
    CONVERT_TO_CHART = "convert_to_chart"
    HYBRID = "hybrid"  # Show both table and chart


class ThemeType(str, Enum):
    """Available themes for HTML output."""
    LIGHT = "light"
    DARK = "dark"
    PROFESSIONAL = "professional"
    ACADEMIC = "academic"
    MINIMAL = "minimal"


# Request Models
class PDFUploadRequest(BaseModel):
    """Request model for PDF upload."""
    mode: ProcessingMode = ProcessingMode.SECURE
    language: str = "en"


class ContentBlock(BaseModel):
    """A single content block extracted from PDF."""
    id: str
    type: ContentType
    content: str
    page: int
    confidence: float = Field(ge=0, le=1)
    bbox: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}


class PIIRedaction(BaseModel):
    """PII redaction information."""
    id: str
    original: str
    redacted: str
    pii_type: str
    start: int
    end: int
    confidence: float
    block_id: str


class ExtractedDocument(BaseModel):
    """Complete extracted document structure."""
    document_id: str
    filename: str
    total_pages: int
    blocks: List[ContentBlock]
    images: List[str]  # Local image paths
    pii_redactions: List[PIIRedaction] = []
    processing_mode: ProcessingMode
    created_at: datetime


class CoDesignEdit(BaseModel):
    """User edit in Co-Design layer."""
    block_id: str
    new_content: Optional[str] = None
    new_type: Optional[ContentType] = None
    approved: bool = True
    chart_option: Optional[str] = None  # For table→chart: keep_table, convert_to_chart, hybrid
    enable_quiz: Optional[bool] = None  # Enable quiz mode for lists
    enable_code_execution: Optional[bool] = None  # Enable interactive code


class PIIRedactionAction(BaseModel):
    """User action on PII redaction."""
    redaction_id: str
    action: str  # "approve", "undo", "modify"
    new_value: Optional[str] = None


class CoDesignSubmission(BaseModel):
    """User submission from Co-Design layer."""
    document_id: str
    edits: List[CoDesignEdit] = []
    pii_actions: List[PIIRedactionAction] = []
    theme: ThemeType = ThemeType.LIGHT
    theme_override: bool = False
    approved_components: List[str] = []
    chart_conversions: Dict[str, str] = {}  # block_id → chart_option
    quiz_enabled_blocks: List[str] = []  # block_ids with quiz enabled
    code_execution_blocks: List[str] = []  # block_ids with code execution
    timeline_blocks: List[str] = []  # block_ids for timeline widget
    map_blocks: List[str] = []  # block_ids for map widget


class SecureModeConfig(BaseModel):
    """Configuration for Secure Mode."""
    enabled: bool = True
    redact_emails: bool = True
    redact_phones: bool = True
    redact_names: bool = True
    redact_ssn: bool = True
    redact_credit_cards: bool = True
    custom_patterns: List[str] = []  # Regex patterns for custom PII


class LowConfidenceBlock(BaseModel):
    """Block flagged for low OCR confidence."""
    block_id: str
    content: str
    confidence: float
    suggested_fixes: List[str] = []


class SemanticSuggestion(BaseModel):
    """Semantic component suggestion from ERNIE."""
    block_id: str
    suggestion: ComponentSuggestion
    confidence: float
    config: Dict[str, Any] = {}


class ThemeAnalysis(BaseModel):
    """Theme analysis result."""
    suggested_theme: ThemeType
    confidence: float
    reasoning: str


# Response Models
class UploadResponse(BaseModel):
    """Response after PDF upload."""
    document_id: str
    filename: str
    total_pages: int
    processing_mode: ProcessingMode
    message: str


class ExtractionResponse(BaseModel):
    """Response with extracted content."""
    document: ExtractedDocument
    markdown: str
    theme_analysis: Optional[ThemeAnalysis] = None
    semantic_suggestions: List[SemanticSuggestion] = []


class HTMLGenerationResponse(BaseModel):
    """Response with generated HTML."""
    document_id: str
    html: str
    assets: List[str]
    theme: ThemeType
    components_injected: List[str]


class ExportResponse(BaseModel):
    """Response for export operations."""
    document_id: str
    export_type: str
    download_url: Optional[str] = None
    deploy_url: Optional[str] = None
    message: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    services: Dict[str, bool]
