import { useEffect } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import { StatsCards } from '@/components/dashboard/StatsCards'
import { PDFUploader } from '@/components/dashboard/PDFUploader'
import { ProcessingPipeline } from '@/components/dashboard/ProcessingPipeline'
import { QuickActions } from '@/components/dashboard/QuickActions'
import { PreviewPanel } from '@/components/dashboard/PreviewPanel'
import { ThemeSelector } from '@/components/dashboard/ThemeSelector'
import { SemanticSuggestions } from '@/components/dashboard/SemanticSuggestions'
import { KnowledgeGraph } from '@/components/dashboard/KnowledgeGraph'
import { ProcessingProgress } from '@/components/dashboard/ProcessingProgress'
import { ModelSelector } from '@/components/dashboard/ModelSelector'
import { UploadOptions } from '@/components/dashboard/UploadOptions'
import { AccessibilityCheck } from '@/components/dashboard/AccessibilityCheck'
import { LowConfidenceBlocks } from '@/components/dashboard/LowConfidenceBlocks'
import { AuditLogs } from '@/components/dashboard/AuditLogs'
import { PluginsPanel } from '@/components/dashboard/PluginsPanel'
import { CoDesignTabs } from '@/components/dashboard/CoDesignTabs'
import { SettingsPage } from '@/pages/SettingsPage'
import { AnalyticsPage } from '@/pages/AnalyticsPage'
import { ProjectsPage } from '@/pages/ProjectsPage'
import { HistoryPage } from '@/pages/HistoryPage'
import { HelpPage } from '@/pages/HelpPage'
import { useStore } from '@/store/useStore'
import { api } from '@/lib/api'

function UploadPage() {
  const { currentDocument, isUploading, isProcessing, isGenerating, uploadConfig, setUploadConfig, generatedHTML, preview } = useStore()
  const showProgress = isUploading || isProcessing || isGenerating
  const showCoDesign = currentDocument && preview && !isUploading && !isProcessing

  return (
    <div className="flex-1 p-6 overflow-auto grid-pattern">
      <StatsCards />
      
      {showProgress && (
        <div className="mt-6">
          <ProcessingProgress />
        </div>
      )}
      
      <div className="grid grid-cols-3 gap-6 mt-6">
        {/* Left Column - Upload & Co-Design */}
        <div className="col-span-2 space-y-4">
          <PDFUploader />
          <UploadOptions config={uploadConfig} onChange={setUploadConfig} />
          <div className="grid grid-cols-2 gap-4">
            <ThemeSelector />
            <ModelSelector />
          </div>
          
          {/* Co-Design Tabs - Main interaction area */}
          {showCoDesign && <CoDesignTabs />}
          
          <ProcessingPipeline />
          {currentDocument && <KnowledgeGraph />}
        </div>

        {/* Right Column - Actions & Preview */}
        <div className="space-y-4">
          <QuickActions />
          {generatedHTML && <AccessibilityCheck />}
          {currentDocument && <AuditLogs />}
          <PluginsPanel />
          <PreviewPanel />
        </div>
      </div>
    </div>
  )
}

function App() {
  const { currentPage, setSystemReady } = useStore()

  useEffect(() => {
    // Check backend health on mount
    const checkHealth = async () => {
      try {
        await api.checkHealth()
        setSystemReady(true)
      } catch {
        setSystemReady(false)
      }
    }
    checkHealth()
  }, [setSystemReady])

  const renderPage = () => {
    switch (currentPage) {
      case 'upload':
        return <UploadPage />
      case 'projects':
        return <ProjectsPage />
      case 'history':
        return <HistoryPage />
      case 'analytics':
        return <AnalyticsPage />
      case 'settings':
        return <SettingsPage />
      case 'help':
        return <HelpPage />
      default:
        return <UploadPage />
    }
  }

  return (
    <div className="h-screen flex bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        {renderPage()}
      </div>
    </div>
  )
}

export default App
