# PDF2Web AI Weaver - Frontend Integration Guide

This guide helps frontend developers integrate with the PDF2Web backend API to build the Co-Design UI using Streamlit, Gradio, React, or any other framework.

---

## 🆕 What's New

### Multimodal Vision Analysis
The backend now uses **vision models** (via Novita AI) to analyze PDF page images for better component detection:
- **Enhanced Table→Chart Detection**: Visual analysis suggests optimal chart types
- **Quiz Pattern Recognition**: Detects Q&A lists visually
- **Timeline/Map Detection**: Identifies chronological and location data

This happens automatically during semantic analysis - no frontend changes required!

### 🧠 Knowledge Graph Navigation (100% Real-Time)
Auto-generated interactive knowledge graphs that show how concepts relate:
- **Entity Extraction**: Sections, concepts, people, dates, locations
- **Relationship Detection**: references, builds_on, summarizes, defines
- **Interactive Visualization**: Force-directed graph with color-coded nodes
- **Click-to-Navigate**: Jump to any section by clicking nodes
- **Simplify Mode**: Reduce to top 15 nodes for cleaner preview

**Real Server Logs (Not Mock!):**
```
2026-01-01 22:16:07 | INFO | Generating knowledge graph for document 2bb7c96c-...
2026-01-01 22:16:24 | INFO | Generated graph with 23 nodes and 16 edges
```

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [API Base URL](#api-base-url)
3. [Complete User Flow](#complete-user-flow)
4. [API Endpoints Reference](#api-endpoints-reference)
5. [Data Models](#data-models)
6. [UI Components Checklist](#ui-components-checklist)
7. [WebSocket Integration](#websocket-integration)
8. [Code Examples](#code-examples)
9. [Error Handling](#error-handling)

---

## 🚀 Quick Start

### Backend Setup
```bash
cd pdf2web-backend
pip install -r requirements.txt
python -m spacy download en_core_web_lg
python run.py
```

### API Endpoints
- **REST API**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`
- **WebSocket**: `ws://localhost:8000/api/realtime/ws`
- **Health Check**: `http://localhost:8000/api/health/ernie` (shows vision status)

---

## 🔗 API Base URL

```
http://localhost:8000/api
```

All endpoints below are relative to this base URL.

---

## 🔄 Complete User Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 1: UPLOAD SCREEN                                                   │
│ ─────────────────────                                                   │
│ User Action: Select PDF + Choose Mode + Configure PII Options           │
│                                                                         │
│ API Call:                                                               │
│   POST /pdf/upload                                                      │
│   FormData: file, mode, redact_emails, redact_phones, etc.              │
│                                                                         │
│ Response: { document_id, filename, total_pages, processing_mode }       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 2: CO-DESIGN PREVIEW                                               │
│ ─────────────────────────                                               │
│ User Action: Review extracted content, PII, theme suggestions           │
│                                                                         │
│ API Call:                                                               │
│   GET /codesign/{document_id}/preview                                   │
│                                                                         │
│ Response: {                                                             │
│   blocks: [...],           // Content blocks with confidence            │
│   pii_redactions: [...],   // Detected PII for review                   │
│   theme_analysis: {...},   // Suggested theme + confidence              │
│   semantic_suggestions: [...], // Chart/Quiz suggestions                │
│   stats: { total_blocks, low_confidence_count, pii_count }              │
│ }                                                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 3: USER INTERACTIONS (Multiple API calls as user edits)            │
│ ────────────────────────────────────────────────────────────            │
│                                                                         │
│ 3a. Edit Block Content/Type:                                            │
│     POST /codesign/{document_id}/edit-block                             │
│     Body: { block_id, new_content?, new_type? }                         │
│                                                                         │
│ 3b. Handle PII Redaction:                                               │
│     POST /codesign/{document_id}/pii-action                             │
│     Body: { redaction_id, action: "approve"|"undo"|"modify" }           │
│                                                                         │
│ 3c. Get Chart Suggestion for Table:                                     │
│     POST /codesign/{document_id}/chart-suggestion/{block_id}            │
│                                                                         │
│ 3d. Bulk Approve Blocks:                                                │
│     POST /codesign/{document_id}/bulk-approve                           │
│     Body: { approve_all: true } OR { block_ids: [...] }                 │
│                                                                         │
│ 3e. Check What's Sent to Cloud (Transparency):                          │
│     GET /codesign/{document_id}/data-sent-to-cloud                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 4: SUBMIT & GENERATE HTML                                          │
│ ──────────────────────────────                                          │
│ User Action: Confirm all edits, select theme, approve components        │
│                                                                         │
│ API Call:                                                               │
│   POST /codesign/{document_id}/submit                                   │
│   Body: {                                                               │
│     document_id,                                                        │
│     theme: "light"|"dark"|"professional"|"academic"|"minimal",          │
│     theme_override: true/false,                                         │
│     approved_components: ["block-1", "block-2"],                        │
│     chart_conversions: { "block-5": "hybrid" },                         │
│     quiz_enabled_blocks: ["block-8"],                                   │
│     code_execution_blocks: ["block-10"]                                 │
│   }                                                                     │
│                                                                         │
│ Response: { document_id, html, assets, theme, components_injected }     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 5: PREVIEW & EXPORT                                                │
│ ────────────────────────                                                │
│                                                                         │
│ 5a. Preview HTML:                                                       │
│     GET /export/{document_id}/preview-html                              │
│     → Display in iframe                                                 │
│                                                                         │
│ 5b. Download HTML Package:                                              │
│     POST /export/{document_id}/html                                     │
│     GET /export/download/{document_id}/html                             │
│                                                                         │
│ 5c. Download Markdown:                                                  │
│     POST /export/{document_id}/markdown                                 │
│     GET /export/download/{document_id}/markdown                         │
│                                                                         │
│ 5d. Deploy to GitHub Pages:                                             │
│     POST /export/{document_id}/github-pages                             │
│     Body: { repo_name, github_token }                                   │
│                                                                         │
│ 5e. Deploy to Netlify:                                                  │
│     POST /deploy/{document_id}/netlify                                  │
│     Body: { netlify_token, site_name? }                                 │
│                                                                         │
│ 5f. Deploy to Vercel:                                                   │
│     POST /deploy/{document_id}/vercel                                   │
│     Body: { vercel_token, project_name? }                               │
│                                                                         │
│ 5g. Deploy to AWS S3:                                                   │
│     POST /deploy/{document_id}/s3                                       │
│     Body: { aws_access_key, aws_secret_key, bucket_name, region }       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📡 API Endpoints Reference

### PDF Processing

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| `POST` | `/pdf/upload` | Upload PDF | FormData (see below) | `UploadResponse` |
| `GET` | `/pdf/{document_id}` | Get extraction results | - | `ExtractionResponse` |
| `DELETE` | `/pdf/{document_id}` | Delete document | - | `{ message }` |
| `GET` | `/pdf/{document_id}/blocks` | Get content blocks | - | `{ blocks, total }` |
| `GET` | `/pdf/{document_id}/pii` | Get PII redactions | - | `{ redactions, summary }` |

#### Upload FormData Fields
```javascript
{
  file: File,                    // Required: PDF file
  mode: "secure" | "standard",   // Default: "secure"
  language: "en",                // OCR language
  redact_emails: true,           // Redact email addresses
  redact_phones: true,           // Redact phone numbers
  redact_names: true,            // Redact person names
  redact_ssn: true,              // Redact SSN
  redact_credit_cards: true      // Redact credit cards
}
```

### Co-Design Layer

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/codesign/{document_id}/preview` | Get full preview data |
| `GET` | `/codesign/{document_id}/low-confidence` | Get blocks needing review |
| `POST` | `/codesign/{document_id}/edit-block` | Edit single block |
| `POST` | `/codesign/{document_id}/pii-action` | Handle PII redaction |
| `POST` | `/codesign/{document_id}/bulk-approve` | Bulk approve blocks |
| `POST` | `/codesign/{document_id}/chart-suggestion/{block_id}` | Get chart suggestion |
| `GET` | `/codesign/{document_id}/data-sent-to-cloud` | Transparency view |
| `POST` | `/codesign/{document_id}/submit` | Generate final HTML |
| `POST` | `/codesign/{document_id}/regenerate-suggestions` | Refresh suggestions |
| `POST` | `/codesign/{document_id}/reset` | Reset to original |

### Export & Deploy

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/export/{document_id}/html` | Create HTML package |
| `POST` | `/export/{document_id}/markdown` | Create Markdown package |
| `GET` | `/export/download/{document_id}/{type}` | Download export |
| `GET` | `/export/{document_id}/preview-html` | Preview HTML |
| `POST` | `/export/{document_id}/github-pages` | Deploy to GitHub |
| `POST` | `/deploy/{document_id}/netlify` | Deploy to Netlify |
| `POST` | `/deploy/{document_id}/s3` | Deploy to AWS S3 |

### Knowledge Graph (Real-Time AI)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/knowledge-graph/{document_id}/generate` | Generate knowledge graph |
| `GET` | `/knowledge-graph/{document_id}` | Get generated graph |
| `POST` | `/knowledge-graph/{document_id}/simplify` | Simplify to top N nodes |
| `GET` | `/knowledge-graph/{document_id}/sidebar-data` | Get sidebar navigation |
| `POST` | `/deploy/{document_id}/vercel` | Deploy to Vercel |

---

## 📦 Data Models

### ContentBlock
```typescript
interface ContentBlock {
  id: string;
  type: "heading" | "paragraph" | "table" | "list" | "code" | "image" | "quote";
  content: string;
  page: number;
  confidence: number;  // 0.0 - 1.0 (highlight if < 0.8)
  bbox?: number[];
  metadata: {
    font_size?: number;
    is_bold?: boolean;
    user_edited?: boolean;
    user_approved?: boolean;
  };
}
```

### PIIRedaction
```typescript
interface PIIRedaction {
  id: string;
  original: string;      // Original text (show masked in UI)
  redacted: string;      // Redacted placeholder
  pii_type: "EMAIL_ADDRESS" | "PHONE_NUMBER" | "PERSON" | "US_SSN" | "CREDIT_CARD";
  start: number;
  end: number;
  confidence: number;
  block_id: string;
}
```

### ThemeAnalysis
```typescript
interface ThemeAnalysis {
  suggested_theme: "light" | "dark" | "professional" | "academic" | "minimal";
  confidence: number;    // Show as percentage
  reasoning: string;
}
```

### SemanticSuggestion
```typescript
interface SemanticSuggestion {
  block_id: string;
  suggestion: "chart_bar" | "chart_line" | "chart_pie" | "quiz" | "code_block" | "code_executable";
  confidence: number;
  config: object;
}
```

### CoDesignSubmission
```typescript
interface CoDesignSubmission {
  document_id: string;
  theme: "light" | "dark" | "professional" | "academic" | "minimal";
  theme_override: boolean;
  approved_components: string[];      // block IDs
  chart_conversions: {                // block_id → option
    [block_id: string]: "keep_table" | "convert_to_chart" | "hybrid"
  };
  quiz_enabled_blocks: string[];      // block IDs
  code_execution_blocks: string[];    // block IDs
  timeline_blocks: string[];          // block IDs (optional)
  map_blocks: string[];               // block IDs (optional)
  edits: CoDesignEdit[];
  pii_actions: PIIRedactionAction[];
}
```

---

## ✅ UI Components Checklist

### 1. Upload Screen
```
┌─────────────────────────────────────────────────────────────┐
│  📄 Upload PDF                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │         Drag & Drop PDF here                        │   │
│  │              or click to browse                     │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Processing Mode:                                           │
│  ○ 🔒 Secure Mode (Recommended)                            │
│  ○ 📡 Standard Mode                                        │
│                                                             │
│  PII Redaction Options (Secure Mode):                       │
│  ☑ Redact Emails                                           │
│  ☑ Redact Phone Numbers                                    │
│  ☑ Redact Names                                            │
│  ☑ Redact SSN                                              │
│  ☑ Redact Credit Cards                                     │
│                                                             │
│  [Upload & Process]                                         │
└─────────────────────────────────────────────────────────────┘
```

### 2. Co-Design Preview Screen
```
┌─────────────────────────────────────────────────────────────┐
│  📊 Co-Design Preview                    [Accept All] [Reset]│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Stats: 23 blocks | 2 low confidence | 4 PII redacted       │
│                                                             │
│  ┌─ Block 1 ─────────────────────────── Confidence: 95% ─┐ │
│  │ Type: [Heading ▼]                              [Edit] │ │
│  │ # Sales Report 2024                                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─ Block 2 ─────────────────────────── Confidence: 72% ─┐ │
│  │ Type: [Table ▼]                    ⚠️ LOW CONFIDENCE  │ │
│  │ | Product | Sales |                            [Edit] │ │
│  │ |---------|-------|                                   │ │
│  │ | A       | 100   |                                   │ │
│  │                                                       │ │
│  │ 💡 Suggestion: Convert to Bar Chart (80% confidence)  │ │
│  │ ○ Keep Table  ○ Convert to Chart  ● Hybrid (Both)    │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─ Block 3 ─────────────────────────── Confidence: 88% ─┐ │
│  │ Type: [List ▼]                                 [Edit] │ │
│  │ - What is Python? → A programming language            │ │
│  │ - What is JavaScript? → A web scripting language      │ │
│  │                                                       │ │
│  │ 💡 Suggestion: Enable Quiz Mode                       │ │
│  │ ☑ Enable Quiz Widget                                  │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. PII Review Panel
```
┌─────────────────────────────────────────────────────────────┐
│  🔒 PII Redactions (4 found)                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ EMAIL_ADDRESS ──────────────────────────────────────┐  │
│  │ Original: joh***@email.com                           │  │
│  │ Redacted: [EMAIL_REDACTED]                           │  │
│  │ Confidence: 95%                                      │  │
│  │ [Approve] [Undo] [Modify]                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ PHONE_NUMBER ───────────────────────────────────────┐  │
│  │ Original: 555-***-1234                               │  │
│  │ Redacted: [PHONE_REDACTED]                           │  │
│  │ Confidence: 90%                                      │  │
│  │ [Approve] [Undo] [Modify]                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4. Theme Selection
```
┌─────────────────────────────────────────────────────────────┐
│  🎨 Theme Selection                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AI Suggestion: Professional (85% confidence)               │
│  "Document appears to be a formal business report"          │
│                                                             │
│  ☑ Override AI suggestion                                   │
│                                                             │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                   │
│  │Light│ │Dark │ │Prof.│ │Acad.│ │Mini.│                   │
│  │  ○  │ │  ○  │ │  ●  │ │  ○  │ │  ○  │                   │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5. Transparency Modal
```
┌─────────────────────────────────────────────────────────────┐
│  🔍 What Data is Sent to Cloud?                      [X]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Mode: 🔒 Secure Mode                                       │
│                                                             │
│  ✅ Sent to ERNIE:                                          │
│     • Sanitized text structure (Markdown)                   │
│     • Theme preferences                                     │
│     • Component suggestions request                         │
│                                                             │
│  ❌ NOT Sent (Stays Local):                                 │
│     • Raw PDF file                                          │
│     • Images                                                │
│     • Original PII (emails, phones, names)                  │
│                                                             │
│  PII Redacted:                                              │
│     • EMAIL_ADDRESS: 2                                      │
│     • PHONE_NUMBER: 1                                       │
│     • PERSON: 1                                             │
│                                                             │
│  Preview of sanitized content:                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ # Sales Report                                       │  │
│  │ Contact: [EMAIL_REDACTED]                            │  │
│  │ Phone: [PHONE_REDACTED]                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6. Export Options
```
┌─────────────────────────────────────────────────────────────┐
│  📦 Export & Deploy                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Download:                                                  │
│  [📥 Download HTML (ZIP)]  [📥 Download Markdown]           │
│                                                             │
│  Deploy:                                                    │
│  ┌─ GitHub Pages ───────────────────────────────────────┐  │
│  │ Repository: [username/repo-name        ]             │  │
│  │ Token:      [ghp_xxxxxxxxxxxx          ]             │  │
│  │ [🚀 Deploy to GitHub Pages]                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Netlify ────────────────────────────────────────────┐  │
│  │ Token:     [xxxxxxxxxxxxxxxx           ]             │  │
│  │ Site Name: [my-pdf-site (optional)     ]             │  │
│  │ [🚀 Deploy to Netlify]                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Vercel ─────────────────────────────────────────────┐  │
│  │ Token:        [xxxxxxxxxxxxxxxx        ]             │  │
│  │ Project Name: [my-project (optional)   ]             │  │
│  │ [🚀 Deploy to Vercel]                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 WebSocket Integration

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/api/realtime/ws');

ws.onopen = () => {
  // Subscribe to document updates
  ws.send(JSON.stringify({
    action: 'subscribe',
    document_id: 'your-document-id'
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Event:', message.event, message.data);
};
```

### Event Types
```typescript
type WSEventType =
  | 'connected'
  | 'processing_started'
  | 'processing_progress'
  | 'processing_completed'
  | 'processing_error'
  | 'ocr_page_completed'
  | 'pii_detected'
  | 'block_updated'
  | 'suggestions_ready'
  | 'html_generation_completed'
  | 'deploy_completed';
```

### Event Payload Example
```json
{
  "event": "processing_progress",
  "timestamp": "2024-01-15T10:30:00Z",
  "document_id": "uuid",
  "data": {
    "stage": "ocr",
    "progress": 0.5,
    "message": "Processing page 5 of 10"
  }
}
```

---

## 💻 Code Examples

### JavaScript/TypeScript

#### Upload PDF
```typescript
async function uploadPDF(file: File, secureMode: boolean = true) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('mode', secureMode ? 'secure' : 'standard');
  formData.append('redact_emails', 'true');
  formData.append('redact_phones', 'true');
  formData.append('redact_names', 'true');

  const response = await fetch('http://localhost:8000/api/pdf/upload', {
    method: 'POST',
    body: formData
  });

  return response.json();
}
```

#### Get Preview
```typescript
async function getPreview(documentId: string) {
  const response = await fetch(
    `http://localhost:8000/api/codesign/${documentId}/preview`
  );
  return response.json();
}
```

#### Edit Block
```typescript
async function editBlock(documentId: string, blockId: string, newContent: string) {
  const response = await fetch(
    `http://localhost:8000/api/codesign/${documentId}/edit-block`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        block_id: blockId,
        new_content: newContent
      })
    }
  );
  return response.json();
}
```

#### Submit Co-Design
```typescript
async function submitCoDesign(documentId: string, options: {
  theme: string;
  themeOverride: boolean;
  chartConversions: Record<string, string>;
  quizBlocks: string[];
}) {
  const response = await fetch(
    `http://localhost:8000/api/codesign/${documentId}/submit`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_id: documentId,
        theme: options.theme,
        theme_override: options.themeOverride,
        approved_components: Object.keys(options.chartConversions),
        chart_conversions: options.chartConversions,
        quiz_enabled_blocks: options.quizBlocks,
        code_execution_blocks: [],
        edits: [],
        pii_actions: []
      })
    }
  );
  return response.json();
}
```

### Python (Streamlit)

```python
import streamlit as st
import requests

API_BASE = "http://localhost:8000/api"

# Upload
uploaded_file = st.file_uploader("Upload PDF", type="pdf")
secure_mode = st.checkbox("Secure Mode", value=True)

if uploaded_file and st.button("Process"):
    files = {"file": uploaded_file}
    data = {"mode": "secure" if secure_mode else "standard"}
    response = requests.post(f"{API_BASE}/pdf/upload", files=files, data=data)
    st.session_state.document_id = response.json()["document_id"]

# Preview
if "document_id" in st.session_state:
    preview = requests.get(
        f"{API_BASE}/codesign/{st.session_state.document_id}/preview"
    ).json()
    
    for block in preview["blocks"]:
        with st.expander(f"Block {block['id']} - {block['type']} ({block['confidence']*100:.0f}%)"):
            new_content = st.text_area("Content", block["content"], key=block["id"])
            if st.button("Save", key=f"save_{block['id']}"):
                requests.post(
                    f"{API_BASE}/codesign/{st.session_state.document_id}/edit-block",
                    json={"block_id": block["id"], "new_content": new_content}
                )
```

---

## ⚠️ Error Handling

### HTTP Status Codes
| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad Request | Show validation error |
| 404 | Not Found | Document doesn't exist |
| 500 | Server Error | Show error, retry |

### Error Response Format
```json
{
  "detail": "Error message here"
}
```

### Example Error Handling
```typescript
async function apiCall(url: string, options?: RequestInit) {
  const response = await fetch(url, options);
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'API Error');
  }
  
  return response.json();
}
```

---

## 🎯 Testing Checklist for Frontend

Use these scenarios to verify your UI implementation:

| Test | Steps | Expected Result |
|------|-------|-----------------|
| **Privacy Test** | Upload resume with phone number in Secure Mode | Phone appears as `[PHONE_REDACTED]` in preview |
| **Interaction Test** | Upload PDF with sales table, select "Convert to Chart" | Generated HTML contains Chart.js visualization |
| **Review Test** | Upload low-quality scan, edit OCR errors, submit | Corrections appear in final HTML |
| **Theme Override** | Select different theme than AI suggestion | Generated HTML uses selected theme |
| **Transparency** | Click "What data is sent to cloud?" | Modal shows sanitized content, no raw PII |

---

## 📞 Support

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: GET http://localhost:8000/health
