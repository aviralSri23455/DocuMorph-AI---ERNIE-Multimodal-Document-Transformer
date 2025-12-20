import { BarChart3, PieChart, LineChart, HelpCircle, Code, Clock, MapPin, Play, Table } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useStore, ChartType } from '@/store/useStore'
import { cn } from '@/lib/utils'

const suggestionIcons: Record<string, typeof BarChart3> = {
  chart_bar: BarChart3,
  chart_pie: PieChart,
  chart_line: LineChart,
  quiz: HelpCircle,
  code_block: Code,
  code_executable: Play,
  timeline: Clock,
  map: MapPin,
}

type ChartOption = 'keep_table' | 'convert_to_chart' | 'hybrid'

const chartTypeOptions: { type: ChartType; icon: typeof BarChart3; label: string }[] = [
  { type: 'bar', icon: BarChart3, label: 'Bar' },
  { type: 'line', icon: LineChart, label: 'Line' },
  { type: 'pie', icon: PieChart, label: 'Pie' },
]

export function SemanticSuggestions() {
  const { preview, semanticSelections, updateChartConversion, updateChartType, toggleQuizBlock, toggleCodeBlock, toggleTimelineBlock, toggleMapBlock } = useStore()

  if (!preview?.semantic_suggestions.length) {
    return null
  }

  const isChartSuggestion = (s: string) => s.startsWith('chart_')
  const isTimeline = (s: string) => s === 'timeline'
  const isMap = (s: string) => s === 'map'

  return (
    <Card className="p-4 bg-card/50 border-border">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-medium text-foreground">AI Suggestions</h3>
        <span className="text-xs text-muted-foreground">{preview.semantic_suggestions.length} suggestions</span>
      </div>
      <div className="space-y-3">
        {preview.semantic_suggestions.map((suggestion) => {
          const Icon = suggestionIcons[suggestion.suggestion] || BarChart3
          const confidence = Math.round(suggestion.confidence * 100)
          const isChart = isChartSuggestion(suggestion.suggestion)
          const isQuiz = suggestion.suggestion === 'quiz'
          const isCodeExec = suggestion.suggestion === 'code_executable'
          
          return (
            <div key={`${suggestion.block_id}-${suggestion.suggestion}`} className="p-3 rounded-lg border border-border bg-secondary/30 hover:border-cyan-500/30 transition-colors">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-cyan-500/10">
                  <Icon className="w-4 h-4 text-cyan-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-foreground capitalize">{suggestion.suggestion.replace(/_/g, ' ')}</span>
                    <span className={cn("text-xs px-1.5 py-0.5 rounded", confidence >= 80 ? "bg-emerald-500/10 text-emerald-400" : confidence >= 60 ? "bg-yellow-500/10 text-yellow-400" : "bg-red-500/10 text-red-400")}>{confidence}%</span>
                    {suggestion.config?.source === 'vision' && <span className="text-xs px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400">Vision</span>}
                  </div>
                  <p className="text-xs text-muted-foreground">Block: {suggestion.block_id}</p>
                </div>
              </div>

              {/* Chart conversion options */}
              {isChart && (
                <div className="mt-3 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Convert:</span>
                    {(['keep_table', 'convert_to_chart', 'hybrid'] as ChartOption[]).map((opt) => (
                      <button key={opt} onClick={() => updateChartConversion(suggestion.block_id, opt)} className={cn("text-xs px-2 py-1 rounded border transition-colors", semanticSelections.chartConversions[suggestion.block_id] === opt ? "border-cyan-500 bg-cyan-500/10 text-cyan-400" : "border-border text-muted-foreground hover:border-cyan-500/50")}>
                        {opt === 'keep_table' && <><Table className="w-3 h-3 inline mr-1" />Table</>}
                        {opt === 'convert_to_chart' && <><BarChart3 className="w-3 h-3 inline mr-1" />Chart</>}
                        {opt === 'hybrid' && 'Both'}
                      </button>
                    ))}
                  </div>
                  {/* Chart type selection (bar/line/pie) */}
                  {(semanticSelections.chartConversions[suggestion.block_id] === 'convert_to_chart' || semanticSelections.chartConversions[suggestion.block_id] === 'hybrid') && (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground">Type:</span>
                      {chartTypeOptions.map(({ type, icon: ChartIcon, label }) => (
                        <button key={type} onClick={() => updateChartType(suggestion.block_id, type)} className={cn("text-xs px-2 py-1 rounded border transition-colors flex items-center gap-1", semanticSelections.chartTypes[suggestion.block_id] === type ? "border-purple-500 bg-purple-500/10 text-purple-400" : "border-border text-muted-foreground hover:border-purple-500/50")}>
                          <ChartIcon className="w-3 h-3" />{label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Quiz toggle */}
              {isQuiz && (
                <div className="mt-3">
                  <Button size="sm" variant={semanticSelections.quizEnabledBlocks.includes(suggestion.block_id) ? "default" : "outline"} className="h-7 text-xs" onClick={() => toggleQuizBlock(suggestion.block_id)}>
                    {semanticSelections.quizEnabledBlocks.includes(suggestion.block_id) ? '✓ Quiz Enabled' : 'Enable Quiz'}
                  </Button>
                </div>
              )}

              {/* Code execution toggle */}
              {isCodeExec && (
                <div className="mt-3">
                  <Button size="sm" variant={semanticSelections.codeExecutionBlocks.includes(suggestion.block_id) ? "default" : "outline"} className="h-7 text-xs" onClick={() => toggleCodeBlock(suggestion.block_id)}>
                    {semanticSelections.codeExecutionBlocks.includes(suggestion.block_id) ? '✓ Execution Enabled' : 'Enable Execution'}
                  </Button>
                </div>
              )}

              {/* Timeline toggle */}
              {isTimeline(suggestion.suggestion) && (
                <div className="mt-3">
                  <Button size="sm" variant={semanticSelections.timelineBlocks.includes(suggestion.block_id) ? "default" : "outline"} className="h-7 text-xs" onClick={() => toggleTimelineBlock(suggestion.block_id)}>
                    {semanticSelections.timelineBlocks.includes(suggestion.block_id) ? '✓ Timeline Enabled' : 'Enable Timeline'}
                  </Button>
                </div>
              )}

              {/* Map toggle */}
              {isMap(suggestion.suggestion) && (
                <div className="mt-3">
                  <Button size="sm" variant={semanticSelections.mapBlocks.includes(suggestion.block_id) ? "default" : "outline"} className="h-7 text-xs" onClick={() => toggleMapBlock(suggestion.block_id)}>
                    {semanticSelections.mapBlocks.includes(suggestion.block_id) ? '✓ Map Enabled' : 'Enable Map'}
                  </Button>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </Card>
  )
}
