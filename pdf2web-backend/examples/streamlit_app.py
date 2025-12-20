"""
DocuMorph AI - Enhanced Streamlit Co-Design UI

🏆 DEV.to Hackathon Entry - Best ERNIE Multimodal Application using Novita API

Complete implementation with:
- Real-time WebSocket updates
- Knowledge Graph visualization
- Accessibility checks
- All semantic injection features (Charts, Quizzes, Code, Timeline, Map)
- Full deployment options

Run with: streamlit run examples/streamlit_app.py
"""
import streamlit as st
import requests
import time
from typing import Optional

# Configuration
API_BASE = "http://localhost:8000/api"

# Page config
st.set_page_config(
    page_title="DocuMorph AI",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark cyberpunk theme with high contrast
st.markdown("""
<style>
    /* Main background */
    .stApp { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); }
    
    /* Header gradient text */
    .main-header { 
        background: linear-gradient(90deg, #6fa8dc 0%, #93d5cf 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5em;
        font-weight: 700;
    }
    
    /* Stat cards */
    .stat-card {
        background: rgba(78, 121, 167, 0.2);
        border: 1px solid rgba(111, 168, 220, 0.5);
        border-radius: 12px;
        padding: 15px;
        text-align: center;
    }
    .stat-value { font-size: 2em; font-weight: 700; color: #6fa8dc; }
    .stat-label { color: #b8c5d6; font-size: 0.9em; }
    
    /* Confidence colors */
    .confidence-high { color: #5cb85c; }
    .confidence-medium { color: #f0ad4e; }
    .confidence-low { color: #ff6b6b; }
    .pii-badge { 
        background: #ff6b6b; 
        color: white; 
        padding: 2px 8px; 
        border-radius: 4px; 
        font-size: 0.8em;
    }
    
    /* ===== HIGH CONTRAST TEXT FIXES ===== */
    
    /* All text elements - force white/light colors */
    .stApp p, .stApp span, .stApp label, .stApp div {
        color: #f0f4f8 !important;
    }
    
    /* Headers */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: #ffffff !important;
    }
    
    /* Sidebar - force all text to be visible */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%) !important;
    }
    [data-testid="stSidebar"] * {
        color: #f0f4f8 !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    
    /* Radio buttons and checkboxes */
    .stRadio > label, .stCheckbox > label {
        color: #f0f4f8 !important;
    }
    .stRadio label span, .stCheckbox label span {
        color: #f0f4f8 !important;
    }
    
    /* Selectbox */
    .stSelectbox label, .stSelectbox > div > div {
        color: #f0f4f8 !important;
    }
    
    /* ===== FILE UPLOADER FIX ===== */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 2px dashed rgba(111, 168, 220, 0.6) !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }
    [data-testid="stFileUploader"] label, 
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] small {
        color: #f0f4f8 !important;
    }
    [data-testid="stFileUploader"] section {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 2px dashed rgba(111, 168, 220, 0.6) !important;
        border-radius: 10px !important;
    }
    [data-testid="stFileUploader"] section > div {
        color: #f0f4f8 !important;
    }
    /* Browse files button */
    [data-testid="stFileUploader"] button,
    [data-testid="baseButton-secondary"] {
        background: #4a7ab8 !important;
        color: #ffffff !important;
        border: none !important;
        padding: 8px 20px !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    [data-testid="stFileUploader"] button:hover,
    [data-testid="baseButton-secondary"]:hover {
        background: #5a8ac8 !important;
    }
    
    /* Drag and drop text */
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 2px dashed rgba(111, 168, 220, 0.7) !important;
    }
    [data-testid="stFileUploaderDropzone"] * {
        color: #c8d4e0 !important;
    }
    
    /* Subheaders */
    .stSubheader, [data-testid="stSubheader"] {
        color: #ffffff !important;
    }
    
    /* Captions - slightly dimmer but still readable */
    .stCaption, small {
        color: #a8b8c8 !important;
    }
    
    /* Dividers */
    hr {
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Info/warning boxes text */
    .stAlert p, .stAlert span {
        color: #1a1a2e !important;
    }
    
    /* Theme dropdown fix */
    [data-testid="stSelectbox"] > div > div {
        background: rgba(30, 41, 59, 0.9) !important;
        border: 1px solid rgba(111, 168, 220, 0.5) !important;
        color: #f0f4f8 !important;
    }
</style>
""", unsafe_allow_html=True)


def api_call(method: str, endpoint: str, **kwargs) -> Optional[dict]:
    """Make API call with error handling."""
    try:
        url = f"{API_BASE}{endpoint}"
        response = requests.request(method, url, timeout=60, **kwargs)
        if response.status_code == 200:
            return response.json()
        else:
            error_detail = response.json().get('detail', 'Unknown error') if response.text else response.status_code
            st.error(f"API Error: {error_detail}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Make sure the server is running on localhost:8000")
        return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. The server may be processing a large file.")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def get_confidence_class(confidence: float) -> str:
    """Get CSS class based on confidence level."""
    if confidence >= 0.8:
        return "confidence-high"
    elif confidence >= 0.6:
        return "confidence-medium"
    return "confidence-low"


def render_sidebar():
    """Render the sidebar with navigation and status."""
    with st.sidebar:
        st.markdown('<h2 class="main-header">🔮 DocuMorph</h2>', unsafe_allow_html=True)
        st.caption("AI-Powered PDF to Interactive HTML")
        
        st.divider()
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["🏠 Home", "📊 Analytics", "⚙️ Settings", "❓ Help"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # System Status
        st.subheader("System Status")
        health = api_call("GET", "/health/ernie")
        if health:
            status_color = "🟢" if health.get("configured") else "🔴"
            st.write(f"{status_color} LLM: {health.get('model', 'Not configured')}")
            if health.get("vision_enabled"):
                st.write(f"👁️ Vision: {health.get('vision_model', 'N/A')}")
        else:
            st.write("🔴 Backend not connected")
        
        # Current document info
        if "document_id" in st.session_state:
            st.divider()
            st.subheader("Current Document")
            st.write(f"📄 {st.session_state.get('filename', 'Unknown')}")
            st.write(f"🔑 ID: `{st.session_state.document_id[:8]}...`")
        
        return page


def render_upload_screen():
    """Render the PDF upload screen with all options."""
    st.markdown('<h1 class="main-header">Upload PDF</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type="pdf",
            help="Upload a PDF to convert to interactive HTML (max 50MB)"
        )
        
        if uploaded_file:
            st.info(f"📄 **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
    
    with col2:
        st.subheader("🔧 Processing Options")
        
        mode = st.radio(
            "Processing Mode",
            ["secure", "standard"],
            format_func=lambda x: "🔒 Secure Mode (Local PII)" if x == "secure" else "📡 Standard Mode",
            help="Secure Mode redacts PII locally before cloud processing"
        )
        
        st.session_state.processing_mode = mode
        
        if mode == "secure":
            st.write("**PII Redaction:**")
            col_a, col_b = st.columns(2)
            with col_a:
                redact_emails = st.checkbox("📧 Emails", value=True)
                redact_phones = st.checkbox("📱 Phones", value=True)
                redact_names = st.checkbox("👤 Names", value=True)
            with col_b:
                redact_ssn = st.checkbox("🔢 SSN", value=True)
                redact_cards = st.checkbox("💳 Cards", value=True)
        else:
            redact_emails = redact_phones = redact_names = redact_ssn = redact_cards = False
        
        st.divider()
        
        # Theme pre-selection
        st.subheader("🎨 Theme")
        theme = st.selectbox(
            "Select Theme",
            ["light", "dark", "professional", "academic", "minimal"],
            format_func=lambda x: {
                "light": "☀️ Light",
                "dark": "🌙 Dark", 
                "professional": "💼 Professional",
                "academic": "📚 Academic",
                "minimal": "✨ Minimal"
            }[x]
        )
        st.session_state.selected_theme = theme
    
    # Process button
    if uploaded_file:
        if st.button("🚀 Process PDF", type="primary", use_container_width=True):
            with st.spinner("Processing PDF... This may take a moment."):
                progress_bar = st.progress(0, text="Uploading...")
                
                files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                data = {
                    "mode": mode,
                    "redact_emails": str(redact_emails).lower(),
                    "redact_phones": str(redact_phones).lower(),
                    "redact_names": str(redact_names).lower(),
                    "redact_ssn": str(redact_ssn).lower(),
                    "redact_credit_cards": str(redact_cards).lower()
                }
                
                progress_bar.progress(20, text="Extracting content...")
                result = api_call("POST", "/pdf/upload", files=files, data=data)
                
                if result:
                    progress_bar.progress(60, text="Analyzing document...")
                    st.session_state.document_id = result["document_id"]
                    st.session_state.filename = result["filename"]
                    st.session_state.total_pages = result.get("total_pages", 1)
                    
                    progress_bar.progress(100, text="Complete!")
                    time.sleep(0.5)
                    st.session_state.page = "preview"
                    st.rerun()


def render_preview_screen():
    """Render the Co-Design preview screen with all features."""
    document_id = st.session_state.document_id
    
    # Header
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
    with col1:
        st.markdown(f'<h1 class="main-header">Co-Design: {st.session_state.filename}</h1>', unsafe_allow_html=True)
    with col2:
        if st.button("✅ Accept All", help="Approve all PII redactions"):
            api_call("POST", f"/codesign/{document_id}/bulk-approve", json={"approve_all": True})
            st.rerun()
    with col3:
        if st.button("🔄 Reset", help="Reset all changes"):
            api_call("POST", f"/codesign/{document_id}/reset")
            st.rerun()
    with col4:
        if st.button("🔍 Transparency", help="View data sent to cloud"):
            st.session_state.show_transparency = True
    with col5:
        if st.button("⚡ Auto-Convert", help="AI handles everything"):
            with st.spinner("AI is processing..."):
                result = api_call("POST", f"/codesign/{document_id}/auto-convert")
                if result:
                    st.session_state.generated_html = result.get("html")
                    st.session_state.page = "output"
                    st.rerun()
    
    # Get preview data
    preview = api_call("GET", f"/codesign/{document_id}/preview")
    if not preview:
        st.error("Failed to load preview data")
        return
    
    # Stats bar
    stats = preview.get("stats", {})
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f'''<div class="stat-card">
            <div class="stat-value">{stats.get("total_blocks", 0)}</div>
            <div class="stat-label">Total Blocks</div>
        </div>''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''<div class="stat-card">
            <div class="stat-value">{stats.get("low_confidence_count", 0)}</div>
            <div class="stat-label">Low Confidence</div>
        </div>''', unsafe_allow_html=True)
    with col3:
        st.markdown(f'''<div class="stat-card">
            <div class="stat-value">{stats.get("pii_count", 0)}</div>
            <div class="stat-label">PII Redacted</div>
        </div>''', unsafe_allow_html=True)
    with col4:
        st.markdown(f'''<div class="stat-card">
            <div class="stat-value">{stats.get("suggestion_count", 0)}</div>
            <div class="stat-label">Suggestions</div>
        </div>''', unsafe_allow_html=True)
    with col5:
        st.markdown(f'''<div class="stat-card">
            <div class="stat-value">{st.session_state.get("total_pages", 1)}</div>
            <div class="stat-label">Pages</div>
        </div>''', unsafe_allow_html=True)
    
    st.divider()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📝 Content", "🔒 PII Review", "💡 Semantic", "🎨 Theme", "🗺️ Knowledge Graph", "⚙️ Export"
    ])
    
    with tab1:
        render_content_tab(preview, document_id)
    with tab2:
        render_pii_tab(preview, document_id)
    with tab3:
        render_semantic_tab(preview, document_id)
    with tab4:
        render_theme_tab(preview, document_id)
    with tab5:
        render_knowledge_graph_tab(document_id)
    with tab6:
        render_export_tab(preview, document_id)
    
    # Transparency modal
    if st.session_state.get("show_transparency"):
        render_transparency_modal(document_id)
    
    # Generate button
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 Generate Interactive HTML", type="primary", use_container_width=True):
            st.session_state.page = "generate"
            st.rerun()


def render_content_tab(preview: dict, document_id: str):
    """Render content blocks tab with inline editing."""
    blocks = preview.get("blocks", [])
    suggestions = {s["block_id"]: s for s in preview.get("semantic_suggestions", [])}
    
    # Filter options
    col1, col2 = st.columns([1, 3])
    with col1:
        filter_type = st.selectbox(
            "Filter by type",
            ["all", "heading", "paragraph", "table", "list", "code", "image"],
            format_func=lambda x: "All Types" if x == "all" else x.capitalize()
        )
    with col2:
        show_low_confidence = st.checkbox("Show only low confidence blocks", value=False)
    
    # Filter blocks
    filtered_blocks = blocks
    if filter_type != "all":
        filtered_blocks = [b for b in blocks if b["type"] == filter_type]
    if show_low_confidence:
        filtered_blocks = [b for b in filtered_blocks if b.get("confidence", 1.0) < 0.8]
    
    st.write(f"Showing {len(filtered_blocks)} of {len(blocks)} blocks")
    
    for block in filtered_blocks:
        confidence = block.get("confidence", 1.0)
        is_low_confidence = confidence < 0.8
        has_suggestion = block["id"] in suggestions
        
        # Block header
        icon = {"heading": "📌", "paragraph": "📄", "table": "📊", "list": "📋", "code": "💻", "image": "🖼️", "quote": "💬"}.get(block["type"], "📄")
        conf_class = get_confidence_class(confidence)
        
        with st.expander(
            f"{icon} {block['type'].upper()} (Page {block.get('page', 0) + 1}) - "
            f"{'⚠️ ' if is_low_confidence else ''}{confidence*100:.0f}% confidence"
            f"{' 💡' if has_suggestion else ''}",
            expanded=is_low_confidence
        ):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                new_content = st.text_area(
                    "Content",
                    block["content"],
                    key=f"content_{block['id']}",
                    height=120,
                    label_visibility="collapsed"
                )
                
                if new_content != block["content"]:
                    if st.button("💾 Save Changes", key=f"save_{block['id']}"):
                        result = api_call(
                            "POST",
                            f"/codesign/{document_id}/edit-block",
                            json={"block_id": block["id"], "new_content": new_content}
                        )
                        if result:
                            st.success("Saved!")
                            st.rerun()
            
            with col2:
                # Block type selector
                block_types = ["heading", "paragraph", "table", "list", "code", "image", "quote"]
                current_idx = block_types.index(block["type"]) if block["type"] in block_types else 1
                new_type = st.selectbox(
                    "Type",
                    block_types,
                    index=current_idx,
                    key=f"type_{block['id']}"
                )
                
                if new_type != block["type"]:
                    if st.button("Update", key=f"update_type_{block['id']}"):
                        api_call(
                            "POST",
                            f"/codesign/{document_id}/edit-block",
                            json={"block_id": block["id"], "new_type": new_type}
                        )
                        st.rerun()
                
                # Confidence indicator
                st.markdown(f'<span class="{conf_class}">Confidence: {confidence*100:.0f}%</span>', unsafe_allow_html=True)
            
            # Show suggestion if available
            if has_suggestion:
                suggestion = suggestions[block["id"]]
                st.info(f"💡 **Suggestion:** {suggestion['suggestion']} ({suggestion['confidence']*100:.0f}% confidence)")


def render_pii_tab(preview: dict, document_id: str):
    """Render PII review tab with approve/undo actions."""
    redactions = preview.get("pii_redactions", [])
    
    if not redactions:
        st.success("✅ No PII detected in this document.")
        st.info("If you're in Standard Mode, PII detection is skipped. Switch to Secure Mode to enable.")
        return
    
    st.write(f"**{len(redactions)} PII items detected and redacted:**")
    
    # Group by type
    pii_by_type = {}
    for r in redactions:
        pii_type = r.get("pii_type", "UNKNOWN")
        if pii_type not in pii_by_type:
            pii_by_type[pii_type] = []
        pii_by_type[pii_type].append(r)
    
    # Show summary
    cols = st.columns(len(pii_by_type))
    for i, (pii_type, items) in enumerate(pii_by_type.items()):
        with cols[i]:
            icon = {"EMAIL_ADDRESS": "📧", "PHONE_NUMBER": "📱", "PERSON": "👤", "US_SSN": "🔢", "CREDIT_CARD": "💳"}.get(pii_type, "🔒")
            st.metric(f"{icon} {pii_type}", len(items))
    
    st.divider()
    
    # Individual redactions
    for redaction in redactions:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                pii_type = redaction.get("pii_type", "UNKNOWN")
                icon = {"EMAIL_ADDRESS": "📧", "PHONE_NUMBER": "📱", "PERSON": "👤", "US_SSN": "🔢", "CREDIT_CARD": "💳"}.get(pii_type, "🔒")
                st.write(f"**{icon} {pii_type}**")
                
                # Show masked original
                original = redaction.get("original", "")
                masked = original[:2] + "***" + original[-2:] if len(original) > 4 else "***"
                st.write(f"Original: `{masked}`")
                st.write(f"Redacted: `{redaction.get('redacted', '[REDACTED]')}`")
            
            with col2:
                conf = redaction.get("confidence", 0.8)
                conf_class = get_confidence_class(conf)
                st.markdown(f'<span class="{conf_class}">{conf*100:.0f}% confidence</span>', unsafe_allow_html=True)
            
            with col3:
                if st.button("✅ Approve", key=f"approve_{redaction['id']}"):
                    api_call(
                        "POST",
                        f"/codesign/{document_id}/pii-action",
                        json={"redaction_id": redaction["id"], "action": "approve"}
                    )
                    st.rerun()
            
            with col4:
                if st.button("↩️ Undo", key=f"undo_{redaction['id']}"):
                    api_call(
                        "POST",
                        f"/codesign/{document_id}/pii-action",
                        json={"redaction_id": redaction["id"], "action": "undo"}
                    )
                    st.rerun()
            
            st.divider()


def render_semantic_tab(preview: dict, document_id: str):
    """Render semantic suggestions tab with interactive options."""
    suggestions = preview.get("semantic_suggestions", [])
    blocks = {b["id"]: b for b in preview.get("blocks", [])}
    
    if not suggestions:
        st.info("No semantic suggestions available. The AI will analyze your content for interactive components.")
        if st.button("🔄 Regenerate Suggestions"):
            with st.spinner("Analyzing content..."):
                api_call("POST", f"/codesign/{document_id}/regenerate-suggestions")
                st.rerun()
        return
    
    st.write(f"**{len(suggestions)} interactive component suggestions:**")
    
    # Group by type
    charts = [s for s in suggestions if "chart" in s["suggestion"].lower()]
    quizzes = [s for s in suggestions if "quiz" in s["suggestion"].lower()]
    code_blocks = [s for s in suggestions if "code" in s["suggestion"].lower()]
    # Note: 'others' category available for future use (timeline, map, etc.)
    _ = [s for s in suggestions if s not in charts + quizzes + code_blocks]
    
    # Charts section
    if charts:
        st.subheader("📊 Chart Suggestions")
        for suggestion in charts:
            block = blocks.get(suggestion["block_id"], {})
            with st.expander(f"Table → Chart (Page {block.get('page', 0) + 1})", expanded=True):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.text_area("Table Content", block.get("content", "")[:300] + "...", height=100, disabled=True)
                
                with col2:
                    chart_option = st.radio(
                        "Conversion",
                        ["keep_table", "convert_to_chart", "hybrid"],
                        format_func=lambda x: {"keep_table": "📋 Keep Table", "convert_to_chart": "📊 Convert to Chart", "hybrid": "📊📋 Hybrid"}[x],
                        key=f"chart_opt_{suggestion['block_id']}",
                        horizontal=False
                    )
                    st.session_state[f"chart_option_{suggestion['block_id']}"] = chart_option
                    
                    if chart_option != "keep_table":
                        chart_type = st.selectbox(
                            "Chart Type",
                            ["bar", "line", "pie"],
                            format_func=lambda x: {"bar": "📊 Bar", "line": "📈 Line", "pie": "🥧 Pie"}[x],
                            key=f"chart_type_{suggestion['block_id']}"
                        )
                        st.session_state[f"chart_type_{suggestion['block_id']}"] = chart_type
    
    # Quiz section
    if quizzes:
        st.subheader("❓ Quiz Suggestions")
        for suggestion in quizzes:
            block = blocks.get(suggestion["block_id"], {})
            with st.expander(f"List → Quiz (Page {block.get('page', 0) + 1})"):
                st.text_area("List Content", block.get("content", "")[:200], height=80, disabled=True)
                enable_quiz = st.checkbox(
                    "Enable Quiz Mode",
                    key=f"quiz_{suggestion['block_id']}",
                    value=True
                )
                st.session_state[f"quiz_enabled_{suggestion['block_id']}"] = enable_quiz
    
    # Code section
    if code_blocks:
        st.subheader("💻 Code Block Suggestions")
        for suggestion in code_blocks:
            block = blocks.get(suggestion["block_id"], {})
            with st.expander(f"Code Block (Page {block.get('page', 0) + 1})"):
                st.code(block.get("content", "")[:300])
                enable_exec = st.checkbox(
                    "Enable Code Execution (JavaScript only)",
                    key=f"exec_{suggestion['block_id']}",
                    help="⚠️ Only enable for trusted code"
                )
                st.session_state[f"exec_enabled_{suggestion['block_id']}"] = enable_exec


def render_theme_tab(preview: dict, document_id: str):
    """Render theme selection tab."""
    theme_analysis = preview.get("theme_analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if theme_analysis:
            suggested = theme_analysis.get("suggested_theme", "light")
            confidence = theme_analysis.get("confidence", 0.5)
            reasoning = theme_analysis.get("reasoning", "")
            
            st.info(f"""
            💡 **AI Recommendation: {suggested.upper()}** ({confidence*100:.0f}% confidence)
            
            _{reasoning}_
            """)
        
        st.subheader("Select Theme")
        
        themes = ["light", "dark", "professional", "academic", "minimal"]
        theme_info = {
            "light": ("☀️", "Clean and bright, ideal for general documents"),
            "dark": ("🌙", "Easy on the eyes, great for technical content"),
            "professional": ("💼", "Corporate look, perfect for business documents"),
            "academic": ("📚", "Scholarly style with serif fonts"),
            "minimal": ("✨", "Simple and distraction-free")
        }
        
        default_theme = st.session_state.get("selected_theme", theme_analysis.get("suggested_theme", "light") if theme_analysis else "light")
        
        for theme in themes:
            icon, desc = theme_info[theme]
            is_selected = theme == default_theme
            
            col_a, col_b = st.columns([1, 4])
            with col_a:
                if st.button(f"{icon} {theme.capitalize()}", key=f"theme_{theme}", type="primary" if is_selected else "secondary"):
                    st.session_state.selected_theme = theme
                    st.session_state.theme_override = True
                    st.rerun()
            with col_b:
                st.caption(desc)
    
    with col2:
        st.subheader("Preview")
        selected = st.session_state.get("selected_theme", "light")
        
        # Theme preview box
        preview_styles = {
            "light": "background: #fff; color: #333; border: 1px solid #ddd;",
            "dark": "background: #1a1a2e; color: #eaeaea; border: 1px solid #333;",
            "professional": "background: #fafafa; color: #2c3e50; border: 1px solid #e2e8f0;",
            "academic": "background: #fffef5; color: #333; border: 1px solid #d4d4aa; font-family: Georgia;",
            "minimal": "background: #fff; color: #111; border: 1px solid #eee;"
        }
        
        st.markdown(f'''
        <div style="{preview_styles.get(selected, preview_styles['light'])} padding: 20px; border-radius: 8px;">
            <h3 style="margin: 0 0 10px 0;">Sample Heading</h3>
            <p style="margin: 0;">This is how your content will look with the {selected} theme.</p>
        </div>
        ''', unsafe_allow_html=True)
        
        st.session_state.theme_override = st.checkbox(
            "Override AI suggestion",
            value=st.session_state.get("theme_override", False)
        )


def render_knowledge_graph_tab(document_id: str):
    """Render knowledge graph visualization tab."""
    st.subheader("🗺️ Document Knowledge Graph")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        use_ai = st.checkbox("Use AI for entity extraction", value=True)
        max_nodes = st.slider("Max nodes", 10, 50, 25)
        
        if st.button("🔄 Generate Graph", type="primary"):
            with st.spinner("Generating knowledge graph..."):
                result = api_call(
                    "POST",
                    f"/knowledge-graph/{document_id}/generate",
                    json={"use_ai": use_ai, "max_nodes": max_nodes}
                )
                if result:
                    st.session_state.knowledge_graph = result
                    st.success(f"Generated graph with {result['metadata']['total_nodes']} nodes and {result['metadata']['total_edges']} edges")
    
    with col1:
        graph = st.session_state.get("knowledge_graph")
        
        if graph:
            # Display graph metadata
            metadata = graph.get("metadata", {})
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Nodes", metadata.get("total_nodes", 0))
            col_b.metric("Edges", metadata.get("total_edges", 0))
            col_c.metric("Entity Types", len(metadata.get("entity_types", [])))
            
            # Display nodes by type
            st.write("**Entities by Type:**")
            nodes = graph.get("nodes", [])
            
            entity_types = {}
            for node in nodes:
                node_type = node.get("data", {}).get("type", "unknown")
                if node_type not in entity_types:
                    entity_types[node_type] = []
                entity_types[node_type].append(node)
            
            for entity_type, type_nodes in entity_types.items():
                with st.expander(f"{entity_type.capitalize()} ({len(type_nodes)})"):
                    for node in type_nodes[:10]:
                        st.write(f"• {node.get('label', 'Unknown')}")
                    if len(type_nodes) > 10:
                        st.caption(f"... and {len(type_nodes) - 10} more")
            
            # Table of Contents
            toc = graph.get("structure", {}).get("toc", [])
            if toc:
                st.write("**Document Structure:**")
                for item in toc:
                    indent = "  " * (item.get("level", 1) - 1)
                    st.write(f"{indent}• {item.get('title', 'Untitled')} (Page {item.get('page', 0) + 1})")
        else:
            st.info("Click 'Generate Graph' to create a knowledge graph from your document.")


def render_export_tab(preview: dict, document_id: str):
    """Render export and deployment settings tab."""
    st.subheader("📤 Export Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Export Format**")
        export_format = st.radio(
            "Format",
            ["html", "markdown"],
            format_func=lambda x: "📦 HTML Package (ZIP)" if x == "html" else "📝 Markdown + Images",
            label_visibility="collapsed"
        )
        st.session_state.export_format = export_format
        
        st.write("**Accessibility**")
        enable_a11y = st.checkbox("Enable accessibility enhancements", value=True)
        if enable_a11y:
            wcag_level = st.selectbox("WCAG Level", ["A", "AA", "AAA"], index=1)
            st.session_state.wcag_level = wcag_level
    
    with col2:
        st.write("**Deployment Target**")
        deploy_option = st.selectbox(
            "Deploy To",
            ["none", "github", "netlify", "vercel", "s3"],
            format_func=lambda x: {
                "none": "💾 Download Only",
                "github": "🐙 GitHub Pages",
                "netlify": "🔷 Netlify",
                "vercel": "▲ Vercel",
                "s3": "☁️ AWS S3"
            }[x]
        )
        st.session_state.deploy_option = deploy_option
        
        if deploy_option == "github":
            st.session_state.github_repo = st.text_input("Repository (user/repo)", placeholder="username/my-site")
            st.session_state.github_token = st.text_input("GitHub Token", type="password", help="Personal access token with repo permissions")
        
        elif deploy_option == "netlify":
            st.session_state.netlify_token = st.text_input("Netlify Token", type="password")
            st.session_state.netlify_site = st.text_input("Site Name (optional)", placeholder="my-pdf-site")
        
        elif deploy_option == "vercel":
            st.session_state.vercel_token = st.text_input("Vercel Token", type="password")
            st.session_state.vercel_project = st.text_input("Project Name (optional)")
        
        elif deploy_option == "s3":
            st.session_state.aws_key = st.text_input("AWS Access Key")
            st.session_state.aws_secret = st.text_input("AWS Secret Key", type="password")
            st.session_state.s3_bucket = st.text_input("Bucket Name")
            st.session_state.s3_region = st.selectbox("Region", ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"])


def render_transparency_modal(document_id: str):
    """Render transparency modal showing what data is sent to cloud."""
    with st.sidebar:
        st.header("🔍 Data Transparency")
        
        data = api_call("GET", f"/codesign/{document_id}/data-sent-to-cloud")
        if data:
            mode_icon = "🔒" if data.get("is_secure_mode") else "📡"
            st.write(f"**Mode:** {mode_icon} {'Secure' if data.get('is_secure_mode') else 'Standard'}")
            
            st.subheader("✅ Sent to Cloud")
            st.write("• Sanitized text structure")
            st.write("• Theme preferences")
            st.write("• Component selections")
            
            st.subheader("❌ NOT Sent")
            st.write("• Raw PDF file")
            st.write("• Original images")
            st.write("• Original PII values")
            
            pii_redacted = data.get("pii_redacted", {})
            if pii_redacted:
                st.subheader("🔒 PII Redacted")
                for pii_type, count in pii_redacted.items():
                    st.write(f"• {pii_type}: {count}")
            
            st.subheader("📄 Content Preview")
            content = data.get("content_to_send", "")
            preview_text = content[:500] + "..." if len(content) > 500 else content
            st.code(preview_text, language=None)
        
        if st.button("Close", use_container_width=True):
            st.session_state.show_transparency = False
            st.rerun()


def render_generate_screen():
    """Render the HTML generation screen."""
    document_id = st.session_state.document_id
    
    st.markdown('<h1 class="main-header">Generating Interactive HTML</h1>', unsafe_allow_html=True)
    
    # Get preview data
    preview = api_call("GET", f"/codesign/{document_id}/preview")
    if not preview:
        st.error("Failed to load document data")
        return
    
    # Collect all settings
    chart_conversions = {}
    quiz_blocks = []
    code_blocks = []
    timeline_blocks = []
    map_blocks = []
    
    for block in preview.get("blocks", []):
        block_id = block["id"]
        
        # Chart options
        if f"chart_option_{block_id}" in st.session_state:
            chart_conversions[block_id] = st.session_state[f"chart_option_{block_id}"]
        
        # Quiz options
        if st.session_state.get(f"quiz_enabled_{block_id}"):
            quiz_blocks.append(block_id)
        
        # Code execution options
        if st.session_state.get(f"exec_enabled_{block_id}"):
            code_blocks.append(block_id)
    
    # Build submission
    approved_components = list(chart_conversions.keys()) + quiz_blocks + code_blocks
    
    submission = {
        "document_id": document_id,
        "theme": st.session_state.get("selected_theme", "light"),
        "theme_override": st.session_state.get("theme_override", False),
        "approved_components": approved_components,
        "chart_conversions": chart_conversions,
        "quiz_enabled_blocks": quiz_blocks,
        "code_execution_blocks": code_blocks,
        "timeline_blocks": timeline_blocks,
        "map_blocks": map_blocks
    }
    
    # Progress display
    progress_bar = st.progress(0, text="Preparing...")
    status_text = st.empty()
    
    # Generate HTML
    progress_bar.progress(20, text="Analyzing semantic components...")
    status_text.write("🔍 Analyzing content structure...")
    
    progress_bar.progress(40, text="Generating interactive components...")
    status_text.write("📊 Creating charts, quizzes, and code blocks...")
    
    progress_bar.progress(60, text="Applying theme...")
    status_text.write(f"🎨 Applying {st.session_state.get('selected_theme', 'light')} theme...")
    
    result = api_call("POST", f"/codesign/{document_id}/submit", json=submission)
    
    if result:
        progress_bar.progress(80, text="Finalizing...")
        status_text.write("✨ Finalizing HTML output...")
        
        # Apply accessibility enhancements if enabled
        if st.session_state.get("wcag_level"):
            api_call("POST", f"/accessibility/enhance/{document_id}")
        
        progress_bar.progress(100, text="Complete!")
        status_text.empty()
        
        st.success("✅ HTML Generated Successfully!")
        
        # Store result
        st.session_state.generated_html = result.get("html", "")
        st.session_state.components_injected = result.get("components_injected", [])
        
        # Show stats
        col1, col2, col3 = st.columns(3)
        col1.metric("Theme", result.get("theme", "light").capitalize())
        col2.metric("Components Injected", len(result.get("components_injected", [])))
        col3.metric("Assets", len(result.get("assets", [])))
        
        st.divider()
        
        # Preview
        st.subheader("📄 Preview")
        with st.container():
            st.components.v1.html(result["html"], height=600, scrolling=True)
        
        st.divider()
        
        # Export options
        render_export_buttons(document_id)
    else:
        progress_bar.empty()
        status_text.empty()
        st.error("Failed to generate HTML. Please try again.")
        
        if st.button("🔄 Retry"):
            st.rerun()


def render_export_buttons(document_id: str):
    """Render export and deployment buttons."""
    st.subheader("📤 Export & Deploy")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Download**")
        
        # HTML download
        if st.button("📦 Download HTML (ZIP)", use_container_width=True):
            with st.spinner("Creating package..."):
                api_call("POST", f"/export/{document_id}/html")
                try:
                    response = requests.get(f"{API_BASE}/export/download/{document_id}/html", timeout=30)
                    if response.status_code == 200:
                        filename = st.session_state.filename.replace(".pdf", "")
                        st.download_button(
                            "💾 Save HTML Package",
                            data=response.content,
                            file_name=f"{filename}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Download failed: {e}")
        
        # Markdown download
        if st.button("📝 Download Markdown", use_container_width=True):
            with st.spinner("Creating package..."):
                api_call("POST", f"/export/{document_id}/markdown")
                try:
                    response = requests.get(f"{API_BASE}/export/download/{document_id}/markdown", timeout=30)
                    if response.status_code == 200:
                        filename = st.session_state.filename.replace(".pdf", "")
                        st.download_button(
                            "💾 Save Markdown Package",
                            data=response.content,
                            file_name=f"{filename}_markdown.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Download failed: {e}")
    
    with col2:
        st.write("**Deploy**")
        deploy_option = st.session_state.get("deploy_option", "none")
        
        if deploy_option == "github":
            if st.button("🐙 Deploy to GitHub Pages", use_container_width=True):
                repo = st.session_state.get("github_repo")
                token = st.session_state.get("github_token")
                if repo and token:
                    with st.spinner("Deploying to GitHub Pages..."):
                        result = api_call(
                            "POST",
                            f"/export/{document_id}/github-pages",
                            json={"repo_name": repo, "github_token": token}
                        )
                        if result:
                            st.success(f"✅ Deployed! URL: {result.get('deploy_url')}")
                            st.link_button("🔗 Open Site", result.get('deploy_url'))
                else:
                    st.warning("Please configure GitHub settings in the Export tab")
        
        elif deploy_option == "netlify":
            if st.button("🔷 Deploy to Netlify", use_container_width=True):
                token = st.session_state.get("netlify_token")
                site = st.session_state.get("netlify_site")
                if token:
                    with st.spinner("Deploying to Netlify..."):
                        result = api_call(
                            "POST",
                            f"/deploy/{document_id}/netlify",
                            json={"netlify_token": token, "site_name": site}
                        )
                        if result:
                            st.success(f"✅ Deployed! URL: {result.get('deploy_url')}")
                            st.link_button("🔗 Open Site", result.get('deploy_url'))
                else:
                    st.warning("Please configure Netlify settings in the Export tab")
        
        elif deploy_option == "vercel":
            if st.button("▲ Deploy to Vercel", use_container_width=True):
                token = st.session_state.get("vercel_token")
                project = st.session_state.get("vercel_project")
                if token:
                    with st.spinner("Deploying to Vercel..."):
                        result = api_call(
                            "POST",
                            f"/deploy/{document_id}/vercel",
                            json={"vercel_token": token, "project_name": project}
                        )
                        if result:
                            st.success(f"✅ Deployed! URL: {result.get('deploy_url')}")
                            st.link_button("🔗 Open Site", result.get('deploy_url'))
                else:
                    st.warning("Please configure Vercel settings in the Export tab")
        
        elif deploy_option == "s3":
            if st.button("☁️ Deploy to AWS S3", use_container_width=True):
                aws_key = st.session_state.get("aws_key")
                aws_secret = st.session_state.get("aws_secret")
                bucket = st.session_state.get("s3_bucket")
                region = st.session_state.get("s3_region", "us-east-1")
                if aws_key and aws_secret and bucket:
                    with st.spinner("Deploying to S3..."):
                        result = api_call(
                            "POST",
                            f"/deploy/{document_id}/s3",
                            json={
                                "aws_access_key": aws_key,
                                "aws_secret_key": aws_secret,
                                "bucket_name": bucket,
                                "region": region
                            }
                        )
                        if result:
                            st.success(f"✅ Deployed! URL: {result.get('deploy_url')}")
                            st.link_button("🔗 Open Site", result.get('deploy_url'))
                else:
                    st.warning("Please configure AWS settings in the Export tab")
        else:
            st.info("Select a deployment target in the Export tab")
    
    with col3:
        st.write("**Actions**")
        
        if st.button("🔄 Convert Another PDF", use_container_width=True, type="primary"):
            # Clear session state
            keys_to_keep = []
            for key in list(st.session_state.keys()):
                if key not in keys_to_keep:
                    del st.session_state[key]
            st.session_state.page = "upload"
            st.rerun()
        
        if st.button("✏️ Edit in Co-Design", use_container_width=True):
            st.session_state.page = "preview"
            st.rerun()


def render_output_screen():
    """Render the output screen for auto-converted documents."""
    st.markdown('<h1 class="main-header">Conversion Complete!</h1>', unsafe_allow_html=True)
    
    document_id = st.session_state.document_id
    html_content = st.session_state.get("generated_html", "")
    
    if html_content:
        st.success("✅ Your PDF has been converted to interactive HTML!")
        
        # Preview
        st.subheader("📄 Preview")
        st.components.v1.html(html_content, height=600, scrolling=True)
        
        st.divider()
        
        # Export buttons
        render_export_buttons(document_id)
    else:
        st.error("No HTML content available. Please try again.")
        if st.button("🔄 Start Over"):
            st.session_state.page = "upload"
            st.rerun()


def render_analytics_page():
    """Render analytics page."""
    st.markdown('<h1 class="main-header">Analytics</h1>', unsafe_allow_html=True)
    
    st.info("Analytics dashboard coming soon! Track your conversion history, processing times, and more.")
    
    # Placeholder stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Documents Processed", "0")
    col2.metric("Avg Processing Time", "0s")
    col3.metric("Components Injected", "0")
    col4.metric("Success Rate", "100%")


def render_settings_page():
    """Render settings page."""
    st.markdown('<h1 class="main-header">Settings</h1>', unsafe_allow_html=True)
    
    st.subheader("🔧 Default Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Processing**")
        st.selectbox("Default Mode", ["secure", "standard"], format_func=lambda x: "🔒 Secure" if x == "secure" else "📡 Standard")
        st.selectbox("Default Theme", ["light", "dark", "professional", "academic", "minimal"])
        st.selectbox("Default Language", ["en", "zh", "es", "fr", "de", "ja", "ko"])
    
    with col2:
        st.write("**PII Detection**")
        st.slider("Detection Threshold", 0.5, 1.0, 0.7)
        st.multiselect(
            "PII Types to Detect",
            ["EMAIL_ADDRESS", "PHONE_NUMBER", "PERSON", "US_SSN", "CREDIT_CARD"],
            default=["EMAIL_ADDRESS", "PHONE_NUMBER", "PERSON"]
        )
    
    st.divider()
    
    st.subheader("🎨 Appearance")
    st.checkbox("Dark Mode", value=True)
    st.checkbox("Show Confidence Scores", value=True)
    st.checkbox("Auto-expand Low Confidence Blocks", value=True)


def render_help_page():
    """Render help page."""
    st.markdown('<h1 class="main-header">Help & Documentation</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ## 🚀 Quick Start
    
    1. **Upload** a PDF file
    2. **Review** the extracted content in the Co-Design layer
    3. **Customize** themes, charts, quizzes, and more
    4. **Generate** interactive HTML
    5. **Export** or deploy to your favorite platform
    
    ## 🔒 Secure Mode
    
    When enabled, PII (emails, phone numbers, names, SSN, credit cards) is detected and redacted 
    **locally** before any data is sent to the cloud AI for processing.
    
    ## 💡 Semantic Injection
    
    The AI automatically detects:
    - **Tables** → Suggests interactive charts (bar, line, pie)
    - **Q&A Lists** → Suggests interactive quizzes
    - **Code Blocks** → Suggests syntax highlighting and execution
    
    ## 📤 Deployment Options
    
    - **GitHub Pages** - Free hosting with custom domain support
    - **Netlify** - Instant deploys with CDN
    - **Vercel** - Serverless deployment platform
    - **AWS S3** - Static website hosting
    
    ## 🔗 API Documentation
    
    Full API documentation is available at: `http://localhost:8000/docs`
    """)


def main():
    """Main application entry point."""
    # Render sidebar and get navigation
    nav_page = render_sidebar()
    
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "upload"
    
    # Handle navigation from sidebar
    if nav_page == "📊 Analytics":
        render_analytics_page()
        return
    elif nav_page == "⚙️ Settings":
        render_settings_page()
        return
    elif nav_page == "❓ Help":
        render_help_page()
        return
    
    # Main flow pages
    if st.session_state.page == "upload":
        render_upload_screen()
    elif st.session_state.page == "preview":
        render_preview_screen()
    elif st.session_state.page == "generate":
        render_generate_screen()
    elif st.session_state.page == "output":
        render_output_screen()


if __name__ == "__main__":
    main()
