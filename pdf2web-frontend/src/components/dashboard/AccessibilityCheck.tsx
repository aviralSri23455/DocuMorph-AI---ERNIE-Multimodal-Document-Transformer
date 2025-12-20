import { useState } from 'react'
import { Accessibility, CheckCircle, AlertTriangle, XCircle, Loader2 } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Progress } from '@/components/ui/progress'
import { useStore } from '@/store/useStore'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

interface AccessibilityIssue {
  type: 'error' | 'warning' | 'info'
  message: string
  element?: string
  suggestion?: string
}

interface AccessibilityResult {
  passed: boolean
  score: number
  level: string
  issues: AccessibilityIssue[]
}

export function AccessibilityCheck() {
  const { generatedHTML, currentDocument } = useStore()
  const [wcagLevel, setWcagLevel] = useState('AA')
  const [isChecking, setIsChecking] = useState(false)
  const [result, setResult] = useState<AccessibilityResult | null>(null)

  const runCheck = async () => {
    if (!generatedHTML || !currentDocument) return
    setIsChecking(true)
    try {
      const data = await api.checkAccessibility(currentDocument.document_id, wcagLevel)
      setResult(data)
    } catch (err) {
      console.error('Accessibility check failed:', err)
    } finally {
      setIsChecking(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-emerald-400'
    if (score >= 70) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getIssueIcon = (type: string) => {
    switch (type) {
      case 'error': return <XCircle className="w-4 h-4 text-red-400" />
      case 'warning': return <AlertTriangle className="w-4 h-4 text-yellow-400" />
      default: return <CheckCircle className="w-4 h-4 text-cyan-400" />
    }
  }

  return (
    <Card className="p-4 bg-card/50 border-border">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Accessibility className="w-5 h-5 text-cyan-400" />
          <h3 className="font-medium text-foreground">Accessibility Check</h3>
        </div>
        <Select value={wcagLevel} onValueChange={setWcagLevel}>
          <SelectTrigger className="w-24 h-8">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="A">WCAG A</SelectItem>
            <SelectItem value="AA">WCAG AA</SelectItem>
            <SelectItem value="AAA">WCAG AAA</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {!generatedHTML ? (
        <p className="text-sm text-muted-foreground text-center py-4">Generate HTML first to check accessibility</p>
      ) : (
        <>
          <Button onClick={runCheck} disabled={isChecking} className="w-full mb-4" variant="outline">
            {isChecking ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Accessibility className="w-4 h-4 mr-2" />}
            {isChecking ? 'Checking...' : 'Run WCAG Check'}
          </Button>

          {result && (
            <div className="space-y-4">
              {/* Score */}
              <div className="text-center p-4 rounded-lg bg-secondary">
                <p className={cn("text-4xl font-bold", getScoreColor(result.score))}>{result.score}</p>
                <p className="text-sm text-muted-foreground">Accessibility Score</p>
                <Progress value={result.score} className="mt-2" />
              </div>

              {/* Status */}
              <div className={cn(
                "flex items-center gap-2 p-3 rounded-lg",
                result.passed ? "bg-emerald-500/10" : "bg-red-500/10"
              )}>
                {result.passed ? (
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-400" />
                )}
                <span className={result.passed ? "text-emerald-400" : "text-red-400"}>
                  {result.passed ? `Passes WCAG ${result.level}` : `Fails WCAG ${result.level}`}
                </span>
              </div>

              {/* Issues */}
              {result.issues.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium text-foreground">Issues ({result.issues.length})</p>
                  <div className="max-h-40 overflow-auto space-y-2">
                    {result.issues.map((issue, i) => (
                      <div key={i} className="p-2 rounded-lg bg-secondary/50 text-sm">
                        <div className="flex items-start gap-2">
                          {getIssueIcon(issue.type)}
                          <div>
                            <p className="text-foreground">{issue.message}</p>
                            {issue.suggestion && (
                              <p className="text-xs text-muted-foreground mt-1">💡 {issue.suggestion}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </Card>
  )
}
