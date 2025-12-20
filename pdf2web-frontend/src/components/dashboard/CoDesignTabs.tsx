import { useState } from 'react'
import { FileText, Shield, Sparkles, Eye, CheckCheck, Loader2 } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ContentBlocksEditor } from './ContentBlocksEditor'
import { PIIReviewPanel } from './PIIReviewPanel'
import { SemanticSuggestions } from './SemanticSuggestions'
import { TransparencyModal } from './TransparencyModal'
import { useStore } from '@/store/useStore'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

type TabId = 'blocks' | 'pii' | 'semantic' | 'transparency'

interface Tab {
  id: TabId
  label: string
  icon: typeof FileText
  badge?: number
}

export function CoDesignTabs() {
  const { currentDocument, preview, setPreview, secureMode } = useStore()
  const [activeTab, setActiveTab] = useState<TabId>('blocks')
  const [transparencyOpen, setTransparencyOpen] = useState(false)
  const [isBulkApproving, setIsBulkApproving] = useState(false)

  const tabs: Tab[] = [
    { 
      id: 'blocks', 
      label: 'Content Blocks', 
      icon: FileText,
      badge: preview?.stats?.total_blocks || 0
    },
    { 
      id: 'pii', 
      label: 'PII Review', 
      icon: Shield,
      badge: preview?.stats?.pii_count || 0
    },
    { 
      id: 'semantic', 
      label: 'AI Suggestions', 
      icon: Sparkles,
      badge: preview?.semantic_suggestions?.length || 0
    },
    { 
      id: 'transparency', 
      label: 'Transparency', 
      icon: Eye,
      badge: undefined
    },
  ]

  const handleBulkApprove = async () => {
    if (!currentDocument) return
    setIsBulkApproving(true)
    try {
      await api.bulkApprove(currentDocument.document_id)
      const newPreview = await api.getPreview(currentDocument.document_id)
      setPreview(newPreview)
    } catch (err) {
      console.error('Bulk approve failed:', err)
    } finally {
      setIsBulkApproving(false)
    }
  }

  if (!currentDocument) {
    return (
      <Card className="p-6 bg-card/50 border-border">
        <div className="text-center py-8 text-muted-foreground">
          <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="text-sm">Upload a PDF to start the Co-Design process</p>
          <p className="text-xs mt-1 text-muted-foreground/70">
            Review and edit extracted content before generating HTML
          </p>
        </div>
      </Card>
    )
  }

  return (
    <Card className="bg-card/50 border-border overflow-hidden">
      {/* Header with Accept All button */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <h2 className="font-semibold text-foreground flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-cyan-400" />
          Co-Design Layer
        </h2>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            className="h-8 text-xs hover:border-emerald-500/50 hover:bg-emerald-500/10"
            onClick={handleBulkApprove}
            disabled={isBulkApproving || !preview?.stats?.low_confidence_count}
          >
            {isBulkApproving ? (
              <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
            ) : (
              <CheckCheck className="w-3.5 h-3.5 mr-1.5 text-emerald-400" />
            )}
            Accept All
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border">
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          
          return (
            <button
              key={tab.id}
              onClick={() => tab.id === 'transparency' ? setTransparencyOpen(true) : setActiveTab(tab.id)}
              className={cn(
                "flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors relative",
                isActive 
                  ? "text-cyan-400 border-b-2 border-cyan-400 -mb-px" 
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
              )}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{tab.label}</span>
              {tab.badge !== undefined && tab.badge > 0 && (
                <span className={cn(
                  "text-xs px-1.5 py-0.5 rounded-full",
                  isActive ? "bg-cyan-500/20 text-cyan-400" : "bg-secondary text-muted-foreground"
                )}>
                  {tab.badge}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      <div className="p-4">
        {activeTab === 'blocks' && <ContentBlocksEditorInline />}
        {activeTab === 'pii' && <PIIReviewInline />}
        {activeTab === 'semantic' && <SemanticSuggestionsInline />}
      </div>

      {/* Transparency Modal */}
      <TransparencyModal open={transparencyOpen} onOpenChange={setTransparencyOpen} />
    </Card>
  )
}

// Inline versions without Card wrapper for use inside tabs
function ContentBlocksEditorInline() {
  const { currentDocument, preview, setPreview } = useStore()
  const [editingBlock, setEditingBlock] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [editType, setEditType] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [expandedBlocks, setExpandedBlocks] = useState<Set<string>>(new Set())

  const blocks = preview?.blocks || []
  const blockTypes = ['heading', 'paragraph', 'table', 'list', 'code', 'image', 'quote']
  const blockTypeIcons: Record<string, string> = {
    heading: '📌', paragraph: '📝', table: '📊', list: '📋', code: '💻', image: '🖼️', quote: '💬',
  }

  const toggleExpand = (blockId: string) => {
    const newExpanded = new Set(expandedBlocks)
    if (newExpanded.has(blockId)) newExpanded.delete(blockId)
    else newExpanded.add(blockId)
    setExpandedBlocks(newExpanded)
  }

  const startEditing = (block: { block_id: string; content: string; type: string }) => {
    setEditingBlock(block.block_id)
    setEditContent(block.content)
    setEditType(block.type)
  }

  const cancelEditing = () => {
    setEditingBlock(null)
    setEditContent('')
    setEditType('')
  }

  const handleSaveBlock = async (blockId: string) => {
    if (!currentDocument) return
    setIsSaving(true)
    try {
      const originalType = blocks.find(b => b.block_id === blockId)?.type
      await api.editBlock(currentDocument.document_id, blockId, editContent, editType !== originalType ? editType : undefined)
      const newPreview = await api.getPreview(currentDocument.document_id)
      setPreview(newPreview)
      cancelEditing()
    } catch (err) {
      console.error('Failed to save block:', err)
    } finally {
      setIsSaving(false)
    }
  }

  if (blocks.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No content blocks extracted yet</p>
      </div>
    )
  }

  return (
    <div className="space-y-2 max-h-[400px] overflow-auto pr-1">
      {blocks.map((block, index) => {
        const isEditing = editingBlock === block.block_id
        const isExpanded = expandedBlocks.has(block.block_id)
        const isLowConfidence = block.confidence < 0.8
        const icon = blockTypeIcons[block.type] || '📄'
        const blockKey = block.block_id || `block-${index}`

        return (
          <div
            key={blockKey}
            className={cn(
              "rounded-lg border transition-all",
              isLowConfidence ? "border-yellow-500/30 bg-yellow-500/5" : "border-border bg-secondary/30",
              isEditing && "ring-2 ring-cyan-500"
            )}
          >
            <div
              className="flex items-center justify-between p-3 cursor-pointer hover:bg-white/5"
              onClick={() => !isEditing && toggleExpand(block.block_id)}
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <span className="text-base">{icon}</span>
                {isEditing ? (
                  <select
                    value={editType}
                    onChange={(e) => setEditType(e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                    className="h-6 px-2 text-xs rounded bg-background border border-border"
                  >
                    {blockTypes.map(t => <option key={`opt-${t}`} value={t}>{t}</option>)}
                  </select>
                ) : (
                  <span className="text-xs px-2 py-0.5 rounded bg-secondary text-muted-foreground uppercase">{block.type}</span>
                )}
                <span className="text-xs text-muted-foreground">P{block.page + 1}</span>
                <span className={cn(
                  "text-xs px-1.5 py-0.5 rounded",
                  block.confidence >= 0.9 ? "bg-emerald-500/10 text-emerald-400" :
                  block.confidence >= 0.8 ? "bg-cyan-500/10 text-cyan-400" :
                  "bg-yellow-500/10 text-yellow-400"
                )}>
                  {Math.round(block.confidence * 100)}%
                </span>
                {!isExpanded && !isEditing && (
                  <span className="text-xs text-muted-foreground truncate flex-1">{block.content.substring(0, 40)}...</span>
                )}
              </div>
              <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                {isEditing ? (
                  <>
                    <Button size="icon" variant="ghost" className="h-7 w-7" onClick={() => handleSaveBlock(block.block_id)} disabled={isSaving}>
                      {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCheck className="w-3.5 h-3.5 text-emerald-400" />}
                    </Button>
                    <Button size="icon" variant="ghost" className="h-7 w-7" onClick={cancelEditing}>
                      <span className="text-red-400 text-xs">✕</span>
                    </Button>
                  </>
                ) : (
                  <Button size="icon" variant="ghost" className="h-7 w-7" onClick={() => startEditing(block)}>
                    <FileText className="w-3.5 h-3.5" />
                  </Button>
                )}
              </div>
            </div>
            {(isExpanded || isEditing) && (
              <div className="px-3 pb-3">
                {isEditing ? (
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="w-full p-2 rounded bg-background border border-border text-sm resize-none focus:outline-none focus:ring-1 focus:ring-cyan-500"
                    rows={4}
                  />
                ) : (
                  <p className="text-sm text-foreground/80 whitespace-pre-wrap">{block.content}</p>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function PIIReviewInline() {
  const { currentDocument, preview, setPreview } = useStore()
  const [loadingId, setLoadingId] = useState<string | null>(null)

  const redactions = preview?.pii_redactions || []
  const piiTypeIcons: Record<string, string> = {
    EMAIL_ADDRESS: '📧', PHONE_NUMBER: '📱', PERSON: '👤', US_SSN: '🔢', CREDIT_CARD: '💳',
  }

  const handleAction = async (redactionId: string, action: 'approve' | 'undo') => {
    if (!currentDocument) return
    setLoadingId(redactionId)
    try {
      await api.piiAction(currentDocument.document_id, redactionId, action)
      const newPreview = await api.getPreview(currentDocument.document_id)
      setPreview(newPreview)
    } catch (err) {
      console.error(`Failed to ${action} PII:`, err)
    } finally {
      setLoadingId(null)
    }
  }

  if (redactions.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Shield className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No PII detected in this document</p>
        <p className="text-xs mt-1">Document appears clean of sensitive data</p>
      </div>
    )
  }

  return (
    <div className="space-y-3 max-h-[400px] overflow-auto pr-1">
      {redactions.map((r, index) => {
        const icon = piiTypeIcons[r.pii_type] || '🔒'
        const isLoading = loadingId === r.id
        const redactionKey = r.id || `pii-${index}`
        return (
          <div key={redactionKey} className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/5">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span>{icon}</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-amber-500/10 text-amber-400">{r.pii_type}</span>
                  <span className="text-xs text-muted-foreground">{Math.round(r.confidence * 100)}%</span>
                </div>
                <div className="text-xs space-y-1">
                  <div><span className="text-muted-foreground">Original:</span> <code className="px-1 rounded bg-red-500/10 text-red-300">{r.original.substring(0, 3)}***</code></div>
                  <div><span className="text-muted-foreground">Redacted:</span> <code className="px-1 rounded bg-emerald-500/10 text-emerald-300">{r.redacted}</code></div>
                </div>
              </div>
              <div className="flex gap-1">
                <Button size="sm" variant="ghost" className="h-7 px-2 text-xs hover:bg-emerald-500/10" onClick={() => handleAction(r.id, 'approve')} disabled={isLoading}>
                  {isLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : '✓'}
                </Button>
                <Button size="sm" variant="ghost" className="h-7 px-2 text-xs hover:bg-red-500/10" onClick={() => handleAction(r.id, 'undo')} disabled={isLoading}>
                  ↩
                </Button>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function SemanticSuggestionsInline() {
  const { preview } = useStore()
  
  if (!preview?.semantic_suggestions?.length) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Sparkles className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No AI suggestions available</p>
        <p className="text-xs mt-1">Suggestions appear after processing</p>
      </div>
    )
  }

  // Reuse the existing SemanticSuggestions component content
  return <SemanticSuggestions />
}
