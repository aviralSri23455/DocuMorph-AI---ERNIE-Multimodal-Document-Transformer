import { useState } from 'react'
import { Save, Key, Globe, Shield, Palette } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

export function SettingsPage() {
  const [settings, setSettings] = useState({
    defaultSecureMode: true,
    enableVision: true,
    enableKnowledgeGraph: true,
    defaultTheme: 'dark',
    language: 'en',
    wcagLevel: 'AA',
  })

  return (
    <div className="flex-1 p-6 overflow-auto grid-pattern">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Settings</h2>
          <p className="text-muted-foreground">Configure your DocuMorph preferences</p>
        </div>

        {/* API Keys */}
        <Card className="bg-card/50 border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Key className="w-5 h-5 text-cyan-400" />
              API Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground">ERNIE API Key (Novita AI)</label>
              <input
                type="password"
                placeholder="sk_..."
                className="w-full mt-1 px-3 py-2 rounded-md bg-background border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-cyan-500"
                defaultValue=""
              />
              <p className="text-xs text-muted-foreground mt-1">$25 free credits available</p>
            </div>
            <div>
              <label className="text-sm font-medium text-foreground">DeepSeek API Key</label>
              <input
                type="password"
                placeholder="sk-..."
                className="w-full mt-1 px-3 py-2 rounded-md bg-background border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-cyan-500"
                defaultValue=""
              />
            </div>
          </CardContent>
        </Card>

        {/* Privacy Settings */}
        <Card className="bg-card/50 border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Shield className="w-5 h-5 text-cyan-400" />
              Privacy & Security
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-foreground">Default Secure Mode</p>
                <p className="text-sm text-muted-foreground">Enable PII redaction by default</p>
              </div>
              <Switch
                checked={settings.defaultSecureMode}
                onCheckedChange={(checked) => setSettings({ ...settings, defaultSecureMode: checked })}
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-foreground">Vision Analysis</p>
                <p className="text-sm text-muted-foreground">Use ERNIE Vision for enhanced detection</p>
              </div>
              <Switch
                checked={settings.enableVision}
                onCheckedChange={(checked) => setSettings({ ...settings, enableVision: checked })}
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-foreground">Knowledge Graph</p>
                <p className="text-sm text-muted-foreground">Generate knowledge graphs with DeepSeek</p>
              </div>
              <Switch
                checked={settings.enableKnowledgeGraph}
                onCheckedChange={(checked) => setSettings({ ...settings, enableKnowledgeGraph: checked })}
              />
            </div>
          </CardContent>
        </Card>

        {/* Appearance */}
        <Card className="bg-card/50 border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Palette className="w-5 h-5 text-cyan-400" />
              Appearance
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground">Default Output Theme</label>
              <Select
                value={settings.defaultTheme}
                onValueChange={(value) => setSettings({ ...settings, defaultTheme: value })}
              >
                <SelectTrigger className="w-full mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="light">Light</SelectItem>
                  <SelectItem value="dark">Dark</SelectItem>
                  <SelectItem value="professional">Professional</SelectItem>
                  <SelectItem value="academic">Academic</SelectItem>
                  <SelectItem value="minimal">Minimal</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Accessibility */}
        <Card className="bg-card/50 border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Globe className="w-5 h-5 text-cyan-400" />
              Accessibility & Language
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground">WCAG Compliance Level</label>
              <Select
                value={settings.wcagLevel}
                onValueChange={(value) => setSettings({ ...settings, wcagLevel: value })}
              >
                <SelectTrigger className="w-full mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="A">Level A</SelectItem>
                  <SelectItem value="AA">Level AA (Recommended)</SelectItem>
                  <SelectItem value="AAA">Level AAA</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium text-foreground">Default Language</label>
              <Select
                value={settings.language}
                onValueChange={(value) => setSettings({ ...settings, language: value })}
              >
                <SelectTrigger className="w-full mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="zh">中文</SelectItem>
                  <SelectItem value="es">Español</SelectItem>
                  <SelectItem value="fr">Français</SelectItem>
                  <SelectItem value="de">Deutsch</SelectItem>
                  <SelectItem value="ja">日本語</SelectItem>
                  <SelectItem value="ko">한국어</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Button variant="glow" className="w-full gap-2">
          <Save className="w-4 h-4" />
          Save Settings
        </Button>
      </div>
    </div>
  )
}
