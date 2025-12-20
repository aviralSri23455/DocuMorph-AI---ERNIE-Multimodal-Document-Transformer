import { useState, useEffect } from 'react'
import { Eye, Code, Edit3, Check, X, AlertTriangle, BarChart3, Loader2, CheckCircle } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useStore } from '@/store/useStore'
import { cn } from '@/lib/utils'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '@/lib/api'

const blockTypes = ['heading', 'paragraph', 'table', 'list', 'code', 'image', 'quote']

export function PreviewPanel() {
  const { preview, generatedHTML, currentDocument, setPreview } = useStore()
  const [editingBlock, setEditingBlock] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [editType, setEditType] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [approvedPIIs, setApprovedPIIs] = useState<Set<string>>(new Set())
  const [processingPII, setProcessingPII] = useState<string | null>(null)

  // Reset approved PIIs when document changes
  useEffect(() => {
    setApprovedPIIs(new Set())
  }, [currentDocument?.document_id])

  const handleSaveBlock = async (blockId: string) => {
    if (!currentDocument) return
    setIsSaving(true)
    try {
      await api.editBlock(currentDocument.document_id, blockId, editContent, editType || undefined)
      // Refresh preview
      const newPreview = await api.getPreview(currentDocument.document_id)
      setPreview(newPreview)
      setEditingBlock(null)
    } catch (err) {
      console.error('Failed to save block:', err)
    } finally {
      setIsSaving(false)
    }
  }

  const handlePIIAction = async (redactionId: string, action: 'approve' | 'undo' | 'modify') => {
    console.log('PII Action called:', { redactionId, action, docId: currentDocument?.document_id })
    if (!currentDocument) {
      console.error('No current document')
      return
    }
    if (processingPII) {
      console.log('Already processing:', processingPII)
      return
    }
    if (!redactionId) {
      console.error('No redaction ID provided')
      return
    }
    setProcessingPII(redactionId)
    try {
      const result = await api.piiAction(currentDocument.document_id, redactionId, action)
      console.log('PII action result:', result)
      if (action === 'approve') {
        // Mark as approved locally for visual feedback - use functional update
        setApprovedPIIs(prev => {
          const newSet = new Set(prev)
          newSet.add(redactionId)
          console.log('Updated approved PIIs:', [...newSet])
          return newSet
        })
      } else if (action === 'undo') {
        // Remove from approved and refresh preview (undo removes from backend)
        setApprovedPIIs(prev => {
          const newSet = new Set(prev)
          newSet.delete(redactionId)
          return newSet
        })
        const newPreview = await api.getPreview(currentDocument.document_id)
        setPreview(newPreview)
      }
    } catch (err) {
      console.error('PII action failed:', err)
    } finally {
      setProcessingPII(null)
    }
  }

  const handleBulkApprove = async () => {
    if (!currentDocument) return
    try {
      await api.bulkApprove(currentDocument.document_id)
      // Mark all PIIs as approved
      if (preview?.pii_redactions) {
        setApprovedPIIs(new Set(preview.pii_redactions.map((p, i) => p.id || p.redaction_id || `pii-${i}`)))
      }
    } catch (err) {
      console.error('Bulk approve failed:', err)
    }
  }

  // Helper to get PII ID consistently
  const getPIIId = (pii: { id?: string; redaction_id?: string }, index: number) => pii.id || pii.redaction_id || `pii-${index}`
  
  // Count pending (not yet approved) PII items
  const pendingPIICount = preview?.pii_redactions?.filter((p, i) => !approvedPIIs.has(getPIIId(p, i))).length || 0
  const allPIIApproved = preview?.pii_redactions && preview.pii_redactions.length > 0 && pendingPIICount === 0
  
  // Debug logging
  useEffect(() => {
    if (preview?.pii_redactions) {
      console.log('PII Redactions:', preview.pii_redactions.map((p, i) => ({ 
        id: p.id, 
        redaction_id: p.redaction_id, 
        computed_id: getPIIId(p, i),
        pii_type: p.pii_type 
      })))
      console.log('Approved PIIs:', [...approvedPIIs])
    }
  }, [preview?.pii_redactions, approvedPIIs])

  if (!currentDocument) {
    return (
      <Card className="p-6 bg-card/50 border-border h-full flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <Eye className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Upload a PDF to see preview</p>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-4 bg-card/50 border-border h-full flex flex-col">
      <Tabs defaultValue="blocks" className="flex-1 flex flex-col">
        <TabsList className="grid w-full grid-cols-3 mb-4">
          <TabsTrigger value="blocks" className="gap-2">
            <Edit3 className="w-4 h-4" />
            Blocks
          </TabsTrigger>
          <TabsTrigger value="pii" className="gap-2">
            <AlertTriangle className="w-4 h-4" />
            PII ({preview?.stats.pii_count || 0})
          </TabsTrigger>
          <TabsTrigger value="html" className="gap-2">
            <Code className="w-4 h-4" />
            HTML
          </TabsTrigger>
        </TabsList>

        <TabsContent value="blocks" className="flex-1 overflow-auto space-y-3">
          {/* Stats bar */}
          {preview && (
            <div className="flex items-center justify-between text-xs text-muted-foreground pb-2 border-b border-border">
              <span>{preview.stats.total_blocks} blocks • {preview.stats.low_confidence_count} need review</span>
              <Button size="sm" variant="ghost" className="h-6 text-xs" onClick={handleBulkApprove}>Accept All</Button>
            </div>
          )}
          <AnimatePresence>
            {preview?.blocks.map((block, index) => {
              const suggestion = preview.semantic_suggestions?.find(s => s.block_id === block.block_id)
              return (
                <motion.div
                  key={block.block_id || `block-${index}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.03 }}
                  className={cn(
                    "p-3 rounded-lg border transition-all",
                    block.confidence < 0.8 
                      ? "border-yellow-500/30 bg-yellow-500/5" 
                      : "border-border bg-secondary/30",
                    editingBlock === block.block_id && "ring-2 ring-cyan-500"
                  )}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      {editingBlock === block.block_id ? (
                        <Select value={editType || block.type} onValueChange={setEditType}>
                          <SelectTrigger className="h-6 w-24 text-xs">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {blockTypes.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                          </SelectContent>
                        </Select>
                      ) : (
                        <span className="text-xs px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 uppercase">{block.type}</span>
                      )}
                      <span className="text-xs text-muted-foreground">P{block.page}</span>
                      <span className={cn("text-xs px-1.5 py-0.5 rounded", block.confidence >= 0.8 ? "bg-emerald-500/10 text-emerald-400" : "bg-yellow-500/10 text-yellow-400")}>
                        {Math.round(block.confidence * 100)}%
                      </span>
                      {suggestion && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400 flex items-center gap-1">
                          <BarChart3 className="w-3 h-3" />{suggestion.suggestion.replace('_', ' ')}
                        </span>
                      )}
                    </div>
                    <div className="flex gap-1">
                      {editingBlock === block.block_id ? (
                        <>
                          <Button size="icon" variant="ghost" className="h-6 w-6" onClick={() => handleSaveBlock(block.block_id)} disabled={isSaving}>
                            {isSaving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3 text-emerald-400" />}
                          </Button>
                          <Button size="icon" variant="ghost" className="h-6 w-6" onClick={() => setEditingBlock(null)}>
                            <X className="w-3 h-3 text-red-400" />
                          </Button>
                        </>
                      ) : (
                        <Button size="icon" variant="ghost" className="h-6 w-6" onClick={() => { setEditingBlock(block.block_id); setEditContent(block.content); setEditType(block.type) }}>
                          <Edit3 className="w-3 h-3" />
                        </Button>
                      )}
                    </div>
                  </div>
                  {editingBlock === block.block_id ? (
                    <textarea value={editContent} onChange={(e) => setEditContent(e.target.value)} className="w-full p-2 rounded bg-background border border-border text-sm resize-none focus:outline-none focus:ring-1 focus:ring-cyan-500" rows={3} />
                  ) : (
                    <p className="text-sm text-foreground/80 line-clamp-2">{block.content}</p>
                  )}
                </motion.div>
              )
            })}
          </AnimatePresence>
          {!preview?.blocks.length && (
            <div className="text-center text-muted-foreground py-8">
              <p>Processing document...</p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="pii" className="flex-1 overflow-auto space-y-3">
          {preview?.pii_redactions && preview.pii_redactions.length > 0 && (
            <div className="flex items-center justify-between text-xs text-muted-foreground pb-2 border-b border-border">
              <span>
                {allPIIApproved ? (
                  <span className="text-emerald-400 flex items-center gap-1">
                    <CheckCircle className="w-3 h-3" /> All {preview.pii_redactions.length} PII items approved
                  </span>
                ) : (
                  <>{pendingPIICount} of {preview.pii_redactions.length} PII items pending</>
                )}
              </span>
              {!allPIIApproved && (
                <Button size="sm" variant="ghost" className="h-6 text-xs text-emerald-400" onClick={handleBulkApprove}>Approve All</Button>
              )}
            </div>
          )}
          {allPIIApproved && (
            <div className="text-center py-4 text-emerald-400 bg-emerald-500/10 rounded-lg border border-emerald-500/30">
              <CheckCircle className="w-8 h-8 mx-auto mb-2" />
              <p className="text-sm font-medium">All PII redactions approved!</p>
              <p className="text-xs text-muted-foreground mt-1">Click "Generate HTML" to continue</p>
            </div>
          )}
          {preview?.pii_redactions?.map((pii, index) => {
            // Use id or redaction_id as fallback
            const piiId = pii.id || pii.redaction_id || `pii-${index}`
            const isApproved = approvedPIIs.has(piiId)
            const isProcessing = processingPII === piiId
            return (
              <motion.div 
                key={piiId} 
                className={cn(
                  "p-3 rounded-lg border transition-all",
                  isApproved 
                    ? "border-emerald-500/30 bg-emerald-500/5" 
                    : "border-red-500/30 bg-red-500/5"
                )}
                initial={false}
                animate={{ opacity: isApproved ? 0.7 : 1 }}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={cn(
                      "text-xs px-2 py-0.5 rounded uppercase",
                      isApproved ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
                    )}>
                      {(pii.pii_type || pii.type || 'PII').replace(/_/g, ' ')}
                    </span>
                    {isApproved && <CheckCircle className="w-3 h-3 text-emerald-400" />}
                  </div>
                  <div className="flex gap-1">
                    {!isApproved ? (
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="h-6 text-xs text-emerald-400" 
                        onClick={() => handlePIIAction(piiId, 'approve')}
                        disabled={isProcessing}
                      >
                        {isProcessing ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Approve'}
                      </Button>
                    ) : (
                      <span className="text-xs text-emerald-400 px-2">Approved</span>
                    )}
                    <Button 
                      size="sm" 
                      variant="ghost" 
                      className="h-6 text-xs text-yellow-400" 
                      onClick={() => handlePIIAction(piiId, 'undo')}
                      disabled={isProcessing}
                    >
                      Undo
                    </Button>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-red-400 line-through">{pii.original?.slice(0, 3) || '***'}***</span>
                  <span className="text-muted-foreground">→</span>
                  <span className="text-emerald-400">{pii.redacted || '[REDACTED]'}</span>
                </div>
              </motion.div>
            )
          })}
          {(!preview?.pii_redactions || preview.pii_redactions.length === 0) && (
            <div className="text-center text-muted-foreground py-8">
              <AlertTriangle className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No PII detected</p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="html" className="flex-1 overflow-auto">
          {generatedHTML ? (
            <div className="relative h-full min-h-[300px]">
              <div className="absolute top-2 right-2 z-10 flex gap-2">
                <Button size="sm" variant="secondary" className="h-7 text-xs" onClick={() => window.open('about:blank')?.document.write(generatedHTML)}>
                  <Eye className="w-3 h-3 mr-1" /> Full Preview
                </Button>
              </div>
              <iframe
                srcDoc={generatedHTML}
                className="w-full h-full min-h-[300px] rounded-lg border border-border bg-white"
                title="HTML Preview"
                sandbox="allow-scripts"
              />
            </div>
          ) : (
            <div className="text-center text-muted-foreground py-8">
              <Code className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Generate HTML to see preview</p>
              <p className="text-xs mt-2">Click "Generate HTML" or "Auto Convert"</p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </Card>
  )
}
