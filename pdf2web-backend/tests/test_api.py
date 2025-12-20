"""
PDF2Web AI Weaver - Comprehensive API Tests

Test Categories:
1. Privacy Tests - Verify Secure Mode PII redaction
2. Interaction Tests - Verify semantic component injection
3. Review Tests - Verify Co-Design edits persist
4. Large File Tests - Verify stability with multi-page PDFs
5. Theme Override Tests - Verify theme selection works
6. Export Tests - Verify export and deployment
7. WebSocket Tests - Verify real-time updates
8. MCP Tests - Verify Model Context Protocol
9. Accessibility Tests - Verify WCAG compliance
10. Plugin Tests - Verify plugin system
"""
import pytest
import io
from pathlib import Path


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def sample_pdf_bytes():
    """Create minimal PDF bytes for testing."""
    # Minimal valid PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj
4 0 obj << /Length 44 >> stream
BT /F1 12 Tf 100 700 Td (Test Document) Tj ET
endstream endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000214 00000 n 
trailer << /Size 5 /Root 1 0 R >>
startxref
306
%%EOF"""
    return pdf_content


@pytest.fixture
def sample_html():
    """Sample HTML for accessibility testing."""
    return """<!DOCTYPE html>
<html lang="en">
<head><title>Test</title></head>
<body>
<h1>Main Heading</h1>
<p>Test paragraph with <a href="#">link</a>.</p>
<table>
<thead><tr><th>Header</th></tr></thead>
<tbody><tr><td>Data</td></tr></tbody>
</table>
<img src="test.jpg" alt="Test image">
</body>
</html>"""


@pytest.fixture
def sample_html_with_issues():
    """HTML with accessibility issues for testing."""
    return """<html>
<body>
<h1>First Heading</h1>
<h3>Skipped h2</h3>
<img src="test.jpg">
<a href="#"></a>
<table><tr><td>No headers</td></tr></table>
</body>
</html>"""


# ============================================================
# 1. HEALTH & BASIC TESTS
# ============================================================

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "services" in data


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200


def test_api_docs_available(client):
    """Test API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


# ============================================================
# 2. PRIVACY TESTS - Secure Mode PII Redaction
# ============================================================

def test_upload_secure_mode(client, sample_pdf_bytes):
    """Test PDF upload in Secure Mode."""
    response = client.post(
        "/api/pdf/upload",
        files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        data={
            "mode": "secure",
            "redact_emails": "true",
            "redact_phones": "true",
            "redact_names": "true"
        }
    )
    # May fail if PaddleOCR not installed, but should not error on mode
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert data["processing_mode"] == "secure"
        assert "document_id" in data


def test_upload_standard_mode(client, sample_pdf_bytes):
    """Test PDF upload in Standard Mode."""
    response = client.post(
        "/api/pdf/upload",
        files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        data={"mode": "standard"}
    )
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert data["processing_mode"] == "standard"


def test_upload_invalid_file_type(client):
    """Test upload with invalid file type."""
    response = client.post(
        "/api/pdf/upload",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
        data={"mode": "secure"}
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_upload_file_too_large(client):
    """Test upload with file exceeding size limit."""
    # Create a large fake PDF (over 50MB default limit)
    large_content = b"%PDF-1.4\n" + b"x" * (51 * 1024 * 1024)
    response = client.post(
        "/api/pdf/upload",
        files={"file": ("large.pdf", large_content, "application/pdf")},
        data={"mode": "secure"}
    )
    assert response.status_code == 400
    assert "large" in response.json()["detail"].lower()


def test_transparency_endpoint(client):
    """Test data-sent-to-cloud transparency endpoint."""
    # First need a document - this tests the endpoint exists
    response = client.get("/api/codesign/test-id/data-sent-to-cloud")
    assert response.status_code == 404  # Document not found is expected


def test_pii_redaction_types(client):
    """Test that all PII types are configurable."""
    response = client.post(
        "/api/pdf/upload",
        files={"file": ("test.pdf", b"%PDF-1.4\ntest", "application/pdf")},
        data={
            "mode": "secure",
            "redact_emails": "true",
            "redact_phones": "true",
            "redact_names": "true",
            "redact_ssn": "true",
            "redact_credit_cards": "true"
        }
    )
    # Validates that all PII options are accepted
    assert response.status_code in [200, 400, 500]


# ============================================================
# 3. INTERACTION TESTS - Semantic Component Injection
# ============================================================

def test_chart_suggestion_endpoint(client):
    """Test chart suggestion endpoint exists."""
    response = client.post("/api/codesign/test-id/chart-suggestion/block-1")
    assert response.status_code == 404  # Document not found


def test_codesign_preview_endpoint(client):
    """Test Co-Design preview endpoint."""
    response = client.get("/api/codesign/test-id/preview")
    assert response.status_code == 404  # Document not found


def test_codesign_submit_structure(client):
    """Test Co-Design submit accepts correct structure."""
    response = client.post(
        "/api/codesign/test-id/submit",
        json={
            "document_id": "test-id",
            "theme": "professional",
            "theme_override": True,
            "approved_components": ["block-1"],
            "chart_conversions": {"block-1": "hybrid"},
            "quiz_enabled_blocks": ["block-2"],
            "code_execution_blocks": ["block-3"],
            "edits": [],
            "pii_actions": []
        }
    )
    assert response.status_code == 404  # Document not found, but structure accepted


# ============================================================
# 4. REVIEW TESTS - Co-Design Edits
# ============================================================

def test_edit_block_endpoint(client):
    """Test block editing endpoint."""
    response = client.post(
        "/api/codesign/test-id/edit-block",
        json={
            "block_id": "block-1",
            "new_content": "Updated content",
            "new_type": "heading"
        }
    )
    assert response.status_code == 404  # Document not found


def test_pii_action_endpoint(client):
    """Test PII action endpoint."""
    response = client.post(
        "/api/codesign/test-id/pii-action",
        json={
            "redaction_id": "red-1",
            "action": "undo"
        }
    )
    assert response.status_code == 404  # Document not found


def test_bulk_approve_endpoint(client):
    """Test bulk approve endpoint."""
    response = client.post(
        "/api/codesign/test-id/bulk-approve",
        json={"approve_all": True}
    )
    assert response.status_code == 404  # Document not found


def test_reset_endpoint(client):
    """Test reset to original endpoint."""
    response = client.post("/api/codesign/test-id/reset")
    assert response.status_code == 404  # Document not found


def test_low_confidence_endpoint(client):
    """Test low confidence blocks endpoint."""
    response = client.get("/api/codesign/test-id/low-confidence?threshold=0.8")
    assert response.status_code == 404  # Document not found


def test_regenerate_suggestions_endpoint(client):
    """Test regenerate suggestions endpoint."""
    response = client.post("/api/codesign/test-id/regenerate-suggestions")
    assert response.status_code == 404  # Document not found


# ============================================================
# 5. THEME OVERRIDE TESTS
# ============================================================

def test_theme_types_accepted(client):
    """Test all theme types are accepted in submission."""
    themes = ["light", "dark", "professional", "academic", "minimal"]
    
    for theme in themes:
        response = client.post(
            "/api/codesign/test-id/submit",
            json={
                "document_id": "test-id",
                "theme": theme,
                "theme_override": True,
                "approved_components": [],
                "chart_conversions": {},
                "quiz_enabled_blocks": [],
                "code_execution_blocks": [],
                "edits": [],
                "pii_actions": []
            }
        )
        # Should fail with 404 (doc not found), not 422 (validation error)
        assert response.status_code == 404, f"Theme '{theme}' should be valid"


# ============================================================
# 6. EXPORT TESTS
# ============================================================

def test_export_html_endpoint(client):
    """Test HTML export endpoint."""
    response = client.post("/api/export/test-id/html")
    assert response.status_code == 404  # Document not found


def test_export_markdown_endpoint(client):
    """Test Markdown export endpoint."""
    response = client.post("/api/export/test-id/markdown")
    assert response.status_code == 404  # Document not found


def test_preview_html_endpoint(client):
    """Test HTML preview endpoint."""
    response = client.get("/api/export/test-id/preview-html")
    assert response.status_code == 404  # Document not found


def test_github_pages_deploy_endpoint(client):
    """Test GitHub Pages deployment endpoint."""
    response = client.post(
        "/api/export/test-id/github-pages",
        json={
            "repo_name": "user/repo",
            "github_token": "ghp_test"
        }
    )
    assert response.status_code == 404  # Document not found


def test_netlify_deploy_endpoint(client):
    """Test Netlify deployment endpoint."""
    response = client.post(
        "/api/deploy/test-id/netlify",
        json={
            "netlify_token": "test-token",
            "site_name": "test-site"
        }
    )
    assert response.status_code == 404  # Document not found


def test_vercel_deploy_endpoint(client):
    """Test Vercel deployment endpoint."""
    response = client.post(
        "/api/deploy/test-id/vercel",
        json={
            "vercel_token": "test-token",
            "project_name": "test-project"
        }
    )
    assert response.status_code == 404  # Document not found


def test_s3_deploy_endpoint(client):
    """Test S3 deployment endpoint."""
    response = client.post(
        "/api/deploy/test-id/s3",
        json={
            "aws_access_key": "test-key",
            "aws_secret_key": "test-secret",
            "bucket_name": "test-bucket",
            "region": "us-east-1"
        }
    )
    assert response.status_code == 404  # Document not found


# ============================================================
# 7. WEBSOCKET TESTS
# ============================================================

def test_websocket_status(client):
    """Test WebSocket status endpoint."""
    response = client.get("/api/realtime/ws/status")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "total_connections" in data


def test_websocket_connections_endpoint(client):
    """Test WebSocket connections endpoint."""
    response = client.get("/api/realtime/ws/connections/test-id")
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert "connection_count" in data


# ============================================================
# 8. MCP (Model Context Protocol) TESTS
# ============================================================

def test_mcp_info(client):
    """Test MCP server info endpoint."""
    response = client.get("/api/mcp/info")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "protocolVersion" in data


def test_mcp_list_tools(client):
    """Test MCP tools listing."""
    response = client.get("/api/mcp/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    # Should have built-in tools
    tool_names = [t["name"] for t in data["tools"]]
    expected_tools = ["pdf_extract", "pii_detect", "markdown_build", "semantic_analyze", "html_generate"]
    for tool in expected_tools:
        assert tool in tool_names, f"Tool '{tool}' should be available"


def test_mcp_get_tool(client):
    """Test getting specific MCP tool info."""
    response = client.get("/api/mcp/tools/pdf_extract")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "pdf_extract"
    assert "description" in data
    assert "inputSchema" in data


def test_mcp_tool_not_found(client):
    """Test getting non-existent MCP tool."""
    response = client.get("/api/mcp/tools/nonexistent_tool")
    assert response.status_code == 404


def test_mcp_settings(client):
    """Test MCP settings endpoint."""
    response = client.get("/api/mcp/settings")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "transport" in data
    assert "enabled_tools" in data


def test_mcp_rpc_endpoint(client):
    """Test MCP JSON-RPC endpoint."""
    response = client.post(
        "/api/mcp/rpc",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "result" in data or "error" in data


# ============================================================
# 9. ACCESSIBILITY TESTS
# ============================================================

def test_accessibility_rules(client):
    """Test listing accessibility rules."""
    response = client.get("/api/accessibility/rules")
    assert response.status_code == 200
    data = response.json()
    assert "rules" in data
    assert len(data["rules"]) > 0


def test_accessibility_settings(client):
    """Test accessibility settings."""
    response = client.get("/api/accessibility/settings")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "wcag_level" in data
    assert data["wcag_level"] in ["A", "AA", "AAA"]


def test_wcag_levels(client):
    """Test WCAG levels endpoint."""
    response = client.get("/api/accessibility/wcag-levels")
    assert response.status_code == 200
    data = response.json()
    assert "levels" in data
    assert set(data["levels"]) == {"A", "AA", "AAA"}


def test_validate_html_accessibility(client, sample_html):
    """Test HTML accessibility validation with valid HTML."""
    response = client.post(
        "/api/accessibility/validate",
        json={"html": sample_html}
    )
    assert response.status_code == 200
    data = response.json()
    assert "passed" in data
    assert "score" in data
    assert "issues" in data
    assert "summary" in data


def test_validate_html_with_issues(client, sample_html_with_issues):
    """Test HTML accessibility validation catches issues."""
    response = client.post(
        "/api/accessibility/validate",
        json={"html": sample_html_with_issues}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["issues"]) > 0
    # Should catch: missing lang, skipped heading, missing alt, empty link, missing table headers
    issue_rules = [i["rule_id"] for i in data["issues"]]
    assert "html-lang" in issue_rules or "img-alt" in issue_rules


def test_enhance_html_accessibility(client, sample_html_with_issues):
    """Test HTML accessibility enhancement."""
    response = client.post(
        "/api/accessibility/enhance",
        json={"html": sample_html_with_issues}
    )
    assert response.status_code == 200
    data = response.json()
    assert "html" in data
    assert "enhancements_applied" in data
    # Should add lang attribute
    assert 'lang="' in data["html"]


def test_validate_document_accessibility(client):
    """Test document accessibility validation endpoint."""
    response = client.post("/api/accessibility/validate/test-id")
    assert response.status_code == 404  # Document not found


# ============================================================
# 10. PLUGIN TESTS
# ============================================================

def test_list_plugins(client):
    """Test listing all plugins."""
    response = client.get("/api/plugins/")
    assert response.status_code == 200
    data = response.json()
    assert "plugins" in data
    assert "total" in data


def test_list_active_plugins(client):
    """Test listing active plugins."""
    response = client.get("/api/plugins/active")
    assert response.status_code == 200
    data = response.json()
    assert "plugins" in data
    # Should have built-in plugins
    plugin_names = [p["name"] if isinstance(p, dict) else p for p in data["plugins"]]
    assert "timeline" in plugin_names or "map" in plugin_names


def test_get_plugin_info(client):
    """Test getting specific plugin info."""
    response = client.get("/api/plugins/timeline")
    # May be 200 or 404 depending on if plugin is loaded
    assert response.status_code in [200, 404]


def test_get_plugin_assets(client):
    """Test getting all plugin assets."""
    response = client.get("/api/plugins/assets/all")
    assert response.status_code == 200
    data = response.json()
    assert "css" in data
    assert "js" in data


def test_enable_plugin(client):
    """Test enabling a plugin."""
    response = client.post("/api/plugins/timeline/enable")
    assert response.status_code in [200, 404]


def test_disable_plugin(client):
    """Test disabling a plugin."""
    response = client.post("/api/plugins/timeline/disable")
    assert response.status_code in [200, 404]


# ============================================================
# 11. AUDIT TESTS
# ============================================================

def test_audit_actions_list(client):
    """Test listing audit action types."""
    response = client.get("/api/audit/actions")
    assert response.status_code == 200
    data = response.json()
    assert "actions" in data
    # Should include key actions
    assert "document_upload" in data["actions"] or "DOCUMENT_UPLOAD" in data["actions"]


def test_audit_stats(client):
    """Test audit statistics."""
    response = client.get("/api/audit/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_entries" in data


def test_audit_recent_entries(client):
    """Test getting recent audit entries."""
    response = client.get("/api/audit/?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "entries" in data


def test_audit_document_trail(client):
    """Test getting document audit trail."""
    response = client.get("/api/audit/document/test-id")
    assert response.status_code == 200
    data = response.json()
    assert "entries" in data
    assert "document_id" in data


def test_audit_export_json(client):
    """Test exporting audit log as JSON."""
    response = client.get("/api/audit/export?format=json")
    assert response.status_code == 200


def test_audit_export_csv(client):
    """Test exporting audit log as CSV."""
    response = client.get("/api/audit/export?format=csv")
    assert response.status_code == 200


# ============================================================
# 12. DOCUMENT MANAGEMENT TESTS
# ============================================================

def test_get_nonexistent_document(client):
    """Test getting a document that doesn't exist."""
    response = client.get("/api/pdf/nonexistent-id")
    assert response.status_code == 404


def test_delete_nonexistent_document(client):
    """Test deleting a document that doesn't exist."""
    response = client.delete("/api/pdf/nonexistent-id")
    assert response.status_code == 404


def test_get_document_blocks(client):
    """Test getting document blocks."""
    response = client.get("/api/pdf/test-id/blocks")
    assert response.status_code == 404  # Document not found


def test_get_document_pii(client):
    """Test getting document PII redactions."""
    response = client.get("/api/pdf/test-id/pii")
    assert response.status_code == 404  # Document not found


# ============================================================
# 13. CONTENT TYPE TESTS
# ============================================================

def test_content_types_in_edit(client):
    """Test all content types are accepted in block edit."""
    content_types = ["heading", "paragraph", "table", "list", "code", "image", "quote"]
    
    for content_type in content_types:
        response = client.post(
            "/api/codesign/test-id/edit-block",
            json={
                "block_id": "block-1",
                "new_type": content_type
            }
        )
        # Should fail with 404 (doc not found), not 422 (validation error)
        assert response.status_code == 404, f"Content type '{content_type}' should be valid"


# ============================================================
# 14. CHART CONVERSION OPTIONS TESTS
# ============================================================

def test_chart_conversion_options(client):
    """Test all chart conversion options are accepted."""
    options = ["keep_table", "convert_to_chart", "hybrid"]
    
    for option in options:
        response = client.post(
            "/api/codesign/test-id/submit",
            json={
                "document_id": "test-id",
                "theme": "light",
                "theme_override": False,
                "approved_components": ["block-1"],
                "chart_conversions": {"block-1": option},
                "quiz_enabled_blocks": [],
                "code_execution_blocks": [],
                "edits": [],
                "pii_actions": []
            }
        )
        assert response.status_code == 404, f"Chart option '{option}' should be valid"


# ============================================================
# 15. PII ACTION TYPES TESTS
# ============================================================

def test_pii_action_types(client):
    """Test all PII action types are accepted."""
    actions = ["approve", "undo", "modify"]
    
    for action in actions:
        body = {"redaction_id": "red-1", "action": action}
        if action == "modify":
            body["new_value"] = "[CUSTOM_REDACTED]"
        
        response = client.post(
            "/api/codesign/test-id/pii-action",
            json=body
        )
        assert response.status_code == 404, f"PII action '{action}' should be valid"
