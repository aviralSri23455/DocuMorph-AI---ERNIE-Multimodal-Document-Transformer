import { useState, useEffect } from 'react'
import { ScrollText, Clock, User, RefreshCw, Loader2 } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useStore } from '@/store/useStore'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

interface AuditLogEntry {
  id: string
  timestamp: string
  action: string
  user: string
  details: string
  document_id: string
}

export function AuditLogs() {
  const { currentDocument } = useStore()
  const [logs, setLogs] = useState<AuditLogEntry[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const fetchLogs = async () => {
    if (!currentDocument) return
    setIsLoading(true)
    try {
      const data = await api.getAuditLogs(currentDocument.document_id)
      setLogs(data.logs || [])
    } catch (err) {
      console.error('Failed to fetch audit logs:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (expanded && currentDocument) {
      fetchLogs()
    }
  }, [expanded, currentDocument])

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  }

  const getActionColor = (action: string) => {
    if (action.includes('upload')) return 'text-cyan-400'
    if (action.includes('edit')) return 'text-yellow-400'
    if (action.includes('delete')) return 'text-red-400'
    if (action.includes('generate')) return 'text-emerald-400'
    if (action.includes('export')) return 'text-purple-400'
    return 'text-muted-foreground'
  }

  if (!currentDocument) return null

  return (
    <Card className="p-4 bg-card/50 border-border">
      <div
        className="w-full flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <ScrollText className="w-5 h-5 text-cyan-400" />
          <h3 className="font-medium text-foreground">Audit Logs</h3>
          {logs.length > 0 && (
            <span className="text-xs px-2 py-0.5 rounded bg-secondary text-muted-foreground">
              {logs.length} entries
            </span>
          )}
        </div>
        <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); fetchLogs() }} disabled={isLoading}>
          <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
        </Button>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-border">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <ScrollText className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No audit logs yet</p>
              <p className="text-xs mt-1">Actions will be logged here</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-48 overflow-auto">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className="p-2 rounded-lg bg-secondary/30 hover:bg-secondary/50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={cn("text-sm font-medium", getActionColor(log.action))}>
                      {log.action}
                    </span>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="w-3 h-3" />
                      {formatTime(log.timestamp)}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <User className="w-3 h-3" />
                    <span>{log.user || 'System'}</span>
                    {log.details && (
                      <>
                        <span>•</span>
                        <span className="truncate">{log.details}</span>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </Card>
  )
}
