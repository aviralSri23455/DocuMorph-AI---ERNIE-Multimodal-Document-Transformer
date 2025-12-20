import { useState, useEffect } from 'react'
import { Puzzle, RefreshCw, Loader2, Settings2, Clock, MapPin } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

interface Plugin {
  id: string
  name: string
  description: string
  version: string
  enabled: boolean
  type: 'widget' | 'export' | 'analysis'
  icon?: string
}

const pluginIcons: Record<string, typeof Puzzle> = {
  timeline: Clock,
  map: MapPin,
}

export function PluginsPanel() {
  const [plugins, setPlugins] = useState<Plugin[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const fetchPlugins = async () => {
    setIsLoading(true)
    try {
      const data = await api.getPlugins()
      setPlugins(data.plugins || [])
    } catch (err) {
      console.error('Failed to fetch plugins:', err)
      // Set default plugins if API fails
      setPlugins([
        { id: 'timeline-widget', name: 'Timeline Widget', description: 'Visualize chronological events', version: '1.0.0', enabled: true, type: 'widget' },
        { id: 'map-widget', name: 'Map Widget', description: 'Interactive maps with Leaflet.js', version: '1.0.0', enabled: true, type: 'widget' },
        { id: 'quiz-widget', name: 'Quiz Widget', description: 'Interactive Q&A from lists', version: '1.0.0', enabled: true, type: 'widget' },
        { id: 'code-exec-widget', name: 'Code Execution', description: 'Run JavaScript in browser', version: '1.0.0', enabled: true, type: 'widget' },
        { id: 'chart-js-widget', name: 'Chart.js Integration', description: 'Bar, Line, Pie charts', version: '1.0.0', enabled: true, type: 'widget' },
        { id: 'prism-widget', name: 'Prism.js Highlighting', description: 'Syntax highlighting for code', version: '1.0.0', enabled: true, type: 'widget' },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (expanded) {
      fetchPlugins()
    }
  }, [expanded])

  const togglePlugin = (pluginId: string) => {
    setPlugins(plugins.map(p => 
      p.id === pluginId ? { ...p, enabled: !p.enabled } : p
    ))
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'widget': return 'bg-cyan-500/10 text-cyan-400'
      case 'export': return 'bg-purple-500/10 text-purple-400'
      case 'analysis': return 'bg-emerald-500/10 text-emerald-400'
      default: return 'bg-secondary text-muted-foreground'
    }
  }

  return (
    <Card className="p-4 bg-card/50 border-border">
      <button
        className="w-full flex items-center justify-between"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <Puzzle className="w-5 h-5 text-cyan-400" />
          <h3 className="font-medium text-foreground">Plugins</h3>
          <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400">
            {plugins.filter(p => p.enabled).length} active
          </span>
        </div>
        <Settings2 className={cn("w-4 h-4 transition-transform", expanded && "rotate-90")} />
      </button>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-border">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs text-muted-foreground">Manage semantic injection plugins</p>
            <Button size="sm" variant="ghost" onClick={fetchPlugins} disabled={isLoading}>
              <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
            </Button>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
            </div>
          ) : (
            <div className="space-y-2 max-h-64 overflow-auto">
              {plugins.map((plugin) => {
                const Icon = pluginIcons[plugin.id] || Puzzle
                return (
                  <div
                    key={plugin.id}
                    className={cn(
                      "p-3 rounded-lg border transition-all",
                      plugin.enabled 
                        ? "border-cyan-500/30 bg-cyan-500/5" 
                        : "border-border bg-secondary/30"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          "p-2 rounded-lg",
                          plugin.enabled ? "bg-cyan-500/10" : "bg-secondary"
                        )}>
                          <Icon className={cn(
                            "w-4 h-4",
                            plugin.enabled ? "text-cyan-400" : "text-muted-foreground"
                          )} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className={cn(
                              "text-sm font-medium",
                              plugin.enabled ? "text-foreground" : "text-muted-foreground"
                            )}>
                              {plugin.name}
                            </span>
                            <span className={cn("text-xs px-1.5 py-0.5 rounded", getTypeColor(plugin.type))}>
                              {plugin.type}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground">{plugin.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">v{plugin.version}</span>
                        <Switch
                          checked={plugin.enabled}
                          onCheckedChange={() => togglePlugin(plugin.id)}
                        />
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          <div className="mt-3 p-2 rounded-lg bg-secondary/50 text-xs text-muted-foreground">
            <p>💡 Plugins add interactive widgets to generated HTML</p>
          </div>
        </div>
      )}
    </Card>
  )
}
