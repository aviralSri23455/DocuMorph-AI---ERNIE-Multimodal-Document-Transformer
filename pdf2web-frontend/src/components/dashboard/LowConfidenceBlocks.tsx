import { useState, useEffect } from 'react'
import { AlertTriangle, Edit3, Check, X, Loader2, RefreshCw } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useStore } from '@/store/useStore'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

interface LowConfidenceBlock {
  block_id: string
  type: string
  content: string
  confidence: number
  page: number
}

const blockTypes = ['heading', 'paragraph', 'table', 'list', 'code', 'image', 'quote']

export function LowConfidenceBlocks() {
  const { currentDocument, setPreview } = useStore()
  const [blocks, setBlocks] = useState<LowConfidenceBlock[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [editingBlock, setEditingBlock] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [editType, setEditType] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  const fetchLowConfidence = async () => {
    if (!currentDocument) return
    setIsLoading(true)
    try {
      const data = await api.getLowConfidenceBlocks(currentDocument.document_id)
      setBlocks(data.low_confidence_blocks || [])
    } catch (err) {
      console.error('Failed to fetch low confidence blocks:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchLowConfidence()
  }, [currentDocument])

  const handleSaveBlock = async (blockId: string) => {
    if (!currentDocument) return
    setIsSaving(true)
    try {
      await api.editBlock(currentDocument.document_id, blockId, editContent, editType || undefined)
      const newPreview = await api.getPreview(currentDocument.document_id)
      setPreview(newPreview)
      setEditingBlock(null)
      fetchLowConfidence()
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
          <AlertTriangle className="w-5 h-5 text-yellow-400" />
          <h3 className="font-medium text-foreground">Low Confidence Blocks</h3>
          <span className="text-xs px-2 py-0.5 rounded bg-yellow-500/10 text-yellow-400">
            {blocks.length} need review
          </span>
        </div>
        <Button size="sm" variant="ghost" onClick={fetchLowConfidence} disabled={isLoading}>
          <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
        </div>
      ) : blocks.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <AlertTriangle className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No low confidence blocks found</p>
          <p className="text-xs mt-1">All blocks have high OCR confidence</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-64 overflow-auto">
          {blocks.map((block) => (
            <div
              key={block.block_id}
              className={cn(
                "p-3 rounded-lg border transition-all",
                "border-yellow-500/30 bg-yellow-500/5",
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
                    <span className="text-xs px-2 py-0.5 rounded bg-yellow-500/10 text-yellow-400 uppercase">
                      {block.type}
                    </span>
                  )}
                  <span className="text-xs text-muted-foreground">P{block.page}</span>
                  <span className="text-xs px-1.5 py-0.5 rounded bg-red-500/10 text-red-400">
                    {Math.round(block.confidence * 100)}%
                  </span>
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
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-6 w-6"
                      onClick={() => {
                        setEditingBlock(block.block_id)
                        setEditContent(block.content)
                        setEditType(block.type)
                      }}
                    >
                      <Edit3 className="w-3 h-3" />
                    </Button>
                  )}
                </div>
              </div>
              {editingBlock === block.block_id ? (
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className="w-full p-2 rounded bg-background border border-border text-sm resize-none focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  rows={3}
                />
              ) : (
                <p className="text-sm text-foreground/80 line-clamp-2">{block.content}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}
