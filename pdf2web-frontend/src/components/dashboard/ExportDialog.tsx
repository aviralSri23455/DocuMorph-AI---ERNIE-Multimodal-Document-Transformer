import { useState } from 'react'
import { Download, Globe, Github, Loader2, Cloud, FileText, Triangle } from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useStore } from '@/store/useStore'
import { api } from '@/lib/api'

interface ExportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function ExportDialog({ open, onOpenChange }: ExportDialogProps) {
  const { currentDocument } = useStore()
  const [isExporting, setIsExporting] = useState(false)
  const [netlifyToken, setNetlifyToken] = useState('')
  const [siteName, setSiteName] = useState('')
  const [githubRepo, setGithubRepo] = useState('')
  const [githubToken, setGithubToken] = useState('')
  const [vercelToken, setVercelToken] = useState('')
  const [vercelProject, setVercelProject] = useState('')
  const [awsAccessKey, setAwsAccessKey] = useState('')
  const [awsSecretKey, setAwsSecretKey] = useState('')
  const [s3Bucket, setS3Bucket] = useState('')
  const [s3Region, setS3Region] = useState('us-east-1')

  const handleDownloadZip = async () => {
    if (!currentDocument) return
    setIsExporting(true)
    try {
      await api.exportHTML(currentDocument.document_id)
      const blob = await api.downloadHTML(currentDocument.document_id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${currentDocument.filename.replace('.pdf', '')}.zip`
      a.click()
      URL.revokeObjectURL(url)
      onOpenChange(false)
    } catch (err) {
      console.error('Download failed:', err)
    } finally {
      setIsExporting(false)
    }
  }

  const handleDownloadHTML = async () => {
    if (!currentDocument) return
    setIsExporting(true)
    try {
      // Get raw HTML from store or fetch it
      const { generatedHTML } = useStore.getState()
      const htmlContent = generatedHTML || await api.previewHTML(currentDocument.document_id)
      const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${currentDocument.filename.replace('.pdf', '')}.html`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      onOpenChange(false)
    } catch (err) {
      console.error('HTML download failed:', err)
    } finally {
      setIsExporting(false)
    }
  }

  const handleNetlifyDeploy = async () => {
    if (!currentDocument || !netlifyToken || !siteName) return
    setIsExporting(true)
    try {
      await api.deployNetlify(currentDocument.document_id, netlifyToken, siteName)
      onOpenChange(false)
    } catch (err) {
      console.error('Netlify deploy failed:', err)
    } finally {
      setIsExporting(false)
    }
  }

  const handleGithubDeploy = async () => {
    if (!currentDocument || !githubRepo || !githubToken) return
    setIsExporting(true)
    try {
      await api.deployGitHub(currentDocument.document_id, githubRepo, githubToken)
      onOpenChange(false)
    } catch (err) {
      console.error('GitHub deploy failed:', err)
    } finally {
      setIsExporting(false)
    }
  }

  const handleMarkdownDownload = async () => {
    if (!currentDocument) return
    setIsExporting(true)
    try {
      await api.exportMarkdown(currentDocument.document_id)
      const blob = await api.downloadMarkdown(currentDocument.document_id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${currentDocument.filename.replace('.pdf', '')}.md`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Markdown download failed:', err)
    } finally {
      setIsExporting(false)
    }
  }

  const handleVercelDeploy = async () => {
    if (!currentDocument || !vercelToken) return
    setIsExporting(true)
    try {
      await api.deployVercel(currentDocument.document_id, vercelToken, vercelProject || undefined)
      onOpenChange(false)
    } catch (err) {
      console.error('Vercel deploy failed:', err)
    } finally {
      setIsExporting(false)
    }
  }

  const handleS3Deploy = async () => {
    if (!currentDocument || !awsAccessKey || !awsSecretKey || !s3Bucket) return
    setIsExporting(true)
    try {
      await api.deployS3(currentDocument.document_id, awsAccessKey, awsSecretKey, s3Bucket, s3Region)
      onOpenChange(false)
    } catch (err) {
      console.error('S3 deploy failed:', err)
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Export & Deploy</DialogTitle>
          <DialogDescription>Download or deploy your generated HTML</DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="download" className="mt-4">
          <TabsList className="grid w-full grid-cols-3 mb-2">
            <TabsTrigger value="download"><Download className="w-3 h-3 mr-1" />Download</TabsTrigger>
            <TabsTrigger value="netlify"><Globe className="w-3 h-3 mr-1" />Netlify</TabsTrigger>
            <TabsTrigger value="github"><Github className="w-3 h-3 mr-1" />GitHub</TabsTrigger>
          </TabsList>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="vercel"><Triangle className="w-3 h-3 mr-1" />Vercel</TabsTrigger>
            <TabsTrigger value="s3"><Cloud className="w-3 h-3 mr-1" />AWS S3</TabsTrigger>
          </TabsList>

          <TabsContent value="download" className="space-y-4 mt-4">
            <p className="text-sm text-muted-foreground">Download the generated files to your computer.</p>
            <div className="grid grid-cols-2 gap-2">
              <Button onClick={handleDownloadHTML} disabled={isExporting} variant="glow">
                {isExporting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
                HTML File
              </Button>
              <Button onClick={handleDownloadZip} disabled={isExporting} variant="outline">
                <Download className="w-4 h-4 mr-2" />
                ZIP Package
              </Button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Button onClick={handleMarkdownDownload} disabled={isExporting} variant="outline">
                <FileText className="w-4 h-4 mr-2" />
                Markdown
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="netlify" className="space-y-4 mt-4">
            <div>
              <label className="text-sm font-medium">Netlify Token</label>
              <input type="password" value={netlifyToken} onChange={(e) => setNetlifyToken(e.target.value)} placeholder="Enter Netlify access token" className="w-full mt-1 px-3 py-2 rounded-md bg-background border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-cyan-500" />
            </div>
            <div>
              <label className="text-sm font-medium">Site Name</label>
              <input type="text" value={siteName} onChange={(e) => setSiteName(e.target.value)} placeholder="my-pdf-site" className="w-full mt-1 px-3 py-2 rounded-md bg-background border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-cyan-500" />
            </div>
            <Button onClick={handleNetlifyDeploy} disabled={isExporting || !netlifyToken || !siteName} className="w-full" variant="glow">
              {isExporting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Globe className="w-4 h-4 mr-2" />}
              Deploy to Netlify
            </Button>
          </TabsContent>

          <TabsContent value="github" className="space-y-4 mt-4">
            <div>
              <label className="text-sm font-medium">Repository</label>
              <input type="text" value={githubRepo} onChange={(e) => setGithubRepo(e.target.value)} placeholder="username/repo" className="w-full mt-1 px-3 py-2 rounded-md bg-background border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-cyan-500" />
            </div>
            <div>
              <label className="text-sm font-medium">GitHub Token</label>
              <input type="password" value={githubToken} onChange={(e) => setGithubToken(e.target.value)} placeholder="ghp_..." className="w-full mt-1 px-3 py-2 rounded-md bg-background border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-cyan-500" />
            </div>
            <Button onClick={handleGithubDeploy} disabled={isExporting || !githubRepo || !githubToken} className="w-full" variant="glow">
              {isExporting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Github className="w-4 h-4 mr-2" />}
              Deploy to GitHub Pages
            </Button>
          </TabsContent>

          <TabsContent value="vercel" className="space-y-4 mt-4">
            <div>
              <label className="text-sm font-medium">Vercel Token</label>
              <input type="password" value={vercelToken} onChange={(e) => setVercelToken(e.target.value)} placeholder="Enter Vercel token" className="w-full mt-1 px-3 py-2 rounded-md bg-background border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-cyan-500" />
            </div>
            <div>
              <label className="text-sm font-medium">Project Name (optional)</label>
              <input type="text" value={vercelProject} onChange={(e) => setVercelProject(e.target.value)} placeholder="my-project" className="w-full mt-1 px-3 py-2 rounded-md bg-background border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-cyan-500" />
            </div>
            <Button onClick={handleVercelDeploy} disabled={isExporting || !vercelToken} className="w-full" variant="glow">
              {isExporting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Triangle className="w-4 h-4 mr-2" />}
              Deploy to Vercel
            </Button>
          </TabsContent>

          <TabsContent value="s3" className="space-y-3 mt-4">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-sm font-medium">AWS Access Key</label>
                <input type="password" value={awsAccessKey} onChange={(e) => setAwsAccessKey(e.target.value)} placeholder="AKIA..." className="w-full mt-1 px-3 py-2 rounded-md bg-background border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-cyan-500 text-sm" />
              </div>
              <div>
                <label className="text-sm font-medium">AWS Secret Key</label>
                <input type="password" value={awsSecretKey} onChange={(e) => setAwsSecretKey(e.target.value)} placeholder="Secret..." className="w-full mt-1 px-3 py-2 rounded-md bg-background border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-cyan-500 text-sm" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-sm font-medium">Bucket Name</label>
                <input type="text" value={s3Bucket} onChange={(e) => setS3Bucket(e.target.value)} placeholder="my-bucket" className="w-full mt-1 px-3 py-2 rounded-md bg-background border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-cyan-500 text-sm" />
              </div>
              <div>
                <label className="text-sm font-medium">Region</label>
                <input type="text" value={s3Region} onChange={(e) => setS3Region(e.target.value)} placeholder="us-east-1" className="w-full mt-1 px-3 py-2 rounded-md bg-background border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-cyan-500 text-sm" />
              </div>
            </div>
            <Button onClick={handleS3Deploy} disabled={isExporting || !awsAccessKey || !awsSecretKey || !s3Bucket} className="w-full" variant="glow">
              {isExporting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Cloud className="w-4 h-4 mr-2" />}
              Deploy to AWS S3
            </Button>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
