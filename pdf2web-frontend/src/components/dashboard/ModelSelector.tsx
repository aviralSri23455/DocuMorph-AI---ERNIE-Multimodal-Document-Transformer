import { useState, useEffect } from 'react'
import { Brain, Eye, Sparkles, Zap, Settings2 } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'
import { useStore } from '@/store/useStore'

// ERNIE models available on Novita AI
const textModels = [
  { id: 'baidu/ernie-4.5-21B-a3b', name: 'ERNIE 4.5 21B', cost: '$', speed: 'Fast', desc: 'Recommended' },
  { id: 'baidu/ernie-4.5-21B-a3b-thinking', name: 'ERNIE 4.5 Thinking', cost: '$$', speed: 'Medium', desc: 'With reasoning' },
  { id: 'baidu/ernie-4.5-300b-a47b-paddle', name: 'ERNIE 4.5 300B', cost: '$$$', speed: 'Slow', desc: 'Most capable' },
]

// ERNIE Vision models on Novita AI
const visionModels = [
  { id: 'baidu/ernie-4.5-vl-28b-a3b', name: 'ERNIE 4.5 VL 28B', desc: 'Multimodal analysis' },
  { id: 'baidu/ernie-4.5-vl-28b-a3b-thinking', name: 'ERNIE 4.5 VL Thinking', desc: 'Vision + reasoning' },
]

// DeepSeek models on Novita AI (for MCP mode)
const mcpModels = [
  { id: 'deepseek/deepseek-v3-turbo', name: 'DeepSeek V3 Turbo', desc: 'Fast, recommended' },
  { id: 'deepseek/deepseek-v3.2', name: 'DeepSeek V3.2', desc: 'Latest version' },
  { id: 'deepseek/deepseek-r1-turbo', name: 'DeepSeek R1 Turbo', desc: 'Reasoning model' },
]

export function ModelSelector() {
  const { modelConfig, setModelConfig } = useStore()
  const [expanded, setExpanded] = useState(false)
  const [health, setHealth] = useState<{ configured: boolean; vision_enabled: boolean } | null>(null)

  const updateConfig = (updates: Partial<typeof modelConfig>) => {
    setModelConfig({ ...modelConfig, ...updates })
  }

  useEffect(() => {
    api.checkErnieHealth().then(setHealth).catch(() => {})
  }, [])

  return (
    <Card className="p-4 bg-card/50 border-border">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-cyan-400" />
          <h3 className="font-medium text-foreground">AI Models</h3>
        </div>
        <Button size="sm" variant="ghost" onClick={() => setExpanded(!expanded)}>
          <Settings2 className="w-4 h-4" />
        </Button>
      </div>

      {/* Quick Status */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className={cn("p-2 rounded-lg text-center", health?.configured ? "bg-emerald-500/10" : "bg-yellow-500/10")}>
          <Brain className={cn("w-4 h-4 mx-auto mb-1", health?.configured ? "text-emerald-400" : "text-yellow-400")} />
          <p className="text-xs text-muted-foreground">ERNIE</p>
        </div>
        <div className={cn("p-2 rounded-lg text-center", modelConfig.enableVision ? "bg-emerald-500/10" : "bg-secondary")}>
          <Eye className={cn("w-4 h-4 mx-auto mb-1", modelConfig.enableVision ? "text-emerald-400" : "text-muted-foreground")} />
          <p className="text-xs text-muted-foreground">Vision</p>
        </div>
        <div className={cn("p-2 rounded-lg text-center", modelConfig.enableMCP ? "bg-purple-500/10" : "bg-secondary")}>
          <Zap className={cn("w-4 h-4 mx-auto mb-1", modelConfig.enableMCP ? "text-purple-400" : "text-muted-foreground")} />
          <p className="text-xs text-muted-foreground">MCP</p>
        </div>
      </div>

      {expanded && (
        <div className="space-y-4 pt-4 border-t border-border">
          {/* Text Model Selection */}
          <div>
            <label className="text-sm font-medium text-foreground mb-2 block">ERNIE Model (Main)</label>
            <Select value={modelConfig.textModel} onValueChange={(v) => updateConfig({ textModel: v })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {textModels.map((m) => (
                  <SelectItem key={m.id} value={m.id}>
                    <div className="flex items-center gap-2">
                      <span>{m.name}</span>
                      <span className="text-xs text-muted-foreground">{m.cost} • {m.speed}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Vision Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-foreground">Vision Analysis</p>
              <p className="text-xs text-muted-foreground">Enhanced table/chart detection</p>
            </div>
            <Switch checked={modelConfig.enableVision} onCheckedChange={(v) => updateConfig({ enableVision: v })} />
          </div>

          {/* Vision Model (if enabled) */}
          {modelConfig.enableVision && (
            <div>
              <label className="text-sm font-medium text-foreground mb-2 block">Vision Model</label>
              <Select value={modelConfig.visionModel} onValueChange={(v) => updateConfig({ visionModel: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {visionModels.map((m) => (
                    <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* MCP Toggle - Uses DeepSeek */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-foreground">MCP Mode (DeepSeek)</p>
              <p className="text-xs text-muted-foreground">Auto-convert with DeepSeek AI</p>
            </div>
            <Switch checked={modelConfig.enableMCP} onCheckedChange={(v) => updateConfig({ enableMCP: v })} />
          </div>

          {modelConfig.enableMCP && (
            <div className="p-3 rounded-lg bg-purple-500/5 border border-purple-500/20">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="w-4 h-4 text-purple-400" />
                <span className="text-sm font-medium text-purple-400">MCP Mode Active</span>
              </div>
              <p className="text-xs text-muted-foreground mb-2">
                Uses DeepSeek via Novita AI for automatic processing. Upload PDF and it converts automatically!
              </p>
              <Select value={modelConfig.textModel} onValueChange={(v) => updateConfig({ textModel: v })}>
                <SelectTrigger className="h-8">
                  <SelectValue placeholder="Select DeepSeek model" />
                </SelectTrigger>
                <SelectContent>
                  {mcpModels.map((m) => (
                    <SelectItem key={m.id} value={m.id}>
                      <span>{m.name}</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Knowledge Graph Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-foreground">Knowledge Graph</p>
              <p className="text-xs text-muted-foreground">Entity extraction visualization</p>
            </div>
            <Switch checked={modelConfig.enableKnowledgeGraph} onCheckedChange={(v) => updateConfig({ enableKnowledgeGraph: v })} />
          </div>

          {/* Cost Info */}
          <div className="p-3 rounded-lg bg-secondary">
            <p className="text-xs text-muted-foreground">All models via Novita AI</p>
            <p className="text-sm font-medium text-foreground">
              {modelConfig.enableMCP ? 'DeepSeek: ~$0.001/request' : 'ERNIE: ~$0.01-0.05/doc'}
            </p>
          </div>
        </div>
      )}
    </Card>
  )
}
