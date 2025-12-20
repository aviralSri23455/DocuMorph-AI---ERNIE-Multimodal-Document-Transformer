const API_BASE = '/api'

export interface UploadResponse {
  document_id: string
  filename: string
  total_pages: number
  processing_mode: 'secure' | 'standard'
}

export interface PreviewBlock {
  block_id: string
  type: string
  content: string
  confidence: number
  page: number
  position: { x: number; y: number; width: number; height: number }
}

export interface PIIRedaction {
  id: string
  pii_type: string
  original: string
  redacted: string
  start: number
  end: number
  confidence: number
  block_id: string
  // Alias for compatibility
  redaction_id?: string
  type?: string
}

export interface PreviewResponse {
  blocks: PreviewBlock[]
  pii_redactions: PIIRedaction[]
  theme_analysis: { suggested_theme: string; confidence: number }
  semantic_suggestions: Array<{
    block_id: string
    suggestion: string
    confidence: number
    config?: Record<string, unknown>
  }>
  stats: {
    total_blocks: number
    low_confidence_count: number
    pii_count: number
  }
}

export interface GenerateResponse {
  document_id: string
  html: string
  assets: string[]
  theme: string
  components_injected: string[]
}

export interface HealthResponse {
  status: string
  configured: boolean
  model: string | null
  api_url?: string | null
  vision_enabled: boolean
  vision_model: string | null
  message?: string
}

export interface StatsResponse {
  documents_processed: number
  avg_processing_time: number
  semantic_injections: number
  success_rate: number
}

class ApiClient {
  private ws: WebSocket | null = null
  private wsListeners: Map<string, Set<(data: unknown) => void>> = new Map()

  async uploadPDF(
    file: File,
    mode: 'secure' | 'standard',
    piiOptions?: {
      redact_emails?: boolean
      redact_phones?: boolean
      redact_names?: boolean
      redact_ssn?: boolean
      redact_credit_cards?: boolean
    },
    language: string = 'en'
  ): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('mode', mode)
    formData.append('language', language)
    if (piiOptions) {
      Object.entries(piiOptions).forEach(([key, value]) => {
        formData.append(key, String(value))
      })
    }

    // Use AbortController for timeout (5 minutes for large PDFs with OCR)
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 300000) // 5 min timeout

    try {
      const res = await fetch(`${API_BASE}/pdf/upload`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      })
      clearTimeout(timeoutId)
      if (!res.ok) throw new Error(await res.text())
      return res.json()
    } catch (error) {
      clearTimeout(timeoutId)
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Upload timeout - PDF processing is taking too long. Try a smaller file.')
      }
      throw error
    }
  }

  async getPreview(documentId: string): Promise<PreviewResponse> {
    const res = await fetch(`${API_BASE}/codesign/${documentId}/preview`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async editBlock(documentId: string, blockId: string, newContent: string, newType?: string) {
    const res = await fetch(`${API_BASE}/codesign/${documentId}/edit-block`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ block_id: blockId, new_content: newContent, new_type: newType }),
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async piiAction(documentId: string, redactionId: string, action: 'approve' | 'undo' | 'modify') {
    const res = await fetch(`${API_BASE}/codesign/${documentId}/pii-action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ redaction_id: redactionId, action }),
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async bulkApprove(documentId: string) {
    const res = await fetch(`${API_BASE}/codesign/${documentId}/bulk-approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approve_all: true }),
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async generateHTML(
    documentId: string,
    options: {
      theme?: string
      theme_override?: boolean
      approved_components?: string[]
      chart_conversions?: Record<string, string>
      quiz_enabled_blocks?: string[]
      code_execution_blocks?: string[]
      timeline_blocks?: string[]
      map_blocks?: string[]
    }
  ): Promise<GenerateResponse> {
    const res = await fetch(`${API_BASE}/codesign/${documentId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: documentId, ...options }),
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async exportHTML(documentId: string) {
    const res = await fetch(`${API_BASE}/export/${documentId}/html`, { method: 'POST' })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async downloadHTML(documentId: string): Promise<Blob> {
    const res = await fetch(`${API_BASE}/export/download/${documentId}/html`)
    if (!res.ok) throw new Error(await res.text())
    return res.blob()
  }

  async deployNetlify(documentId: string, netlifyToken: string, siteName: string) {
    const res = await fetch(`${API_BASE}/deploy/${documentId}/netlify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ netlify_token: netlifyToken, site_name: siteName }),
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async deployGitHub(documentId: string, repoName: string, githubToken: string) {
    const res = await fetch(`${API_BASE}/export/${documentId}/github-pages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_name: repoName, github_token: githubToken }),
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async checkHealth(): Promise<{ status: string }> {
    const res = await fetch('/health')
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async checkErnieHealth(): Promise<HealthResponse> {
    try {
      const res = await fetch(`${API_BASE}/health/ernie`)
      if (!res.ok) {
        // Return a default response instead of throwing
        return {
          status: 'error',
          configured: false,
          model: null,
          vision_enabled: false,
          vision_model: null,
        } as HealthResponse
      }
      return res.json()
    } catch {
      // Return a default response on network error
      return {
        status: 'error',
        configured: false,
        model: null,
        vision_enabled: false,
        vision_model: null,
      } as HealthResponse
    }
  }

  async getTransparency(documentId: string) {
    const res = await fetch(`${API_BASE}/codesign/${documentId}/data-sent-to-cloud`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  // Knowledge Graph endpoints
  async generateKnowledgeGraph(documentId: string) {
    const res = await fetch(`${API_BASE}/knowledge-graph/${documentId}/generate`, { method: 'POST' })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async getKnowledgeGraph(documentId: string) {
    const res = await fetch(`${API_BASE}/knowledge-graph/${documentId}`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async simplifyKnowledgeGraph(documentId: string, maxNodes: number = 20) {
    const res = await fetch(`${API_BASE}/knowledge-graph/${documentId}/simplify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ max_nodes: maxNodes }),
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async getKnowledgeGraphSidebar(documentId: string) {
    const res = await fetch(`${API_BASE}/knowledge-graph/${documentId}/sidebar-data`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  // Additional Co-Design endpoints
  async getLowConfidenceBlocks(documentId: string) {
    const res = await fetch(`${API_BASE}/codesign/${documentId}/low-confidence`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async getChartSuggestion(documentId: string, blockId: string) {
    const res = await fetch(`${API_BASE}/codesign/${documentId}/chart-suggestion/${blockId}`, { method: 'POST' })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async regenerateSuggestions(documentId: string) {
    const res = await fetch(`${API_BASE}/codesign/${documentId}/regenerate-suggestions`, { method: 'POST' })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async resetDocument(documentId: string) {
    const res = await fetch(`${API_BASE}/codesign/${documentId}/reset`, { method: 'POST' })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async autoConvert(documentId: string) {
    const res = await fetch(`${API_BASE}/codesign/${documentId}/auto-convert`, { method: 'POST' })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  // Additional Export endpoints
  async exportMarkdown(documentId: string) {
    const res = await fetch(`${API_BASE}/export/${documentId}/markdown`, { method: 'POST' })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async downloadMarkdown(documentId: string): Promise<Blob> {
    const res = await fetch(`${API_BASE}/export/download/${documentId}/markdown`)
    if (!res.ok) throw new Error(await res.text())
    return res.blob()
  }

  async previewHTML(documentId: string): Promise<string> {
    const res = await fetch(`${API_BASE}/export/${documentId}/preview-html`)
    if (!res.ok) throw new Error(await res.text())
    return res.text()
  }

  // Additional Deploy endpoints
  async deployVercel(documentId: string, vercelToken: string, projectName?: string) {
    const res = await fetch(`${API_BASE}/deploy/${documentId}/vercel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ vercel_token: vercelToken, project_name: projectName }),
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async deployS3(documentId: string, awsAccessKey: string, awsSecretKey: string, bucketName: string, region: string) {
    const res = await fetch(`${API_BASE}/deploy/${documentId}/s3`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ aws_access_key: awsAccessKey, aws_secret_key: awsSecretKey, bucket_name: bucketName, region }),
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  // Accessibility check
  async checkAccessibility(documentId: string, wcagLevel: string = 'AA') {
    const res = await fetch(`${API_BASE}/accessibility/validate/${documentId}?wcag_level=${wcagLevel}`, {
      method: 'POST',
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async enhanceAccessibility(documentId: string) {
    const res = await fetch(`${API_BASE}/accessibility/enhance/${documentId}`, {
      method: 'POST',
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async getAccessibilityRules() {
    const res = await fetch(`${API_BASE}/accessibility/rules`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  // Get audit logs
  async getAuditLogs(documentId: string) {
    const res = await fetch(`${API_BASE}/audit/${documentId}/logs`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  // Get plugins
  async getPlugins() {
    const res = await fetch(`${API_BASE}/plugins`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  // Delete document
  async deleteDocument(documentId: string) {
    const res = await fetch(`${API_BASE}/pdf/${documentId}`, { method: 'DELETE' })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  // Get document blocks
  async getBlocks(documentId: string) {
    const res = await fetch(`${API_BASE}/pdf/${documentId}/blocks`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  // Get PII redactions
  async getPIIRedactions(documentId: string) {
    const res = await fetch(`${API_BASE}/pdf/${documentId}/pii`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  // MCP endpoints
  async getMCPTools() {
    const res = await fetch(`${API_BASE}/mcp/tools`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async getMCPInfo() {
    const res = await fetch(`${API_BASE}/mcp/info`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  async callMCPTool(toolName: string, args: Record<string, unknown>) {
    const res = await fetch(`${API_BASE}/mcp/tools/${toolName}/call`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(args),
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  // WebSocket for real-time updates
  connectWebSocket(documentId: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: 'subscribe', document_id: documentId }))
      return
    }

    this.ws = new WebSocket(`ws://localhost:8000/api/realtime/ws`)
    
    this.ws.onopen = () => {
      this.ws?.send(JSON.stringify({ action: 'subscribe', document_id: documentId }))
    }

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      const listeners = this.wsListeners.get(data.type)
      listeners?.forEach(cb => cb(data))
    }
  }

  onWebSocketEvent(eventType: string, callback: (data: unknown) => void) {
    if (!this.wsListeners.has(eventType)) {
      this.wsListeners.set(eventType, new Set())
    }
    this.wsListeners.get(eventType)!.add(callback)
    return () => this.wsListeners.get(eventType)?.delete(callback)
  }

  disconnectWebSocket() {
    this.ws?.close()
    this.ws = null
  }
}

export const api = new ApiClient()
