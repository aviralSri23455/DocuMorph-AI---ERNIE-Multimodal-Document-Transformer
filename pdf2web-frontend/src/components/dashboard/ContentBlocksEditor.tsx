import { useState } from 'react'
import { FileText, Edit3, Check, X, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useStore } from '@/store/useStore'
import { api, PreviewBlock } from '@/lib/api'
import { cn } from '@/lib/utils'

const blockTypes = ['heading', 'paragraph', 'table', 'list', 'code', 'image', 'quote']

const blockTypeIcons: Record<string, string> = {
  heading: '📌',
  paragraph: '📝',
  table: '📊',
  list: '📋',
  code: '💻',
  image: '🖼️',
  quote: '💬',
}

interface ContentBlocksEditorProps {
  showAll?: boolean
}

export function ContentBlocksEditor({ showAll = true }: ContentBlocksEditorProps) {
  const { currentDocument, preview, setPreview } = useStore()
  const [editingBlock, setEditingBlock] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [editType, setEditType] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [expandedBlocks, setExpandedBlocks] = useState<Set<string>>(new Set())

  const blocks = preview?.blocks || []
  const displayBlocks = showAll ? blocks : blocks.filter(b => b.confidence < 0.8)

  const toggleExpand = (blockId: string) => {
    const newExpanded = new Set(expandedBlocks)
    if (newExpanded.has(blockId)) {
      newExpanded.delete(blockId)
    } else {
      newExpanded.add(blockId)
    }
    setExpandedBlocks(newExpanded)
  }

  const startEditing = (block: PreviewBlock) => {
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
      await api.editBlock(
        currentDocument.document_id,
        blockId,
        editContent,
        editType !== preview?.blocks.find(b => b.block_id === blockId)?.type ? editType : undefined
      )
      const newPreview = await api.getPreview(currentDocument.document_id)
      setPreview(newPreview)
      cancelEditing()
    } catch (err) {
      console.error('Failed to save block:', err)
    } finally {
      setIsSaving(false)
    }
  }

  if (!currentDocument) return null

  return (
    <Card className="p-4 bg-card/50 border-border">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-cyan-400" />
          <h3 className="font-medium text-foreground">Content Blocks</h3>
          <span className="text-xs px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400">
            {displayBlocks.length} blocks
          </span>
        </div>
      </div>

      {displayBlocks.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No content blocks</p>
          <p className="text-xs mt-1">Upload a PDF to see extracted content</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-96 overflow-auto pr-1">
          {displayBlocks.map((block) => {
            const isEditing = editingBlock === block.block_id
            const isExpanded = expandedBlocks.has(block.block_id)
            const isLowConfidence = block.confidence < 0.8
            const icon = blockTypeIcons[block.type] || '📄'

            return (
              <div
                key={block.block_id}
                className={cn(
                  "rounded-lg border transition-all",
                  isLowConfidence ? "border-yellow-500/30 bg-yellow-500/5" : "border-border bg-secondary/30",
                  isEditing && "ring-2 ring-cyan-500"
                )}
              >
                {/* Header */}
                <div
                  className="flex items-center justify-between p-3 cursor-pointer hover:bg-white/5"
                  onClick={() => !isEditing && toggleExpand(block.block_id)}
                >
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <span className="text-base">{icon}</span>
                    {isEditing ? (
                      <Select value={editType} onValueChange={setEditType}>
                        <SelectTrigger className="h-6 w-28 text-xs" onClick={(e) => e.stopPropagation()}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {blockTypes.map(t => (
                            <SelectItem key={t} value={t} className="text-xs">
                              {blockTypeIcons[t]} {t}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      <span className="text-xs px-2 py-0.5 rounded bg-secondary text-muted-foreground uppercase">
                        {block.type}
                      </span>
                    )}
                    <span className="text-xs text-muted-foreground">P{block.page + 1}</span>
                    <span className={cn(
                      "text-xs px-1.5 py-0.5 rounded",
                      block.confidence >= 0.9 ? "bg-emerald-500/10 text-emerald-400" :
                      block.confidence >= 0.8 ? "bg-cyan-500/10 text-cyan-400" :
                      block.confidence >= 0.6 ? "bg-yellow-500/10 text-yellow-400" :
                      "bg-red-500/10 text-red-400"
                    )}>
                      {Math.round(block.confidence * 100)}%
                    </span>
                    {!isExpanded && !isEditing && (
                      <span className="text-xs text-muted-foreground truncate flex-1">
                        {block.content.substring(0, 50)}...
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                    {isEditing ? (
                      <>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          onClick={() => handleSaveBlock(block.block_id)}
                          disabled={isSaving}
                        >
                          {isSaving ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                          )}
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          onClick={cancelEditing}
                        >
                          <X className="w-3.5 h-3.5 text-red-400" />
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          onClick={() => startEditing(block)}
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                        </Button>
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4 text-muted-foreground" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-muted-foreground" />
                        )}
                      </>
                    )}
                  </div>
                </div>

                {/* Content */}
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
                      <p className="text-sm text-foreground/80 whitespace-pre-wrap">
                        {block.content}
                      </p>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </Card>
  )
}
