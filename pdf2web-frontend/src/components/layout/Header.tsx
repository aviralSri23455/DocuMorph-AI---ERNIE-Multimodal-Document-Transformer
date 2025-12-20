import { Zap } from 'lucide-react'
import { Switch } from '@/components/ui/switch'
import { useStore } from '@/store/useStore'

export function Header() {
  const { modelConfig, setModelConfig } = useStore()

  const toggleMCP = () => {
    setModelConfig({ ...modelConfig, enableMCP: !modelConfig.enableMCP })
  }

  return (
    <header className="h-16 border-b border-border bg-card/50 backdrop-blur-sm flex items-center justify-between px-6">
      <div>
        <h1 className="text-2xl font-bold">
          <span className="text-cyan-400">Docu</span>
          <span className="text-foreground">Morph</span>
          <span className="text-muted-foreground ml-2 font-normal">AI</span>
        </h1>
        <p className="text-sm text-muted-foreground">
          Transform static PDFs into dynamic, interactive HTML experiences
        </p>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-secondary/50 border border-border">
          <Zap className={`w-4 h-4 ${modelConfig.enableMCP ? 'text-cyan-400' : 'text-muted-foreground'}`} />
          <span className="text-sm text-muted-foreground">MCP</span>
          <Switch checked={modelConfig.enableMCP} onCheckedChange={toggleMCP} />
        </div>
      </div>
    </header>
  )
}
