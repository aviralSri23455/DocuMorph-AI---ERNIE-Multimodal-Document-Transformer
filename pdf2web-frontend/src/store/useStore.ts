import { create } from 'zustand'
import { api, PreviewResponse, UploadResponse } from '@/lib/api'

export type ProcessingStep = 'upload' | 'extract' | 'codesign' | 'generate' | 'output'
export type Theme = 'light' | 'dark' | 'professional' | 'academic' | 'minimal'

export interface PIIOptions {
  redact_emails: boolean
  redact_phones: boolean
  redact_names: boolean
  redact_ssn: boolean
  redact_credit_cards: boolean
}

export interface UploadConfig {
  mode: 'secure' | 'standard'
  language: string
  piiOptions: PIIOptions
}

export interface ModelConfig {
  textModel: string
  visionModel: string
  enableVision: boolean
  enableKnowledgeGraph: boolean
  enableMCP: boolean
}

export type ChartType = 'bar' | 'line' | 'pie'

export interface SemanticSelections {
  chartConversions: Record<string, 'keep_table' | 'convert_to_chart' | 'hybrid'>
  chartTypes: Record<string, ChartType>
  quizEnabledBlocks: string[]
  codeExecutionBlocks: string[]
  timelineBlocks: string[]
  mapBlocks: string[]
}

interface AppState {
  // Navigation
  currentPage: 'upload' | 'projects' | 'history' | 'analytics' | 'settings' | 'help'
  setCurrentPage: (page: AppState['currentPage']) => void

  // Upload config
  uploadConfig: UploadConfig
  setUploadConfig: (config: UploadConfig) => void

  // Model config
  modelConfig: ModelConfig
  setModelConfig: (config: ModelConfig) => void

  // Processing mode (derived from uploadConfig)
  secureMode: boolean
  setSecureMode: (secure: boolean) => void

  // Document state
  currentDocument: UploadResponse | null
  setCurrentDocument: (doc: UploadResponse | null) => void

  // Preview data
  preview: PreviewResponse | null
  setPreview: (preview: PreviewResponse | null) => void

  // Processing pipeline
  currentStep: ProcessingStep
  setCurrentStep: (step: ProcessingStep) => void
  processingProgress: number
  setProcessingProgress: (progress: number) => void

  // Theme selection
  selectedTheme: Theme
  setSelectedTheme: (theme: Theme) => void

  // Generated HTML
  generatedHTML: string | null
  setGeneratedHTML: (html: string | null) => void

  // Semantic selections
  semanticSelections: SemanticSelections
  setSemanticSelections: (selections: SemanticSelections) => void
  updateChartConversion: (blockId: string, option: 'keep_table' | 'convert_to_chart' | 'hybrid') => void
  updateChartType: (blockId: string, chartType: ChartType) => void
  toggleQuizBlock: (blockId: string) => void
  toggleCodeBlock: (blockId: string) => void
  toggleTimelineBlock: (blockId: string) => void
  toggleMapBlock: (blockId: string) => void

  // Stats
  stats: {
    documentsProcessed: number
    avgProcessingTime: number
    semanticInjections: number
    successRate: number
  }
  setStats: (stats: AppState['stats']) => void
  resetStats: () => void

  // System status
  systemReady: boolean
  setSystemReady: (ready: boolean) => void

  // Loading states
  isUploading: boolean
  setIsUploading: (uploading: boolean) => void
  isProcessing: boolean
  setIsProcessing: (processing: boolean) => void
  isGenerating: boolean
  setIsGenerating: (generating: boolean) => void

  // Error handling
  error: string | null
  setError: (error: string | null) => void

  // Track upload start time for accurate processing time
  uploadStartTime: number
  setUploadStartTime: (time: number) => void

  // Actions
  uploadPDF: (file: File) => Promise<void>
  fetchPreview: () => Promise<void>
  generateHTML: () => Promise<void>
  reset: () => void
}

// Session-only stats (reset on refresh)
const initialStats = {
  documentsProcessed: 0,
  avgProcessingTime: 0,
  semanticInjections: 0,
  successRate: 0,
}

export const useStore = create<AppState>()(
    (set, get) => ({
  // Initial state
  currentPage: 'upload',
  setCurrentPage: (page) => set({ currentPage: page }),

  uploadConfig: {
    mode: 'secure',
    language: 'en',
    piiOptions: {
      redact_emails: true,
      redact_phones: true,
      redact_names: true,
      redact_ssn: true,
      redact_credit_cards: true,
    },
  },
  setUploadConfig: (config) => set({ uploadConfig: config, secureMode: config.mode === 'secure' }),

  modelConfig: {
    textModel: 'baidu/ernie-4.5-21B-a3b',
    visionModel: 'baidu/ernie-4.5-vl-28b-a3b',
    enableVision: true,
    enableKnowledgeGraph: true,
    enableMCP: false,
  },
  setModelConfig: (config) => set({ modelConfig: config }),

  secureMode: true,
  setSecureMode: (secure) => set({ secureMode: secure, uploadConfig: { ...get().uploadConfig, mode: secure ? 'secure' : 'standard' } }),

  currentDocument: null,
  setCurrentDocument: (doc) => set({ currentDocument: doc }),

  preview: null,
  setPreview: (preview) => set({ preview }),

  currentStep: 'upload',
  setCurrentStep: (step) => set({ currentStep: step }),
  processingProgress: 0,
  setProcessingProgress: (progress) => set({ processingProgress: progress }),

  selectedTheme: 'dark',
  setSelectedTheme: (theme) => set({ selectedTheme: theme }),

  generatedHTML: null,
  setGeneratedHTML: (html) => set({ generatedHTML: html }),

  semanticSelections: {
    chartConversions: {},
    chartTypes: {},
    quizEnabledBlocks: [],
    codeExecutionBlocks: [],
    timelineBlocks: [],
    mapBlocks: [],
  },
  setSemanticSelections: (selections) => set({ semanticSelections: selections }),
  updateChartConversion: (blockId, option) => set((state) => ({
    semanticSelections: {
      ...state.semanticSelections,
      chartConversions: { ...state.semanticSelections.chartConversions, [blockId]: option },
    },
  })),
  updateChartType: (blockId, chartType) => set((state) => ({
    semanticSelections: {
      ...state.semanticSelections,
      chartTypes: { ...state.semanticSelections.chartTypes, [blockId]: chartType },
    },
  })),
  toggleQuizBlock: (blockId) => set((state) => {
    const blocks = state.semanticSelections.quizEnabledBlocks
    const newBlocks = blocks.includes(blockId) ? blocks.filter((b) => b !== blockId) : [...blocks, blockId]
    return { semanticSelections: { ...state.semanticSelections, quizEnabledBlocks: newBlocks } }
  }),
  toggleCodeBlock: (blockId) => set((state) => {
    const blocks = state.semanticSelections.codeExecutionBlocks
    const newBlocks = blocks.includes(blockId) ? blocks.filter((b) => b !== blockId) : [...blocks, blockId]
    return { semanticSelections: { ...state.semanticSelections, codeExecutionBlocks: newBlocks } }
  }),
  toggleTimelineBlock: (blockId) => set((state) => {
    const blocks = state.semanticSelections.timelineBlocks
    const newBlocks = blocks.includes(blockId) ? blocks.filter((b) => b !== blockId) : [...blocks, blockId]
    return { semanticSelections: { ...state.semanticSelections, timelineBlocks: newBlocks } }
  }),
  toggleMapBlock: (blockId) => set((state) => {
    const blocks = state.semanticSelections.mapBlocks
    const newBlocks = blocks.includes(blockId) ? blocks.filter((b) => b !== blockId) : [...blocks, blockId]
    return { semanticSelections: { ...state.semanticSelections, mapBlocks: newBlocks } }
  }),

  stats: { ...initialStats },
  setStats: (newStats) => set({ stats: { ...newStats } }),
  resetStats: () => set({ stats: { ...initialStats } }),

  systemReady: false,
  setSystemReady: (ready) => set({ systemReady: ready }),

  isUploading: false,
  setIsUploading: (uploading) => set({ isUploading: uploading }),
  isProcessing: false,
  setIsProcessing: (processing) => set({ isProcessing: processing }),
  isGenerating: false,
  setIsGenerating: (generating) => set({ isGenerating: generating }),

  error: null,
  setError: (error) => set({ error }),

  // Track upload start time for processing time calculation
  uploadStartTime: 0,
  setUploadStartTime: (time: number) => set({ uploadStartTime: time }),

  // Actions
  uploadPDF: async (file: File) => {
    const { uploadConfig, modelConfig, setIsUploading, setIsProcessing, setIsGenerating, setCurrentDocument, setCurrentStep, setError, setProcessingProgress, setGeneratedHTML, setPreview, setUploadStartTime } = get()
    
    // Track start time for processing duration
    const startTime = Date.now()
    setUploadStartTime(startTime)
    
    // Reset state
    set({ 
      isUploading: true, 
      isProcessing: false, 
      isGenerating: false,
      error: null, 
      processingProgress: 0,
      currentStep: 'upload',
      generatedHTML: null,
      preview: null
    })

    try {
      // Step 1: Upload
      setCurrentStep('upload')
      setProcessingProgress(10)
      
      const response = await api.uploadPDF(file, uploadConfig.mode, uploadConfig.piiOptions, uploadConfig.language)
      setCurrentDocument(response)
      
      // Step 2: Extract
      setCurrentStep('extract')
      setProcessingProgress(25)
      setIsUploading(false)
      setIsProcessing(true)
      
      // If MCP mode is enabled, auto-convert immediately
      if (modelConfig.enableMCP) {
        // Step 3: Skip co-design, go to generate
        setCurrentStep('generate')
        setProcessingProgress(50)
        setIsProcessing(false)
        setIsGenerating(true)
        
        try {
          // Call auto-convert endpoint - AI handles everything
          const autoResult = await api.autoConvert(response.document_id)
          
          // Step 4: Output
          setGeneratedHTML(autoResult.html)
          setCurrentStep('output')
          setProcessingProgress(100)
          setIsGenerating(false)
          
          // Update stats for auto-convert - use full processing time from upload start
          const { stats, setStats, uploadStartTime, preview: currentPreview } = get()
          const processingTime = Math.round((Date.now() - (uploadStartTime || startTime)) / 1000)
          const newDocsProcessed = stats.documentsProcessed + 1
          const newAvgTime = stats.documentsProcessed === 0 
            ? processingTime 
            : Math.round((stats.avgProcessingTime * stats.documentsProcessed + processingTime) / newDocsProcessed)
          const injections = autoResult.components_injected?.length || currentPreview?.semantic_suggestions?.length || 0
          setStats({
            documentsProcessed: newDocsProcessed,
            avgProcessingTime: newAvgTime > 0 ? newAvgTime : 1,
            semanticInjections: stats.semanticInjections + injections,
            successRate: Math.round((newDocsProcessed / (newDocsProcessed + 0.1)) * 100),
          })
          
          // Also fetch preview for display
          try {
            const preview = await api.getPreview(response.document_id)
            setPreview(preview)
          } catch {
            // Preview fetch is optional in MCP mode
          }
        } catch (autoConvertErr) {
          // Auto-convert failed, fall back to normal co-design flow
          console.warn('MCP auto-convert failed, falling back to co-design:', autoConvertErr)
          setIsGenerating(false)
          setIsProcessing(true)
          // Fall through to normal preview flow
          await get().fetchPreview()
        }
      } else {
        // Normal flow - fetch preview for co-design
        await get().fetchPreview()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      setIsUploading(false)
      setIsProcessing(false)
      setIsGenerating(false)
    }
  },

  fetchPreview: async () => {
    const { currentDocument, setPreview, setCurrentStep, setIsProcessing, setError, setProcessingProgress } = get()
    if (!currentDocument) return

    setIsProcessing(true)
    setError(null)

    try {
      const preview = await api.getPreview(currentDocument.document_id)
      setPreview(preview)
      setCurrentStep('codesign')
      setProcessingProgress(50)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get preview')
    } finally {
      setIsProcessing(false)
    }
  },

  generateHTML: async () => {
    const { currentDocument, selectedTheme, semanticSelections, setGeneratedHTML, setCurrentStep, setIsGenerating, setError, setProcessingProgress, stats, setStats, uploadStartTime, preview } = get()
    if (!currentDocument) return

    setIsGenerating(true)
    setError(null)
    setProcessingProgress(75)

    try {
      // Get all suggestion block IDs as approved components
      const approvedComponents = preview?.semantic_suggestions?.map(s => s.block_id) || []
      
      const response = await api.generateHTML(currentDocument.document_id, {
        theme: selectedTheme,
        theme_override: true,
        approved_components: approvedComponents,
        chart_conversions: semanticSelections.chartConversions,
        quiz_enabled_blocks: semanticSelections.quizEnabledBlocks,
        code_execution_blocks: semanticSelections.codeExecutionBlocks,
        timeline_blocks: semanticSelections.timelineBlocks,
        map_blocks: semanticSelections.mapBlocks,
      })
      setGeneratedHTML(response.html)
      setCurrentStep('output')
      setProcessingProgress(100)
      
      // Update stats - use full processing time from upload start
      const processingTime = Math.round((Date.now() - (uploadStartTime || Date.now())) / 1000)
      const newDocsProcessed = stats.documentsProcessed + 1
      const newAvgTime = stats.documentsProcessed === 0 
        ? processingTime 
        : Math.round((stats.avgProcessingTime * stats.documentsProcessed + processingTime) / newDocsProcessed)
      
      // Count injections: from response OR from preview suggestions
      const injections = response.components_injected?.length || preview?.semantic_suggestions?.length || 0
      
      setStats({
        documentsProcessed: newDocsProcessed,
        avgProcessingTime: newAvgTime > 0 ? newAvgTime : 1, // Minimum 1 second
        semanticInjections: stats.semanticInjections + injections,
        successRate: Math.round((newDocsProcessed / (newDocsProcessed + 0.1)) * 100),
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate HTML')
    } finally {
      setIsGenerating(false)
    }
  },

  reset: () => set({
    currentDocument: null,
    preview: null,
    currentStep: 'upload',
    processingProgress: 0,
    generatedHTML: null,
    error: null,
    semanticSelections: {
      chartConversions: {},
      chartTypes: {},
      quizEnabledBlocks: [],
      codeExecutionBlocks: [],
      timelineBlocks: [],
      mapBlocks: [],
    },
  }),
}))
