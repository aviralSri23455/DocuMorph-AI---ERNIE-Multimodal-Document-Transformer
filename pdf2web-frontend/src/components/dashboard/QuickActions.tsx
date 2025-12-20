import { useState } from 'react'
import { Sparkles, Shield, Download, Wand2, RotateCcw, RefreshCw } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useStore } from '@/store/useStore'
import { ExportDialog } from './ExportDialog'
import { TransparencyModal } from './TransparencyModal'
import { api } from '@/lib/api'

export function QuickActions() {
  const { currentDocument, generateHTML, isGenerating, generatedHTML, preview, setPreview, reset } = useStore()
  const [exportOpen, setExportOpen] = useState(false)
  const [transparencyOpen, setTransparencyOpen] = useState(false)
  const [isAutoConverting, setIsAutoConverting] = useState(false)

  const handleAutoConvert = async () => {
    if (!currentDocument) return
    setIsAutoConverting(true)
    try {
      const result = await api.autoConvert(currentDocument.document_id)
      // Auto-convert returns generated HTML directly
      if (result.html) {
        useStore.getState().setGeneratedHTML(result.html)
        useStore.getState().setCurrentStep('output')
      }
    } catch (err) {
      console.error('Auto-convert failed:', err)
    } finally {
      setIsAutoConverting(false)
    }
  }

  const handleRegenerateSuggestions = async () => {
    if (!currentDocument) return
    try {
      const newPreview = await api.regenerateSuggestions(currentDocument.document_id)
      setPreview(newPreview)
    } catch (err) {
      console.error('Regenerate suggestions failed:', err)
    }
  }

  const handleReset = async () => {
    if (!currentDocument) return
    try {
      await api.resetDocument(currentDocument.document_id)
      reset()
    } catch (err) {
      console.error('Reset failed:', err)
    }
  }

  return (
    <Card className="p-4 bg-card/50 border-border">
      <h3 className="font-medium text-foreground mb-3">Quick Actions</h3>
      <div className="grid grid-cols-2 gap-2">
        <Button variant="outline" className="h-auto py-3 flex flex-col items-center gap-1 hover:border-cyan-500/50 hover:bg-cyan-500/5" onClick={generateHTML} disabled={!currentDocument || isGenerating}>
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span className="text-xs">Generate HTML</span>
        </Button>
        <Button variant="outline" className="h-auto py-3 flex flex-col items-center gap-1 hover:border-cyan-500/50 hover:bg-cyan-500/5" onClick={handleAutoConvert} disabled={!currentDocument || isAutoConverting}>
          <Wand2 className="w-4 h-4 text-cyan-400" />
          <span className="text-xs">Auto Convert</span>
        </Button>
        <Button variant="outline" className="h-auto py-3 flex flex-col items-center gap-1 hover:border-cyan-500/50 hover:bg-cyan-500/5" onClick={() => setTransparencyOpen(true)} disabled={!currentDocument}>
          <Shield className="w-4 h-4 text-cyan-400" />
          <span className="text-xs">Transparency</span>
        </Button>
        <Button variant="outline" className="h-auto py-3 flex flex-col items-center gap-1 hover:border-cyan-500/50 hover:bg-cyan-500/5" onClick={() => setExportOpen(true)} disabled={!generatedHTML}>
          <Download className="w-4 h-4 text-cyan-400" />
          <span className="text-xs">Export</span>
        </Button>
        <Button variant="outline" className="h-auto py-3 flex flex-col items-center gap-1 hover:border-cyan-500/50 hover:bg-cyan-500/5" onClick={handleRegenerateSuggestions} disabled={!preview}>
          <RefreshCw className="w-4 h-4 text-cyan-400" />
          <span className="text-xs">Refresh AI</span>
        </Button>
        <Button variant="outline" className="h-auto py-3 flex flex-col items-center gap-1 hover:border-red-500/50 hover:bg-red-500/5" onClick={handleReset} disabled={!currentDocument}>
          <RotateCcw className="w-4 h-4 text-red-400" />
          <span className="text-xs">Reset</span>
        </Button>
      </div>
      <ExportDialog open={exportOpen} onOpenChange={setExportOpen} />
      <TransparencyModal open={transparencyOpen} onOpenChange={setTransparencyOpen} />
    </Card>
  )
}
