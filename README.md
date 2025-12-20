# DocuMorph AI - ERNIE Multimodal Document Transformer

> 🏆 **DEV.to Hackathon Entry** - Best ERNIE Multimodal Application using Novita API

Transform static PDFs into dynamic, responsive, and interactive HTML webpages with AI-powered semantic injection and multimodal vision analysis.

**Powered by:** ERNIE 4.5 + PaddleOCR + Novita AI

![Backend Screenshot](Output%20Scrren%20Shot/Backend%20Paddle%20Scrren%20Shot.png)

## ✨ Features

- 🔒 **Privacy-First**: Local OCR with PaddleOCR, PII detection with Presidio/spaCy
- 👁️ **Multimodal Vision**: ERNIE Vision analyzes PDF pages for smart component detection
- 🎨 **Co-Design Layer**: Human-in-the-loop editing before final generation
- 📊 **Semantic Injection**: Auto-convert tables→charts, lists→quizzes, code→executable blocks
- 🧠 **Knowledge Graph**: AI-generated interactive document navigation
- 🚀 **One-Click Deploy**: GitHub Pages, Netlify, Vercel, AWS S3

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ (3.11 recommended)
- Node.js 18+
- Novita AI API key ([Get $25 free credits](https://novita.ai/))

### 1. Clone & Setup Backend

```bash
cd pdf2web-backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate
# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_lg

# Configure environment
cp .env.example .env
# Edit .env and add your Novita AI API key
```

### 2. Setup Frontend

```bash
cd pdf2web-frontend
npm install
```

### 3. Add Your API Key

Edit `pdf2web-backend/.env`:
```bash
ERNIE_API_KEY=your-novita-api-key-here
DEEPSEEK_API_KEY=your-novita-api-key-here
```

### 4. Run

```bash
# Terminal 1: Backend
cd pdf2web-backend
.\venv\Scripts\activate  # Windows
python run.py

# Terminal 2: Frontend
cd pdf2web-frontend
npm run dev
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Built-in UI**: http://localhost:8000/ui

## 📁 Project Structure

```
├── pdf2web-backend/     # FastAPI backend
│   ├── app/             # Application code
│   ├── examples/        # Streamlit/Gradio apps
│   └── .env.example     # Environment template
├── pdf2web-frontend/    # React frontend
└── docs/                # Documentation
```

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [Backend README](pdf2web-backend/README.md) | Full backend documentation |
| [Frontend README](pdf2web-frontend/README.md) | Frontend integration guide |
| [API Quick Reference](docs/API_QUICK_REFERENCE.md) | API endpoints reference |
| [Frontend Integration](docs/FRONTEND_INTEGRATION_GUIDE.md) | Integration guide |

## 🎯 Three Ways to Use

1. **React Frontend** (Full Features): `npm run dev` in frontend
2. **Streamlit App** (Python Native): `streamlit run examples/streamlit_app.py`
3. **Built-in Dashboard** (No Install): Open http://localhost:8000/ui

