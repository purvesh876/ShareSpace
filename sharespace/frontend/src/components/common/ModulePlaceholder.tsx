import * as React from "react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import { Info, Sparkles, AlertCircle } from "lucide-react"

interface ModulePlaceholderProps {
  title: string
  subtitle: string
  stepNumber: number
  icon: React.ReactNode
  lifecycleStage: string
  description: string
  previewContent?: React.ReactNode
  expectedFeatures: string[]
}

export function ModulePlaceholder({
  title,
  subtitle,
  stepNumber,
  icon,
  lifecycleStage,
  description,
  previewContent,
  expectedFeatures,
}: ModulePlaceholderProps) {
  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-white border border-slate-200 shadow-xs">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-700 flex-shrink-0 mt-0.5">
            {icon}
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">{title}</h2>
              <Badge variant="info">{lifecycleStage}</Badge>
              <Badge variant="warning">Roadmap: Step {stepNumber}</Badge>
            </div>
            <p className="text-sm text-slate-500 max-w-2xl">{subtitle}</p>
          </div>
        </div>

        <div className="flex-shrink-0">
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-xs font-medium text-slate-700">
            <Sparkles className="w-3.5 h-3.5 text-amber-600" />
            <span>Interactive Foundation</span>
          </div>
        </div>
      </div>

      {/* Security & Lifecycle Notice */}
      <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 flex items-start gap-3 text-xs text-blue-900">
        <Info className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold text-blue-950">Institutional Workflow Context:</p>
          <p className="text-blue-900/90 leading-relaxed text-xs">{description}</p>
        </div>
      </div>

      {/* Main Preview Area */}
      {previewContent && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Workflow Interface Preview</CardTitle>
                <CardDescription>
                  Simulated user experience for this institutional milestone.
                </CardDescription>
              </div>
              <Badge variant="secondary">Mock Demonstration</Badge>
            </div>
          </CardHeader>
          <CardContent>{previewContent}</CardContent>
        </Card>
      )}

      {/* Feature Delivery Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold text-slate-900">
            Capabilities Bound in Step {stepNumber}
          </CardTitle>
          <CardDescription>
            The backend engine and storage guards powering this view:
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-slate-700">
            {expectedFeatures.map((feat, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 flex-shrink-0" />
                <span>{feat}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <div className="flex items-center gap-2 p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900">
        <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
        <span>
          Note: This screen serves as an architectural blueprint. Real PostgreSQL database mutations, token verification, and file uploads will be connected in Step {stepNumber}.
        </span>
      </div>
    </div>
  )
}
