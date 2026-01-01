import { useState, useRef, useEffect, useCallback } from 'react'
import { Network, Minimize2, Eye, Loader2, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useStore } from '@/store/useStore'
import { api } from '@/lib/api'

interface GraphNode {
  id: string
  label: string
  title?: string
  type?: string
  group?: string
  color?: string
  data?: {
    type: string
    block_id?: string
    page?: number
    confidence?: number
  }
  // For rendering
  x?: number
  y?: number
  vx?: number
  vy?: number
}

interface GraphEdge {
  id: string
  from: string
  to: string
  label?: string
  color?: string
  type?: string
}

interface KnowledgeGraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  metadata?: {
    total_nodes: number
    total_edges: number
    entity_types: string[]
    relationship_types: string[]
  }
}

export function KnowledgeGraph() {
  const { currentDocument } = useStore()
  const [graph, setGraph] = useState<KnowledgeGraphData | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isSimplified, setIsSimplified] = useState(false)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [zoom, setZoom] = useState(1)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const animationRef = useRef<number>()
  const nodesRef = useRef<GraphNode[]>([])

  const nodeColors: Record<string, string> = {
    section: '#4e79a7',
    concept: '#f28e2c',
    person: '#e15759',
    date: '#76b7b2',
    location: '#59a14f',
    table: '#edc949',
    figure: '#af7aa1',
    definition: '#ff9da7',
    organization: '#9c755f',
  }

  const generateGraph = async () => {
    if (!currentDocument) return
    setIsGenerating(true)
    setSelectedNode(null)
    try {
      const data = await api.generateKnowledgeGraph(currentDocument.document_id)
      setGraph(data)
      setIsSimplified(false)
    } catch (err) {
      console.error('Failed to generate knowledge graph:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  const simplifyGraph = async () => {
    if (!currentDocument || !graph) return
    try {
      const data = await api.simplifyKnowledgeGraph(currentDocument.document_id, 15)
      // Reset nodes to force re-initialization with new data
      nodesRef.current = []
      setGraph(data)
      setIsSimplified(true)
    } catch (err) {
      console.error('Failed to simplify graph:', err)
    }
  }

  // Initialize node positions
  const initializeNodes = useCallback((nodes: GraphNode[], width: number, height: number) => {
    const centerX = width / 2
    const centerY = height / 2
    const radius = Math.min(width, height) * 0.38

    return nodes.map((node, i) => {
      const angle = (2 * Math.PI * i) / nodes.length
      return {
        ...node,
        x: centerX + radius * Math.cos(angle) + (Math.random() - 0.5) * 80,
        y: centerY + radius * Math.sin(angle) + (Math.random() - 0.5) * 80,
        vx: 0,
        vy: 0,
      }
    })
  }, [])

  // Force-directed simulation step
  const simulateForces = useCallback((nodes: GraphNode[], edges: GraphEdge[], width: number, height: number) => {
    const centerX = width / 2
    const centerY = height / 2
    
    // Apply forces
    nodes.forEach((node, i) => {
      let fx = 0, fy = 0
      
      // Stronger repulsion from other nodes for better spacing
      nodes.forEach((other, j) => {
        if (i === j) return
        const dx = (node.x || 0) - (other.x || 0)
        const dy = (node.y || 0) - (other.y || 0)
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const force = 5000 / (dist * dist)  // Increased repulsion
        fx += (dx / dist) * force
        fy += (dy / dist) * force
      })
      
      // Attraction to connected nodes
      edges.forEach(edge => {
        let other: GraphNode | undefined
        if (edge.from === node.id) other = nodes.find(n => n.id === edge.to)
        else if (edge.to === node.id) other = nodes.find(n => n.id === edge.from)
        if (other) {
          const dx = (other.x || 0) - (node.x || 0)
          const dy = (other.y || 0) - (node.y || 0)
          fx += dx * 0.006
          fy += dy * 0.006
        }
      })
      
      // Center gravity
      fx += (centerX - (node.x || 0)) * 0.0005
      fy += (centerY - (node.y || 0)) * 0.0005
      
      // Update velocity with damping
      node.vx = ((node.vx || 0) + fx) * 0.7
      node.vy = ((node.vy || 0) + fy) * 0.7
      
      // Update position with more padding
      node.x = Math.max(70, Math.min(width - 70, (node.x || 0) + (node.vx || 0)))
      node.y = Math.max(55, Math.min(height - 55, (node.y || 0) + (node.vy || 0)))
    })
    
    return nodes
  }, [])

  // Draw the graph
  const drawGraph = useCallback(() => {
    const canvas = canvasRef.current
    const container = containerRef.current
    if (!canvas || !container || !graph) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const width = container.clientWidth
    const height = 380  // Taller canvas
    canvas.width = width * window.devicePixelRatio
    canvas.height = height * window.devicePixelRatio
    canvas.style.width = `${width}px`
    canvas.style.height = `${height}px`
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio)

    // Clear
    ctx.fillStyle = '#0a0a0f'
    ctx.fillRect(0, 0, width, height)

    // Draw grid pattern
    ctx.strokeStyle = '#1a1a2e'
    ctx.lineWidth = 0.5
    for (let x = 0; x < width; x += 20) {
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, height)
      ctx.stroke()
    }
    for (let y = 0; y < height; y += 20) {
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(width, y)
      ctx.stroke()
    }

    ctx.save()
    ctx.translate(width / 2, height / 2)
    ctx.scale(zoom, zoom)
    ctx.translate(-width / 2, -height / 2)

    const nodes = nodesRef.current

    // Draw edges
    graph.edges.forEach(edge => {
      const fromNode = nodes.find(n => n.id === edge.from)
      const toNode = nodes.find(n => n.id === edge.to)
      if (!fromNode || !toNode) return

      // Draw curved edge for better visibility
      ctx.beginPath()
      ctx.strokeStyle = edge.color || '#6b7280'
      ctx.lineWidth = 2
      ctx.moveTo(fromNode.x || 0, fromNode.y || 0)
      ctx.lineTo(toNode.x || 0, toNode.y || 0)
      ctx.stroke()

      // Draw arrow
      const angle = Math.atan2((toNode.y || 0) - (fromNode.y || 0), (toNode.x || 0) - (fromNode.x || 0))
      const arrowX = (toNode.x || 0) - Math.cos(angle) * 24
      const arrowY = (toNode.y || 0) - Math.sin(angle) * 24
      ctx.beginPath()
      ctx.moveTo(arrowX, arrowY)
      ctx.lineTo(arrowX - 10 * Math.cos(angle - 0.4), arrowY - 10 * Math.sin(angle - 0.4))
      ctx.lineTo(arrowX - 10 * Math.cos(angle + 0.4), arrowY - 10 * Math.sin(angle + 0.4))
      ctx.closePath()
      ctx.fillStyle = edge.color || '#6b7280'
      ctx.fill()
    })

    // Draw nodes - LARGER and more visible
    nodes.forEach(node => {
      const type = node.data?.type || node.group || node.type || 'concept'
      const color = node.color || nodeColors[type] || '#64748b'
      const isSelected = selectedNode?.id === node.id
      const radius = isSelected ? 24 : 20  // Bigger nodes

      // Outer glow for all nodes
      ctx.beginPath()
      ctx.arc(node.x || 0, node.y || 0, radius + 4, 0, Math.PI * 2)
      ctx.fillStyle = `${color}22`
      ctx.fill()

      // Stronger glow effect for selected
      if (isSelected) {
        ctx.beginPath()
        ctx.arc(node.x || 0, node.y || 0, radius + 12, 0, Math.PI * 2)
        ctx.fillStyle = `${color}44`
        ctx.fill()
      }

      // Node circle
      ctx.beginPath()
      ctx.arc(node.x || 0, node.y || 0, radius, 0, Math.PI * 2)
      ctx.fillStyle = color
      ctx.fill()
      ctx.strokeStyle = isSelected ? '#fff' : '#0f0f14'
      ctx.lineWidth = isSelected ? 4 : 3
      ctx.stroke()

      // Label with background for readability
      const label = node.label.length > 18 ? node.label.slice(0, 16) + '...' : node.label
      ctx.font = 'bold 12px Inter, system-ui, sans-serif'
      const textWidth = ctx.measureText(label).width
      
      // Label background
      ctx.fillStyle = 'rgba(10, 10, 15, 0.85)'
      ctx.fillRect((node.x || 0) - textWidth / 2 - 4, (node.y || 0) + radius + 6, textWidth + 8, 18)
      
      // Label text
      ctx.fillStyle = '#f1f5f9'
      ctx.textAlign = 'center'
      ctx.fillText(label, node.x || 0, (node.y || 0) + radius + 19)
    })

    ctx.restore()
  }, [graph, selectedNode, zoom, nodeColors])

  // Handle canvas click
  const handleCanvasClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas || !graph) return

    const rect = canvas.getBoundingClientRect()
    const x = (e.clientX - rect.left) / zoom
    const y = (e.clientY - rect.top) / zoom

    const clickedNode = nodesRef.current.find(node => {
      const dx = (node.x || 0) - x
      const dy = (node.y || 0) - y
      return Math.sqrt(dx * dx + dy * dy) < 20
    })

    setSelectedNode(clickedNode || null)
  }, [graph, zoom])

  // Animation loop
  useEffect(() => {
    if (!graph || graph.nodes.length === 0) return

    const container = containerRef.current
    if (!container) return

    const width = container.clientWidth
    const height = 380  // Match canvas height

    // Initialize nodes if needed
    if (nodesRef.current.length !== graph.nodes.length) {
      nodesRef.current = initializeNodes(graph.nodes, width, height)
    }

    let iterations = 0
    const maxIterations = 150

    const animate = () => {
      if (iterations < maxIterations) {
        nodesRef.current = simulateForces(nodesRef.current, graph.edges, width, height)
        iterations++
      }
      drawGraph()
      animationRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [graph, drawGraph, initializeNodes, simulateForces])

  return (
    <Card className="p-4 bg-card/50 border-border">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Network className="w-5 h-5 text-cyan-400" />
          <h3 className="font-medium text-foreground">Knowledge Graph</h3>
        </div>
        <div className="flex gap-2">
          {graph && (
            <>
              <Button size="sm" variant="ghost" onClick={() => setZoom(z => Math.min(2, z + 0.2))}>
                <ZoomIn className="w-4 h-4" />
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setZoom(z => Math.max(0.5, z - 0.2))}>
                <ZoomOut className="w-4 h-4" />
              </Button>
              <Button size="sm" variant="ghost" onClick={simplifyGraph} disabled={isSimplified}>
                <Minimize2 className="w-4 h-4 mr-1" />
                Simplify
              </Button>
            </>
          )}
          <Button size="sm" variant="outline" onClick={generateGraph} disabled={!currentDocument || isGenerating}>
            {isGenerating ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Eye className="w-4 h-4 mr-1" />}
            {graph ? 'Regenerate' : 'Generate'}
          </Button>
        </div>
      </div>

      {graph ? (
        <div className="space-y-3">
          {/* Entity Types Legend */}
          <div className="flex flex-wrap gap-2">
            {(graph.metadata?.entity_types || []).map((type) => (
              <span key={type} className="flex items-center gap-1 text-xs px-2 py-1 rounded bg-secondary">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: nodeColors[type] || '#64748b' }} />
                {type}
              </span>
            ))}
          </div>

          {/* Interactive Graph Canvas */}
          <div ref={containerRef} className="relative rounded-lg border border-border overflow-hidden">
            <canvas
              ref={canvasRef}
              onClick={handleCanvasClick}
              className="cursor-pointer"
              style={{ display: 'block' }}
            />
            <div className="absolute bottom-2 left-2 text-xs text-muted-foreground bg-background/80 px-2 py-1 rounded">
              {graph.metadata?.total_nodes || graph.nodes.length} nodes • {graph.metadata?.total_edges || graph.edges.length} relationships
            </div>
          </div>

          {/* Selected Node Info */}
          {selectedNode && (
            <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/30">
              <p className="text-sm font-medium text-cyan-400">{selectedNode.label}</p>
              <p className="text-xs text-muted-foreground mt-1">
                Type: {selectedNode.data?.type || selectedNode.group || 'unknown'}
                {selectedNode.data?.page !== undefined && ` • Page ${selectedNode.data.page + 1}`}
              </p>
            </div>
          )}

          {/* Section Navigation */}
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Click nodes to navigate:</p>
            <div className="max-h-24 overflow-auto space-y-1">
              {graph.nodes.filter(n => (n.data?.type || n.group) === 'section').slice(0, 6).map((node) => (
                <button
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`w-full text-left text-sm px-2 py-1 rounded transition-colors ${
                    selectedNode?.id === node.id 
                      ? 'bg-cyan-500/20 text-cyan-400' 
                      : 'hover:bg-cyan-500/10 text-foreground/80 hover:text-cyan-400'
                  }`}
                >
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
