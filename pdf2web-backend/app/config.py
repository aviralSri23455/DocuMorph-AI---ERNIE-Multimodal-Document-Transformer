"""Application configuration settings."""
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "DocuMorph AI"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:8501"
    
    # ERNIE API Configuration (via Novita AI)
    ernie_model: str = "baidu/ernie-3.5-8k"  # ERNIE model on Novita AI
    ernie_api_key: Optional[str] = None
    ernie_api_url: str = "https://api.novita.ai/v3/openai/chat/completions"
    ernie_access_token: Optional[str] = None  # For Baidu direct API only
    ernie_request_timeout: int = 60
    ernie_max_tokens: int = 1000  # Limit tokens to save credits
    ernie_temperature: float = 0.7
    
    # ERNIE Vision Model (for enhanced table/chart detection)
    ernie_vision_model: str = "baidu/ernie-4.5-vl-28b-a3b"
    enable_vision_analysis: bool = True  # Use vision for better component detection
    
    # DeepSeek API Configuration (for knowledge graph / MCP multi-model)
    deepseek_api_key: Optional[str] = None
    deepseek_api_url: str = "https://api.novita.ai/v3/openai/chat/completions"
    deepseek_model: str = "deepseek/deepseek-v3-turbo"
    enable_knowledge_graph: bool = True  # Enable knowledge graph generation
    
    # Storage
    upload_dir: Path = Path("./uploads")
    output_dir: Path = Path("./outputs")
    temp_dir: Path = Path("./temp")
    max_file_size_mb: int = 50
    
    # Privacy / Secure Mode
    default_secure_mode: bool = True
    pii_detection_threshold: float = 0.7
    default_pii_types: str = "EMAIL_ADDRESS,PHONE_NUMBER,PERSON,US_SSN,CREDIT_CARD"
    
    # OCR Settings
    ocr_language: str = "en"
    max_pages: int = 100
    image_dpi: int = 300
    ocr_confidence_threshold: float = 0.8
    
    # Co-Design Layer
    low_confidence_threshold: float = 0.8
    max_blocks_per_page: int = 50
    enable_theme_suggestions: bool = True
    
    # Semantic Injection
    enable_chart_suggestions: bool = True
    enable_quiz_suggestions: bool = True
    enable_code_execution: bool = True
    default_chart_type: str = "bar"
    
    # Logging & Telemetry
    log_level: str = "INFO"
    log_format: str = "json"
    enable_telemetry: bool = False
    
    # Export & Deployment
    export_cleanup_hours: int = 24
    max_export_size_mb: int = 100
    github_token: Optional[str] = None
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60
    
    # Plugin Extensibility
    enable_plugins: bool = True
    plugins_dir: Path = Path("./plugins")
    enabled_plugins: str = "charts,quizzes,code_blocks"
    allow_plugin_scripts: bool = True
    plugin_sandbox_mode: bool = True
    
    # Audit & Timestamps (Co-Design)
    enable_audit_log: bool = True
    audit_log_dir: Path = Path("./audit_logs")
    enable_action_timestamps: bool = True
    timestamp_format: str = "iso"  # iso, unix, human
    track_pii_actions: bool = True
    track_block_edits: bool = True
    track_theme_changes: bool = True
    audit_log_retention_days: int = 90
    
    # MCP (Model Context Protocol)
    enable_mcp_server: bool = True
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 8001
    mcp_transport: str = "sse"  # stdio, sse, websocket
    mcp_enabled_tools: str = "pdf_extract,pii_detect,markdown_build,semantic_analyze,html_generate"
    mcp_auth_enabled: bool = False
    mcp_auth_token: Optional[str] = None
    
    # Lightweight UI (Streamlit/Gradio)
    ui_framework: str = "streamlit"  # streamlit, gradio
    streamlit_port: int = 8501
    gradio_port: int = 7860
    enable_live_preview: bool = True
    preview_refresh_interval: int = 2
    
    # WebSocket (Real-time Updates)
    enable_websocket: bool = True
    websocket_port: int = 8002
    websocket_ping_interval: int = 30
    
    # Caching
    enable_cache: bool = True
    cache_type: str = "memory"  # memory, redis
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 1000
    
    # Background Tasks
    enable_background_tasks: bool = True
    task_broker: str = "memory"  # memory, redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Lightweight Database
    db_type: str = "tinydb"  # tinydb, sqlite
    db_path: Path = Path("./data/pdf2web.db")
    sqlite_url: str = "sqlite:///./data/pdf2web.sqlite"
    
    # Progress Tracking
    enable_progress_tracking: bool = True
    progress_update_interval: float = 0.5
    
    # Interactive Components - Charts
    chart_default_width: int = 600
    chart_default_height: int = 400
    chart_animation_enabled: bool = True
    chart_responsive: bool = True
    chart_colors: str = "4e79a7,f28e2c,e15759,76b7b2,59a14f,edc949,af7aa1,ff9da7,9c755f,bab0ab"
    
    # Interactive Components - Quiz
    quiz_show_feedback: bool = True
    quiz_allow_retry: bool = True
    quiz_shuffle_options: bool = False
    
    # Interactive Components - Code
    code_theme: str = "prism"
    code_line_numbers: bool = True
    code_copy_button: bool = True
    code_max_height: int = 500
    
    # Interactive Components - Timeline/Map Widgets
    enable_timeline_widget: bool = True
    timeline_default_style: str = "horizontal"
    enable_map_widget: bool = True
    map_default_provider: str = "openstreetmap"
    
    # Accessibility
    enable_accessibility_checks: bool = True
    wcag_level: str = "AA"  # A, AA, AAA
    auto_aria_labels: bool = True
    support_high_contrast: bool = True
    screen_reader_optimized: bool = True
    keyboard_navigation: bool = True
    enable_skip_links: bool = True
    
    # Internationalization
    default_language: str = "en"
    supported_languages: str = "en,zh,es,fr,de,ja,ko"
    auto_detect_language: bool = True
    support_rtl: bool = True
    
    # Document Processing Enhancements
    table_extraction_method: str = "paddleocr"  # paddleocr, tabula, camelot
    enable_table_structure: bool = True
    extract_pdf_metadata: bool = True
    enable_layout_analysis: bool = True
    auto_heading_levels: bool = True
    auto_list_detection: bool = True
    
    # Theme Settings
    available_themes: str = "light,dark,professional,academic,minimal"
    default_theme: str = "light"
    allow_custom_css: bool = True
    enable_theme_preview: bool = True
    
    # Output HTML Settings
    minify_html: bool = False
    inline_css: bool = True
    include_viewport_meta: bool = True
    responsive_breakpoints: str = "768,1024,1200"
    include_print_styles: bool = True
    
    # Image Handling
    image_quality: int = 85
    max_image_dimension: int = 2000
    output_image_format: str = "original"  # original, webp, png, jpg
    enable_lazy_loading: bool = True
    auto_alt_text: bool = True
    
    # Performance
    ocr_concurrent_pages: int = 4
    ernie_retry_attempts: int = 3
    ernie_retry_delay: int = 1
    max_concurrent_documents: int = 5
    memory_limit_per_doc: int = 512
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def default_pii_types_list(self) -> List[str]:
        """Parse default PII types from comma-separated string."""
        return [pii.strip() for pii in self.default_pii_types.split(",")]
    
    @property
    def enabled_plugins_list(self) -> List[str]:
        """Parse enabled plugins from comma-separated string."""
        return [plugin.strip() for plugin in self.enabled_plugins.split(",")]
    
    @property
    def chart_colors_list(self) -> List[str]:
        """Parse chart colors from comma-separated string."""
        return [color.strip() for color in self.chart_colors.split(",")]
    
    @property
    def supported_languages_list(self) -> List[str]:
        """Parse supported languages from comma-separated string."""
        return [lang.strip() for lang in self.supported_languages.split(",")]
    
    @property
    def available_themes_list(self) -> List[str]:
        """Parse available themes from comma-separated string."""
        return [theme.strip() for theme in self.available_themes.split(",")]
    
    @property
    def responsive_breakpoints_list(self) -> List[int]:
        """Parse responsive breakpoints from comma-separated string."""
        return [int(bp.strip()) for bp in self.responsive_breakpoints.split(",")]
    
    @property
    def mcp_enabled_tools_list(self) -> List[str]:
        """Parse MCP enabled tools from comma-separated string."""
        return [tool.strip() for tool in self.mcp_enabled_tools.split(",")]


settings = Settings()

# Ensure directories exist
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
settings.temp_dir.mkdir(parents=True, exist_ok=True)
settings.audit_log_dir.mkdir(parents=True, exist_ok=True)
settings.plugins_dir.mkdir(parents=True, exist_ok=True)
settings.db_path.parent.mkdir(parents=True, exist_ok=True)
