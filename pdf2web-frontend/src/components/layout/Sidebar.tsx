import { Upload, FolderOpen, History, BarChart3, Settings, HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useStore } from '@/store/useStore'

const navItems = [
  { id: 'upload', label: 'Upload', icon: Upload },
  { id: 'projects', label: 'Projects', icon: FolderOpen },
  { id: 'history', label: 'History', icon: History },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'settings', label: 'Settings', icon: Settings },
  { id: 'help', label: 'Help', icon: HelpCircle },
] as const

export function Sidebar() {
  const { currentPage, setCurrentPage, systemReady } = useStore()

  return (
    <aside className="w-56 bg-card border-r border-border flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-teal-500 flex items-center justify-center shadow-lg shadow-cyan-500/30">
            <span className="text-white font-bold text-lg">P</span>
          </div>
          <div>
            <h1 className="font-bold text-foreground">DocuMorph</h1>
            <p className="text-xs text-muted-foreground">AI</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = currentPage === item.id
          return (
            <button
              key={item.id}
              onClick={() => setCurrentPage(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all",
                isActive
                  ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary"
              )}
            >
              <Icon className={cn("w-5 h-5", isActive && "text-cyan-400")} />
              {item.label}
            </button>
          )
        })}
      </nav>

      {/* System Status */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-2">
          <div className={cn(
            "w-2 h-2 rounded-full",
            systemReady ? "bg-emerald-500 animate-pulse" : "bg-yellow-500"
          )} />
          <span className="text-sm text-muted-foreground">
            {systemReady ? "System Ready" : "Connecting..."}
          </span>
        </div>
      </div>
    </aside>
  )
}
