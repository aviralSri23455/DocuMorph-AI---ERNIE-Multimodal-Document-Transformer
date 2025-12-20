import { Sun, Moon, Briefcase, GraduationCap, Minus } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { useStore, Theme } from '@/store/useStore'
import { cn } from '@/lib/utils'

const themes: { id: Theme; label: string; icon: typeof Sun; colors: string[] }[] = [
  { id: 'light', label: 'Light', icon: Sun, colors: ['#ffffff', '#f8fafc', '#e2e8f0'] },
  { id: 'dark', label: 'Dark', icon: Moon, colors: ['#0f172a', '#1e293b', '#334155'] },
  { id: 'professional', label: 'Professional', icon: Briefcase, colors: ['#1e3a5f', '#2563eb', '#60a5fa'] },
  { id: 'academic', label: 'Academic', icon: GraduationCap, colors: ['#fef3c7', '#f59e0b', '#92400e'] },
  { id: 'minimal', label: 'Minimal', icon: Minus, colors: ['#fafafa', '#a1a1aa', '#27272a'] },
]

export function ThemeSelector() {
  const { selectedTheme, setSelectedTheme, preview } = useStore()

  return (
    <Card className="p-4 bg-card/50 border-border">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-medium text-foreground">Output Theme</h3>
        {preview?.theme_analysis && (
          <span className="text-xs px-2 py-1 rounded bg-cyan-500/10 text-cyan-400">
            Suggested: {preview.theme_analysis.suggested_theme}
          </span>
        )}
      </div>
      <div className="grid grid-cols-5 gap-2">
        {themes.map((theme) => {
          const Icon = theme.icon
          const isSelected = selectedTheme === theme.id
          return (
            <button
              key={theme.id}
              onClick={() => setSelectedTheme(theme.id)}
              className={cn(
                "p-3 rounded-lg border transition-all flex flex-col items-center gap-2",
                isSelected
                  ? "border-cyan-500 bg-cyan-500/10 ring-2 ring-cyan-500/30"
                  : "border-border hover:border-cyan-500/50"
              )}
            >
              <div className="flex gap-0.5">
                {theme.colors.map((color, i) => (
                  <div
                    key={i}
                    className="w-3 h-3 rounded-sm"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
              <Icon className={cn(
                "w-4 h-4",
                isSelected ? "text-cyan-400" : "text-muted-foreground"
              )} />
              <span className={cn(
                "text-xs",
                isSelected ? "text-cyan-400" : "text-muted-foreground"
              )}>
                {theme.label}
              </span>
            </button>
          )
        })}
      </div>
    </Card>
  )
}
