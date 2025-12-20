import { FileText, FolderOpen } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useStore } from '@/store/useStore'

export function ProjectsPage() {
  const { setCurrentPage } = useStore()

  return (
    <div className="flex-1 p-6 overflow-auto grid-pattern">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-foreground">Projects</h2>
            <p className="text-muted-foreground">Manage your converted documents</p>
          </div>
          <Button variant="glow" onClick={() => setCurrentPage('upload')}>New Project</Button>
        </div>

        <Card className="p-12 bg-card/50 border-border border-dashed">
          <div className="flex flex-col items-center justify-center text-center">
            <div className="p-4 rounded-full bg-cyan-500/10 mb-4">
              <FolderOpen className="w-12 h-12 text-cyan-400" />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">No projects yet</h3>
            <p className="text-muted-foreground mb-4 max-w-md">
              Upload a PDF to get started. Your converted documents will appear here.
            </p>
            <Button variant="glow" onClick={() => setCurrentPage('upload')}>
              <FileText className="w-4 h-4 mr-2" />
              Upload PDF
            </Button>
          </div>
        </Card>
      </div>
    </div>
  )
}
