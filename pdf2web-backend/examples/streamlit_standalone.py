"""
PDF2Web AI Weaver - Standalone Streamlit App

A simple standalone version that works without the FastAPI backend.
Uses local services directly.

Run with: streamlit run examples/streamlit_standalone.py
"""
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ocr_service import ocr_service
from app.services.pii_service import pii_service
from app.services.markdown_service import markdown_service
from app.services.html_generator import html_generator
from app.models.schemas import ThemeType, ContentBlock
from app.config import settings
import tempfile
import asyncio

st.set_page_config(page_title="PDF2Web AI Weaver", layout="wide", page_icon="📄")

st.title("📄 PDF2Web AI Weaver")
st.caption("Convert static PDFs into interactive HTML")


def run_async(coro):
    """Run async function in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# --- Sidebar Options ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    secure_mode = st.toggle("🔐 Secure Mode (Redact PII)", value=True)
    
    if secure_mode:
        st.subheader("PII Options")
        redact_emails = st.checkbox("Redact Emails", value=True)
        redact_phones = st.checkbox("Redact Phones", value=True)
        redact_names = st.checkbox("Redact Names", value=True)
        redact_ssn = st.checkbox("Redact SSN", value=True)
        redact_cards = st.checkbox("Redact Credit Cards", value=True)
    else:
        redact_emails = redact_phones = redact_names = redact_ssn = redact_cards = False
    
    st.divider()
    
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

# --- Main Content ---
uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_pdf:
    st.success(f"✅ Uploaded: {uploaded_pdf.name}")
    
    if st.button("🚀 Convert to HTML", type="primary", use_container_width=True):
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_pdf.read())
            tmp_path = Path(tmp.name)
        
        try:
            # Step 1: OCR Extraction
            with st.spinner("📖 Extracting text with OCR..."):
                blocks, images, page_images = run_async(
                    ocr_service.extract_from_pdf(tmp_path, save_page_images=False)
                )
                st.info(f"Extracted {len(blocks)} content blocks")
            
            # Step 2: PII Redaction (Secure Mode)
            pii_redactions = []
            if secure_mode:
                with st.spinner("🔒 Scanning for PII..."):
                    pii_config = {
                        "redact_emails": redact_emails,
                        "redact_phones": redact_phones,
                        "redact_names": redact_names,
                        "redact_ssn": redact_ssn,
                        "redact_credit_cards": redact_cards
                    }
                    blocks, pii_redactions = run_async(
                        pii_service.scan_and_redact(blocks, config=pii_config)
                    )
                    if pii_redactions:
                        st.warning(f"🔐 Redacted {len(pii_redactions)} PII items")
            
            # Step 3: Build Markdown
            with st.spinner("📝 Building Markdown..."):
                markdown_content = run_async(
                    markdown_service.build_markdown(blocks)
                )
            
            # Step 4: Generate HTML
            with st.spinner("🎨 Generating HTML..."):
                html_content = run_async(
                    html_generator.generate(
                        blocks=blocks,
                        theme=ThemeType(theme),
                        suggestions=[],
                        approved_components=[],
                        images=images
                    )
                )
            
            st.success("✅ Conversion Complete!")
            
            # --- Results ---
            tab1, tab2, tab3 = st.tabs(["🌐 HTML Preview", "📝 Markdown", "📊 Details"])
            
            with tab1:
                st.components.v1.html(html_content, height=600, scrolling=True)
                st.download_button(
                    "📥 Download HTML",
                    data=html_content,
                    file_name=f"{uploaded_pdf.name.replace('.pdf', '')}.html",
                    mime="text/html"
                )
            
            with tab2:
                st.code(markdown_content, language="markdown")
                st.download_button(
                    "📥 Download Markdown",
                    data=markdown_content,
                    file_name=f"{uploaded_pdf.name.replace('.pdf', '')}.md",
                    mime="text/markdown"
                )
            
            with tab3:
                col1, col2, col3 = st.columns(3)
                col1.metric("Content Blocks", len(blocks))
                col2.metric("Images Found", len(images))
                col3.metric("PII Redacted", len(pii_redactions))
                
                if pii_redactions:
                    st.subheader("PII Summary")
                    pii_summary = run_async(pii_service.get_pii_summary(pii_redactions))
                    for pii_type, info in pii_summary.items():
                        st.write(f"- **{pii_type}**: {info['count']} items ({info['avg_confidence']*100:.0f}% avg confidence)")
        
        finally:
            # Cleanup temp file
            tmp_path.unlink(missing_ok=True)

else:
    # Show instructions when no file uploaded
    st.info("👆 Upload a PDF file to get started")
    
    with st.expander("ℹ️ How it works"):
        st.markdown("""
        1. **Upload** - Drop your PDF file
        2. **OCR** - Text is extracted using PaddleOCR (runs locally)
        3. **Secure Mode** - PII is detected and redacted locally (optional)
        4. **Convert** - Markdown is generated and converted to styled HTML
        5. **Download** - Get your interactive HTML file
        
        **Privacy**: In Secure Mode, all PII detection happens locally. 
        Your sensitive data never leaves your machine.
        """)
