import { History } from 'lucide-react'
import { Card } from '@/components/ui/card'

export function HistoryPage() {
  return (
    <div className="flex-1 p-6 overflow-auto grid-pattern">
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-foreground">History</h2>
          <p className="text-muted-foreground">Recent activity and audit log</p>
        </div>

        <Card className="p-12 bg-card/50 border-border border-dashed">
          <div className="flex flex-col items-center justify-center text-center">
            <div className="p-4 rounded-full bg-cyan-500/10 mb-4">
              <History className="w-12 h-12 text-cyan-400" />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">No activity yet</h3>
            <p className="text-muted-foreground max-w-md">
              Your processing history will appear here after you upload and convert PDFs.
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
}
