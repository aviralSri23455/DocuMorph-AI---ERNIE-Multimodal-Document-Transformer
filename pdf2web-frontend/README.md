# DocuMorph AI - Frontend

> 🏆 **DEV.to Hackathon Entry** - Best ERNIE Multimodal Application using Novita API

Dark cyberpunk-themed React frontend for DocuMorph AI with complete backend integration.

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   React Frontend │  │  Streamlit App   │  │   Built-in UI    │  │
│  │   (Port 3000)    │  │  (Port 8501)     │  │   (Port 8000)    │  │
│  │                  │  │                  │  │                  │  │
│  │  • Full Co-Design│  │  • Quick Preview │  │  • Single Page   │  │
│  │  • Real-time     │  │  • Python Native │  │  • No Install    │  │
│  │  • Analytics     │  │  • Rapid Proto   │  │  • Embedded      │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │
│           │                     │                     │             │
│           └─────────────────────┼─────────────────────┘             │
│                                 │                                    │
│                                 ▼                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Backend (Port 8000)                │  │
│  │                                                               │  │
│  │  /api/pdf/upload          → OCR + PII Detection (Local)      │  │
│  │  /api/codesign/{id}/*     → Co-Design Layer APIs             │  │
│  │  /api/export/{id}/*       → HTML/Markdown Export             │  │
│  │  /api/deploy/{id}/*       → Netlify/Vercel/S3/GitHub         │  │
│  │  /api/knowledge-graph/*   → Knowledge Graph Generation (Real-time AI)  │  │
│  │  /api/mcp/*               → MCP Tool Access                  │  │
│  │  /api/realtime/ws         → WebSocket Real-time Updates      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                 │                                    │
│                                 ▼                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    AI Services (Novita AI)                    │  │
│  │                                                               │  │
│  │  ERNIE-4.5 (Text)    → Theme Analysis, HTML Generation       │  │
│  │  ERNIE-4.5-VL (Vision) → Table/Chart/Quiz Detection          │  │
│  │  DeepSeek            → Knowledge Graph Generation            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 Three Ways to Use PDF2Web

### 1. React Frontend (Recommended for Production)
```bash
cd pdf2web-frontend
npm install
npm run dev
# Open http://localhost:3000
```

### 2. Streamlit App (Quick Prototyping)
```bash
cd pdf2web-backend
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac
streamlit run examples/streamlit_app.py --server.headless true
# Open http://localhost:8501
```

### 3. Built-in Dashboard (No Install)
```bash
cd pdf2web-backend
python run.py
# Open http://localhost:8000/ui
```

---

## ✨ Features

### 🧠 Knowledge Graph (100% Real-Time AI)

Interactive document navigation that separates DocuMorph from 90% of PDF converters:

| Feature | Description |
|---------|-------------|
| **Real-Time Generation** | Every graph generated live using ERNIE AI (~17 seconds) |
| **Entity Extraction** | Sections, concepts, people, dates, locations, organizations |
| **Relationship Detection** | references, builds_on, summarizes, defines, contains |
| **Force-Directed Layout** | Color-coded nodes with natural clustering |
| **Click-to-Navigate** | Jump to any section by clicking nodes |
| **Simplify Mode** | Reduce to top 15 nodes for cleaner preview |

```
Real Server Logs (Not Mock!):
2026-01-01 22:16:07 | INFO | Generating knowledge graph for document 2bb7c96c-...
2026-01-01 22:16:24 | INFO | Generated graph with 23 nodes and 16 edges
```

### Co-Design Layer (Human-in-the-Loop)
The Co-Design Layer is the core interaction point where users review and refine AI-extracted content before final HTML generation.

| Tab | Features |
|-----|----------|
| **Content Blocks** | Edit ALL blocks, change types (heading→paragraph), confidence scores |
| **PII Review** | Approve/undo redactions, see original vs redacted values |
| **AI Suggestions** | Chart conversions, quiz toggles, timeline/map widgets |
| **Transparency** | See exactly what data is sent to cloud |

### Real-Time Stats Dashboard
- Documents Processed (persisted across sessions)
- Average Processing Time
- Semantic Injections count
- Success Rate
- **Live updates** with animations when values change

### Semantic Component Injection
| Component | Source | Widget |
|-----------|--------|--------|
| Tables | Vision AI detects | Chart.js (Bar/Line/Pie) |
| Q&A Lists | Vision AI detects | Quiz.js (Interactive) |
| Code Blocks | OCR detects | Prism.js + Execution |
| Timelines | Vision AI detects | Timeline Widget |
| Locations | Vision AI detects | Leaflet.js Maps |

### Privacy & Security
- **Secure Mode**: PII redacted locally before cloud processing
- **Transparency Modal**: Shows exactly what data leaves your machine
- **Local OCR**: PaddleOCR runs entirely on your device

---

## 📁 Project Structure

```
pdf2web-frontend/
├── src/
│   ├── components/
│   │   ├── dashboard/
│   │   │   ├── CoDesignTabs.tsx       # 🆕 Tabbed Co-Design interface
│   │   │   ├── ContentBlocksEditor.tsx # 🆕 Edit ALL content blocks
│   │   │   ├── PIIReviewPanel.tsx     # 🆕 PII approve/undo panel
│   │   │   ├── SemanticSuggestions.tsx # Chart/Quiz/Timeline options
│   │   │   ├── LowConfidenceBlocks.tsx # Blocks needing review
│   │   │   ├── TransparencyModal.tsx  # Data sent to cloud
│   │   │   ├── StatsCards.tsx         # Real-time animated stats
│   │   │   ├── PDFUploader.tsx        # Drag-drop upload
│   │   │   ├── PreviewPanel.tsx       # HTML preview
│   │   │   ├── QuickActions.tsx       # Generate/Auto/Export
│   │   │   ├── ThemeSelector.tsx      # 5 output themes
│   │   │   ├── ModelSelector.tsx      # ERNIE/DeepSeek/MCP
│   │   │   ├── KnowledgeGraph.tsx     # Interactive force-directed graph (real-time)
│   │   │   ├── AccessibilityCheck.tsx # WCAG validation
│   │   │   ├── AuditLogs.tsx          # Activity logging
│   │   │   └── PluginsPanel.tsx       # Plugin management
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   └── Sidebar.tsx
│   │   └── ui/ (shadcn components)
│   ├── pages/
│   │   ├── AnalyticsPage.tsx          # 🆕 Charts & statistics
│   │   ├── SettingsPage.tsx
│   │   ├── ProjectsPage.tsx
│   │   ├── HistoryPage.tsx
│   │   └── HelpPage.tsx
│   ├── store/
│   │   └── useStore.ts                # Zustand + persist middleware
│   ├── lib/
│   │   ├── api.ts                     # Full API client + WebSocket
│   │   └── utils.ts
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── vite.config.ts
```

---

## 🔌 API Integration

### Upload Flow
```typescript
// 1. Upload PDF
const result = await api.uploadPDF(file, 'secure', {
  redact_emails: true,
  redact_phones: true,
  redact_names: true
})

// 2. Get Co-Design Preview
const preview = await api.getPreview(result.document_id)
// Returns: blocks, pii_redactions, theme_analysis, semantic_suggestions

// 3. Edit blocks (optional)
await api.editBlock(docId, blockId, newContent, newType)

// 4. Handle PII (optional)
await api.piiAction(docId, redactionId, 'approve') // or 'undo'

// 5. Generate HTML
const html = await api.generateHTML(docId, {
  theme: 'professional',
  chart_conversions: { 'block-1': 'convert_to_chart' },
  quiz_enabled_blocks: ['block-5']
})
```

### MCP Mode (AI Auto-Convert)
```typescript
// Skip Co-Design, let AI handle everything
const result = await api.autoConvert(docId)
// Returns generated HTML immediately
```

### WebSocket Real-Time Updates
```typescript
api.connectWebSocket(documentId)
api.onWebSocketEvent('processing_progress', (data) => {
  updateProgress(data.progress)
})
api.onWebSocketEvent('html_generation_completed', (data) => {
  showPreview(data.html)
})
```

---

## 🎨 Streamlit Integration

The Streamlit app (`examples/streamlit_app.py`) provides a Python-native UI that connects to the same backend:

```python
# How Streamlit connects to the backend
API_BASE = "http://localhost:8000/api"

# Upload PDF
response = requests.post(f"{API_BASE}/pdf/upload", files=files, data=data)

# Get preview
preview = requests.get(f"{API_BASE}/codesign/{doc_id}/preview").json()

# Edit block
requests.post(f"{API_BASE}/codesign/{doc_id}/edit-block", json={
    "block_id": block_id,
    "new_content": edited_text
})

# Generate HTML
result = requests.post(f"{API_BASE}/codesign/{doc_id}/submit", json={
    "theme": "professional",
    "chart_conversions": chart_options
})
```

### Streamlit Features
- **Upload Screen**: Mode selection, PII options
- **Preview Screen**: Tabbed interface (Content Blocks, PII Review, Theme, Settings)
- **Generate Screen**: HTML preview, download buttons, deployment options

### Running Streamlit
```bash
# Make sure backend is running first
cd pdf2web-backend
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac
python run.py

# In another terminal
cd pdf2web-backend
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac
streamlit run examples/streamlit_app.py --server.headless true
```

### 📁 Data Storage

Streamlit doesn't store data - it's just a UI. All data is stored by the **backend**:

| Location | Contents |
|----------|----------|
| `pdf2web-backend/uploads/` | Uploaded PDFs, images |
| `pdf2web-backend/outputs/` | Generated HTML |
| `pdf2web-backend/data/` | Document store |
| `pdf2web-backend/audit_logs/` | Activity logs |

### ✅ Verify Streamlit is Working

1. **Check Backend is Running**:
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "healthy", ...}
   
   curl http://localhost:8000/api/health/ernie
   # Should return: {"status": "ok", "configured": true, "model": "baidu/ernie-4.5-21B-a3b", ...}
   ```

2. **Check Streamlit is Connected**:
   - Open http://localhost:8501
   - You should see the PDF2Web AI Weaver interface
   - Upload a PDF - if it processes successfully, Streamlit is connected to the backend

3. **Check in Browser Console** (React Frontend):
   - Open http://localhost:3000
   - Open Developer Tools (F12) → Network tab
   - Upload a PDF
   - You should see requests to `/api/pdf/upload` returning 200 OK

4. **Backend Logs**:
   When Streamlit/Frontend uploads a PDF, you'll see in the backend terminal:
   ```
   INFO: 127.0.0.1:XXXXX - "POST /api/pdf/upload HTTP/1.1" 200 OK
   INFO: 127.0.0.1:XXXXX - "GET /api/codesign/{id}/preview HTTP/1.1" 200 OK
   ```

---

## 🔧 Configuration

### Environment Variables
The frontend uses Vite's proxy to connect to the backend:

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000'
    }
  }
})
```

### State Persistence
Stats are persisted to localStorage using Zustand middleware:

```typescript
// useStore.ts
export const useStore = create<AppState>()(
  persist(
    (set, get) => ({ /* state */ }),
    {
      name: 'pdf2web-stats',
      partialize: (state) => ({ stats: state.stats })
    }
  )
)
```

---

## 📊 Tech Stack

| Category | Technology |
|----------|------------|
| Framework | React 18 + TypeScript |
| Build | Vite |
| Styling | Tailwind CSS + CSS Variables |
| Components | shadcn/ui (Radix primitives) |
| Animations | Framer Motion |
| Charts | Recharts |
| State | Zustand + persist middleware |
| File Upload | react-dropzone |

---

## 🚀 Quick Start

```bash
# 1. Start backend
cd pdf2web-backend
pip install -r requirements.txt
python -m spacy download en_core_web_lg
python run.py

# 2. Start frontend
cd pdf2web-frontend
npm install
npm run dev

# 3. Open http://localhost:3000
```

---

## 📝 License

MIT
