'use client'

import { useState } from 'react'
import { LayoutGrid, CalendarDays, Megaphone, MonitorSmartphone, Mails, Check, Copy, type LucideIcon } from 'lucide-react'
import { ExecutionPlanData } from '@/app/studio/page'

interface Props {
  plan: ExecutionPlanData
}

type Tab = 'lean_canvas' | 'roadmap' | 'marketing' | 'landing_page' | 'outreach'

const TABS: { id: Tab; label: string; Icon: LucideIcon }[] = [
  { id: 'lean_canvas', label: 'Lean Canvas', Icon: LayoutGrid },
  { id: 'roadmap', label: '30-Day Roadmap', Icon: CalendarDays },
  { id: 'marketing', label: 'Marketing', Icon: Megaphone },
  { id: 'landing_page', label: 'Landing Page', Icon: MonitorSmartphone },
  { id: 'outreach', label: 'Outreach Templates', Icon: Mails },
]

const CANVAS_FIELDS = [
  { key: 'problem', label: 'Problem' },
  { key: 'solution', label: 'Solution' },
  { key: 'unique_value_proposition', label: 'Unique Value' },
  { key: 'unfair_advantage', label: 'Unfair Advantage' },
  { key: 'customer_segments', label: 'Customer Segments' },
  { key: 'key_metrics', label: 'Key Metrics' },
  { key: 'channels', label: 'Channels' },
  { key: 'cost_structure', label: 'Cost Structure' },
  { key: 'revenue_streams', label: 'Revenue Streams' },
]

export default function ExecutionPlan({ plan }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('lean_canvas')
  const [copied, setCopied] = useState<string | null>(null)

  const copyText = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(null), 2000)
  }

  return (
    <div className="card space-y-6 animate-slide-up">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-graphite">{plan.startup_name}</h2>
          <p className="text-brand-600 mt-1">{plan.value_proposition}</p>
        </div>
        <div className="text-right">
          <div className="text-xs text-muted mb-1">Elevator pitch</div>
          <div className="text-sm text-graphite/80 max-w-xs italic">&ldquo;{plan.elevator_pitch}&rdquo;</div>
        </div>
      </div>

      {/* Customer Persona */}
      <div className="bg-canvas rounded-xl p-4 border border-hairline">
        <div className="text-xs text-muted mb-1">Target customer persona</div>
        <p className="text-sm text-graphite/80">{plan.customer_persona}</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap">
        {TABS.map(tab => {
          const Icon = tab.Icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm border transition-colors ${
                activeTab === tab.id
                  ? 'bg-graphite border-graphite text-canvas'
                  : 'bg-white border-hairline text-muted hover:border-graphite/40'
              }`}
            >
              <Icon className="w-4 h-4" aria-hidden="true" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      <div className="min-h-[300px]">

        {activeTab === 'lean_canvas' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {CANVAS_FIELDS.map(field => (
              <div key={field.key} className="p-3 rounded-xl border border-hairline bg-canvas">
                <div className="text-xs font-semibold text-muted mb-2 uppercase tracking-wider">
                  {field.label}
                </div>
                <p className="text-sm text-graphite/80">
                  {plan.lean_canvas[field.key] || '—'}
                </p>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'roadmap' && (
          <div className="space-y-3">
            {plan.thirty_day_roadmap.map((milestone, i) => (
              <div key={i} className="flex gap-4 items-start">
                <div className="w-8 h-8 rounded-full bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-xs font-semibold text-brand-700 flex-shrink-0">
                  {i + 1}
                </div>
                <div className="flex-1 p-3 bg-canvas rounded-xl border border-hairline text-sm text-graphite/80">
                  {milestone}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'marketing' && (
          <div className="space-y-4">
            <div className="p-4 bg-canvas rounded-xl border border-hairline">
              <h4 className="font-semibold mb-2 text-sm text-muted uppercase tracking-wider">Marketing strategy</h4>
              <p className="text-sm text-graphite/80 whitespace-pre-line">{plan.marketing_strategy}</p>
            </div>
            <div className="p-4 bg-canvas rounded-xl border border-hairline">
              <h4 className="font-semibold mb-2 text-sm text-muted uppercase tracking-wider">First 10 customers</h4>
              <p className="text-sm text-graphite/80 whitespace-pre-line">{plan.customer_acquisition_plan}</p>
            </div>
          </div>
        )}

        {activeTab === 'landing_page' && (
          <div className="relative">
            <button
              onClick={() => copyText(plan.landing_page_copy, 'landing')}
              className="absolute top-2 right-2 btn-secondary text-xs py-1 px-3"
            >
              {copied === 'landing' ? (
                <><Check className="w-3.5 h-3.5 text-brand-600" aria-hidden="true" /> Copied</>
              ) : (
                <><Copy className="w-3.5 h-3.5" aria-hidden="true" /> Copy</>
              )}
            </button>
            <div className="p-4 bg-canvas rounded-xl border border-hairline">
              <pre className="text-sm text-graphite/80 whitespace-pre-wrap font-sans">
                {plan.landing_page_copy}
              </pre>
            </div>
          </div>
        )}

        {activeTab === 'outreach' && (
          <div className="space-y-4">
            {Object.entries(plan.customer_outreach_templates).map(([key, template]) => (
              <div key={key} className="relative">
                <button
                  onClick={() => copyText(template, key)}
                  className="absolute top-2 right-2 btn-secondary text-xs py-1 px-3 z-10"
                >
                  {copied === key ? (
                    <><Check className="w-3.5 h-3.5 text-brand-600" aria-hidden="true" /> Copied</>
                  ) : (
                    <><Copy className="w-3.5 h-3.5" aria-hidden="true" /> Copy</>
                  )}
                </button>
                <div className="p-4 bg-canvas rounded-xl border border-hairline">
                  <h4 className="font-semibold mb-2 text-xs text-muted uppercase tracking-wider">
                    {key.replace(/_/g, ' ')}
                  </h4>
                  <pre className="text-sm text-graphite/80 whitespace-pre-wrap font-sans">
                    {template}
                  </pre>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
