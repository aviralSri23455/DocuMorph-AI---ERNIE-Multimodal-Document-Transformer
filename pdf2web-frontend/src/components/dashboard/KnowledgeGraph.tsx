import { useState } from 'react'
import { Network, Minimize2, Eye, Loader2 } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useStore } from '@/store/useStore'
import { api } from '@/lib/api'

interface GraphNode {
  id: string
  label: string
  type: string
  properties?: Record<string, unknown>
}

interface GraphEdge {
  source: string
  target: string
  relationship: string
}

interface KnowledgeGraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  entity_types: string[]
}

export function KnowledgeGraph() {
  const { currentDocument } = useStore()
  const [graph, setGraph] = useState<KnowledgeGraphData | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isSimplified, setIsSimplified] = useState(false)

  const generateGraph = async () => {
    if (!currentDocument) return
    setIsGenerating(true)
    try {
      const data = await api.generateKnowledgeGraph(currentDocument.document_id)
      setGraph(data)
    } catch (err) {
      console.error('Failed to generate knowledge graph:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  const simplifyGraph = async () => {
    if (!currentDocument || !graph) return
    try {
      const data = await api.simplifyKnowledgeGraph(currentDocument.document_id)
      setGraph(data)
      setIsSimplified(true)
    } catch (err) {
      console.error('Failed to simplify graph:', err)
    }
  }

  const nodeColors: Record<string, string> = {
    concept: '#06b6d4',
    person: '#f59e0b',
    date: '#10b981',
    location: '#8b5cf6',
    section: '#ec4899',
  }

  return (
    <Card className="p-4 bg-card/50 border-border">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Network className="w-5 h-5 text-cyan-400" />
          <h3 className="font-medium text-foreground">Knowledge Graph</h3>
        </div>
        <div className="flex gap-2">
          {graph && (
            <Button size="sm" variant="ghost" onClick={simplifyGraph} disabled={isSimplified}>
              <Minimize2 className="w-4 h-4 mr-1" />
              Simplify
            </Button>
          )}
          <Button size="sm" variant="outline" onClick={generateGraph} disabled={!currentDocument || isGenerating}>
            {isGenerating ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Eye className="w-4 h-4 mr-1" />}
            {graph ? 'Regenerate' : 'Generate'}
          </Button>
        </div>
      </div>

      {graph ? (
        <div className="space-y-4">
          {/* Entity Types Legend */}
          <div className="flex flex-wrap gap-2">
            {(graph.entity_types || []).map((type) => (
              <span key={type} className="flex items-center gap-1 text-xs px-2 py-1 rounded bg-secondary">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: nodeColors[type] || '#64748b' }} />
                {type}
              </span>
            ))}
          </div>

          {/* Graph Visualization Placeholder */}
          <div className="h-48 rounded-lg border border-border bg-background/50 flex items-center justify-center relative overflow-hidden">
            <div className="absolute inset-0 grid-pattern opacity-50" />
            <div className="relative z-10 text-center">
              <p className="text-sm text-muted-foreground">{(graph.nodes || []).length} nodes • {(graph.edges || []).length} relationships</p>
              <p className="text-xs text-muted-foreground mt-1">Use vis.js or Cytoscape.js for interactive view</p>
            </div>
            {/* Simple node preview */}
            <div className="absolute inset-4 flex flex-wrap gap-2 items-center justify-center">
              {(graph.nodes || []).slice(0, 8).map((node) => (
                <div key={node.id} className="px-2 py-1 rounded text-xs border" style={{ borderColor: nodeColors[node.type] || '#64748b', color: nodeColors[node.type] || '#64748b' }}>
                  {node.label}
                </div>
              ))}
              {(graph.nodes || []).length > 8 && <span className="text-xs text-muted-foreground">+{graph.nodes.length - 8} more</span>}
            </div>
          </div>

          {/* Sidebar Navigation Data */}
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">Click nodes to navigate:</p>
            <div className="max-h-32 overflow-auto space-y-1">
              {(graph.nodes || []).filter(n => n.type === 'section').map((node) => (
                <button key={node.id} className="w-full text-left text-sm px-2 py-1 rounded hover:bg-cyan-500/10 text-foreground/80 hover:text-cyan-400 transition-colors">
                  → {node.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="h-32 flex items-center justify-center text-muted-foreground text-sm">
          {currentDocument ? 'Click Generate to create knowledge graph' : 'Upload a PDF first'}
        </div>
      )}
    </Card>
  )
}
