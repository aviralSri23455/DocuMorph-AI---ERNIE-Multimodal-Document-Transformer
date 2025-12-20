import { useState, useEffect } from 'react'
import { Eye, Shield, Cloud, Lock, AlertCircle } from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { useStore } from '@/store/useStore'
import { api } from '@/lib/api'

interface TransparencyData {
  mode: string
  sent_to_cloud: string[]
  not_sent: string[]
  pii_summary: Record<string, number>
  sanitized_preview: string
}

interface TransparencyModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function TransparencyModal({ open, onOpenChange }: TransparencyModalProps) {
  const { currentDocument, secureMode } = useStore()
  const [data, setData] = useState<TransparencyData | null>(null)

  useEffect(() => {
    if (open && currentDocument) {
      api.getTransparency(currentDocument.document_id).then(setData).catch(console.error)
    }
  }, [open, currentDocument])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Eye className="w-5 h-5 text-cyan-400" />
            What Data is Sent to Cloud?
          </DialogTitle>
          <DialogDescription>Transparency view of data processing</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {/* Mode Badge */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Mode:</span>
            <span className={`flex items-center gap-1 px-2 py-1 rounded text-sm ${secureMode ? 'bg-cyan-500/10 text-cyan-400' : 'bg-yellow-500/10 text-yellow-400'}`}>
              {secureMode ? <Lock className="w-3 h-3" /> : <Cloud className="w-3 h-3" />}
              {secureMode ? 'Secure Mode' : 'Standard Mode'}
            </span>
          </div>

          {/* Sent to Cloud */}
          <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
            <p className="text-sm font-medium text-emerald-400 mb-2 flex items-center gap-1">
              <Cloud className="w-4 h-4" /> Sent to ERNIE:
            </p>
            <ul className="text-sm text-foreground/80 space-y-1">
              <li>• Sanitized text structure (Markdown)</li>
              <li>• Theme preferences</li>
              <li>• Component suggestions request</li>
              {!secureMode && <li>• Page images (for vision analysis)</li>}
            </ul>
          </div>

          {/* NOT Sent */}
          <div className="p-3 rounded-lg bg-red-500/5 border border-red-500/20">
            <p className="text-sm font-medium text-red-400 mb-2 flex items-center gap-1">
              <Shield className="w-4 h-4" /> NOT Sent (Stays Local):
            </p>
            <ul className="text-sm text-foreground/80 space-y-1">
              <li>• Raw PDF file</li>
              {secureMode && <li>• Images</li>}
              <li>• Original PII (emails, phones, names)</li>
            </ul>
          </div>

          {/* PII Summary */}
          {data?.pii_summary && Object.keys(data.pii_summary).length > 0 && (
            <div className="p-3 rounded-lg bg-secondary">
              <p className="text-sm font-medium text-foreground mb-2 flex items-center gap-1">
                <AlertCircle className="w-4 h-4 text-yellow-400" /> PII Redacted:
              </p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(data.pii_summary).map(([type, count]) => (
                  <span key={type} className="text-xs px-2 py-1 rounded bg-yellow-500/10 text-yellow-400">
                    {type.replace('_', ' ')}: {count}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Sanitized Preview */}
          {data?.sanitized_preview && (
            <div>
              <p className="text-sm text-muted-foreground mb-2">Preview of sanitized content:</p>
              <pre className="p-3 rounded-lg bg-background border border-border text-xs text-foreground/80 max-h-32 overflow-auto whitespace-pre-wrap">
                {data.sanitized_preview}
              </pre>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
