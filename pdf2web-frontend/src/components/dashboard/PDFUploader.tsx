import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Loader2, RefreshCw } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useStore } from '@/store/useStore'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'

export function PDFUploader() {
  const { uploadPDF, isUploading, currentDocument, error, reset } = useStore()

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file && file.type === 'application/pdf') {
      uploadPDF(file)
    }
  }, [uploadPDF])

  const handleNewUpload = () => {
    reset()
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: isUploading,
  })

  return (
    <Card className="p-6 bg-card/50 border-border">
      <div
        {...getRootProps()}
        className={cn(
          "relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all",
          isDragActive 
            ? "border-cyan-500 bg-cyan-500/5" 
            : "border-border hover:border-cyan-500/50 hover:bg-cyan-500/5",
          isUploading && "pointer-events-none opacity-50"
        )}
      >
        <input {...getInputProps()} />
        
        {/* Corner brackets */}
        <div className="absolute top-3 left-3 w-4 h-4 border-l-2 border-t-2 border-cyan-500/50" />
        <div className="absolute top-3 right-3 w-4 h-4 border-r-2 border-t-2 border-cyan-500/50" />
        <div className="absolute bottom-3 left-3 w-4 h-4 border-l-2 border-b-2 border-cyan-500/50" />
        <div className="absolute bottom-3 right-3 w-4 h-4 border-r-2 border-b-2 border-cyan-500/50" />

        <AnimatePresence mode="wait">
          {isUploading ? (
            <motion.div
              key="uploading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center"
            >
              <Loader2 className="w-12 h-12 text-cyan-400 animate-spin mb-4" />
              <p className="text-foreground font-medium">Processing PDF...</p>
              <p className="text-sm text-muted-foreground mt-1">Extracting content and analyzing structure</p>
            </motion.div>
          ) : currentDocument ? (
            <motion.div
              key="uploaded"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center"
            >
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center mb-4">
                <FileText className="w-6 h-6 text-emerald-400" />
              </div>
              <p className="text-foreground font-medium">{currentDocument.filename}</p>
              <p className="text-sm text-muted-foreground mt-1">
                {currentDocument.total_pages} pages • {currentDocument.processing_mode} mode
              </p>
              <Button
                variant="outline"
                size="sm"
                className="mt-4 hover:border-cyan-500/50 hover:bg-cyan-500/10"
                onClick={(e) => {
                  e.stopPropagation()
                  handleNewUpload()
                }}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                New Upload
              </Button>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center"
            >
              <div className="w-12 h-12 rounded-xl bg-secondary flex items-center justify-center mb-4">
                <Upload className="w-6 h-6 text-muted-foreground" />
              </div>
              <p className="text-foreground font-medium">
                {isDragActive ? "Drop your PDF here" : "Drag & drop your PDF"}
              </p>
              <p className="text-sm text-muted-foreground mt-1">or click to browse files</p>
            </motion.div>
          )}
        </AnimatePresence>

        {error && (
          <p className="text-sm text-red-400 mt-4">{error}</p>
        )}
      </div>
    </Card>
  )
}
