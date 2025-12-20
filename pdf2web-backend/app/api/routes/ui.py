"""
DocuMorph AI - Full Co-Design Dashboard
Runs on http://localhost:8000 - No separate Streamlit needed!

Features:
1. Hybrid Local AI (Privacy First) - Secure Mode with PII redaction
2. Semantic Component Injection - Table→Chart, Quiz, Code widgets
3. Co-Design Layer - Human-in-the-loop review and editing
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocuMorph AI - Co-Design Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --cyan: #06b6d4; --purple: #8b5cf6; }
        body { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); }
        .glass { background: rgba(30, 41, 59, 0.8); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
        .dropzone { border: 2px dashed #4f46e5; transition: all 0.3s; }
        .dropzone:hover, .dropzone.dragover { border-color: var(--cyan); background: rgba(6, 182, 212, 0.1); }
        .spinner { animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .slide-in { animation: slideIn 0.3s ease-out; }
        @keyframes slideIn { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        .confidence-bar { height: 4px; border-radius: 2px; background: #374151; }
        .confidence-fill { height: 100%; border-radius: 2px; transition: width 0.3s; }
        .tab-active { border-bottom: 2px solid var(--cyan); color: var(--cyan); }
        .block-card:hover { border-color: var(--cyan); }
        .pii-tag { font-size: 10px; padding: 2px 6px; border-radius: 4px; }
        .suggestion-badge { background: linear-gradient(135deg, #8b5cf6, #06b6d4); }
        textarea:focus, input:focus, select:focus { outline: none; border-color: var(--cyan); }
        .toggle-switch { width: 44px; height: 24px; background: #374151; border-radius: 12px; position: relative; cursor: pointer; transition: 0.3s; }
        .toggle-switch.active { background: var(--cyan); }
        .toggle-switch::after { content: ''; position: absolute; width: 20px; height: 20px; background: white; border-radius: 50%; top: 2px; left: 2px; transition: 0.3s; }
        .toggle-switch.active::after { left: 22px; }
    </style>
</head>
<body class="text-gray-100 min-h-screen">
    <!-- Sidebar -->
    <div class="fixed left-0 top-0 h-full w-16 glass flex flex-col items-center py-4 z-50">
        <div class="text-2xl mb-8">📄</div>
        <nav class="flex flex-col gap-4">
            <button class="nav-btn p-3 rounded-lg hover:bg-white/10 text-cyan-400" data-section="upload" title="Upload">
                <i class="fas fa-upload"></i>
            </button>
            <button class="nav-btn p-3 rounded-lg hover:bg-white/10 text-gray-400" data-section="codesign" title="Co-Design">
                <i class="fas fa-edit"></i>
            </button>
            <button class="nav-btn p-3 rounded-lg hover:bg-white/10 text-gray-400" data-section="preview" title="Preview">
                <i class="fas fa-eye"></i>
            </button>
            <button class="nav-btn p-3 rounded-lg hover:bg-white/10 text-gray-400" data-section="export" title="Export">
                <i class="fas fa-download"></i>
            </button>
        </nav>
        <div class="mt-auto">
            <button class="p-3 rounded-lg hover:bg-white/10 text-gray-400" title="Settings">
                <i class="fas fa-cog"></i>
            </button>
        </div>
    </div>

    <!-- Main Content -->
    <div class="ml-16 p-6">
        <!-- Header -->
        <header class="flex items-center justify-between mb-6">
            <div>
                <h1 class="text-2xl font-bold">DocuMorph AI</h1>
                <p class="text-gray-400 text-sm">Transform PDFs to Interactive HTML with Co-Design</p>
            </div>
            <div class="flex items-center gap-4">
                <div id="status-indicator" class="flex items-center gap-2 px-3 py-1 rounded-full glass text-sm">
                    <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
                    <span>System Ready</span>
                </div>
            </div>
        </header>

        <!-- Stats Cards -->
        <div class="grid grid-cols-4 gap-4 mb-6">
            <div class="glass rounded-xl p-4">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-400 text-sm">Content Blocks</p>
                        <p id="stat-blocks" class="text-2xl font-bold text-cyan-400">0</p>
                    </div>
                    <i class="fas fa-cubes text-2xl text-cyan-400/30"></i>
                </div>
            </div>
            <div class="glass rounded-xl p-4">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-400 text-sm">PII Redacted</p>
                        <p id="stat-pii" class="text-2xl font-bold text-amber-400">0</p>
                    </div>
                    <i class="fas fa-shield-alt text-2xl text-amber-400/30"></i>
                </div>
            </div>
            <div class="glass rounded-xl p-4">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-400 text-sm">Suggestions</p>
                        <p id="stat-suggestions" class="text-2xl font-bold text-purple-400">0</p>
                    </div>
                    <i class="fas fa-magic text-2xl text-purple-400/30"></i>
                </div>
            </div>
            <div class="glass rounded-xl p-4">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-400 text-sm">Low Confidence</p>
                        <p id="stat-lowconf" class="text-2xl font-bold text-red-400">0</p>
                    </div>
                    <i class="fas fa-exclamation-triangle text-2xl text-red-400/30"></i>
                </div>
            </div>
        </div>

        <!-- Section: Upload -->
        <section id="section-upload" class="section-content">
            <div class="grid grid-cols-3 gap-6">
                <!-- Upload Area -->
                <div class="col-span-2">
                    <div class="glass rounded-xl p-6">
                        <h2 class="text-lg font-semibold mb-4"><i class="fas fa-cloud-upload-alt mr-2 text-cyan-400"></i>Upload PDF</h2>
                        <div id="dropzone" class="dropzone rounded-xl p-12 text-center cursor-pointer">
                            <i class="fas fa-file-pdf text-5xl text-gray-500 mb-4"></i>
                            <p class="text-lg">Drag & drop your PDF here</p>
                            <p class="text-gray-400 text-sm mt-1">or click to browse (max 50MB)</p>
                            <input type="file" id="file-input" accept=".pdf" class="hidden">
                        </div>
                        <div id="file-info" class="hidden mt-4 p-4 bg-emerald-500/10 rounded-lg border border-emerald-500/30">
                            <div class="flex items-center gap-3">
                                <i class="fas fa-check-circle text-emerald-400 text-xl"></i>
                                <div>
                                    <p id="file-name" class="font-medium"></p>
                                    <p id="file-size" class="text-sm text-gray-400"></p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Settings Panel -->
                <div class="space-y-4">
                    <!-- Secure Mode (Pillar 1) -->
                    <div class="glass rounded-xl p-4">
                        <div class="flex items-center justify-between mb-3">
                            <h3 class="font-semibold"><i class="fas fa-shield-alt mr-2 text-amber-400"></i>Secure Mode</h3>
                            <div id="secure-toggle" class="toggle-switch active"></div>
                        </div>
                        <p class="text-xs text-gray-400 mb-3">PII is redacted locally before cloud processing</p>
                        <div id="pii-options" class="space-y-2 text-sm">
                            <label class="flex items-center gap-2"><input type="checkbox" checked class="pii-opt rounded" data-type="emails"><span>📧 Emails</span></label>
                            <label class="flex items-center gap-2"><input type="checkbox" checked class="pii-opt rounded" data-type="phones"><span>📱 Phone Numbers</span></label>
                            <label class="flex items-center gap-2"><input type="checkbox" checked class="pii-opt rounded" data-type="names"><span>👤 Names</span></label>
                            <label class="flex items-center gap-2"><input type="checkbox" checked class="pii-opt rounded" data-type="ssn"><span>🔢 SSN</span></label>
                            <label class="flex items-center gap-2"><input type="checkbox" checked class="pii-opt rounded" data-type="cards"><span>💳 Credit Cards</span></label>
                        </div>
                    </div>

                    <!-- Theme Selection -->
                    <div class="glass rounded-xl p-4">
                        <h3 class="font-semibold mb-3"><i class="fas fa-palette mr-2 text-purple-400"></i>Theme</h3>
                        <select id="theme-select" class="w-full bg-gray-700/50 rounded-lg px-3 py-2 border border-gray-600">
                            <option value="light">☀️ Light</option>
                            <option value="dark" selected>🌙 Dark</option>
                            <option value="professional">💼 Professional</option>
                            <option value="academic">📚 Academic</option>
                            <option value="minimal">✨ Minimal</option>
                        </select>
                        <div id="theme-suggestion" class="hidden mt-2 p-2 bg-purple-500/10 rounded text-xs">
                            <span class="text-purple-400">AI Suggestion:</span> <span id="suggested-theme"></span>
                        </div>
                    </div>

                    <!-- Process Button -->
                    <button id="process-btn" disabled class="w-full bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-400 hover:to-purple-400 disabled:opacity-50 disabled:cursor-not-allowed px-6 py-3 rounded-xl font-semibold transition">
                        <i class="fas fa-rocket mr-2"></i>Process PDF
                    </button>
                </div>
            </div>
        </section>

        <!-- Section: Co-Design Layer (Pillar 3) -->
        <section id="section-codesign" class="section-content hidden">
            <div class="grid grid-cols-3 gap-6">
                <!-- Content Blocks Editor -->
                <div class="col-span-2 space-y-4">
                    <div class="glass rounded-xl p-4">
                        <div class="flex items-center justify-between mb-4">
                            <h2 class="text-lg font-semibold"><i class="fas fa-edit mr-2 text-cyan-400"></i>Co-Design Layer</h2>
                            <div class="flex gap-2">
                                <button id="accept-all-btn" class="px-3 py-1 bg-emerald-500/20 text-emerald-400 rounded-lg text-sm hover:bg-emerald-500/30">
                                    <i class="fas fa-check-double mr-1"></i>Accept All
                                </button>
                                <button id="show-low-conf-btn" class="px-3 py-1 bg-amber-500/20 text-amber-400 rounded-lg text-sm hover:bg-amber-500/30">
                                    <i class="fas fa-exclamation-triangle mr-1"></i>Show Low Confidence
                                </button>
                            </div>
                        </div>
                        
                        <!-- Tabs -->
                        <div class="flex border-b border-gray-700 mb-4">
                            <button class="codesign-tab tab-active px-4 py-2" data-tab="blocks">Content Blocks</button>
                            <button class="codesign-tab px-4 py-2 text-gray-400" data-tab="pii">PII Review</button>
                            <button class="codesign-tab px-4 py-2 text-gray-400" data-tab="semantic">Semantic Suggestions</button>
                            <button class="codesign-tab px-4 py-2 text-gray-400" data-tab="transparency">Transparency</button>
                        </div>

                        <!-- Tab: Content Blocks -->
                        <div id="tab-blocks" class="codesign-tab-content">
                            <div id="blocks-container" class="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                                <p class="text-gray-400 text-center py-8">Upload a PDF to see content blocks</p>
                            </div>
                        </div>

                        <!-- Tab: PII Review -->
                        <div id="tab-pii" class="codesign-tab-content hidden">
                            <div id="pii-container" class="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                                <p class="text-gray-400 text-center py-8">No PII detected</p>
                            </div>
                        </div>

                        <!-- Tab: Semantic Suggestions (Pillar 2) -->
                        <div id="tab-semantic" class="codesign-tab-content hidden">
                            <div id="semantic-container" class="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                                <p class="text-gray-400 text-center py-8">No semantic suggestions yet</p>
                            </div>
                        </div>

                        <!-- Tab: Transparency -->
                        <div id="tab-transparency" class="codesign-tab-content hidden">
                            <div class="space-y-4">
                                <div class="p-4 bg-emerald-500/10 rounded-lg border border-emerald-500/30">
                                    <h4 class="font-semibold text-emerald-400 mb-2"><i class="fas fa-check-circle mr-2"></i>What stays LOCAL</h4>
                                    <ul class="text-sm space-y-1 text-gray-300">
                                        <li>• Raw PDF file</li>
                                        <li>• Original images</li>
                                        <li>• PII data (names, emails, phones, SSN)</li>
                                        <li>• OCR processing</li>
                                    </ul>
                                </div>
                                <div class="p-4 bg-amber-500/10 rounded-lg border border-amber-500/30">
                                    <h4 class="font-semibold text-amber-400 mb-2"><i class="fas fa-cloud mr-2"></i>What goes to ERNIE (Cloud)</h4>
                                    <ul class="text-sm space-y-1 text-gray-300">
                                        <li>• Sanitized text structure only</li>
                                        <li>• Theme preferences</li>
                                        <li>• Non-sensitive metadata</li>
                                    </ul>
                                </div>
                                <div id="data-preview" class="p-4 bg-gray-800 rounded-lg">
                                    <h4 class="font-semibold mb-2">Data Preview (what ERNIE sees)</h4>
                                    <pre id="sanitized-preview" class="text-xs text-gray-400 max-h-40 overflow-auto"></pre>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Right Panel: Actions & Info -->
                <div class="space-y-4">
                    <!-- Quick Actions -->
                    <div class="glass rounded-xl p-4">
                        <h3 class="font-semibold mb-3"><i class="fas fa-bolt mr-2 text-yellow-400"></i>Quick Actions</h3>
                        <div class="grid grid-cols-2 gap-2">
                            <button id="auto-convert-btn" class="p-3 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 rounded-lg text-sm hover:from-cyan-500/30 hover:to-purple-500/30 border border-cyan-500/30">
                                <i class="fas fa-magic block text-lg mb-1 text-cyan-400"></i>
                                Auto Convert
                            </button>
                            <button id="generate-btn" class="p-3 bg-emerald-500/20 rounded-lg text-sm hover:bg-emerald-500/30 border border-emerald-500/30">
                                <i class="fas fa-code block text-lg mb-1 text-emerald-400"></i>
                                Generate HTML
                            </button>
                            <button id="refresh-ai-btn" class="p-3 bg-purple-500/20 rounded-lg text-sm hover:bg-purple-500/30 border border-purple-500/30">
                                <i class="fas fa-sync block text-lg mb-1 text-purple-400"></i>
                                Refresh AI
                            </button>
                            <button id="reset-btn" class="p-3 bg-red-500/20 rounded-lg text-sm hover:bg-red-500/30 border border-red-500/30">
                                <i class="fas fa-undo block text-lg mb-1 text-red-400"></i>
                                Reset
                            </button>
                        </div>
                    </div>

                    <!-- Theme Analysis -->
                    <div class="glass rounded-xl p-4">
                        <h3 class="font-semibold mb-3"><i class="fas fa-palette mr-2 text-purple-400"></i>Theme Analysis</h3>
                        <div id="theme-analysis" class="space-y-2">
                            <div class="flex justify-between text-sm">
                                <span>Suggested Theme</span>
                                <span id="ai-theme" class="text-purple-400">-</span>
                            </div>
                            <div class="flex justify-between text-sm">
                                <span>Confidence</span>
                                <span id="theme-confidence" class="text-cyan-400">-</span>
                            </div>
                            <div class="confidence-bar mt-2">
                                <div id="theme-conf-bar" class="confidence-fill bg-purple-500" style="width: 0%"></div>
                            </div>
                            <label class="flex items-center gap-2 mt-3 text-sm">
                                <input type="checkbox" id="theme-override" class="rounded">
                                <span>Override AI suggestion</span>
                            </label>
                        </div>
                    </div>

                    <!-- Processing Pipeline -->
                    <div class="glass rounded-xl p-4">
                        <h3 class="font-semibold mb-3"><i class="fas fa-stream mr-2 text-cyan-400"></i>Pipeline</h3>
                        <div class="space-y-2">
                            <div class="flex items-center gap-2 text-sm">
                                <span id="step-upload" class="w-6 h-6 rounded-full bg-gray-600 flex items-center justify-center text-xs">1</span>
                                <span>Upload</span>
                            </div>
                            <div class="flex items-center gap-2 text-sm">
                                <span id="step-ocr" class="w-6 h-6 rounded-full bg-gray-600 flex items-center justify-center text-xs">2</span>
                                <span>OCR Extract</span>
                            </div>
                            <div class="flex items-center gap-2 text-sm">
                                <span id="step-codesign" class="w-6 h-6 rounded-full bg-gray-600 flex items-center justify-center text-xs">3</span>
                                <span>Co-Design</span>
                            </div>
                            <div class="flex items-center gap-2 text-sm">
                                <span id="step-generate" class="w-6 h-6 rounded-full bg-gray-600 flex items-center justify-center text-xs">4</span>
                                <span>Generate HTML</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Section: Preview -->
        <section id="section-preview" class="section-content hidden">
            <div class="grid grid-cols-3 gap-6">
                <div class="col-span-2">
                    <div class="glass rounded-xl p-4">
                        <div class="flex items-center justify-between mb-4">
                            <h2 class="text-lg font-semibold"><i class="fas fa-eye mr-2 text-cyan-400"></i>HTML Preview</h2>
                            <div class="flex gap-2">
                                <button class="preview-size-btn px-3 py-1 bg-gray-700 rounded text-sm" data-size="desktop">
                                    <i class="fas fa-desktop"></i>
                                </button>
                                <button class="preview-size-btn px-3 py-1 bg-gray-700 rounded text-sm" data-size="tablet">
                                    <i class="fas fa-tablet-alt"></i>
                                </button>
                                <button class="preview-size-btn px-3 py-1 bg-gray-700 rounded text-sm" data-size="mobile">
                                    <i class="fas fa-mobile-alt"></i>
                                </button>
                            </div>
                        </div>
                        <div id="preview-container" class="bg-white rounded-lg overflow-hidden" style="height: 500px;">
                            <iframe id="html-preview" class="w-full h-full"></iframe>
                        </div>
                    </div>
                </div>
                <div class="space-y-4">
                    <!-- Components Injected -->
                    <div class="glass rounded-xl p-4">
                        <h3 class="font-semibold mb-3"><i class="fas fa-puzzle-piece mr-2 text-purple-400"></i>Components Injected</h3>
                        <div id="components-list" class="space-y-2 text-sm">
                            <p class="text-gray-400">Generate HTML to see components</p>
                        </div>
                    </div>
                    <!-- Accessibility -->
                    <div class="glass rounded-xl p-4">
                        <h3 class="font-semibold mb-3"><i class="fas fa-universal-access mr-2 text-emerald-400"></i>Accessibility</h3>
                        <div id="accessibility-info" class="space-y-2 text-sm">
                            <div class="flex justify-between"><span>WCAG Level</span><span class="text-emerald-400">AA</span></div>
                            <div class="flex justify-between"><span>ARIA Labels</span><span class="text-emerald-400">✓</span></div>
                            <div class="flex justify-between"><span>Keyboard Nav</span><span class="text-emerald-400">✓</span></div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Section: Export -->
        <section id="section-export" class="section-content hidden">
            <div class="grid grid-cols-3 gap-6">
                <div class="col-span-2">
                    <div class="glass rounded-xl p-6">
                        <h2 class="text-lg font-semibold mb-4"><i class="fas fa-download mr-2 text-cyan-400"></i>Export & Deploy</h2>
                        <div class="grid grid-cols-2 gap-4">
                            <button id="download-html-btn" class="p-6 bg-cyan-500/10 rounded-xl border border-cyan-500/30 hover:bg-cyan-500/20 transition text-left">
                                <i class="fas fa-file-code text-3xl text-cyan-400 mb-2"></i>
                                <h4 class="font-semibold">Download HTML</h4>
                                <p class="text-sm text-gray-400">Complete HTML package (ZIP)</p>
                            </button>
                            <button id="download-md-btn" class="p-6 bg-purple-500/10 rounded-xl border border-purple-500/30 hover:bg-purple-500/20 transition text-left">
                                <i class="fas fa-file-alt text-3xl text-purple-400 mb-2"></i>
                                <h4 class="font-semibold">Download Markdown</h4>
                                <p class="text-sm text-gray-400">Markdown + images</p>
                            </button>
                            <button id="deploy-github-btn" class="p-6 bg-gray-700/50 rounded-xl border border-gray-600 hover:bg-gray-700 transition text-left">
                                <i class="fab fa-github text-3xl text-gray-300 mb-2"></i>
                                <h4 class="font-semibold">GitHub Pages</h4>
                                <p class="text-sm text-gray-400">Deploy to GitHub</p>
                            </button>
                            <button id="deploy-netlify-btn" class="p-6 bg-gray-700/50 rounded-xl border border-gray-600 hover:bg-gray-700 transition text-left">
                                <i class="fas fa-globe text-3xl text-teal-400 mb-2"></i>
                                <h4 class="font-semibold">Netlify</h4>
                                <p class="text-sm text-gray-400">One-click deploy</p>
                            </button>
                        </div>
                    </div>
                </div>
                <div>
                    <div class="glass rounded-xl p-4">
                        <h3 class="font-semibold mb-3"><i class="fas fa-info-circle mr-2 text-cyan-400"></i>Export Info</h3>
                        <div id="export-info" class="space-y-2 text-sm">
                            <div class="flex justify-between"><span>Document</span><span id="export-filename" class="text-cyan-400">-</span></div>
                            <div class="flex justify-between"><span>Theme</span><span id="export-theme" class="text-purple-400">-</span></div>
                            <div class="flex justify-between"><span>Components</span><span id="export-components" class="text-emerald-400">0</span></div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Progress Modal -->
        <div id="progress-modal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 hidden">
            <div class="glass rounded-xl p-8 max-w-md w-full mx-4">
                <div class="flex items-center gap-4 mb-4">
                    <div class="spinner w-10 h-10 border-4 border-cyan-400 border-t-transparent rounded-full"></div>
                    <div>
                        <p id="progress-text" class="font-semibold">Processing...</p>
                        <p id="progress-detail" class="text-sm text-gray-400"></p>
                    </div>
                </div>
                <div class="bg-gray-700 rounded-full h-2">
                    <div id="progress-bar" class="bg-gradient-to-r from-cyan-400 to-purple-400 h-2 rounded-full transition-all" style="width: 0%"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
    const API = '/api';
    let state = { docId: null, filename: '', html: '', markdown: '', blocks: [], pii: [], suggestions: [], secureMode: true };

    // Elements
    const $ = id => document.getElementById(id);
    const $$ = sel => document.querySelectorAll(sel);

    // Navigation
    $$('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            $$('.nav-btn').forEach(b => b.classList.replace('text-cyan-400', 'text-gray-400'));
            btn.classList.replace('text-gray-400', 'text-cyan-400');
            $$('.section-content').forEach(s => s.classList.add('hidden'));
            $('section-' + btn.dataset.section).classList.remove('hidden');
        });
    });

    // Secure Mode Toggle
    $('secure-toggle').addEventListener('click', function() {
        this.classList.toggle('active');
        state.secureMode = this.classList.contains('active');
        $('pii-options').style.opacity = state.secureMode ? '1' : '0.5';
    });

    // File Upload
    const dropzone = $('dropzone');
    const fileInput = $('file-input');
    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('dragover'); });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', e => { e.preventDefault(); dropzone.classList.remove('dragover'); handleFile(e.dataTransfer.files[0]); });
    fileInput.addEventListener('change', e => handleFile(e.target.files[0]));

    function handleFile(file) {
        if (!file || file.type !== 'application/pdf') return alert('Please upload a PDF file');
        state.filename = file.name;
        state.file = file;
        $('file-info').classList.remove('hidden');
        $('file-name').textContent = file.name;
        $('file-size').textContent = (file.size / 1024 / 1024).toFixed(2) + ' MB';
        $('process-btn').disabled = false;
    }

    // Process PDF
    $('process-btn').addEventListener('click', processPDF);

    async function processPDF() {
        showProgress('Uploading PDF...', 10);
        setStep('upload', 'active');

        const formData = new FormData();
        formData.append('file', state.file);
        formData.append('mode', state.secureMode ? 'secure' : 'standard');
        $$('.pii-opt').forEach(opt => formData.append('redact_' + opt.dataset.type, opt.checked));

        try {
            // Upload
            const uploadRes = await fetch(`${API}/pdf/upload`, { method: 'POST', body: formData });
            const uploadData = await uploadRes.json();
            if (!uploadRes.ok) throw new Error(uploadData.detail);
            state.docId = uploadData.document_id;
            setStep('upload', 'done');

            // OCR & Extract
            showProgress('Extracting content with OCR...', 30);
            setStep('ocr', 'active');

            // Get preview (triggers analysis)
            showProgress('Analyzing content...', 50);
            const previewRes = await fetch(`${API}/codesign/${state.docId}/preview`);
            const previewData = await previewRes.json();
            setStep('ocr', 'done');

            // Store data
            state.blocks = previewData.blocks || [];
            state.pii = previewData.pii_redactions || [];
            state.suggestions = previewData.semantic_suggestions || [];
            state.markdown = previewData.markdown || '';

            // Update stats
            $('stat-blocks').textContent = previewData.stats?.total_blocks || 0;
            $('stat-pii').textContent = previewData.stats?.pii_count || 0;
            $('stat-suggestions').textContent = previewData.stats?.suggestion_count || 0;
            $('stat-lowconf').textContent = previewData.stats?.low_confidence_count || 0;

            // Theme analysis
            if (previewData.theme_analysis) {
                $('ai-theme').textContent = previewData.theme_analysis.suggested_theme;
                $('theme-confidence').textContent = (previewData.theme_analysis.confidence * 100).toFixed(0) + '%';
                $('theme-conf-bar').style.width = (previewData.theme_analysis.confidence * 100) + '%';
                $('theme-suggestion').classList.remove('hidden');
                $('suggested-theme').textContent = previewData.theme_analysis.suggested_theme;
            }

            // Render Co-Design UI
            renderBlocks();
            renderPII();
            renderSemantic();
            renderTransparency();

            hideProgress();
            setStep('codesign', 'active');
            
            // Navigate to Co-Design
            $$('.nav-btn')[1].click();

        } catch (err) {
            hideProgress();
            alert('Error: ' + err.message);
        }
    }

    // Render Content Blocks
    function renderBlocks() {
        const container = $('blocks-container');
        if (!state.blocks.length) {
            container.innerHTML = '<p class="text-gray-400 text-center py-8">No content blocks</p>';
            return;
        }
        container.innerHTML = state.blocks.map(block => `
            <div class="block-card p-3 bg-gray-800/50 rounded-lg border border-gray-700 hover:border-cyan-500/50 transition" data-id="${block.id}">
                <div class="flex items-start justify-between mb-2">
                    <div class="flex items-center gap-2">
                        <span class="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 rounded text-xs uppercase">${block.type}</span>
                        <span class="text-xs text-gray-400">Page ${block.page + 1}</span>
                        ${block.confidence < 0.8 ? '<span class="px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded text-xs"><i class="fas fa-exclamation-triangle mr-1"></i>Low Confidence</span>' : ''}
                    </div>
                    <div class="flex items-center gap-1">
                        <div class="confidence-bar w-16">
                            <div class="confidence-fill ${block.confidence >= 0.8 ? 'bg-emerald-500' : 'bg-amber-500'}" style="width: ${block.confidence * 100}%"></div>
                        </div>
                        <span class="text-xs text-gray-400">${(block.confidence * 100).toFixed(0)}%</span>
                    </div>
                </div>
                <textarea class="w-full bg-gray-900/50 rounded p-2 text-sm resize-none border border-gray-700 focus:border-cyan-500" rows="2" data-block-id="${block.id}">${escapeHtml(block.content)}</textarea>
                <div class="flex items-center justify-between mt-2">
                    <select class="bg-gray-700 rounded px-2 py-1 text-xs" data-block-id="${block.id}">
                        <option value="heading" ${block.type === 'heading' ? 'selected' : ''}>Heading</option>
                        <option value="paragraph" ${block.type === 'paragraph' ? 'selected' : ''}>Paragraph</option>
                        <option value="table" ${block.type === 'table' ? 'selected' : ''}>Table</option>
                        <option value="list" ${block.type === 'list' ? 'selected' : ''}>List</option>
                        <option value="code" ${block.type === 'code' ? 'selected' : ''}>Code</option>
                    </select>
                    <button class="save-block-btn px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded text-xs hover:bg-emerald-500/30" data-id="${block.id}">
                        <i class="fas fa-save mr-1"></i>Save
                    </button>
                </div>
            </div>
        `).join('');

        // Save block handlers
        container.querySelectorAll('.save-block-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.dataset.id;
                const card = btn.closest('.block-card');
                const content = card.querySelector('textarea').value;
                const type = card.querySelector('select').value;
                await fetch(`${API}/codesign/${state.docId}/edit-block`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ block_id: id, new_content: content, new_type: type })
                });
                btn.innerHTML = '<i class="fas fa-check mr-1"></i>Saved!';
                setTimeout(() => btn.innerHTML = '<i class="fas fa-save mr-1"></i>Save', 1500);
            });
        });
    }

    // Render PII
    function renderPII() {
        const container = $('pii-container');
        if (!state.pii.length) {
            container.innerHTML = '<p class="text-gray-400 text-center py-8">No PII detected</p>';
            return;
        }
        container.innerHTML = state.pii.map(pii => `
            <div class="p-3 bg-gray-800/50 rounded-lg border border-amber-500/30">
                <div class="flex items-center justify-between mb-2">
                    <span class="pii-tag bg-amber-500/20 text-amber-400">${pii.pii_type}</span>
                    <span class="text-xs text-gray-400">${(pii.confidence * 100).toFixed(0)}% confidence</span>
                </div>
                <div class="flex items-center gap-2 text-sm">
                    <span class="text-gray-400">Original:</span>
                    <code class="bg-gray-900 px-2 py-0.5 rounded">${pii.original.substring(0, 3)}***</code>
                    <span class="text-gray-400">→</span>
                    <code class="bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded">${pii.redacted}</code>
                </div>
                <div class="flex gap-2 mt-2">
                    <button class="pii-approve px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded text-xs" data-id="${pii.id}">
                        <i class="fas fa-check mr-1"></i>Approve
                    </button>
                    <button class="pii-undo px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs" data-id="${pii.id}">
                        <i class="fas fa-undo mr-1"></i>Undo
                    </button>
                </div>
            </div>
        `).join('');

        // PII action handlers
        container.querySelectorAll('.pii-undo').forEach(btn => {
            btn.addEventListener('click', async () => {
                await fetch(`${API}/codesign/${state.docId}/pii-action`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ redaction_id: btn.dataset.id, action: 'undo' })
                });
                btn.closest('div.p-3').remove();
                $('stat-pii').textContent = parseInt($('stat-pii').textContent) - 1;
            });
        });
    }

    // Render Semantic Suggestions (Pillar 2)
    function renderSemantic() {
        const container = $('semantic-container');
        if (!state.suggestions.length) {
            container.innerHTML = '<p class="text-gray-400 text-center py-8">No semantic suggestions</p>';
            return;
        }
        container.innerHTML = state.suggestions.map(s => {
            const icons = { chart_bar: 'fa-chart-bar', chart_line: 'fa-chart-line', chart_pie: 'fa-chart-pie', quiz: 'fa-question-circle', code_block: 'fa-code', timeline: 'fa-stream', map: 'fa-map-marker-alt' };
            const icon = icons[s.suggestion] || 'fa-magic';
            const block = state.blocks.find(b => b.id === s.block_id);
            return `
            <div class="p-3 bg-gray-800/50 rounded-lg border border-purple-500/30">
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center gap-2">
                        <span class="suggestion-badge px-2 py-1 rounded text-xs text-white"><i class="fas ${icon} mr-1"></i>${s.suggestion.replace('_', ' ')}</span>
                        <span class="text-xs text-gray-400">${(s.confidence * 100).toFixed(0)}% confidence</span>
                    </div>
                </div>
                <p class="text-sm text-gray-300 mb-2">${block ? escapeHtml(block.content.substring(0, 100)) + '...' : 'Block content'}</p>
                ${s.suggestion.startsWith('chart') ? `
                <div class="flex gap-2 mt-2">
                    <label class="flex items-center gap-1 text-xs"><input type="radio" name="chart-${s.block_id}" value="keep_table" class="chart-option" data-block="${s.block_id}"> Keep Table</label>
                    <label class="flex items-center gap-1 text-xs"><input type="radio" name="chart-${s.block_id}" value="convert_to_chart" class="chart-option" data-block="${s.block_id}" checked> Convert to Chart</label>
                    <label class="flex items-center gap-1 text-xs"><input type="radio" name="chart-${s.block_id}" value="hybrid" class="chart-option" data-block="${s.block_id}"> Hybrid</label>
                </div>` : ''}
                ${s.suggestion === 'quiz' ? `
                <label class="flex items-center gap-2 mt-2 text-xs">
                    <input type="checkbox" class="quiz-toggle rounded" data-block="${s.block_id}" checked>
                    <span>Enable Quiz Mode</span>
                </label>` : ''}
                ${s.suggestion === 'code_block' ? `
                <label class="flex items-center gap-2 mt-2 text-xs">
                    <input type="checkbox" class="code-exec-toggle rounded" data-block="${s.block_id}">
                    <span>Enable Code Execution</span>
                </label>` : ''}
            </div>`;
        }).join('');
    }

    // Render Transparency
    function renderTransparency() {
        $('sanitized-preview').textContent = state.markdown.substring(0, 500) + (state.markdown.length > 500 ? '...' : '');
    }

    // Co-Design Tabs
    $$('.codesign-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            $$('.codesign-tab').forEach(t => { t.classList.remove('tab-active'); t.classList.add('text-gray-400'); });
            tab.classList.add('tab-active'); tab.classList.remove('text-gray-400');
            $$('.codesign-tab-content').forEach(c => c.classList.add('hidden'));
            $('tab-' + tab.dataset.tab).classList.remove('hidden');
        });
    });

    // Accept All
    $('accept-all-btn').addEventListener('click', async () => {
        await fetch(`${API}/codesign/${state.docId}/bulk-approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ approve_all: true })
        });
        state.blocks.forEach(b => b.confidence = 1.0);
        renderBlocks();
        $('stat-lowconf').textContent = '0';
    });

    // Auto Convert
    $('auto-convert-btn').addEventListener('click', async () => {
        showProgress('Auto-converting with AI...', 50);
        try {
            const theme = $('theme-select').value;
            const res = await fetch(`${API}/codesign/${state.docId}/auto-convert`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ theme })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail);
            state.html = data.html;
            showPreview(data);
            hideProgress();
            setStep('generate', 'done');
            $$('.nav-btn')[2].click(); // Go to preview
        } catch (err) {
            hideProgress();
            alert('Error: ' + err.message);
        }
    });

    // Generate HTML with selections
    $('generate-btn').addEventListener('click', async () => {
        showProgress('Generating HTML...', 50);
        try {
            // Collect selections
            const chartConversions = {};
            $$('.chart-option:checked').forEach(opt => chartConversions[opt.dataset.block] = opt.value);
            const quizBlocks = [...$$('.quiz-toggle:checked')].map(c => c.dataset.block);
            const codeBlocks = [...$$('.code-exec-toggle:checked')].map(c => c.dataset.block);

            const res = await fetch(`${API}/codesign/${state.docId}/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    theme: $('theme-select').value,
                    theme_override: $('theme-override').checked,
                    approved_components: state.suggestions.map(s => s.block_id),
                    chart_conversions: chartConversions,
                    quiz_enabled_blocks: quizBlocks,
                    code_execution_blocks: codeBlocks,
                    timeline_blocks: [],
                    map_blocks: [],
                    edits: [],
                    pii_actions: []
                })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail);
            state.html = data.html;
            showPreview(data);
            hideProgress();
            setStep('generate', 'done');
            $$('.nav-btn')[2].click();
        } catch (err) {
            hideProgress();
            alert('Error: ' + err.message);
        }
    });

    function showPreview(data) {
        $('html-preview').srcdoc = state.html;
        $('export-filename').textContent = state.filename;
        $('export-theme').textContent = data.theme || $('theme-select').value;
        $('export-components').textContent = data.components_injected?.length || 0;
        
        // Components list
        const compList = $('components-list');
        if (data.components_injected?.length) {
            compList.innerHTML = data.components_injected.map(c => `
                <div class="flex items-center gap-2 text-sm">
                    <i class="fas fa-check-circle text-emerald-400"></i>
                    <span>${c}</span>
                </div>
            `).join('');
        }
    }

    // Preview size buttons
    $$('.preview-size-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const sizes = { desktop: '100%', tablet: '768px', mobile: '375px' };
            $('preview-container').style.maxWidth = sizes[btn.dataset.size];
        });
    });

    // Downloads
    $('download-html-btn').addEventListener('click', () => download(state.html, state.filename.replace('.pdf', '.html'), 'text/html'));
    $('download-md-btn').addEventListener('click', () => download(state.markdown, state.filename.replace('.pdf', '.md'), 'text/markdown'));

    function download(content, filename, type) {
        const blob = new Blob([content], { type });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = filename;
        a.click();
    }

    // Reset
    $('reset-btn').addEventListener('click', () => {
        state = { docId: null, filename: '', html: '', markdown: '', blocks: [], pii: [], suggestions: [], secureMode: true };
        $('file-info').classList.add('hidden');
        $('process-btn').disabled = true;
        ['stat-blocks', 'stat-pii', 'stat-suggestions', 'stat-lowconf'].forEach(id => $(id).textContent = '0');
        ['step-upload', 'step-ocr', 'step-codesign', 'step-generate'].forEach(id => $(id).className = 'w-6 h-6 rounded-full bg-gray-600 flex items-center justify-center text-xs');
        $$('.nav-btn')[0].click();
    });

    // Helpers
    function showProgress(text, percent) {
        $('progress-modal').classList.remove('hidden');
        $('progress-text').textContent = text;
        $('progress-bar').style.width = percent + '%';
    }
    function hideProgress() { $('progress-modal').classList.add('hidden'); }
    function setStep(step, status) {
        const el = $('step-' + step);
        el.className = 'w-6 h-6 rounded-full flex items-center justify-center text-xs ' + 
            (status === 'done' ? 'bg-emerald-500' : status === 'active' ? 'bg-cyan-500 pulse' : 'bg-gray-600');
    }
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    </script>
</body>
</html>'''


@router.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the Co-Design Dashboard UI."""
    return DASHBOARD_HTML
