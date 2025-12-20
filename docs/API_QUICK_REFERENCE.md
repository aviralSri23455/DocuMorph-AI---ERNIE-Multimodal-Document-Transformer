# PDF2Web API Quick Reference Card

## Base URL
```
http://localhost:8000/api
```

## Health Check
```bash
# App health
GET /health

# LLM + Vision status (NEW)
GET /api/health/ernie
# Returns: { configured, model, vision_enabled, vision_model, status }
```

---

## 🔄 Main Workflow (5 Steps)

### Step 1: Upload PDF
```bash
POST /pdf/upload
Content-Type: multipart/form-data

file: <PDF file>
mode: "secure" | "standard"
redact_emails: true
redact_phones: true
redact_names: true
redact_ssn: true
redact_credit_cards: true
```
**Returns:** `{ document_id, filename, total_pages, processing_mode }`

---

### Step 2: Get Preview
```bash
GET /codesign/{document_id}/preview
```
**Returns:**
```json
{
  "blocks": [...],
  "pii_redactions": [...],
  "theme_analysis": { "suggested_theme": "professional", "confidence": 0.85 },
  "semantic_suggestions": [...],
  "stats": { "total_blocks": 23, "low_confidence_count": 2, "pii_count": 4 }
}
```

---

### Step 3: User Edits (as needed)

**Edit Block:**
```bash
POST /codesign/{document_id}/edit-block
{ "block_id": "xxx", "new_content": "...", "new_type": "heading" }
```

**PII Action:**
```bash
POST /codesign/{document_id}/pii-action
{ "redaction_id": "xxx", "action": "approve" | "undo" | "modify" }
```

**Bulk Approve:**
```bash
POST /codesign/{document_id}/bulk-approve
{ "approve_all": true }
```

---

### Step 4: Generate HTML
```bash
POST /codesign/{document_id}/submit
{
  "document_id": "xxx",
  "theme": "light" | "dark" | "professional" | "academic" | "minimal",
  "theme_override": true,
  "approved_components": ["block-1", "block-2"],
  "chart_conversions": { "block-5": "hybrid" },
  "quiz_enabled_blocks": ["block-8"],
  "code_execution_blocks": ["block-10"]
}
```
**Returns:** `{ document_id, html, assets, theme, components_injected }`

---

### Step 5: Export/Deploy

**Download HTML:**
```bash
POST /export/{document_id}/html
GET /export/download/{document_id}/html
```

**Deploy to GitHub Pages:**
```bash
POST /export/{document_id}/github-pages
{ "repo_name": "user/repo", "github_token": "ghp_xxx" }
```

**Deploy to Netlify:**
```bash
POST /deploy/{document_id}/netlify
{ "netlify_token": "xxx", "site_name": "my-site" }
```

---

## 📊 Key Data Types

| Type | Values |
|------|--------|
| **ProcessingMode** | `secure`, `standard` |
| **ContentType** | `heading`, `paragraph`, `table`, `list`, `code`, `image`, `quote` |
| **ThemeType** | `light`, `dark`, `professional`, `academic`, `minimal` |
| **ChartOption** | `keep_table`, `convert_to_chart`, `hybrid` |
| **ComponentSuggestion** | `chart_bar`, `chart_line`, `chart_pie`, `quiz`, `code_block`, `timeline`, `map` |
| **PIIAction** | `approve`, `undo`, `modify` |
| **PIIType** | `EMAIL_ADDRESS`, `PHONE_NUMBER`, `PERSON`, `US_SSN`, `CREDIT_CARD` |

## 🆕 Vision-Enhanced Suggestions

When vision analysis is enabled, `semantic_suggestions` may include:
```json
{
  "block_id": "block-2",
  "suggestion": "chart_bar",
  "confidence": 0.85,
  "config": {
    "source": "vision",           // Detected via vision model
    "data_summary": "Sales data with 4 columns"
  }
}
```

New suggestion types from vision:
- `timeline` - Chronological event data detected
- `map` - Geographic/location data detected

---

## 🔌 WebSocket

**Connect:**
```javascript
ws = new WebSocket('ws://localhost:8000/api/realtime/ws')
```

**Subscribe to document:**
```javascript
ws.send(JSON.stringify({ action: 'subscribe', document_id: 'xxx' }))
```

**Events:** `processing_progress`, `pii_detected`, `block_updated`, `html_generation_completed`

---

## 🔍 Transparency Endpoint
```bash
GET /codesign/{document_id}/data-sent-to-cloud
```
Shows exactly what data is sent to ERNIE (sanitized content only in Secure Mode).

---

## ⚠️ Error Handling

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Bad Request (validation error) |
| 404 | Document not found |
| 500 | Server error |

**Error Response:**
```json
{ "detail": "Error message" }
```
