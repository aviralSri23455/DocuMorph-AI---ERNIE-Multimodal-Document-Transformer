import { useState } from 'react'
import { Shield, Check, Undo2, Edit3, Loader2, AlertTriangle } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useStore } from '@/store/useStore'
import { api, PIIRedaction } from '@/lib/api'
import { cn } from '@/lib/utils'

const piiTypeIcons: Record<string, string> = {
  EMAIL_ADDRESS: '📧',
  PHONE_NUMBER: '📱',
  PERSON: '👤',
  US_SSN: '🔢',
  CREDIT_CARD: '💳',
  US_PASSPORT: '🛂',
  US_DRIVER_LICENSE: '🪪',
  IP_ADDRESS: '🌐',
}

const piiTypeLabels: Record<string, string> = {
  EMAIL_ADDRESS: 'Email',
  PHONE_NUMBER: 'Phone',
  PERSON: 'Name',
  US_SSN: 'SSN',
  CREDIT_CARD: 'Credit Card',
  US_PASSPORT: 'Passport',
  US_DRIVER_LICENSE: 'License',
  IP_ADDRESS: 'IP Address',
}

export function PIIReviewPanel() {
  const { currentDocument, preview, setPreview } = useStore()
  const [loadingId, setLoadingId] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')

  const redactions = preview?.pii_redactions || []

  const handleApprove = async (redactionId: string) => {
    if (!currentDocument) return
    setLoadingId(redactionId)
    try {
      await api.piiAction(currentDocument.document_id, redactionId, 'approve')
      // Refresh preview
      const newPreview = await api.getPreview(currentDocument.document_id)
      setPreview(newPreview)
    } catch (err) {
      console.error('Failed to approve PII:', err)
    } finally {
      setLoadingId(null)
    }
  }

  const handleUndo = async (redactionId: string) => {
    if (!currentDocument) return
    setLoadingId(redactionId)
    try {
      await api.piiAction(currentDocument.document_id, redactionId, 'undo')
      // Refresh preview
      const newPreview = await api.getPreview(currentDocument.document_id)
      setPreview(newPreview)
    } catch (err) {
      console.error('Failed to undo PII:', err)
    } finally {
      setLoadingId(null)
    }
  }

  const handleModify = async (redactionId: string) => {
    if (!currentDocument || !editValue.trim()) return
    setLoadingId(redactionId)
    try {
      // Note: modify action would need backend support for new_value
      await api.piiAction(currentDocument.document_id, redactionId, 'modify')
      const newPreview = await api.getPreview(currentDocument.document_id)
      setPreview(newPreview)
      setEditingId(null)
      setEditValue('')
    } catch (err) {
      console.error('Failed to modify PII:', err)
    } finally {
      setLoadingId(null)
    }
  }

  if (!currentDocument) return null

  return (
    <Card className="p-4 bg-card/50 border-border">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-amber-400" />
          <h3 className="font-medium text-foreground">PII Review</h3>
          <span className="text-xs px-2 py-0.5 rounded bg-amber-500/10 text-amber-400">
            {redactions.length} detected
          </span>
        </div>
      </div>

      {redactions.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <Shield className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No PII detected</p>
          <p className="text-xs mt-1">Document appears clean</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-80 overflow-auto pr-1">
          {redactions.map((redaction: PIIRedaction) => {
            const isLoading = loadingId === redaction.id
            const isEditing = editingId === redaction.id
            const piiType = redaction.pii_type || redaction.type || 'UNKNOWN'
            const icon = piiTypeIcons[piiType] || '🔒'
            const label = piiTypeLabels[piiType] || piiType

            return (
              <div
                key={redaction.id}
                className={cn(
                  "p-3 rounded-lg border transition-all",
                  "border-amber-500/30 bg-amber-500/5",
                  isEditing && "ring-2 ring-cyan-500"
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg">{icon}</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 uppercase">
                        {label}
                      </span>
                      <span className={cn(
                        "text-xs px-1.5 py-0.5 rounded",
                        redaction.confidence >= 0.9 ? "bg-emerald-500/10 text-emerald-400" :
                        redaction.confidence >= 0.7 ? "bg-yellow-500/10 text-yellow-400" :
                        "bg-red-500/10 text-red-400"
                      )}>
                        {Math.round(redaction.confidence * 100)}%
                      </span>
                    </div>
                    
                    <div className="space-y-1 text-sm">
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground text-xs">Original:</span>
                        <code className="px-1.5 py-0.5 rounded bg-red-500/10 text-red-300 text-xs">
                          {redaction.original.substring(0, 3)}***
                        </code>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground text-xs">Redacted:</span>
                        <code className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 text-xs">
                          {redaction.redacted}
                        </code>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1">
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-7 w-7 hover:bg-emerald-500/10"
                      onClick={() => handleApprove(redaction.id)}
                      disabled={isLoading}
                      title="Approve redaction"
                    >
                      {isLoading ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      )}
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-7 w-7 hover:bg-red-500/10"
                      onClick={() => handleUndo(redaction.id)}
                      disabled={isLoading}
                      title="Undo redaction (restore original)"
                    >
                      <Undo2 className="w-3.5 h-3.5 text-red-400" />
                    </Button>
                  </div>
                </div>

                {isEditing && (
                  <div className="mt-2 flex gap-2">
                    <input
                      type="text"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      placeholder="New redaction value..."
                      className="flex-1 px-2 py-1 rounded bg-background border border-border text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
                    />
                    <Button size="sm" onClick={() => handleModify(redaction.id)} disabled={isLoading}>
                      Save
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>
                      Cancel
                    </Button>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {redactions.length > 0 && (
        <div className="mt-3 p-2 rounded bg-amber-500/5 border border-amber-500/20">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-muted-foreground">
              <span className="text-amber-400 font-medium">Secure Mode:</span> PII is redacted locally before any cloud processing. 
              Use "Undo" to restore original text if needed.
            </p>
          </div>
        </div>
      )}
    </Card>
  )
}
