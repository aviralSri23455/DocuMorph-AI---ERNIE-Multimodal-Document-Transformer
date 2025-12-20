import { useEffect, useState } from 'react'
import { Brain, Eye, Sparkles, AlertCircle } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { api, HealthResponse } from '@/lib/api'
import { cn } from '@/lib/utils'

export function AIModelStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await api.checkErnieHealth()
        setHealth(data)
        setError(null)
      } catch {
        setError('Unable to connect to AI service')
      }
    }
    checkHealth()
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  const models = [
    {
      name: 'ERNIE 3.5',
      provider: 'Novita AI',
      status: health?.configured ? 'active' : 'inactive',
      icon: Brain,
      description: 'Text processing & analysis',
    },
    {
      name: 'ERNIE Vision',
      provider: 'Novita AI',
      status: health?.vision_enabled ? 'active' : 'inactive',
      icon: Eye,
      description: 'Image & table detection',
    },
    {
      name: 'DeepSeek',
      provider: 'DeepSeek API',
      status: health?.status !== 'error' ? 'active' : 'inactive',
      icon: Sparkles,
      description: 'Knowledge graph generation',
    },
  ]

  return (
    <Card className="p-4 bg-card/50 border-border">
      <h3 className="font-medium text-foreground mb-4">AI Models</h3>
      {error && (
        <div className="flex items-center gap-2 text-yellow-400 text-sm mb-3 p-2 rounded bg-yellow-500/10">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}
      <div className="space-y-3">
        {models.map((model) => {
          const Icon = model.icon
          return (
            <div
              key={model.name}
              className="flex items-center gap-3 p-2 rounded-lg bg-secondary/30"
            >
              <div className={cn(
                "p-2 rounded-lg",
                model.status === 'active' ? "bg-cyan-500/10" : "bg-secondary"
              )}>
                <Icon className={cn(
                  "w-4 h-4",
                  model.status === 'active' ? "text-cyan-400" : "text-muted-foreground"
                )} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-foreground">{model.name}</span>
                  <span className="text-xs text-muted-foreground">• {model.provider}</span>
                </div>
                <p className="text-xs text-muted-foreground truncate">{model.description}</p>
              </div>
              <div className={cn(
                "w-2 h-2 rounded-full",
                model.status === 'active' ? "bg-emerald-500" : "bg-yellow-500"
              )} />
            </div>
          )
        })}
      </div>
      <p className="text-xs text-muted-foreground mt-3 text-center">
        $25 Novita AI credits available
      </p>
    </Card>
  )
}
