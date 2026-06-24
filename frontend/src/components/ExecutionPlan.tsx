'use client'

import { useState } from 'react'
import { ExecutionPlanData } from '@/app/page'

interface Props {
  plan: ExecutionPlanData
}

type Tab = 'lean_canvas' | 'roadmap' | 'marketing' | 'landing_page' | 'outreach'

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: 'lean_canvas', label: 'Lean Canvas', icon: '🗂️' },
  { id: 'roadmap', label: '30-Day Roadmap', icon: '📅' },
  { id: 'marketing', label: 'Marketing', icon: '📣' },
  { id: 'landing_page', label: 'Landing Page', icon: '🖥️' },
  { id: 'outreach', label: 'Outreach Templates', icon: '✉️' },
]

const CANVAS_FIELDS = [
  { key: 'problem', label: 'Problem', color: 'border-red-800' },
  { key: 'solution', label: 'Solution', color: 'border-green-800' },
  { key: 'unique_value_proposition', label: 'Unique Value', color: 'border-blue-800' },
  { key: 'unfair_advantage', label: 'Unfair Advantage', color: 'border-purple-800' },
  { key: 'customer_segments', label: 'Customer Segments', color: 'border-yellow-800' },
  { key: 'key_metrics', label: 'Key Metrics', color: 'border-orange-800' },
  { key: 'channels', label: 'Channels', color: 'border-teal-800' },
  { key: 'cost_structure', label: 'Cost Structure', color: 'border-pink-800' },
  { key: 'revenue_streams', label: 'Revenue Streams', color: 'border-emerald-800' },
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
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">{plan.startup_name}</h2>
          <p className="text-brand-400 mt-1">{plan.value_proposition}</p>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-500 mb-1">Elevator Pitch</div>
          <div className="text-sm text-gray-300 max-w-xs italic">"{plan.elevator_pitch}"</div>
        </div>
      </div>

      {/* Customer Persona */}
      <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
        <div className="text-xs text-gray-500 mb-1">Target Customer Persona</div>
        <p className="text-sm text-gray-300">{plan.customer_persona}</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-all ${
              activeTab === tab.id
                ? 'bg-brand-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="min-h-[300px]">

        {activeTab === 'lean_canvas' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {CANVAS_FIELDS.map(field => (
              <div key={field.key} className={`p-3 rounded-xl border ${field.color} bg-gray-900/50`}>
                <div className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
                  {field.label}
                </div>
                <p className="text-sm text-gray-300">
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
                <div className="w-8 h-8 rounded-full bg-brand-600/30 border border-brand-600 flex items-center justify-center text-xs font-bold text-brand-400 flex-shrink-0">
                  {i + 1}
                </div>
                <div className="flex-1 p-3 bg-gray-800/50 rounded-xl border border-gray-700 text-sm text-gray-300">
                  {milestone}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'marketing' && (
          <div className="space-y-4">
            <div className="p-4 bg-gray-800/50 rounded-xl border border-gray-700">
              <h4 className="font-semibold mb-2 text-sm text-gray-400 uppercase tracking-wider">Marketing Strategy</h4>
              <p className="text-sm text-gray-300 whitespace-pre-line">{plan.marketing_strategy}</p>
            </div>
            <div className="p-4 bg-gray-800/50 rounded-xl border border-gray-700">
              <h4 className="font-semibold mb-2 text-sm text-gray-400 uppercase tracking-wider">First 10 Customers</h4>
              <p className="text-sm text-gray-300 whitespace-pre-line">{plan.customer_acquisition_plan}</p>
            </div>
          </div>
        )}

        {activeTab === 'landing_page' && (
          <div className="relative">
            <button
              onClick={() => copyText(plan.landing_page_copy, 'landing')}
              className="absolute top-2 right-2 btn-secondary text-xs py-1 px-3"
            >
              {copied === 'landing' ? '✓ Copied' : 'Copy'}
            </button>
            <div className="p-4 bg-gray-800/50 rounded-xl border border-gray-700">
              <pre className="text-sm text-gray-300 whitespace-pre-wrap font-sans">
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
                  {copied === key ? '✓ Copied' : 'Copy'}
                </button>
                <div className="p-4 bg-gray-800/50 rounded-xl border border-gray-700">
                  <h4 className="font-semibold mb-2 text-xs text-gray-500 uppercase tracking-wider">
                    {key.replace(/_/g, ' ')}
                  </h4>
                  <pre className="text-sm text-gray-300 whitespace-pre-wrap font-sans">
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
