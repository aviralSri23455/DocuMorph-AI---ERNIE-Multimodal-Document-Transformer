"""
PDF2Web AI Weaver - Gradio Co-Design UI Example

This is a reference implementation showing how to build the Co-Design UI
using Gradio. Frontend teams can use this as a starting point.

Run with: python examples/gradio_app.py
"""
import gradio as gr
import requests
import json
from typing import Optional, Tuple

# Configuration
API_BASE = "http://localhost:8000/api"


def api_call(method: str, endpoint: str, **kwargs) -> Optional[dict]:
    """Make API call with error handling."""
    try:
        url = f"{API_BASE}{endpoint}"
        response = requests.request(method, url, **kwargs)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.json().get("detail", "Unknown error")}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend. Make sure server is running."}


def upload_pdf(
    file,
    mode: str,
    redact_emails: bool,
    redact_phones: bool,
    redact_names: bool,
    redact_ssn: bool,
    redact_cards: bool
) -> Tuple[str, str, str]:
    """Upload PDF and return document info."""
    if file is None:
        return "", "Please select a PDF file", ""
    
    files = {"file": (file.name, open(file.name, "rb"), "application/pdf")}
    data = {
        "mode": mode,
        "redact_emails": str(redact_emails).lower(),
        "redact_phones": str(redact_phones).lower(),
        "redact_names": str(redact_names).lower(),
        "redact_ssn": str(redact_ssn).lower(),
        "redact_credit_cards": str(redact_cards).lower()
    }
    
    result = api_call("POST", "/pdf/upload", files=files, data=data)
    
    if result and "error" not in result:
        doc_id = result["document_id"]
        status = f"✅ Uploaded: {result['filename']} ({result['total_pages']} pages)"
        
        # Get preview
        preview = api_call("GET", f"/codesign/{doc_id}/preview")
        if preview and "error" not in preview:
            preview_text = format_preview(preview)
        else:
            preview_text = "Error loading preview"
        
        return doc_id, status, preview_text
    else:
        return "", f"❌ Error: {result.get('error', 'Upload failed')}", ""


def format_preview(preview: dict) -> str:
    """Format preview data for display."""
    lines = []
    
    # Stats
    stats = preview.get("stats", {})
    lines.append(f"📊 Stats: {stats.get('total_blocks', 0)} blocks | "
                f"{stats.get('low_confidence_count', 0)} low confidence | "
                f"{stats.get('pii_count', 0)} PII redacted")
    lines.append("")
    
    # Theme suggestion
    theme = preview.get("theme_analysis")
    if theme:
        lines.append(f"🎨 Suggested Theme: {theme['suggested_theme']} "
                    f"({theme['confidence']*100:.0f}% confidence)")
        lines.append("")
    
    # Blocks
    lines.append("📝 Content Blocks:")
    lines.append("-" * 50)
    
    for block in preview.get("blocks", [])[:10]:  # Show first 10
        confidence = block.get("confidence", 1.0)
        warning = "⚠️ " if confidence < 0.8 else ""
        lines.append(f"{warning}[{block['type'].upper()}] ({confidence*100:.0f}%)")
        content = block["content"][:100] + "..." if len(block["content"]) > 100 else block["content"]
        lines.append(f"  {content}")
        lines.append("")
    
    # PII
    pii = preview.get("pii_redactions", [])
    if pii:
        lines.append("🔒 PII Redactions:")
        lines.append("-" * 50)
        for r in pii[:5]:  # Show first 5
            lines.append(f"  {r['pii_type']}: {r['original'][:3]}*** → {r['redacted']}")
    
    # Suggestions
    suggestions = preview.get("semantic_suggestions", [])
    if suggestions:
        lines.append("")
        lines.append("💡 Semantic Suggestions:")
        lines.append("-" * 50)
        for s in suggestions[:5]:
            lines.append(f"  Block {s['block_id'][:8]}: {s['suggestion']} ({s['confidence']*100:.0f}%)")
    
    return "\n".join(lines)


def generate_html(
    document_id: str,
    theme: str,
    theme_override: bool
) -> Tuple[str, str]:
    """Generate HTML from document."""
    if not document_id:
        return "Please upload a PDF first", ""
    
    # Get preview to find blocks
    preview = api_call("GET", f"/codesign/{document_id}/preview")
    if not preview or "error" in preview:
        return "Error loading document", ""
    
    # Build submission
    submission = {
        "document_id": document_id,
        "theme": theme,
        "theme_override": theme_override,
        "approved_components": [b["id"] for b in preview.get("blocks", [])],
        "chart_conversions": {},
        "quiz_enabled_blocks": [],
        "code_execution_blocks": [],
        "timeline_blocks": [],
        "map_blocks": [],
        "edits": [],
        "pii_actions": []
    }
    
    # Add chart conversions for tables
    for s in preview.get("semantic_suggestions", []):
        if "chart" in s["suggestion"]:
            submission["chart_conversions"][s["block_id"]] = "hybrid"
        elif s["suggestion"] == "quiz":
            submission["quiz_enabled_blocks"].append(s["block_id"])
        elif "code" in s["suggestion"]:
            submission["code_execution_blocks"].append(s["block_id"])
    
    result = api_call("POST", f"/codesign/{document_id}/submit", json=submission)
    
    if result and "error" not in result:
        html = result["html"]
        components = ", ".join(result.get("components_injected", []))
        status = f"✅ Generated with theme: {result['theme']}\nComponents: {components}"
        return status, html
    else:
        return f"❌ Error: {result.get('error', 'Generation failed')}", ""


def get_transparency(document_id: str) -> str:
    """Get transparency info about what data is sent to cloud."""
    if not document_id:
        return "Please upload a PDF first"
    
    data = api_call("GET", f"/codesign/{document_id}/data-sent-to-cloud")
    
    if data and "error" not in data:
        lines = [
            f"🔒 Mode: {'Secure' if data['is_secure_mode'] else 'Standard'}",
            "",
            "✅ SENT to Cloud:",
            "  - Sanitized text structure",
            "  - Theme preferences",
            "",
            "❌ NOT Sent (Stays Local):",
            "  - Raw PDF file",
            "  - Images",
            "  - Original PII",
            ""
        ]
        
        if data["pii_redacted"]:
            lines.append("📊 PII Redacted:")
            for pii_type, count in data["pii_redacted"].items():
                lines.append(f"  - {pii_type}: {count}")
        
        lines.append("")
        lines.append("📄 Content Preview:")
        lines.append("-" * 40)
        content = data["content_to_send"]
        lines.append(content[:500] + "..." if len(content) > 500 else content)
        
        return "\n".join(lines)
    else:
        return f"Error: {data.get('error', 'Unknown')}"


def create_ui():
    """Create Gradio interface."""
    
    with gr.Blocks(title="PDF2Web AI Weaver", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 📄 PDF2Web AI Weaver")
        gr.Markdown("Convert PDFs to interactive HTML with AI-powered semantic injection")
        
        # State
        document_id = gr.State("")
        
        with gr.Tabs():
            # Tab 1: Upload
            with gr.TabItem("1️⃣ Upload"):
                with gr.Row():
                    with gr.Column(scale=2):
                        file_input = gr.File(
                            label="Upload PDF",
                            file_types=[".pdf"]
                        )
                    
                    with gr.Column(scale=1):
                        mode = gr.Radio(
                            ["secure", "standard"],
                            label="Processing Mode",
                            value="secure"
                        )
                        
                        gr.Markdown("**PII Redaction Options:**")
                        redact_emails = gr.Checkbox(label="Redact Emails", value=True)
                        redact_phones = gr.Checkbox(label="Redact Phones", value=True)
                        redact_names = gr.Checkbox(label="Redact Names", value=True)
                        redact_ssn = gr.Checkbox(label="Redact SSN", value=True)
                        redact_cards = gr.Checkbox(label="Redact Credit Cards", value=True)
                
                upload_btn = gr.Button("🚀 Upload & Process", variant="primary")
                upload_status = gr.Textbox(label="Status", interactive=False)
            
            # Tab 2: Preview
            with gr.TabItem("2️⃣ Co-Design Preview"):
                preview_text = gr.Textbox(
                    label="Document Preview",
                    lines=20,
                    interactive=False
                )
                
                with gr.Row():
                    transparency_btn = gr.Button("🔍 View Transparency")
                
                transparency_output = gr.Textbox(
                    label="Data Transparency",
                    lines=15,
                    interactive=False,
                    visible=True
                )
            
            # Tab 3: Generate
            with gr.TabItem("3️⃣ Generate HTML"):
                with gr.Row():
                    theme = gr.Dropdown(
                        ["light", "dark", "professional", "academic", "minimal"],
                        label="Theme",
                        value="professional"
                    )
                    theme_override = gr.Checkbox(
                        label="Override AI suggestion",
                        value=False
                    )
                
                generate_btn = gr.Button("🎯 Generate HTML", variant="primary")
                generate_status = gr.Textbox(label="Status", interactive=False)
                
                html_output = gr.HTML(label="Preview")
        
        # Event handlers
        upload_btn.click(
            upload_pdf,
            inputs=[file_input, mode, redact_emails, redact_phones, redact_names, redact_ssn, redact_cards],
            outputs=[document_id, upload_status, preview_text]
        )
        
        transparency_btn.click(
            get_transparency,
            inputs=[document_id],
            outputs=[transparency_output]
        )
        
        generate_btn.click(
            generate_html,
            inputs=[document_id, theme, theme_override],
            outputs=[generate_status, html_output]
        )
    
    return app


if __name__ == "__main__":
    app = create_ui()
    app.launch(server_port=7860)
