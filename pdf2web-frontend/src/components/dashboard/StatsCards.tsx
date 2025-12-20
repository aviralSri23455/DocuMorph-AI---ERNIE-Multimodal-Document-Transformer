import { FileText, Clock, Zap, TrendingUp, RotateCcw, Sparkles } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useStore } from '@/store/useStore'
import { motion, AnimatePresence } from 'framer-motion'

export function StatsCards() {
  const { stats, preview, generatedHTML, resetStats, modelConfig, setModelConfig } = useStore()

  const handleResetStats = () => {
    resetStats()
  }

  const handleToggleMCP = () => {
    setModelConfig({ ...modelConfig, enableMCP: !modelConfig.enableMCP })
  }

  // Calculate dynamic change indicators based on actual data
  const getChangeIndicator = (current: number, type: string) => {
    if (current === 0) return { change: '', type: 'neutral' as const }
    if (type === 'success') return { change: current >= 90 ? '+' : '', type: current >= 90 ? 'positive' as const : 'neutral' as const }
    return { change: '+', type: 'positive' as const }
  }

  const cards = [
    {
      id: 'docs',
      label: 'Documents Processed',
      value: stats.documentsProcessed.toLocaleString(),
      icon: FileText,
      ...getChangeIndicator(stats.documentsProcessed, 'docs'),
    },
    {
      id: 'time',
      label: 'Avg. Processing Time',
      value: stats.avgProcessingTime > 0 ? `${stats.avgProcessingTime}s` : '-',
      icon: Clock,
      change: stats.avgProcessingTime > 0 && stats.avgProcessingTime < 30 ? '-' : '',
      changeType: 'positive' as const,
    },
    {
      id: 'injections',
      label: 'Semantic Injections',
      value: stats.semanticInjections > 0 ? stats.semanticInjections.toLocaleString() : (preview?.semantic_suggestions?.length || 0).toString(),
      icon: Zap,
      ...getChangeIndicator(stats.semanticInjections || preview?.semantic_suggestions?.length || 0, 'injections'),
    },
    {
      id: 'success',
      label: 'Success Rate',
      value: stats.documentsProcessed > 0 ? `${stats.successRate}%` : (generatedHTML ? '100%' : '-'),
      icon: TrendingUp,
      change: '',
      changeType: 'neutral' as const,
    },
  ]

  const hasStats = stats.documentsProcessed > 0

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <Button
          variant={modelConfig.enableMCP ? "default" : "outline"}
          size="sm"
          className={`h-7 text-xs ${modelConfig.enableMCP ? 'bg-cyan-600 hover:bg-cyan-700 text-white' : 'text-muted-foreground hover:text-foreground'}`}
          onClick={handleToggleMCP}
        >
          <Sparkles className="w-3 h-3 mr-1" />
          MCP {modelConfig.enableMCP ? 'ON' : 'OFF'}
        </Button>
        {hasStats && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs text-muted-foreground hover:text-foreground"
            onClick={handleResetStats}
          >
            <RotateCcw className="w-3 h-3 mr-1" />
            Reset Stats
          </Button>
        )}
      </div>
      <div className="grid grid-cols-4 gap-4">
      <AnimatePresence mode="popLayout">
        {cards.map((card, index) => {
          const Icon = card.icon
          return (
            <motion.div
              key={`${card.id}-${card.value}`}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ delay: index * 0.05, duration: 0.2 }}
            >
              <Card className="p-4 bg-card/50 border-border hover:border-cyan-500/30 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="p-2 rounded-lg bg-cyan-500/10">
                    <Icon className="w-5 h-5 text-cyan-400" />
                  </div>
                  {card.change && (
                    <motion.span 
                      key={`change-${card.value}`}
                      initial={{ scale: 1.2 }}
                      animate={{ scale: 1 }}
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        card.changeType === 'positive' 
                          ? 'bg-emerald-500/10 text-emerald-400' 
                          : 'bg-red-500/10 text-red-400'
                      }`}
                    >
                      {card.change}
                    </motion.span>
                  )}
                </div>
                <div className="mt-3">
                  <motion.p 
                    key={`value-${card.value}`}
                    initial={{ opacity: 0.5 }}
                    animate={{ opacity: 1 }}
                    className="text-2xl font-bold text-foreground"
                  >
                    {card.value}
                  </motion.p>
                  <p className="text-sm text-muted-foreground">{card.label}</p>
                </div>
              </Card>
            </motion.div>
          )
        })}
      </AnimatePresence>
      </div>
    </div>
  )
}
