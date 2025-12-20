import { useEffect, useState } from 'react'
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { useStore } from '@/store/useStore'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

interface ProgressEvent {
  stage: string
  progress: number
  message: string
}

export function ProcessingProgress() {
  const { currentDocument, isUploading, isProcessing, isGenerating } = useStore()
  const [events, setEvents] = useState<ProgressEvent[]>([])
  const [currentProgress, setCurrentProgress] = useState(0)
  const [currentMessage, setCurrentMessage] = useState('')

  useEffect(() => {
    if (!currentDocument) return

    // Connect to WebSocket for real-time updates
    api.connectWebSocket(currentDocument.document_id)

    const unsubProgress = api.onWebSocketEvent('processing_progress', (data) => {
      const event = data as { data: ProgressEvent }
      setCurrentProgress(event.data.progress * 100)
      setCurrentMessage(event.data.message)
      setEvents(prev => [...prev, event.data])
    })

    const unsubOCR = api.onWebSocketEvent('ocr_page_completed', (data) => {
      const event = data as { data: { page: number; total: number } }
      setCurrentMessage(`OCR: Page ${event.data.page} of ${event.data.total}`)
    })

    const unsubPII = api.onWebSocketEvent('pii_detected', (data) => {
      const event = data as { data: { type: string; count: number } }
      setCurrentMessage(`PII detected: ${event.data.type}`)
    })

    const unsubComplete = api.onWebSocketEvent('processing_completed', () => {
      setCurrentProgress(100)
      setCurrentMessage('Processing complete!')
    })

    const unsubError = api.onWebSocketEvent('processing_error', (data) => {
      const event = data as { data: { message: string } }
      setCurrentMessage(`Error: ${event.data.message}`)
    })

    return () => {
      unsubProgress()
      unsubOCR()
      unsubPII()
      unsubComplete()
      unsubError()
      api.disconnectWebSocket()
    }
  }, [currentDocument])

  const isActive = isUploading || isProcessing || isGenerating

  if (!isActive && !currentMessage) return null

  return (
    <div className="p-4 rounded-lg border border-border bg-card/50 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isActive ? (
            <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
          ) : currentProgress === 100 ? (
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          ) : (
            <AlertCircle className="w-4 h-4 text-yellow-400" />
          )}
          <span className="text-sm font-medium text-foreground">
            {isUploading ? 'Uploading...' : isProcessing ? 'Processing...' : isGenerating ? 'Generating HTML...' : 'Complete'}
          </span>
        </div>
        <span className="text-sm text-muted-foreground">{Math.round(currentProgress)}%</span>
      </div>

      <Progress value={currentProgress} className="h-2" />

      {currentMessage && (
        <p className="text-xs text-muted-foreground">{currentMessage}</p>
      )}

      {/* Recent Events */}
      {events.length > 0 && (
        <div className="max-h-20 overflow-auto space-y-1">
          {events.slice(-5).map((event, i) => (
            <div key={i} className={cn("text-xs flex items-center gap-2", i === events.length - 1 ? "text-foreground" : "text-muted-foreground")}>
              <span className="w-1 h-1 rounded-full bg-cyan-400" />
              {event.message}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
