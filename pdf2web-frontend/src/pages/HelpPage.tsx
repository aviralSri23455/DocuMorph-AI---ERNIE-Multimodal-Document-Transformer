import { Book, MessageCircle, Github, ExternalLink, Zap, Shield, Code, Palette } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const features = [
  { icon: Zap, title: 'AI-Powered Extraction', desc: 'ERNIE 3.5 & DeepSeek for intelligent content analysis' },
  { icon: Shield, title: 'Privacy First', desc: 'Secure mode with local PII redaction' },
  { icon: Code, title: 'Semantic Injection', desc: 'Auto-convert tables to charts, add quizzes' },
  { icon: Palette, title: 'Theme System', desc: '5 built-in themes with AI suggestions' },
]

const quickStart = [
  { step: 1, title: 'Upload PDF', desc: 'Drag and drop or click to browse' },
  { step: 2, title: 'Review Blocks', desc: 'Edit content and approve PII redactions' },
  { step: 3, title: 'Select Theme', desc: 'Choose output theme or use AI suggestion' },
  { step: 4, title: 'Generate HTML', desc: 'Click Generate to create interactive HTML' },
  { step: 5, title: 'Export/Deploy', desc: 'Download or deploy to Netlify/GitHub' },
]

export function HelpPage() {
  return (
    <div className="flex-1 p-6 overflow-auto grid-pattern">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Help & Documentation</h2>
          <p className="text-muted-foreground">Learn how to use DocuMorph AI</p>
        </div>

        {/* Quick Start */}
        <Card className="bg-card/50 border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Book className="w-5 h-5 text-cyan-400" />
              Quick Start Guide
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-5 gap-4">
              {quickStart.map((item) => (
                <div key={item.step} className="text-center">
                  <div className="w-10 h-10 rounded-full bg-cyan-500/10 text-cyan-400 flex items-center justify-center mx-auto mb-2 font-bold">
                    {item.step}
                  </div>
                  <h4 className="font-medium text-foreground text-sm">{item.title}</h4>
                  <p className="text-xs text-muted-foreground mt-1">{item.desc}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Features */}
        <Card className="bg-card/50 border-border">
          <CardHeader>
            <CardTitle className="text-lg">Key Features</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {features.map((feature) => {
                const Icon = feature.icon
                return (
                  <div key={feature.title} className="flex items-start gap-3 p-3 rounded-lg bg-secondary/30">
                    <div className="p-2 rounded-lg bg-cyan-500/10">
                      <Icon className="w-5 h-5 text-cyan-400" />
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground">{feature.title}</h4>
                      <p className="text-sm text-muted-foreground">{feature.desc}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Links */}
        <div className="grid grid-cols-2 gap-4">
          <Button variant="outline" className="h-auto py-4 justify-start gap-3">
            <Github className="w-5 h-5" />
            <div className="text-left">
              <p className="font-medium">GitHub Repository</p>
              <p className="text-xs text-muted-foreground">View source code</p>
            </div>
            <ExternalLink className="w-4 h-4 ml-auto" />
          </Button>
          <Button variant="outline" className="h-auto py-4 justify-start gap-3">
            <MessageCircle className="w-5 h-5" />
            <div className="text-left">
              <p className="font-medium">Get Support</p>
              <p className="text-xs text-muted-foreground">Contact us for help</p>
            </div>
            <ExternalLink className="w-4 h-4 ml-auto" />
          </Button>
        </div>
      </div>
    </div>
  )
}
