import { useState } from 'react'
import { Shield, Mail, Phone, User, CreditCard, Hash, Globe, ChevronDown, ChevronUp } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { cn } from '@/lib/utils'

export interface PIIOptions {
  redact_emails: boolean
  redact_phones: boolean
  redact_names: boolean
  redact_ssn: boolean
  redact_credit_cards: boolean
}

export interface UploadConfig {
  mode: 'secure' | 'standard'
  language: string
  piiOptions: PIIOptions
}

interface UploadOptionsProps {
  config: UploadConfig
  onChange: (config: UploadConfig) => void
}

const languages = [
  { code: 'en', name: 'English' },
  { code: 'zh', name: '中文 (Chinese)' },
  { code: 'es', name: 'Español' },
  { code: 'fr', name: 'Français' },
  { code: 'de', name: 'Deutsch' },
  { code: 'ja', name: '日本語' },
  { code: 'ko', name: '한국어' },
]

const piiTypes = [
  { key: 'redact_emails', label: 'Email Addresses', icon: Mail, example: 'john@email.com → [EMAIL_REDACTED]' },
  { key: 'redact_phones', label: 'Phone Numbers', icon: Phone, example: '555-123-4567 → [PHONE_REDACTED]' },
  { key: 'redact_names', label: 'Person Names', icon: User, example: 'John Smith → [PERSON_REDACTED]' },
  { key: 'redact_ssn', label: 'SSN', icon: Hash, example: '123-45-6789 → [SSN_REDACTED]' },
  { key: 'redact_credit_cards', label: 'Credit Cards', icon: CreditCard, example: '4111-1111-1111-1111 → [CC_REDACTED]' },
] as const

export function UploadOptions({ config, onChange }: UploadOptionsProps) {
  const [expanded, setExpanded] = useState(false)

  const updatePII = (key: keyof PIIOptions, value: boolean) => {
    onChange({
      ...config,
      piiOptions: { ...config.piiOptions, [key]: value }
    })
  }

  const enabledPIICount = Object.values(config.piiOptions).filter(Boolean).length

  return (
    <Card className="p-4 bg-card/50 border-border">
      <button 
        className="w-full flex items-center justify-between"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-cyan-400" />
          <h3 className="font-medium text-foreground">Upload Options</h3>
          {config.mode === 'secure' && (
            <span className="text-xs px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400">
              {enabledPIICount} PII types
            </span>
          )}
        </div>
        {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {expanded && (
        <div className="mt-4 space-y-4 pt-4 border-t border-border">
          {/* Processing Mode */}
          <div>
            <label className="text-sm font-medium text-foreground mb-2 block">Processing Mode</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => onChange({ ...config, mode: 'secure' })}
                className={cn(
                  "p-3 rounded-lg border text-left transition-all",
                  config.mode === 'secure' 
                    ? "border-cyan-500 bg-cyan-500/10" 
                    : "border-border hover:border-cyan-500/50"
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Shield className={cn("w-4 h-4", config.mode === 'secure' ? "text-cyan-400" : "text-muted-foreground")} />
                  <span className={cn("font-medium", config.mode === 'secure' ? "text-cyan-400" : "text-foreground")}>Secure</span>
                </div>
                <p className="text-xs text-muted-foreground">Local PII redaction, max privacy</p>
              </button>
              <button
                onClick={() => onChange({ ...config, mode: 'standard' })}
                className={cn(
                  "p-3 rounded-lg border text-left transition-all",
                  config.mode === 'standard' 
                    ? "border-cyan-500 bg-cyan-500/10" 
                    : "border-border hover:border-cyan-500/50"
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Globe className={cn("w-4 h-4", config.mode === 'standard' ? "text-cyan-400" : "text-muted-foreground")} />
                  <span className={cn("font-medium", config.mode === 'standard' ? "text-cyan-400" : "text-foreground")}>Standard</span>
                </div>
                <p className="text-xs text-muted-foreground">Full cloud features</p>
              </button>
            </div>
          </div>

          {/* OCR Language */}
          <div>
            <label className="text-sm font-medium text-foreground mb-2 block">OCR Language</label>
            <Select value={config.language} onValueChange={(v) => onChange({ ...config, language: v })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {languages.map((lang) => (
                  <SelectItem key={lang.code} value={lang.code}>{lang.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* PII Options (only in secure mode) */}
          {config.mode === 'secure' && (
            <div>
              <label className="text-sm font-medium text-foreground mb-2 block">PII Redaction Types</label>
              <div className="space-y-2">
                {piiTypes.map((pii) => {
                  const Icon = pii.icon
                  const enabled = config.piiOptions[pii.key]
                  return (
                    <div key={pii.key} className="flex items-center justify-between p-2 rounded-lg bg-secondary/50">
                      <div className="flex items-center gap-2">
                        <Icon className={cn("w-4 h-4", enabled ? "text-cyan-400" : "text-muted-foreground")} />
                        <div>
                          <p className={cn("text-sm", enabled ? "text-foreground" : "text-muted-foreground")}>{pii.label}</p>
                          <p className="text-xs text-muted-foreground">{pii.example}</p>
                        </div>
                      </div>
                      <Switch checked={enabled} onCheckedChange={(v) => updatePII(pii.key, v)} />
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}
