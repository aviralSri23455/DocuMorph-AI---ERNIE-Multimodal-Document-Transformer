import { Upload, Eye, Edit3, Code, Download } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { useStore, ProcessingStep } from '@/store/useStore'
import { cn } from '@/lib/utils'
import { motion } from 'framer-motion'

const steps: { id: ProcessingStep; label: string; sublabel: string; icon: typeof Upload }[] = [
  { id: 'upload', label: 'Upload', sublabel: 'PDF Input', icon: Upload },
  { id: 'extract', label: 'Extract', sublabel: 'OCR Processing', icon: Eye },
  { id: 'codesign', label: 'Co-Design', sublabel: 'Human Review', icon: Edit3 },
  { id: 'generate', label: 'Generate', sublabel: 'AI Transform', icon: Code },
  { id: 'output', label: 'Output', sublabel: 'HTML Export', icon: Download },
]

const stepOrder: ProcessingStep[] = ['upload', 'extract', 'codesign', 'generate', 'output']

export function ProcessingPipeline() {
  const { currentStep } = useStore()
  const currentIndex = stepOrder.indexOf(currentStep)

  return (
    <Card className="p-6 bg-card/50 border-border">
      <div className="flex items-center gap-2 mb-6">
        <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
        <h3 className="font-medium text-foreground">Processing Pipeline</h3>
      </div>

      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const Icon = step.icon
          const isActive = step.id === currentStep
          const isCompleted = index < currentIndex
          const isPending = index > currentIndex

          return (
            <div key={step.id} className="flex items-center">
              <div className="flex flex-col items-center">
                <motion.div
                  initial={false}
                  animate={{
                    scale: isActive ? 1.1 : 1,
                    boxShadow: isActive ? '0 0 20px rgba(6, 182, 212, 0.5)' : 'none',
                  }}
                  className={cn(
                    "w-12 h-12 rounded-xl flex items-center justify-center transition-colors",
                    isActive && "bg-cyan-500 text-white",
                    isCompleted && "bg-cyan-500/20 text-cyan-400 border border-cyan-500/50",
                    isPending && "bg-secondary text-muted-foreground"
                  )}
                >
                  <Icon className="w-5 h-5" />
                </motion.div>
                <p className={cn(
                  "text-sm font-medium mt-2",
                  isActive ? "text-cyan-400" : isCompleted ? "text-foreground" : "text-muted-foreground"
                )}>
                  {step.label}
                </p>
                <p className="text-xs text-muted-foreground">{step.sublabel}</p>
              </div>

              {index < steps.length - 1 && (
                <div className={cn(
                  "w-12 h-0.5 mx-2 mt-[-24px]",
                  index < currentIndex ? "bg-cyan-500" : "bg-border"
                )} />
              )}
            </div>
          )
        })}
      </div>
    </Card>
  )
}
