import { BarChart3, FileText, Clock, Zap, TrendingUp, Sparkles, RotateCcw } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useStore } from '@/store/useStore'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts'

export function AnalyticsPage() {
  const { stats, preview, modelConfig, setModelConfig, resetStats } = useStore()
  
  const hasData = stats.documentsProcessed > 0

  const handleToggleMCP = () => {
    setModelConfig({ ...modelConfig, enableMCP: !modelConfig.enableMCP })
  }

  // Mock historical data based on current stats
  const processingData = [
    { name: 'Mon', docs: Math.max(0, stats.documentsProcessed - 4), time: stats.avgProcessingTime + 5 },
    { name: 'Tue', docs: Math.max(0, stats.documentsProcessed - 3), time: stats.avgProcessingTime + 3 },
    { name: 'Wed', docs: Math.max(0, stats.documentsProcessed - 2), time: stats.avgProcessingTime + 2 },
    { name: 'Thu', docs: Math.max(0, stats.documentsProcessed - 1), time: stats.avgProcessingTime + 1 },
    { name: 'Fri', docs: stats.documentsProcessed, time: stats.avgProcessingTime },
  ]

  const componentData = [
    { name: 'Charts', value: Math.floor(stats.semanticInjections * 0.4) || 0, color: '#06b6d4' },
    { name: 'Quizzes', value: Math.floor(stats.semanticInjections * 0.2) || 0, color: '#8b5cf6' },
    { name: 'Code', value: Math.floor(stats.semanticInjections * 0.25) || 0, color: '#10b981' },
    { name: 'Other', value: Math.floor(stats.semanticInjections * 0.15) || 0, color: '#f59e0b' },
  ]

  const statCards = [
    { label: 'Documents Processed', value: stats.documentsProcessed, icon: FileText, color: 'cyan' },
    { label: 'Avg. Processing Time', value: `${stats.avgProcessingTime}s`, icon: Clock, color: 'purple' },
    { label: 'Semantic Injections', value: stats.semanticInjections, icon: Zap, color: 'emerald' },
    { label: 'Success Rate', value: `${stats.successRate}%`, icon: TrendingUp, color: 'amber' },
  ]

  if (!hasData) {
    return (
      <div className="flex-1 p-6 overflow-auto grid-pattern">
        <div className="space-y-6">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold text-foreground">Analytics</h2>
              <p className="text-muted-foreground">Processing insights and statistics</p>
            </div>
            <Button
              variant={modelConfig.enableMCP ? "default" : "outline"}
              size="sm"
              className={`${modelConfig.enableMCP ? 'bg-cyan-600 hover:bg-cyan-700 text-white' : ''}`}
              onClick={handleToggleMCP}
            >
              <Sparkles className="w-4 h-4 mr-1" />
              MCP {modelConfig.enableMCP ? 'ON' : 'OFF'}
            </Button>
          </div>

          <Card className="p-12 bg-card/50 border-border border-dashed">
            <div className="flex flex-col items-center justify-center text-center">
              <div className="p-4 rounded-full bg-cyan-500/10 mb-4">
                <BarChart3 className="w-12 h-12 text-cyan-400" />
              </div>
              <h3 className="text-lg font-medium text-foreground mb-2">No analytics data yet</h3>
              <p className="text-muted-foreground max-w-md">
                Analytics will be available after you process some documents. Charts and statistics will appear here in real-time.
              </p>
            </div>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 p-6 overflow-auto grid-pattern">
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-foreground">Analytics</h2>
            <p className="text-muted-foreground">Processing insights and statistics</p>
          </div>
          <div className="flex gap-2">
            <Button
              variant={modelConfig.enableMCP ? "default" : "outline"}
              size="sm"
              className={`${modelConfig.enableMCP ? 'bg-cyan-600 hover:bg-cyan-700 text-white' : ''}`}
              onClick={handleToggleMCP}
            >
              <Sparkles className="w-4 h-4 mr-1" />
              MCP {modelConfig.enableMCP ? 'ON' : 'OFF'}
            </Button>
            {hasData && (
              <Button
                variant="outline"
                size="sm"
                onClick={resetStats}
              >
                <RotateCcw className="w-4 h-4 mr-1" />
                Reset
              </Button>
            )}
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-4 gap-4">
          {statCards.map((card) => {
            const Icon = card.icon
            return (
              <Card key={card.label} className="p-4 bg-card/50 border-border">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg bg-${card.color}-500/10`}>
                    <Icon className={`w-5 h-5 text-${card.color}-400`} />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{card.value}</p>
                    <p className="text-xs text-muted-foreground">{card.label}</p>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-2 gap-6">
          {/* Documents Over Time */}
          <Card className="p-4 bg-card/50 border-border">
            <h3 className="font-medium text-foreground mb-4">Documents Processed</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={processingData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                  labelStyle={{ color: '#f3f4f6' }}
                />
                <Bar dataKey="docs" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Processing Time Trend */}
          <Card className="p-4 bg-card/50 border-border">
            <h3 className="font-medium text-foreground mb-4">Processing Time (seconds)</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={processingData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                  labelStyle={{ color: '#f3f4f6' }}
                />
                <Line type="monotone" dataKey="time" stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6' }} />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          {/* Component Distribution */}
          <Card className="p-4 bg-card/50 border-border">
            <h3 className="font-medium text-foreground mb-4">Semantic Components</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={componentData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {componentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex justify-center gap-4 mt-2">
              {componentData.map((item) => (
                <div key={item.name} className="flex items-center gap-1 text-xs">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-muted-foreground">{item.name}</span>
                </div>
              ))}
            </div>
          </Card>

          {/* Recent Activity */}
          <Card className="p-4 bg-card/50 border-border">
            <h3 className="font-medium text-foreground mb-4">Summary</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-2 rounded bg-secondary/50">
                <span className="text-sm text-muted-foreground">Total Documents</span>
                <span className="text-sm font-medium text-foreground">{stats.documentsProcessed}</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-secondary/50">
                <span className="text-sm text-muted-foreground">Components Injected</span>
                <span className="text-sm font-medium text-foreground">{stats.semanticInjections}</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-secondary/50">
                <span className="text-sm text-muted-foreground">Avg. Components/Doc</span>
                <span className="text-sm font-medium text-foreground">
                  {stats.documentsProcessed > 0 ? (stats.semanticInjections / stats.documentsProcessed).toFixed(1) : 0}
                </span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-secondary/50">
                <span className="text-sm text-muted-foreground">Current Suggestions</span>
                <span className="text-sm font-medium text-foreground">{preview?.semantic_suggestions?.length || 0}</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
