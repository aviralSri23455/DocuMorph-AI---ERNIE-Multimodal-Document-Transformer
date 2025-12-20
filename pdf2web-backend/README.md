# DocuMorph AI - ERNIE Multimodal Document Transformer

> 🏆 **DEV.to Hackathon Entry** - Best ERNIE Multimodal Application using Novita API

Transform static PDFs into dynamic, responsive, and interactive HTML webpages with AI-powered semantic injection and multimodal vision analysis.

**Powered by:** ERNIE 4.5 + PaddleOCR + Novita AI

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [**Frontend Integration Guide**](../docs/FRONTEND_INTEGRATION_GUIDE.md) | Complete guide for frontend developers |
| [**API Quick Reference**](../docs/API_QUICK_REFERENCE.md) | Quick API reference card |
| [API Documentation](http://localhost:8000/docs) | Interactive Swagger UI (run server first) |

---

## 🎯 Three Ways to Use PDF2Web

### 1. React Frontend (Full Features)
```bash
cd pdf2web-frontend && npm install && npm run dev
# Open http://localhost:3000
```

### 2. Streamlit App (Python Native)
```bash
cd pdf2web-backend

# Activate virtual environment first
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Run Streamlit
streamlit run examples/streamlit_app.py --server.headless true

# Open http://localhost:8501
```

### 3. Built-in Dashboard (No Install)
```bash
cd pdf2web-backend && python run.py
# Open http://localhost:8000/ui
```

The built-in dashboard provides a complete Co-Design experience without any additional installation:

| Feature | Description |
|---------|-------------|
| **Upload Screen** | Drag & drop PDF upload with Secure Mode toggle |
| **Co-Design Layer** | Content blocks editor, PII review, semantic suggestions |
| **Theme Selection** | AI-suggested themes with override option |
| **Preview** | Live HTML preview with responsive sizing (desktop/tablet/mobile) |
| **Export** | Download HTML/Markdown, deploy to GitHub/Netlify |
| **Real-time Stats** | Content blocks, PII count, suggestions, low confidence indicators |
| **Transparency View** | See exactly what data is sent to cloud |

---

## 🐍 Streamlit Integration

The Streamlit app provides a Python-native UI for rapid prototyping and testing.

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit App (Port 8501)                │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Upload    │  │  Co-Design  │  │   Generate  │        │
│  │   Screen    │──▶│   Preview   │──▶│   Screen    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                │                │                 │
│         ▼                ▼                ▼                 │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              HTTP Requests to Backend                │  │
│  │                                                      │  │
│  │  POST /api/pdf/upload                               │  │
│  │  GET  /api/codesign/{id}/preview                    │  │
│  │  POST /api/codesign/{id}/edit-block                 │  │
│  │  POST /api/codesign/{id}/pii-action                 │  │
│  │  POST /api/codesign/{id}/submit                     │  │
│  │  POST /api/export/{id}/html                         │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Port 8000)                │
│                                                             │
│  • PaddleOCR (Local)     → Text extraction                 │
│  • Presidio/spaCy (Local) → PII detection                  │
│  • ERNIE (Cloud)          → Theme & HTML generation        │
│  • ERNIE Vision (Cloud)   → Component detection            │
└─────────────────────────────────────────────────────────────┘
```

### Running Streamlit

```bash
# Terminal 1: Start backend (required - Streamlit connects to this)
cd pdf2web-backend
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac
python run.py

# Terminal 2: Start Streamlit
cd pdf2web-backend
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac
streamlit run examples/streamlit_app.py --server.headless true
```

### 📁 Data Storage

Streamlit is just a UI - all data is stored by the **backend**:

| Location | Contents |
|----------|----------|
| `uploads/` | Uploaded PDFs, extracted images, page images |
| `outputs/` | Generated HTML packages |
| `temp/` | Temporary processing files |
| `data/` | TinyDB document store |
| `audit_logs/` | Audit log files (JSONL) |

### ✅ Verify Everything is Working

#### 1. Check Backend Health
```bash
# Basic health check
curl http://localhost:8000/health
# Expected: {"status": "healthy", "app": "PDF2Web AI Weaver", ...}

# Check ERNIE/LLM connection
curl http://localhost:8000/api/health/ernie
# Expected: {"status": "ok", "configured": true, "model": "baidu/ernie-4.5-21B-a3b", "vision_enabled": true, ...}
```

#### 2. Check Streamlit Connection
- Open http://localhost:8501
- Upload a test PDF
- If processing starts, Streamlit is connected to backend
- Check backend terminal for request logs:
  ```
  INFO: 127.0.0.1:XXXXX - "POST /api/pdf/upload HTTP/1.1" 200 OK
  ```

#### 3. Check React Frontend Connection
- Open http://localhost:3000
- Open Browser DevTools (F12) → Network tab
- Upload a PDF
- Look for `/api/pdf/upload` request with 200 status

#### 4. Test API Directly
```bash
# Upload a PDF
curl -X POST "http://localhost:8000/api/pdf/upload" \
  -F "file=@test.pdf" \
  -F "mode=secure"

# Get preview (use document_id from upload response)
curl "http://localhost:8000/api/codesign/{document_id}/preview"
```

### Streamlit Features

| Screen | Features |
|--------|----------|
| **Upload** | Mode selection (Secure/Standard), PII options, file upload |
| **Preview** | Content Blocks tab, PII Review tab, Theme tab, Settings tab |
| **Generate** | HTML preview, Download buttons, Deploy options |

### Streamlit Code Example

```python
import streamlit as st
import requests

API_BASE = "http://localhost:8000/api"

# Upload PDF
def upload_pdf(file, mode="secure"):
    files = {"file": (file.name, file, "application/pdf")}
    data = {"mode": mode, "redact_emails": "true"}
    response = requests.post(f"{API_BASE}/pdf/upload", files=files, data=data)
    return response.json()

# Get Co-Design Preview
def get_preview(doc_id):
    response = requests.get(f"{API_BASE}/codesign/{doc_id}/preview")
    return response.json()

# Edit Block
def edit_block(doc_id, block_id, new_content):
    requests.post(f"{API_BASE}/codesign/{doc_id}/edit-block", json={
        "block_id": block_id,
        "new_content": new_content
    })

# Generate HTML
def generate_html(doc_id, theme="professional"):
    response = requests.post(f"{API_BASE}/codesign/{doc_id}/submit", json={
        "theme": theme,
        "chart_conversions": {},
        "quiz_enabled_blocks": []
    })
    return response.json()

# Streamlit UI
st.title("PDF2Web AI Weaver")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")
if uploaded_file:
    result = upload_pdf(uploaded_file)
    st.session_state.doc_id = result["document_id"]
    
    preview = get_preview(st.session_state.doc_id)
    
    # Show blocks
    for block in preview["blocks"]:
        st.text_area(f"Block {block['type']}", block["content"])
    
    if st.button("Generate HTML"):
        html_result = generate_html(st.session_state.doc_id)
        st.components.v1.html(html_result["html"], height=600)
```

---

## 🆕 What's New

### Multimodal Vision Analysis (Novita AI)
- **Enhanced Component Detection**: Uses vision models to analyze PDF page images
- **Better Table→Chart Suggestions**: Visual analysis for accurate chart type recommendations  
- **Quiz Detection**: Identifies Q&A patterns visually
- **Timeline/Map Detection**: Detects chronological and geographic data
- **Configurable**: Enable/disable via `ENABLE_VISION_ANALYSIS` setting

---

## ✨ Features Overview

### 🔒 Secure Mode (Privacy First)
| Feature | Description |
|---------|-------------|
| **Local OCR** | PaddleOCR runs entirely on your device |
| **PII Auto-Detection** | Emails, phones, names, SSN, credit cards |
| **Presidio + spaCy** | Dual-engine PII detection |
| **Transparency** | See exactly what data is sent to cloud |

### 👁️ Multimodal Vision Analysis
| Feature | Description |
|---------|-------------|
| **Page Image Analysis** | Vision model analyzes PDF pages for better detection |
| **Enhanced Table Detection** | Visual analysis suggests optimal chart types |
| **Quiz Pattern Recognition** | Detects Q&A lists visually |
| **Timeline/Map Detection** | Identifies chronological and location data |

### 🧠 Knowledge Graph Navigation (NEW)
| Feature | Description |
|---------|-------------|
| **Auto-Generated Graph** | AI analyzes document to create interactive knowledge graph |
| **Entity Extraction** | Detects concepts, people, dates, locations, sections |
| **Relationship Detection** | Identifies references, builds-on, summarizes relationships |
| **Collapsible Sidebar** | Clickable nodes jump to sections or highlight content |
| **vis.js/Cytoscape.js** | Frontend-ready JSON for interactive visualization |
| **User Approval** | Preview/simplify graph in co-design layer |
| **Multi-Model Support** | Uses DeepSeek or ERNIE for entity/relation extraction |

### 🎨 Co-Design Interaction Layer
| Feature | Description |
|---------|-------------|
| **Theme Selection** | Light, Dark, Professional, Academic, Minimal |
| **AI Theme Suggestions** | With confidence scores |
| **Inline Editing** | Edit any block content directly |
| **PII Review** | Approve, undo, or modify redactions |

### 📊 Semantic Injection
| Feature | Description |
|---------|-------------|
| **Table → Chart** | Bar, Line, Pie charts via Chart.js |
| **List → Quiz** | Interactive quiz widgets |
| **Code Blocks** | Syntax highlighting + execution |
| **Timeline Widget** | Chronological event visualization |
| **Map Widget** | Interactive maps with Leaflet.js |

### 🔄 Real-Time Updates (WebSocket)
| Feature | Description |
|---------|-------------|
| **Processing Events** | Started, progress, completed, error |
| **OCR Events** | Page-by-page progress |
| **PII Events** | Detection notifications |
| **Block Updates** | Real-time edit notifications |

### 📦 Export & Deployment
| Feature | Description |
|---------|-------------|
| **HTML Package** | Download as ZIP |
| **Markdown Export** | Sanitized with images |
| **GitHub Pages** | One-click deploy |
| **Netlify/Vercel/S3** | Cloud deployment options |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ (3.11 recommended)
- 4GB+ RAM
- Novita AI API key ([Get $25 free credits](https://novita.ai/))

### 1. Install Dependencies

```bash
cd pdf2web-backend
pip install -r requirements.txt

# Download spaCy model (required for PII detection)
python -m spacy download en_core_web_lg
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```bash
# ERNIE API via Novita AI (Main Model)
ERNIE_MODEL=baidu/ernie-4.5-21B-a3b
ERNIE_API_KEY=your-novita-api-key
ERNIE_API_URL=https://api.novita.ai/v3/openai/chat/completions

# ERNIE Vision Model (Multimodal)
ERNIE_VISION_MODEL=baidu/ernie-4.5-vl-28b-a3b
ENABLE_VISION_ANALYSIS=true

# DeepSeek via Novita AI (MCP Mode - Optional)
DEEPSEEK_API_KEY=your-novita-api-key  # Same key!
DEEPSEEK_API_URL=https://api.novita.ai/v3/openai/chat/completions
DEEPSEEK_MODEL=deepseek/deepseek-v3-turbo
```

### 3. Run Server

```bash
python run.py
```

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

### 4. Test

```bash
# Health check
curl http://localhost:8000/api/health

# Check LLM + Vision status
curl http://localhost:8000/api/health/ernie
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL PROCESSING                         │
├─────────────────────────────────────────────────────────────┤
│  PDF Upload                                                 │
│      │                                                      │
│      ▼                                                      │
│  ┌─────────────┐    ┌─────────────┐                        │
│  │ PaddleOCR   │───▶│ Page Images │ (for vision analysis)  │
│  │ Extraction  │    │ Saved       │                        │
│  └──────┬──────┘    └──────┬──────┘                        │
│         │                  │                                │
│         ▼                  │                                │
│  ┌─────────────┐           │                                │
│  │ PII Scrub   │ (Presidio/spaCy)                          │
│  └──────┬──────┘           │                                │
│         │                  │                                │
│         ▼                  ▼                                │
│  ┌─────────────────────────────────────┐                   │
│  │      CO-DESIGN LAYER                │                   │
│  │  • Review blocks & PII              │                   │
│  │  • Select theme                     │                   │
│  │  • Choose chart/quiz options        │                   │
│  └──────────────┬──────────────────────┘                   │
└─────────────────┼───────────────────────────────────────────┘
                  │
                  ▼ (Sanitized text + Page images)
┌─────────────────────────────────────────────────────────────┐
│                    CLOUD (Novita AI - ERNIE)                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐                   │
│  │ ERNIE-3.5-8K (Text Model)           │                   │
│  │  • Theme analysis                   │                   │
│  │  • HTML generation                  │                   │
│  └─────────────────────────────────────┘                   │
│                                                             │
│  ┌─────────────────────────────────────┐                   │
│  │ ERNIE-4.0 (Vision Model)            │ ◄── NEW           │
│  │  • Table → Chart detection          │                   │
│  │  • Quiz pattern recognition         │                   │
│  │  • Timeline/Map detection           │                   │
│  └─────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT                                   │
│  • Responsive HTML5 + CSS3                                  │
│  • Chart.js visualizations                                  │
│  • Quiz widgets                                             │
│  • Code highlighting (Prism.js)                             │
│  • Timeline/Map widgets                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
pdf2web-backend/
├── app/
│   ├── api/routes/
│   │   ├── health.py          # Health + ERNIE status
│   │   ├── pdf.py             # PDF upload & extraction
│   │   ├── codesign.py        # Co-Design layer
│   │   ├── export.py          # Export endpoints
│   │   ├── deploy.py          # Netlify/S3/Vercel deploy
│   │   ├── websocket.py       # Real-time updates
│   │   ├── audit.py           # Audit logging
│   │   ├── plugins.py         # Plugin system
│   │   ├── accessibility.py   # WCAG validation
│   │   └── mcp.py             # Model Context Protocol
│   ├── services/
│   │   ├── ocr_service.py     # PaddleOCR + page image saving
│   │   ├── pii_service.py     # Presidio/spaCy PII detection
│   │   ├── ernie_service.py   # LLM + Vision API (Novita AI)
│   │   ├── html_generator.py  # HTML + widgets generation
│   │   ├── document_store.py  # Document state management
│   │   └── plugin_service.py  # Timeline/Map plugins
│   ├── models/schemas.py      # Pydantic models
│   └── config.py              # Configuration
├── docs/
│   ├── FRONTEND_INTEGRATION_GUIDE.md
│   └── API_QUICK_REFERENCE.md
├── examples/
│   ├── streamlit_app.py       # Streamlit UI
│   └── gradio_app.py          # Gradio UI
├── tests/
├── .env.example
├── requirements.txt
└── run.py
```

---

## 🔌 API Endpoints

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | App health check |
| `GET` | `/api/health` | App health check (alias) |
| `GET` | `/api/health/ernie` | LLM + Vision status |

### Built-in Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ui` | Full Co-Design Dashboard (no install needed) |

### PDF Processing
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/pdf/upload` | Upload PDF (Secure/Standard mode) |
| `GET` | `/api/pdf/{id}` | Get extraction results |
| `GET` | `/api/pdf/{id}/blocks` | Get content blocks |
| `GET` | `/api/pdf/{id}/pii` | Get PII redactions |

### Co-Design Layer
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/codesign/{id}/preview` | Full preview data |
| `POST` | `/api/codesign/{id}/edit-block` | Edit block |
| `POST` | `/api/codesign/{id}/pii-action` | Handle PII |
| `POST` | `/api/codesign/{id}/bulk-approve` | Bulk approve |
| `POST` | `/api/codesign/{id}/submit` | Generate HTML |
| `POST` | `/api/codesign/{id}/auto-convert` | 🤖 AI Auto-Convert (MCP Mode) |
| `GET` | `/api/codesign/{id}/data-sent-to-cloud` | Transparency |

### Export & Deploy
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/export/{id}/html` | Create HTML package |
| `POST` | `/api/export/{id}/github-pages` | Deploy to GitHub |
| `POST` | `/api/deploy/{id}/netlify` | Deploy to Netlify |
| `POST` | `/api/deploy/{id}/vercel` | Deploy to Vercel |
| `POST` | `/api/deploy/{id}/s3` | Deploy to AWS S3 |

### Audit Logging
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/audit/{id}/trail` | Get document audit trail |
| `GET` | `/api/audit/recent` | Get recent audit entries |
| `POST` | `/api/audit/export` | Export audit log as JSON |

### WebSocket (Real-Time)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `WS` | `/api/realtime/ws` | WebSocket connection |
| `GET` | `/api/realtime/ws/status` | Connection status |

### Knowledge Graph
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/knowledge-graph/{id}/generate` | Generate knowledge graph |
| `GET` | `/api/knowledge-graph/{id}` | Get generated graph |
| `POST` | `/api/knowledge-graph/{id}/simplify` | Simplify for preview |
| `GET` | `/api/knowledge-graph/{id}/sidebar-data` | Get sidebar navigation data |
| `GET` | `/api/knowledge-graph/{id}/entity-types` | Get entity/relationship types |

---

## 🔧 Configuration

### Core Settings
| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment | `development` |
| `DEBUG` | Debug mode | `true` |
| `PORT` | Server port | `8000` |
| `SECRET_KEY` | Secret key for sessions | `change-me-in-production` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000,http://localhost:8501` |

### LLM API (Novita AI - ERNIE Models)
| Variable | Description | Default |
|----------|-------------|---------|
| `ERNIE_MODEL` | Text model | `baidu/ernie-3.5-8k` |
| `ERNIE_API_KEY` | API key | Required (Novita AI) |
| `ERNIE_API_URL` | API endpoint | `https://api.novita.ai/v3/openai/chat/completions` |
| `ERNIE_VISION_MODEL` | Vision model | `baidu/ernie-4.5-vl-28b-a3b` |
| `ENABLE_VISION_ANALYSIS` | Enable vision | `true` |
| `ERNIE_MAX_TOKENS` | Max tokens per request | `1000` |
| `ERNIE_TEMPERATURE` | Model temperature | `0.7` |

### DeepSeek API (MCP Mode - Optional)
| Variable | Description | Default |
|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | Same as ERNIE (Novita AI) | Uses `ERNIE_API_KEY` |
| `DEEPSEEK_API_URL` | API endpoint | `https://api.novita.ai/v3/openai/chat/completions` |
| `DEEPSEEK_MODEL` | Model name | `deepseek/deepseek-v3-turbo` |
| `ENABLE_KNOWLEDGE_GRAPH` | Enable knowledge graph | `true` |

### Privacy
| Variable | Description | Default |
|----------|-------------|---------|
| `DEFAULT_SECURE_MODE` | Default to secure | `true` |
| `DEFAULT_PII_TYPES` | PII types to redact | `EMAIL_ADDRESS,PHONE_NUMBER,PERSON,US_SSN,CREDIT_CARD` |
| `PII_DETECTION_THRESHOLD` | Confidence threshold | `0.7` |

### OCR
| Variable | Description | Default |
|----------|-------------|---------|
| `OCR_LANGUAGE` | Language | `en` |
| `MAX_PAGES` | Max pages | `100` |
| `IMAGE_DPI` | Image DPI | `300` |
| `OCR_CONFIDENCE_THRESHOLD` | OCR confidence threshold | `0.8` |
| `OCR_CONCURRENT_PAGES` | Concurrent page processing | `4` |

### Audit Logging
| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_AUDIT_LOG` | Enable audit logging | `true` |
| `AUDIT_LOG_DIR` | Audit log directory | `./audit_logs` |
| `TIMESTAMP_FORMAT` | Timestamp format (iso/unix/human) | `iso` |
| `TRACK_PII_ACTIONS` | Track PII approve/undo | `true` |
| `TRACK_BLOCK_EDITS` | Track content edits | `true` |
| `TRACK_THEME_CHANGES` | Track theme changes | `true` |
| `AUDIT_LOG_RETENTION_DAYS` | Log retention period | `90` |

### MCP (Model Context Protocol)
| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_MCP_SERVER` | Enable MCP server | `true` |
| `MCP_SERVER_HOST` | MCP host | `localhost` |
| `MCP_SERVER_PORT` | MCP port | `8001` |
| `MCP_TRANSPORT` | Transport type (sse/stdio/websocket) | `sse` |
| `MCP_ENABLED_TOOLS` | Enabled MCP tools | `pdf_extract,pii_detect,markdown_build,semantic_analyze,html_generate` |
| `MCP_AUTH_ENABLED` | Enable MCP authentication | `false` |

### Interactive Components
| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_CHART_SUGGESTIONS` | Enable chart suggestions | `true` |
| `ENABLE_QUIZ_SUGGESTIONS` | Enable quiz suggestions | `true` |
| `ENABLE_CODE_EXECUTION` | Enable code execution | `true` |
| `ENABLE_TIMELINE_WIDGET` | Enable timeline widget | `true` |
| `ENABLE_MAP_WIDGET` | Enable map widget | `true` |
| `CHART_ANIMATION_ENABLED` | Enable chart animations | `true` |

### Accessibility
| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_ACCESSIBILITY_CHECKS` | Enable WCAG checks | `true` |
| `WCAG_LEVEL` | WCAG compliance level (A/AA/AAA) | `AA` |
| `AUTO_ARIA_LABELS` | Auto-generate ARIA labels | `true` |
| `KEYBOARD_NAVIGATION` | Enable keyboard nav | `true` |

### WebSocket (Real-time Updates)
| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_WEBSOCKET` | Enable WebSocket | `true` |
| `WEBSOCKET_PORT` | WebSocket port | `8002` |
| `WEBSOCKET_PING_INTERVAL` | Ping interval (seconds) | `30` |

### Plugin System
| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_PLUGINS` | Enable plugin system | `true` |
| `PLUGINS_DIR` | Plugins directory | `./plugins` |
| `ENABLED_PLUGINS` | Enabled plugins | `charts,quizzes,code_blocks` |
| `PLUGIN_SANDBOX_MODE` | Run plugins in sandbox | `true` |

---

## 📤 Example: Upload & Process PDF

```bash
# 1. Upload PDF in Secure Mode
curl -X POST "http://localhost:8000/api/pdf/upload" \
  -F "file=@document.pdf" \
  -F "mode=secure" \
  -F "redact_emails=true"

# Response: { "document_id": "uuid", "total_pages": 5 }

# 2. Get Co-Design Preview
curl "http://localhost:8000/api/codesign/{document_id}/preview"

# 3. Submit & Generate HTML
curl -X POST "http://localhost:8000/api/codesign/{document_id}/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "professional",
    "chart_conversions": {"block-2": "hybrid"},
    "quiz_enabled_blocks": ["block-5"]
  }'

# 4. Download HTML
curl -X POST "http://localhost:8000/api/export/{document_id}/html"
```

---

## 🔄 WebSocket Real-Time Updates

```javascript
// Connect
const ws = new WebSocket('ws://localhost:8000/api/realtime/ws');

// Subscribe to document
ws.send(JSON.stringify({
  action: 'subscribe',
  document_id: 'your-document-id'
}));

// Listen for events
ws.onmessage = (event) => {
  const { event: eventType, data } = JSON.parse(event.data);
  
  switch(eventType) {
    case 'processing_progress':
      updateProgressBar(data.progress);
      break;
    case 'pii_detected':
      showPIINotification(data);
      break;
    case 'html_generation_completed':
      showPreview(data.html);
      break;
  }
};
```

### Event Types
| Event | Description |
|-------|-------------|
| `processing_started` | PDF processing began |
| `processing_progress` | Progress update (0-100%) |
| `ocr_page_completed` | Single page OCR done |
| `pii_detected` | PII found |
| `block_updated` | Block was edited |
| `suggestions_ready` | Semantic suggestions ready |
| `html_generation_completed` | HTML generated |
| `processing_error` | Error occurred |

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_api.py::test_health_check
```

---

## 📊 Supported ERNIE Models (Novita AI)

### Text Models (for theme/HTML generation)
| Model | Cost | Speed | Quality |
|-------|------|-------|---------|
| `baidu/ernie-3.5-8k` | $ | Fast | Good (Recommended) |
| `baidu/ernie-4.0-8k` | $$ | Medium | Better |
| `baidu/ernie-4.0-8k-preview` | $$ | Medium | Best |

### Vision-Capable Models (for component detection)
| Model | Cost | Speed | Quality |
|-------|------|-------|---------|
| `baidu/ernie-4.0-8k-preview` | $$ | Medium | Good |

> **Note**: ERNIE models on Novita AI provide excellent Chinese and English support with strong reasoning capabilities.

---

## 🎯 Complete Multimodal Flow: Frontend User Journey

This section explains **exactly how the system works** when a frontend user uploads a PDF, including all features: Hybrid Local/Cloud AI, Privacy Mode, Co-Design Layer, Multimodal Vision, and MCP.

### 📋 Step-by-Step Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND USER UPLOADS PDF                            │
│                     (React/Vue/Streamlit/Gradio UI)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: PDF UPLOAD (POST /api/pdf/upload)                                  │
│  ─────────────────────────────────────────                                  │
│  User selects:                                                              │
│    • mode: "secure" or "standard"                                           │
│    • PII options: redact_emails, redact_phones, redact_names, etc.          │
│                                                                             │
│  Backend receives PDF → Saves to ./uploads/{document_id}.pdf                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: LOCAL OCR EXTRACTION (PaddleOCR-VL)                                │
│  ───────────────────────────────────────────                                │
│  🖥️ RUNS LOCALLY - NO CLOUD                                                 │
│                                                                             │
│  • Extract text blocks with bounding boxes                                  │
│  • Detect content types: heading, paragraph, table, list, code              │
│  • Calculate OCR confidence scores (0-100%)                                 │
│  • Extract embedded images → Save to ./uploads/images/                      │
│  • 📸 Save page images → ./uploads/pages/ (for vision analysis)             │
│                                                                             │
│  Output: List[ContentBlock] + List[image_paths] + Dict[page_images]         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: LOCAL PII DETECTION (Secure Mode Only)                             │
│  ──────────────────────────────────────────────                             │
│  🔒 RUNS LOCALLY - NO CLOUD                                                 │
│                                                                             │
│  If mode == "secure":                                                       │
│    • Presidio analyzer scans all text blocks                                │
│    • Detects: EMAIL, PHONE, PERSON, SSN, CREDIT_CARD, etc.                  │
│    • Redacts PII: "john@email.com" → "[EMAIL_REDACTED]"                     │
│    • Creates PIIRedaction records with original/redacted values             │
│    • User can UNDO redactions later in Co-Design                            │
│                                                                             │
│  Output: Sanitized blocks + PIIRedaction list                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: MARKDOWN BUILDER                                                   │
│  ────────────────────────                                                   │
│  🖥️ RUNS LOCALLY                                                            │
│                                                                             │
│  • Convert ContentBlocks → Structured Markdown                              │
│  • Preserve: headings (#), tables (|), lists (-), code (```)                │
│  • Add metadata comments: <!-- block:id confidence:0.95 -->                 │
│                                                                             │
│  Output: Markdown string (intermediate representation)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 5: CO-DESIGN LAYER (Human-in-the-Loop)                                │
│  ───────────────────────────────────────────                                │
│  👤 USER INTERACTION VIA FRONTEND UI                                        │
│                                                                             │
│  GET /api/codesign/{id}/preview returns:                                    │
│    • blocks: All content blocks with confidence scores                      │
│    • pii_redactions: Detected PII (user can approve/undo)                   │
│    • theme_analysis: AI suggested theme + confidence                        │
│    • semantic_suggestions: Table→Chart, List→Quiz suggestions               │
│    • low_confidence_blocks: Blocks needing review                           │
│                                                                             │
│  User can:                                                                  │
│    ✏️ Edit block content (fix OCR errors)                                   │
│    🔄 Change block type (paragraph → heading)                               │
│    ✅ Approve/Undo PII redactions                                           │
│    🎨 Override theme suggestion                                             │
│    📊 Choose chart options: keep_table / convert_to_chart / hybrid          │
│    ❓ Enable quiz mode for lists                                            │
│    💻 Enable code execution for code blocks                                 │
│    📅 Enable timeline widget                                                │
│    🗺️ Enable map widget                                                     │
│                                                                             │
│  🔍 Transparency: GET /api/codesign/{id}/data-sent-to-cloud                 │
│     Shows exactly what will be sent to ERNIE (no raw PII, no images)        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 6: MULTIMODAL VISION ANALYSIS (ERNIE-4.0 Vision)                      │
│  ─────────────────────────────────────────────────────                      │
│  ☁️ CLOUD API - Novita AI                                                   │
│                                                                             │
│  If ENABLE_VISION_ANALYSIS=true:                                            │
│    • Send page images (base64) to ERNIE-4.0-8k-preview                      │
│    • Vision model analyzes each page visually                               │
│                                                                             │
│  Vision Detection:                                                          │
│    📊 Tables → Suggests best chart type (bar/line/pie)                      │
│    ❓ Q&A Lists → Suggests quiz widget                                      │
│    📅 Chronological data → Suggests timeline widget                         │
│    🗺️ Location data → Suggests map widget                                   │
│                                                                             │
│  Returns: Enhanced SemanticSuggestions with visual confidence               │
│                                                                             │
│  💡 WHY VISION? Text-only analysis might miss:                              │
│     - Table structure (columns, headers)                                    │
│     - Visual Q&A patterns (numbered options)                                │
│     - Timeline layouts                                                      │
│     - Geographic references in context                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 7: THEME ANALYSIS (ERNIE-3.5 Text)                                    │
│  ───────────────────────────────────────                                    │
│  ☁️ CLOUD API - Novita AI                                                   │
│                                                                             │
│  • Send sanitized Markdown to ERNIE-3.5-8k                                  │
│  • Analyze document style and content                                       │
│  • Suggest theme: light/dark/professional/academic/minimal                  │
│  • Return confidence score and reasoning                                    │
│                                                                             │
│  Example response:                                                          │
│    { "theme": "professional", "confidence": 0.85,                           │
│      "reasoning": "Document contains business terminology..." }             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 8: USER SUBMITS (POST /api/codesign/{id}/submit)                      │
│  ─────────────────────────────────────────────────────                      │
│  👤 USER CLICKS "GENERATE HTML"                                             │
│                                                                             │
│  Submission includes:                                                       │
│    • theme: Selected theme (or AI suggestion)                               │
│    • theme_override: true if user changed AI suggestion                     │
│    • approved_components: Block IDs for interactive widgets                 │
│    • chart_conversions: { "block-1": "hybrid", "block-3": "pie" }           │
│    • quiz_enabled_blocks: ["block-5", "block-8"]                            │
│    • code_execution_blocks: ["block-12"]                                    │
│    • timeline_blocks: ["block-15"]                                          │
│    • map_blocks: ["block-18"]                                               │
│    • edits: Any content/type changes made                                   │
│    • pii_actions: Approve/undo decisions                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 9: HTML GENERATION (ERNIE + Local Generator)                          │
│  ─────────────────────────────────────────────────                          │
│  ☁️ CLOUD + 🖥️ LOCAL                                                        │
│                                                                             │
│  Option A: ERNIE generates HTML (cloud)                                     │
│    • Send Markdown + theme + component instructions                         │
│    • ERNIE returns complete HTML with CSS                                   │
│                                                                             │
│  Option B: Local HTML Generator (faster, no cloud)                          │
│    • html_generator.py builds HTML locally                                  │
│    • Injects Chart.js, Quiz.js, Prism.js widgets                            │
│    • Applies theme CSS                                                      │
│                                                                             │
│  Interactive Components Injected:                                           │
│    📊 Chart.js: Bar, Line, Pie charts with tooltips                         │
│    ❓ Quiz.js: Multiple choice with feedback                                │
│    💻 Prism.js: Syntax highlighting + copy button                           │
│    ▶️ Code Execution: Run JavaScript in browser                             │
│    📅 Timeline: Horizontal/vertical event display                           │
│    🗺️ Leaflet.js: Interactive maps with markers                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 10: OUTPUT & EXPORT                                                   │
│  ────────────────────────                                                   │
│                                                                             │
│  Response includes:                                                         │
│    • html: Complete HTML document                                           │
│    • assets: List of included resources                                     │
│    • theme: Applied theme                                                   │
│    • components_injected: List of widgets added                             │
│                                                                             │
│  Export Options:                                                            │
│    📦 POST /api/export/{id}/html → Download ZIP                             │
│    📝 POST /api/export/{id}/markdown → Markdown + images                    │
│    🐙 POST /api/export/{id}/github-pages → Deploy to GitHub                 │
│    🌐 POST /api/deploy/{id}/netlify → Deploy to Netlify                     │
│    ▲ POST /api/deploy/{id}/vercel → Deploy to Vercel                        │
│    ☁️ POST /api/deploy/{id}/s3 → Deploy to AWS S3                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 🔄 How Multiple ERNIE Models Work Together

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NOVITA AI - ERNIE MODEL ORCHESTRATION                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ERNIE-3.5-8K (Text Model) - COST EFFECTIVE                         │   │
│  │  ─────────────────────────────────────────                          │   │
│  │  Used for:                                                          │   │
│  │    • Theme analysis (analyze document style)                        │   │
│  │    • HTML generation (convert Markdown → HTML)                      │   │
│  │    • Text-based semantic analysis (fallback)                        │   │
│  │                                                                     │   │
│  │  Cost: ~$0.001 per 1K tokens                                        │   │
│  │  Speed: Fast (1-3 seconds)                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ERNIE-4.0-8K-Preview (Vision Model) - MULTIMODAL                   │   │
│  │  ────────────────────────────────────────────────                   │   │
│  │  Used for:                                                          │   │
│  │    • Page image analysis (visual understanding)                     │   │
│  │    • Table structure detection (columns, headers)                   │   │
│  │    • Chart type recommendation (bar vs line vs pie)                 │   │
│  │    • Quiz pattern recognition (Q&A layouts)                         │   │
│  │    • Timeline/Map data detection                                    │   │
│  │                                                                     │   │
│  │  Cost: ~$0.003 per 1K tokens + image                                │   │
│  │  Speed: Medium (3-5 seconds per page)                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  WHEN EACH MODEL IS CALLED                                          │   │
│  │  ─────────────────────────────                                      │   │
│  │                                                                     │   │
│  │  1. PDF Upload → OCR (LOCAL, no model)                              │   │
│  │  2. PII Detection → Presidio/spaCy (LOCAL, no model)                │   │
│  │  3. Vision Analysis → ERNIE-4.0 Vision (CLOUD, per page)            │   │
│  │  4. Theme Analysis → ERNIE-3.5 Text (CLOUD, once)                   │   │
│  │  5. HTML Generation → ERNIE-3.5 Text OR Local (configurable)        │   │
│  │                                                                     │   │
│  │  Total API calls for 5-page PDF:                                    │   │
│  │    • 5 vision calls (one per page) - if enabled                     │   │
│  │    • 1 theme analysis call                                          │   │
│  │    • 1 HTML generation call                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 🔒 Privacy: What Data Goes Where?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW & PRIVACY                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ✅ STAYS LOCAL (Never leaves your server):                                 │
│  ─────────────────────────────────────────                                  │
│    • Original PDF file                                                      │
│    • Raw OCR output                                                         │
│    • Original PII (before redaction)                                        │
│    • Extracted images (unless user authorizes)                              │
│    • Audit logs                                                             │
│    • User session data                                                      │
│                                                                             │
│  ☁️ SENT TO CLOUD (Novita AI):                                              │
│  ─────────────────────────────                                              │
│    • Sanitized text (PII redacted in Secure Mode)                           │
│    • Page images (for vision analysis - optional)                           │
│    • Theme preferences                                                      │
│    • Component configuration                                                │
│                                                                             │
│  🔍 TRANSPARENCY ENDPOINT:                                                  │
│  ─────────────────────────                                                  │
│    GET /api/codesign/{id}/data-sent-to-cloud                                │
│                                                                             │
│    Returns:                                                                 │
│    {                                                                        │
│      "is_secure_mode": true,                                                │
│      "pii_redacted": {                                                      │
│        "EMAIL_ADDRESS": 3,                                                  │
│        "PHONE_NUMBER": 2,                                                   │
│        "PERSON": 5                                                          │
│      },                                                                     │
│      "content_to_send": "# Document Title\n\n[EMAIL_REDACTED]...",          │
│      "images_included": false,                                              │
│      "page_images_for_vision": true                                         │
│    }                                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 🔌 MCP (Model Context Protocol) - Complete Integration Guide

#### ⚠️ IMPORTANT: MCP vs Frontend - Understanding the Difference

```
┌─────────────────────────────────────────────────────────────────────────────┐
│           🚨 WHO USES WHAT? - CRITICAL DISTINCTION 🚨                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  👤 FRONTEND USER (Human uploading PDF via UI)                      │   │
│  │  ─────────────────────────────────────────────                      │   │
│  │                                                                     │   │
│  │  Uses: REST API (/api/pdf/upload, /api/codesign/*, etc.)            │   │
│  │                                                                     │   │
│  │  Flow:                                                              │   │
│  │    User → React/Streamlit UI → REST API → Backend → HTML            │   │
│  │                                                                     │   │
│  │  The user NEVER interacts with MCP directly!                        │   │
│  │  MCP endpoints are NOT shown in the frontend UI.                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  🤖 AI ASSISTANT (Claude, GPT, Cursor calling tools)                │   │
│  │  ───────────────────────────────────────────────                    │   │
│  │                                                                     │   │
│  │  Uses: MCP API (/api/mcp/tools/*, /api/mcp/rpc)                     │   │
│  │                                                                     │   │
│  │  Flow:                                                              │   │
│  │    AI Assistant → MCP Protocol → Backend Tools → Result to AI       │   │
│  │                                                                     │   │
│  │  MCP is for PROGRAMMATIC access by AI systems!                      │   │
│  │  No human UI involved - AI calls tools directly.                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  📊 COMPARISON TABLE                                                │   │
│  │  ───────────────────                                                │   │
│  │                                                                     │   │
│  │  Feature              │ Frontend User    │ AI via MCP               │   │
│  │  ─────────────────────┼──────────────────┼────────────────────────  │   │
│  │  Upload PDF           │ POST /api/pdf/   │ pdf_extract tool         │   │
│  │  Review/Edit content  │ Co-Design UI     │ Not available (no UI)    │   │
│  │  Human approval       │ ✅ Yes           │ ❌ No (automated)        │   │
│  │  Real-time progress   │ WebSocket        │ Not needed               │   │
│  │  PII review           │ Interactive UI   │ Automated redaction      │   │
│  │  Theme selection      │ User chooses     │ AI decides               │   │
│  │  Export/Deploy        │ Download/Deploy  │ Returns HTML string      │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### When Does a Frontend User Encounter MCP?

**Short answer: NEVER directly.**

The frontend user uploads a PDF through the UI, and the backend handles everything. MCP is a separate interface for AI assistants to use PDF2Web programmatically.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TWO SEPARATE ENTRY POINTS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                         PDF2Web Backend Server                              │
│                        ┌─────────────────────┐                              │
│                        │                     │                              │
│   👤 Frontend User ───►│  REST API          │──► Same processing pipeline  │
│   (React/Streamlit)    │  /api/pdf/upload   │                              │
│                        │  /api/codesign/*   │                              │
│                        │  /api/export/*     │                              │
│                        │                     │                              │
│                        ├─────────────────────┤                              │
│                        │                     │                              │
│   🤖 AI Assistant ────►│  MCP API           │──► Same processing pipeline  │
│   (Claude/GPT)         │  /api/mcp/tools/*  │                              │
│                        │  /api/mcp/rpc      │                              │
│                        │                     │                              │
│                        └─────────────────────┘                              │
│                                                                             │
│   Both use the SAME backend services (OCR, PII, ERNIE, HTML Generator)     │
│   but through DIFFERENT interfaces!                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Real-World Use Cases

| Scenario | Who Uses | Which API |
|----------|----------|-----------|
| Employee uploads contract PDF via company portal | Human | REST API |
| User converts resume to webpage via Streamlit app | Human | REST API |
| Claude helps user "convert this PDF to HTML" | AI (Claude) | MCP |
| Automated pipeline processes 100 PDFs overnight | Script/AI | MCP |
| Cursor IDE converts documentation PDF | AI (Cursor) | MCP |

---

#### What is MCP?

MCP allows AI assistants (Claude, GPT, Cursor, etc.) to use PDF2Web as a tool. This enables powerful workflows where AI can process PDFs automatically.

##### MCP Explained

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MCP (Model Context Protocol)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MCP is a standard protocol that allows AI assistants to:                   │
│    • Discover available tools (like PDF2Web)                                │
│    • Call tools with parameters                                             │
│    • Receive structured results                                             │
│                                                                             │
│  Think of it as: "Plugins for AI Assistants"                                │
│                                                                             │
│  ┌─────────────┐      MCP Protocol      ┌─────────────────┐                │
│  │ AI Assistant│ ◄──────────────────────► │ PDF2Web Server │                │
│  │ (Claude/GPT)│   JSON-RPC / SSE       │ (MCP Tools)     │                │
│  └─────────────┘                        └─────────────────┘                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### MCP Tools Available

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `pdf_extract` | Extract text from PDF | `pdf_path`, `language` | blocks, images |
| `pii_detect` | Detect/redact PII | `text`, `redact`, `pii_types` | redacted_text, pii_found |
| `markdown_build` | Convert to Markdown | `blocks` | markdown |
| `semantic_analyze` | Get component suggestions | `content`, `content_type` | suggestions |
| `html_generate` | Generate HTML | `markdown`, `theme` | html |
| `theme_analyze` | Suggest theme | `content` | theme, confidence |
| `accessibility_check` | WCAG validation | `html`, `wcag_level` | issues, score |

#### MCP Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MCP USER JOURNEY                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCENARIO: User asks Claude "Convert this PDF to an interactive webpage"   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STEP 1: AI DISCOVERS TOOLS                                         │   │
│  │  ─────────────────────────────                                      │   │
│  │  Claude calls: GET /api/mcp/tools                                   │   │
│  │  Response: List of available PDF2Web tools                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STEP 2: EXTRACT PDF                                                │   │
│  │  ───────────────────────                                            │   │
│  │  Claude calls: POST /api/mcp/tools/pdf_extract/call                 │   │
│  │  Body: { "pdf_path": "/uploads/document.pdf" }                      │   │
│  │  Response: { "blocks": [...], "images": [...] }                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STEP 3: DETECT PII (if sensitive document)                         │   │
│  │  ──────────────────────────────────────────                         │   │
│  │  Claude calls: POST /api/mcp/tools/pii_detect/call                  │   │
│  │  Body: { "text": "...", "redact": true }                            │   │
│  │  Response: { "redacted_text": "...", "pii_found": [...] }           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STEP 4: BUILD MARKDOWN                                             │   │
│  │  ──────────────────────                                             │   │
│  │  Claude calls: POST /api/mcp/tools/markdown_build/call              │   │
│  │  Body: { "blocks": [...] }                                          │   │
│  │  Response: { "markdown": "# Title\n\n..." }                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STEP 5: ANALYZE SEMANTICS                                          │   │
│  │  ─────────────────────────                                          │   │
│  │  Claude calls: POST /api/mcp/tools/semantic_analyze/call            │   │
│  │  Body: { "content": "...", "content_type": "table" }                │   │
│  │  Response: { "suggestions": [{"suggestion": "chart_bar"}] }         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STEP 6: GENERATE HTML                                              │   │
│  │  ─────────────────────                                              │   │
│  │  Claude calls: POST /api/mcp/tools/html_generate/call               │   │
│  │  Body: { "markdown": "...", "theme": "professional" }               │   │
│  │  Response: { "html": "<!DOCTYPE html>..." }                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STEP 7: CHECK ACCESSIBILITY                                        │   │
│  │  ───────────────────────────                                        │   │
│  │  Claude calls: POST /api/mcp/tools/accessibility_check/call         │   │
│  │  Body: { "html": "...", "wcag_level": "AA" }                        │   │
│  │  Response: { "passed": true, "score": 95 }                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  RESULT: Claude returns the generated HTML to the user              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### MCP Configuration

```bash
# .env settings for MCP
ENABLE_MCP_SERVER=true
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8001
MCP_TRANSPORT=sse                    # sse, stdio, websocket
MCP_ENABLED_TOOLS=pdf_extract,pii_detect,markdown_build,semantic_analyze,html_generate,theme_analyze,accessibility_check
MCP_AUTH_ENABLED=false               # Enable for production
MCP_AUTH_TOKEN=your-secret-token     # Required if auth enabled
```

#### MCP API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/mcp/info` | Server info (name, version, capabilities) |
| `GET` | `/api/mcp/tools` | List all available tools |
| `GET` | `/api/mcp/tools/{name}` | Get specific tool info |
| `POST` | `/api/mcp/tools/{name}/call` | Call a tool |
| `POST` | `/api/mcp/rpc` | JSON-RPC endpoint (standard MCP) |
| `GET` | `/api/mcp/sse` | Server-Sent Events stream |
| `GET` | `/api/mcp/settings` | Current MCP settings |

#### Convenience Endpoints (Direct Tool Access)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/mcp/extract-pdf` | Direct PDF extraction |
| `POST` | `/api/mcp/detect-pii` | Direct PII detection |
| `POST` | `/api/mcp/build-markdown` | Direct Markdown building |
| `POST` | `/api/mcp/generate-html` | Direct HTML generation |

#### MCP Client Examples

**JavaScript/TypeScript (for AI integrations):**

```javascript
// MCP Client for PDF2Web

class PDF2WebMCPClient {
  constructor(baseUrl = 'http://localhost:8000/api/mcp') {
    this.baseUrl = baseUrl;
  }

  // List available tools
  async listTools() {
    const response = await fetch(`${this.baseUrl}/tools`);
    return response.json();
  }

  // Call a tool
  async callTool(toolName, arguments) {
    const response = await fetch(`${this.baseUrl}/tools/${toolName}/call`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(arguments)
    });
    return response.json();
  }

  // JSON-RPC call (standard MCP protocol)
  async rpcCall(method, params = {}) {
    const response = await fetch(`${this.baseUrl}/rpc`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: Date.now(),
        method,
        params
      })
    });
    return response.json();
  }

  // Complete PDF to HTML workflow
  async convertPDFToHTML(pdfPath, options = {}) {
    // Step 1: Extract PDF
    const extraction = await this.callTool('pdf_extract', { pdf_path: pdfPath });
    
    // Step 2: Detect PII (if secure mode)
    let blocks = extraction.content.blocks;
    if (options.secureMode) {
      for (let block of blocks) {
        const piiResult = await this.callTool('pii_detect', { 
          text: block.content, 
          redact: true 
        });
        block.content = piiResult.content.redacted_text;
      }
    }
    
    // Step 3: Build Markdown
    const markdown = await this.callTool('markdown_build', { blocks });
    
    // Step 4: Analyze theme
    const theme = await this.callTool('theme_analyze', { 
      content: markdown.content.markdown 
    });
    
    // Step 5: Generate HTML
    const html = await this.callTool('html_generate', {
      markdown: markdown.content.markdown,
      theme: options.theme || theme.content.suggested_theme
    });
    
    // Step 6: Check accessibility
    const accessibility = await this.callTool('accessibility_check', {
      html: html.content.html,
      wcag_level: 'AA'
    });
    
    return {
      html: html.content.html,
      theme: theme.content,
      accessibility: accessibility.content
    };
  }
}

// Usage
const client = new PDF2WebMCPClient();

// Simple tool call
const result = await client.callTool('pii_detect', {
  text: 'Contact john@email.com or call 555-123-4567',
  redact: true
});
console.log(result);
// { "redacted_text": "Contact [EMAIL_REDACTED] or call [PHONE_REDACTED]", ... }

// Complete workflow
const html = await client.convertPDFToHTML('/path/to/document.pdf', {
  secureMode: true,
  theme: 'professional'
});
```

**Python (for backend integrations):**

```python
import httpx
import asyncio

class PDF2WebMCPClient:
    def __init__(self, base_url="http://localhost:8000/api/mcp"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def list_tools(self):
        response = await self.client.get(f"{self.base_url}/tools")
        return response.json()
    
    async def call_tool(self, tool_name: str, arguments: dict):
        response = await self.client.post(
            f"{self.base_url}/tools/{tool_name}/call",
            json=arguments
        )
        return response.json()
    
    async def convert_pdf(self, pdf_path: str, theme: str = "light"):
        # Extract
        extraction = await self.call_tool("pdf_extract", {"pdf_path": pdf_path})
        
        # Build markdown
        markdown = await self.call_tool("markdown_build", {
            "blocks": extraction["content"]["blocks"]
        })
        
        # Generate HTML
        html = await self.call_tool("html_generate", {
            "markdown": markdown["content"]["markdown"],
            "theme": theme
        })
        
        return html["content"]["html"]

# Usage
async def main():
    client = PDF2WebMCPClient()
    
    # List tools
    tools = await client.list_tools()
    print(f"Available tools: {[t['name'] for t in tools['tools']]}")
    
    # Convert PDF
    html = await client.convert_pdf("/path/to/document.pdf", theme="professional")
    print(html[:500])

asyncio.run(main())
```

**cURL Examples:**

```bash
# List all MCP tools
curl http://localhost:8000/api/mcp/tools

# Call pdf_extract tool
curl -X POST http://localhost:8000/api/mcp/tools/pdf_extract/call \
  -H "Content-Type: application/json" \
  -d '{"pdf_path": "./uploads/document.pdf"}'

# Call pii_detect tool
curl -X POST http://localhost:8000/api/mcp/tools/pii_detect/call \
  -H "Content-Type: application/json" \
  -d '{"text": "Email: john@example.com, Phone: 555-1234", "redact": true}'

# Call html_generate tool
curl -X POST http://localhost:8000/api/mcp/tools/html_generate/call \
  -H "Content-Type: application/json" \
  -d '{"markdown": "# Hello World\n\nThis is a test.", "theme": "dark"}'

# JSON-RPC call (standard MCP)
curl -X POST http://localhost:8000/api/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

#### Connecting AI Assistants to PDF2Web MCP

**For Claude Desktop (mcp.json):**

```json
{
  "mcpServers": {
    "pdf2web": {
      "command": "curl",
      "args": ["-N", "http://localhost:8000/api/mcp/sse"],
      "env": {}
    }
  }
}
```

**For Custom AI Integration:**

```javascript
// In your AI assistant's tool configuration
const pdf2webTools = {
  name: "pdf2web",
  description: "Convert PDFs to interactive HTML webpages",
  baseUrl: "http://localhost:8000/api/mcp",
  tools: [
    {
      name: "pdf_extract",
      description: "Extract text and structure from PDF",
      parameters: {
        pdf_path: { type: "string", required: true },
        language: { type: "string", default: "en" }
      }
    },
    // ... other tools
  ]
};
```

#### MCP vs REST API: When to Use Which?

| Use Case | Use MCP | Use REST API |
|----------|---------|--------------|
| AI assistant integration | ✅ | ❌ |
| Frontend web app | ❌ | ✅ |
| Automated pipelines | ✅ | ✅ |
| Human-in-the-loop (Co-Design) | ❌ | ✅ |
| Real-time updates (WebSocket) | ❌ | ✅ |
| Batch processing | ✅ | ✅ |

**Summary:**
- **MCP**: Best for AI assistants that need to discover and call tools programmatically
- **REST API**: Best for frontend apps with user interaction and real-time features

---

### 🧠 Knowledge Graph Navigation - Complete Guide

#### What is Knowledge Graph Navigation?

Knowledge Graph Navigation is a unique feature that transforms long documents (reports, textbooks, research papers) into explorable web apps with interactive navigation. Unlike basic Table of Contents, it creates a semantic map of your document showing how concepts, sections, and entities relate to each other.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE GRAPH ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PDF Document                                                               │
│      │                                                                      │
│      ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ENTITY EXTRACTION (DeepSeek/ERNIE)                                 │   │
│  │  ─────────────────────────────────                                  │   │
│  │  • Sections: Chapter 1, Section 2.1, etc.                           │   │
│  │  • Concepts: Key terms, theories, definitions                       │   │
│  │  • People: Authors, researchers, historical figures                 │   │
│  │  • Dates: Important dates, time periods                             │   │
│  │  • Locations: Places, countries, cities                             │   │
│  │  • Tables/Figures: Data summaries                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  RELATIONSHIP DETECTION                                             │   │
│  │  ─────────────────────────                                          │   │
│  │  • references: "See Section 3 for details"                          │   │
│  │  • builds_on: "Building on concepts from Chapter 1"                 │   │
│  │  • summarizes: "Table X summarizes data from Section Y"             │   │
│  │  • defines: Section defines a concept                               │   │
│  │  • contains: Parent-child hierarchy                                 │   │
│  │  • related_to: Semantic similarity                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  OUTPUT: vis.js/Cytoscape.js Compatible JSON                        │   │
│  │  ─────────────────────────────────────────                          │   │
│  │  {                                                                  │   │
│  │    "nodes": [{"id": "...", "label": "...", "type": "section"}],     │   │
│  │    "edges": [{"from": "...", "to": "...", "type": "references"}],   │   │
│  │    "config": { physics, interaction, layout settings }              │   │
│  │  }                                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Knowledge Graph API Usage

```bash
# 1. Upload PDF first
curl -X POST "http://localhost:8000/api/pdf/upload" \
  -F "file=@document.pdf"
# Response: { "document_id": "uuid" }

# 2. Generate Knowledge Graph
curl -X POST "http://localhost:8000/api/knowledge-graph/{document_id}/generate" \
  -H "Content-Type: application/json" \
  -d '{"use_ai": true}'

# 3. Get Sidebar Navigation Data
curl "http://localhost:8000/api/knowledge-graph/{document_id}/sidebar-data"

# 4. Simplify for Preview (Co-Design Layer)
curl -X POST "http://localhost:8000/api/knowledge-graph/{document_id}/simplify" \
  -H "Content-Type: application/json" \
  -d '{"max_nodes": 15, "entity_types": ["section", "concept"]}'
```

#### Frontend Integration (vis.js Example)

```javascript
// Fetch knowledge graph data
const response = await fetch(`/api/knowledge-graph/${documentId}`);
const graph = await response.json();

// Initialize vis.js network
const container = document.getElementById('knowledge-graph');
const data = {
  nodes: new vis.DataSet(graph.nodes),
  edges: new vis.DataSet(graph.edges)
};
const network = new vis.Network(container, data, graph.config);

// Handle node clicks - jump to section
network.on('click', (params) => {
  if (params.nodes.length > 0) {
    const nodeId = params.nodes[0];
    const node = graph.nodes.find(n => n.id === nodeId);
    if (node.data.block_id) {
      document.getElementById(node.data.block_id).scrollIntoView();
    }
  }
});
```

#### Collapsible Sidebar Integration

```javascript
// Fetch sidebar-optimized data
const sidebarData = await fetch(`/api/knowledge-graph/${documentId}/sidebar-data`).then(r => r.json());

// Render collapsible sidebar
function renderSidebar(data) {
  return `
    <div class="knowledge-sidebar">
      <h3>Document Structure</h3>
      ${data.sections.map(section => `
        <div class="sidebar-node" onclick="jumpToBlock('${section.block_id}')">
          <span style="color: ${section.color}">${section.label}</span>
          ${section.related.length > 0 ? `
            <ul class="related-items">
              ${section.related.map(r => `<li>${r.label}: ${r.type}</li>`).join('')}
            </ul>
          ` : ''}
        </div>
      `).join('')}
      
      <h3>Key Entities</h3>
      ${Object.entries(data.entities).map(([type, items]) => `
        <details>
          <summary>${type} (${items.length})</summary>
          <ul>
            ${items.map(item => `<li onclick="jumpToPage(${item.page})">${item.label}</li>`).join('')}
          </ul>
        </details>
      `).join('')}
    </div>
  `;
}
```

#### Why Knowledge Graph is Unique

| Feature | Basic TOC | Knowledge Graph |
|---------|-----------|-----------------|
| Section navigation | ✅ | ✅ |
| Cross-references | ❌ | ✅ |
| Concept relationships | ❌ | ✅ |
| Entity extraction | ❌ | ✅ |
| Visual graph view | ❌ | ✅ |
| Non-linear exploration | ❌ | ✅ |
| AI-powered analysis | ❌ | ✅ |

**No existing PDF-to-HTML tool auto-creates navigable knowledge graphs.** This turns long documents into explorable web apps, ideal for non-linear reading and learning.

---

#### How MCP is Connected in Backend Code

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BACKEND CODE STRUCTURE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  app/main.py - Routes are registered here:                                  │
│  ─────────────────────────────────────────                                  │
│                                                                             │
│    # REST API routes (for Frontend Users)                                   │
│    app.include_router(pdf.router, prefix="/api/pdf")      # Upload PDF      │
│    app.include_router(codesign.router, prefix="/api/codesign")  # Co-Design │
│    app.include_router(export.router, prefix="/api/export")      # Export    │
│    app.include_router(websocket.router, prefix="/api/realtime") # WebSocket │
│                                                                             │
│    # MCP routes (for AI Assistants)                                         │
│    app.include_router(mcp.router, prefix="/api/mcp")      # MCP Tools       │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  app/api/routes/mcp.py - MCP endpoints:                                     │
│  ──────────────────────────────────────                                     │
│                                                                             │
│    GET  /api/mcp/tools              → List available tools                  │
│    POST /api/mcp/tools/{name}/call  → Call a specific tool                  │
│    POST /api/mcp/rpc                → JSON-RPC endpoint                     │
│    GET  /api/mcp/sse                → Server-Sent Events stream             │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  app/services/mcp_service.py - Tool implementations:                        │
│  ─────────────────────────────────────────────────                          │
│                                                                             │
│    class MCPService:                                                        │
│        def __init__(self):                                                  │
│            self._register_builtin_tools()  # Register all tools             │
│                                                                             │
│        async def call_tool(name, arguments):                                │
│            # Routes to appropriate handler                                  │
│            if name == "pdf_extract":                                        │
│                return await self._handle_pdf_extract(arguments)             │
│            elif name == "pii_detect":                                       │
│                return await self._handle_pii_detect(arguments)              │
│            # ... etc                                                        │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  BOTH REST API and MCP use the SAME underlying services:                    │
│                                                                             │
│    app/services/ocr_service.py      → PaddleOCR extraction                  │
│    app/services/pii_service.py      → Presidio/spaCy PII detection          │
│    app/services/markdown_service.py → Markdown conversion                   │
│    app/services/ernie_service.py    → ERNIE API (theme, semantic, HTML)     │
│    app/services/html_generator.py   → HTML generation with widgets          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Frontend Developer: Adding "MCP Mode" / "AI Auto-Convert" Button

**Q: I want to add an "MCP Mode" or "AI Auto-Convert" button in my frontend. How?**

**A: Use the new `/api/codesign/{id}/auto-convert` endpoint!**

This endpoint provides MCP-style automated processing for frontend users who want instant results without going through the Co-Design review process.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│           🎯 TWO CONVERSION MODES FOR FRONTEND USERS                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  MODE 1: NORMAL MODE (Human-in-the-Loop)                            │   │
│  │  ───────────────────────────────────────                            │   │
│  │                                                                     │   │
│  │  User uploads PDF                                                   │   │
│  │       ↓                                                             │   │
│  │  POST /api/pdf/upload                                               │   │
│  │       ↓                                                             │   │
│  │  GET /api/codesign/{id}/preview  ← User reviews content             │   │
│  │       ↓                                                             │   │
│  │  User edits blocks, approves PII, selects theme                     │   │
│  │       ↓                                                             │   │
│  │  POST /api/codesign/{id}/submit  ← User submits choices             │   │
│  │       ↓                                                             │   │
│  │  HTML generated with user's selections                              │   │
│  │                                                                     │   │
│  │  ✅ Full control over every decision                                │   │
│  │  ✅ Can fix OCR errors                                              │   │
│  │  ✅ Can undo PII redactions                                         │   │
│  │  ❌ Takes more time                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  MODE 2: MCP MODE / AI AUTO-CONVERT (Automated)                     │   │
│  │  ──────────────────────────────────────────────                     │   │
│  │                                                                     │   │
│  │  User uploads PDF                                                   │   │
│  │       ↓                                                             │   │
│  │  POST /api/pdf/upload                                               │   │
│  │       ↓                                                             │   │
│  │  POST /api/codesign/{id}/auto-convert  ← ONE CLICK!                 │   │
│  │       ↓                                                             │   │
│  │  HTML generated automatically with AI decisions                     │   │
│  │                                                                     │   │
│  │  ✅ Instant results (one click)                                     │   │
│  │  ✅ AI chooses best theme                                           │   │
│  │  ✅ Auto-converts tables to charts                                  │   │
│  │  ✅ Auto-enables quizzes, timelines, maps                           │   │
│  │  ❌ No manual review                                                │   │
│  │  ❌ Can't fix OCR errors                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

##### Auto-Convert API Endpoint

```
POST /api/codesign/{document_id}/auto-convert
```

**Request Body (all optional):**
```json
{
  "theme": "professional",      // null = let AI decide
  "auto_charts": true,          // Auto-convert tables to charts
  "auto_quizzes": true,         // Auto-enable quizzes for Q&A lists
  "auto_code_execution": false, // Auto-enable code execution
  "auto_timeline": true,        // Auto-enable timeline widgets
  "auto_map": true              // Auto-enable map widgets
}
```

**Response:**
```json
{
  "document_id": "uuid",
  "html": "<!DOCTYPE html>...",
  "assets": ["image1.png", "image2.png"],
  "theme": "professional",
  "components_injected": ["chart_bar", "quiz", "timeline"]
}
```

##### Frontend Implementation: Two Buttons

```javascript
// Frontend with TWO conversion options

const API_BASE = 'http://localhost:8000/api';

// Upload PDF (same for both modes)
async function uploadPDF(file, secureMode = true) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('mode', secureMode ? 'secure' : 'standard');
  
  const response = await fetch(`${API_BASE}/pdf/upload`, {
    method: 'POST',
    body: formData
  });
  return response.json();
}

// ═══════════════════════════════════════════════════════════════════════════
// OPTION 1: Normal Mode (Co-Design with human review)
// ═══════════════════════════════════════════════════════════════════════════
async function normalModeConvert(documentId, userChoices) {
  // Step 1: Get preview for user to review
  const preview = await fetch(`${API_BASE}/codesign/${documentId}/preview`);
  // ... show preview to user, let them edit ...
  
  // Step 2: Submit with user's choices
  const result = await fetch(`${API_BASE}/codesign/${documentId}/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      theme: userChoices.theme,
      chart_conversions: userChoices.charts,
      quiz_enabled_blocks: userChoices.quizzes,
      // ... other user selections
    })
  });
  return result.json();
}

// ═══════════════════════════════════════════════════════════════════════════
// OPTION 2: MCP Mode / AI Auto-Convert (one click, no review)
// ═══════════════════════════════════════════════════════════════════════════
async function mcpModeConvert(documentId, options = {}) {
  const result = await fetch(`${API_BASE}/codesign/${documentId}/auto-convert`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      theme: options.theme || null,  // null = AI decides
      auto_charts: true,
      auto_quizzes: true,
      auto_code_execution: false,
      auto_timeline: true,
      auto_map: true
    })
  });
  return result.json();
}

// ═══════════════════════════════════════════════════════════════════════════
// UI: Show two buttons after upload
// ═══════════════════════════════════════════════════════════════════════════
function ConversionOptions({ documentId }) {
  return (
    <div className="conversion-options">
      <h3>Choose Conversion Mode:</h3>
      
      {/* Normal Mode Button */}
      <button 
        onClick={() => goToCoDesignPreview(documentId)}
        className="btn-normal"
      >
        📝 Review & Customize
        <small>Edit content, choose theme, select components</small>
      </button>
      
      {/* MCP Mode Button */}
      <button 
        onClick={async () => {
          const result = await mcpModeConvert(documentId);
          showHTMLPreview(result.html);
        }}
        className="btn-mcp"
      >
        🤖 AI Auto-Convert
        <small>Instant results, AI makes all decisions</small>
      </button>
    </div>
  );
}
```

##### Complete Flow with MCP Mode Button

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND USER FLOW WITH MCP MODE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  User opens app                                                             │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  📄 Upload PDF                                                      │   │
│  │  [Choose File] [Secure Mode ✓]                                      │   │
│  │  [Upload]                                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                     │
│       ▼ POST /api/pdf/upload                                                │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ✅ PDF Uploaded Successfully!                                      │   │
│  │                                                                     │   │
│  │  Choose how to convert:                                             │   │
│  │                                                                     │   │
│  │  ┌─────────────────────┐  ┌─────────────────────┐                  │   │
│  │  │  📝 Review &        │  │  🤖 AI Auto-        │                  │   │
│  │  │     Customize       │  │     Convert         │                  │   │
│  │  │                     │  │                     │                  │   │
│  │  │  • Edit content     │  │  • Instant results  │                  │   │
│  │  │  • Choose theme     │  │  • AI decides all   │                  │   │
│  │  │  • Select charts    │  │  • One click        │                  │   │
│  │  │  • Review PII       │  │  • No review        │                  │   │
│  │  └─────────────────────┘  └─────────────────────┘                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│       │                              │                                      │
│       │ User clicks                  │ User clicks                          │
│       │ "Review & Customize"         │ "AI Auto-Convert"                    │
│       │                              │                                      │
│       ▼                              ▼                                      │
│  ┌──────────────────┐          ┌──────────────────┐                        │
│  │ Co-Design UI     │          │ POST /api/       │                        │
│  │ GET /preview     │          │ codesign/{id}/   │                        │
│  │ POST /submit     │          │ auto-convert     │                        │
│  └──────────────────┘          └──────────────────┘                        │
│       │                              │                                      │
│       ▼                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  🎉 HTML Generated!                                                 │   │
│  │                                                                     │   │
│  │  [Preview] [Download ZIP] [Deploy to Netlify]                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

##### When to Use Each Mode

| Scenario | Recommended Mode |
|----------|------------------|
| Important business document | Normal Mode (review everything) |
| Quick personal conversion | MCP Mode (instant) |
| Document with sensitive PII | Normal Mode (review redactions) |
| Batch processing many PDFs | MCP Mode (automated) |
| Document with complex tables | Normal Mode (choose chart types) |
| Simple text document | MCP Mode (fast) |

##### FAQ: MCP Mode vs MCP Protocol

**Q: Is "MCP Mode" button the same as MCP protocol?**

**A: No!** They are different:

| | MCP Mode Button | MCP Protocol |
|---|---|---|
| **Who uses it** | Human user via frontend | AI assistant (Claude, GPT) |
| **How it works** | Calls `/api/codesign/{id}/auto-convert` | Calls `/api/mcp/tools/*` |
| **Interface** | Web UI button | JSON-RPC / SSE |
| **Purpose** | Quick conversion for users | Tool integration for AI |

The "MCP Mode" button gives users the **same automated experience** that an AI assistant would get via MCP, but through a simple button click in the frontend UI.

---

### 💻 Frontend Integration Example (React)

```javascript
// Complete React integration example

import { useState } from 'react';

const API_BASE = 'http://localhost:8000/api';

function PDF2WebConverter() {
  const [documentId, setDocumentId] = useState(null);
  const [preview, setPreview] = useState(null);
  const [html, setHtml] = useState(null);

  // STEP 1: Upload PDF
  const uploadPDF = async (file, secureMode = true) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', secureMode ? 'secure' : 'standard');
    formData.append('redact_emails', 'true');
    formData.append('redact_phones', 'true');
    formData.append('redact_names', 'true');

    const response = await fetch(`${API_BASE}/pdf/upload`, {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    setDocumentId(data.document_id);
    
    // Automatically fetch preview
    await fetchPreview(data.document_id);
  };

  // STEP 2: Get Co-Design Preview
  const fetchPreview = async (docId) => {
    const response = await fetch(`${API_BASE}/codesign/${docId}/preview`);
    const data = await response.json();
    setPreview(data);
    
    // data contains:
    // - blocks: ContentBlock[] with confidence scores
    // - pii_redactions: PIIRedaction[] 
    // - theme_analysis: { suggested_theme, confidence, reasoning }
    // - semantic_suggestions: SemanticSuggestion[]
  };

  // STEP 3: Edit block content
  const editBlock = async (blockId, newContent) => {
    await fetch(`${API_BASE}/codesign/${documentId}/edit-block`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ block_id: blockId, new_content: newContent })
    });
    await fetchPreview(documentId);
  };

  // STEP 4: Handle PII action
  const handlePII = async (redactionId, action) => {
    await fetch(`${API_BASE}/codesign/${documentId}/pii-action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ redaction_id: redactionId, action }) // approve/undo
    });
    await fetchPreview(documentId);
  };

  // STEP 5: Submit and generate HTML
  const generateHTML = async (options) => {
    const response = await fetch(`${API_BASE}/codesign/${documentId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        theme: options.theme || 'professional',
        theme_override: options.themeOverride || false,
        approved_components: options.approvedComponents || [],
        chart_conversions: options.chartConversions || {},
        quiz_enabled_blocks: options.quizBlocks || [],
        code_execution_blocks: options.codeBlocks || [],
        timeline_blocks: options.timelineBlocks || [],
        map_blocks: options.mapBlocks || []
      })
    });
    
    const data = await response.json();
    setHtml(data.html);
  };

  // STEP 6: Export/Deploy
  const exportHTML = async () => {
    await fetch(`${API_BASE}/export/${documentId}/html`, { method: 'POST' });
    window.location.href = `${API_BASE}/export/download/${documentId}/html`;
  };

  const deployToNetlify = async (token) => {
    const response = await fetch(`${API_BASE}/deploy/${documentId}/netlify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ netlify_token: token })
    });
    const data = await response.json();
    return data.deploy_url;
  };

  return (
    <div>
      {/* Your UI components here */}
    </div>
  );
}
```

---

### 🔄 WebSocket Real-Time Progress

```javascript
// Connect to WebSocket for real-time updates

const ws = new WebSocket('ws://localhost:8000/api/realtime/ws');

ws.onopen = () => {
  // Subscribe to document updates
  ws.send(JSON.stringify({
    action: 'subscribe',
    document_id: documentId
  }));
};

ws.onmessage = (event) => {
  const { event: eventType, data } = JSON.parse(event.data);
  
  switch(eventType) {
    case 'processing_started':
      showNotification('Processing started...');
      break;
      
    case 'processing_progress':
      updateProgressBar(data.progress); // 0-100
      updateStatus(data.stage); // 'ocr', 'pii', 'analysis'
      break;
      
    case 'ocr_page_completed':
      updatePageProgress(data.current_page, data.total_pages);
      break;
      
    case 'pii_detected':
      showPIIAlert(data.total_count, data.by_type);
      break;
      
    case 'suggestions_ready':
      refreshSuggestions(data.count, data.summary);
      break;
      
    case 'html_generation_completed':
      showPreview(data.html);
      hideProgressBar();
      break;
      
    case 'processing_error':
      showError(data.error, data.stage);
      break;
  }
};
```

---

### 📊 Cost Estimation (Novita AI)

| Operation | Model Used | Tokens | Cost (approx) |
|-----------|------------|--------|---------------|
| Theme Analysis | ERNIE-3.5-8k | ~500 | $0.0005 |
| Vision Analysis (per page) | ERNIE-4.0-preview | ~1000 + image | $0.003 |
| HTML Generation | ERNIE-3.5-8k | ~2000 | $0.002 |
| **5-page PDF (full features)** | Mixed | ~8000 | **~$0.02** |

With $25 Novita AI credits, you can process approximately **1,250 PDFs** (5 pages each).

---

### 🧪 Testing Checklist

| Test | Command | Expected Result |
|------|---------|-----------------|
| Health Check | `curl localhost:8000/api/health` | `{"status": "healthy"}` |
| ERNIE Status | `curl localhost:8000/api/health/ernie` | `{"text_model": "ok", "vision_model": "ok"}` |
| Upload PDF | `curl -F "file=@test.pdf" localhost:8000/api/pdf/upload` | `{"document_id": "uuid"}` |
| Privacy Test | Upload PDF with email, check PII redacted | Email shows as `[EMAIL_REDACTED]` |
| Vision Test | Upload PDF with table, check chart suggestion | `{"suggestion": "chart_bar"}` |
| Co-Design Test | Edit block content via API | Content updated in preview |
| Export Test | Generate HTML and download | Valid HTML with Chart.js |

---

## 📝 License

MIT License - See LICENSE file for details.
