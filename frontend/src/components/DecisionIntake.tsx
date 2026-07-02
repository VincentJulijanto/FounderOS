'use client'

import { useState } from 'react'
import { ArrowRight } from 'lucide-react'
import { ROSTER } from '@/components/agentRoster'
import type { AnalyzeRequest, CompanyProfile, Decision } from '@/lib/types'

interface Props {
  onSubmit: (req: AnalyzeRequest) => void
}

/**
 * A preset company on the stubbed picker. `id` is the vault folder (company_id);
 * the seed vault ships history for `harborline-logistics` and `lumen-skincare`,
 * so picking one lets the board "remember" prior decisions.
 */
interface CompanyPreset {
  id: string
  profile: CompanyProfile
  seeded: boolean
}

const COMPANY_PRESETS: CompanyPreset[] = [
  {
    id: 'harborline-logistics',
    seeded: true,
    profile: {
      company_name: 'Harborline Logistics',
      sector: 'regional cross-border logistics',
      stage: 'scaling',
      business_model: 'B2B freight + 3PL',
      size_band: '11–50',
      financials: { revenue_band: 'SGD 8–12M revenue', margin: '~31% gross', cash_position: '16 months runway' },
    },
  },
  {
    id: 'lumen-skincare',
    seeded: true,
    profile: {
      company_name: 'Lumen Skincare',
      sector: 'D2C skincare',
      stage: 'scaling',
      business_model: 'D2C e-commerce (Shopify)',
      size_band: '11–50',
      financials: { revenue_band: 'SGD 3–5M revenue', margin: '~68% gross', cash_position: '12 months runway' },
    },
  },
]

const BLANK_PROFILE: CompanyProfile = {
  company_name: '',
  sector: '',
  stage: '',
  business_model: '',
  size_band: '',
  financials: { revenue_band: '', margin: '', cash_position: '' },
}

/** company_id from a free-text company name (stubbed picker → vault folder). */
const slugId = (name: string) =>
  name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'new-company'

export default function DecisionIntake({ onSubmit }: Props) {
  const [presetId, setPresetId] = useState<string>(COMPANY_PRESETS[0].id)
  const [profile, setProfile] = useState<CompanyProfile>(COMPANY_PRESETS[0].profile)
  const [decision, setDecision] = useState({
    question: '',
    context: '',
    budget: '',
    timeline: '',
    optionsText: '',
  })
  const [errors, setErrors] = useState<{ company_name?: string; question?: string }>({})

  const selectPreset = (p: CompanyPreset | null) => {
    if (p) {
      setPresetId(p.id)
      setProfile(p.profile)
    } else {
      setPresetId('__new__')
      setProfile(BLANK_PROFILE)
    }
  }

  const setProfileField = (k: keyof CompanyProfile, v: string) =>
    setProfile(prev => ({ ...prev, [k]: v }))
  const setFinField = (k: keyof CompanyProfile['financials'], v: string) =>
    setProfile(prev => ({ ...prev, financials: { ...prev.financials, [k]: v } }))

  const handleSubmit = () => {
    const nextErrors: typeof errors = {}
    if (!profile.company_name.trim()) {
      nextErrors.company_name = 'Name the company bringing this decision to the board.'
    }
    if (!decision.question.trim()) {
      nextErrors.question = 'Enter the one decision you want the board to evaluate.'
    }
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) return

    const company_id = presetId === '__new__' ? slugId(profile.company_name) : presetId
    const options = decision.optionsText
      .split('\n')
      .map(o => o.trim())
      .filter(Boolean)

    const decisionPayload: Decision = {
      question: decision.question.trim(),
      context: decision.context.trim() || null,
      constraints: {
        budget: decision.budget.trim() || null,
        timeline: decision.timeline.trim() || null,
      },
      options: options.length ? options : null,
    }

    onSubmit({ company_id, profile, decision: decisionPayload })
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8 animate-slide-up">

      {/* Meet your board */}
      <div className="card">
        <h2 className="text-lg font-semibold">Meet your board</h2>
        <p className="text-sm text-muted mt-0.5 mb-5">
          Seven specialised agents evaluate your decision, debate it, and hand back a board-ready memo.
        </p>
        <ul className="grid sm:grid-cols-2 gap-x-6 gap-y-3.5">
          {ROSTER.map(agent => {
            const Icon = agent.Icon
            return (
              <li key={agent.name} className="flex items-start gap-3">
                <span className="mt-0.5 shrink-0 w-8 h-8 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-600">
                  <Icon className="w-4 h-4" aria-hidden="true" />
                </span>
                <div className="min-w-0">
                  <div className="text-sm font-medium text-graphite">{agent.label}</div>
                  <div className="text-xs text-muted leading-snug">{agent.role}</div>
                </div>
              </li>
            )
          })}
        </ul>
      </div>

      {/* Company picker (stubbed) */}
      <div className="card space-y-4">
        <div>
          <h2 className="text-lg font-semibold">Which company?</h2>
          <p className="text-sm text-muted mt-0.5">
            Pick a company to load its board history from the vault, or start a new one.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {COMPANY_PRESETS.map(p => (
            <button
              key={p.id}
              onClick={() => selectPreset(p)}
              className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                presetId === p.id
                  ? 'bg-graphite border-graphite text-canvas'
                  : 'bg-white border-hairline text-muted hover:border-graphite/40'
              }`}
            >
              {p.profile.company_name}
              {p.seeded && <span className="ml-1.5 text-[10px] uppercase tracking-wide opacity-70">has history</span>}
            </button>
          ))}
          <button
            onClick={() => selectPreset(null)}
            className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
              presetId === '__new__'
                ? 'bg-graphite border-graphite text-canvas'
                : 'bg-white border-hairline text-muted hover:border-graphite/40'
            }`}
          >
            + New company
          </button>
        </div>

        {/* Company profile */}
        <div className="grid sm:grid-cols-2 gap-4 pt-2">
          <Field label="Company name *" value={profile.company_name}
            onChange={v => {
              setProfileField('company_name', v)
              if (errors.company_name) setErrors(e => ({ ...e, company_name: undefined }))
            }}
            placeholder="e.g. Harborline Logistics" error={errors.company_name} />
          <Field label="Sector" value={profile.sector}
            onChange={v => setProfileField('sector', v)} placeholder="e.g. regional logistics" />
          <Field label="Stage" value={profile.stage}
            onChange={v => setProfileField('stage', v)} placeholder="e.g. scaling" />
          <Field label="Business model" value={profile.business_model}
            onChange={v => setProfileField('business_model', v)} placeholder="e.g. B2B freight + 3PL" />
          <Field label="Size band" value={profile.size_band}
            onChange={v => setProfileField('size_band', v)} placeholder="e.g. 11–50" />
          <Field label="Revenue band" value={profile.financials.revenue_band}
            onChange={v => setFinField('revenue_band', v)} placeholder="e.g. SGD 8–12M revenue" />
          <Field label="Margin" value={profile.financials.margin ?? ''}
            onChange={v => setFinField('margin', v)} placeholder="e.g. ~31% gross" />
          <Field label="Cash position" value={profile.financials.cash_position ?? ''}
            onChange={v => setFinField('cash_position', v)} placeholder="e.g. 16 months runway" />
        </div>
      </div>

      {/* The decision */}
      <div className="card space-y-4">
        <div>
          <h2 className="text-lg font-semibold">The decision</h2>
          <p className="text-sm text-muted mt-0.5">One call for the board to pressure-test — is this sound, what&rsquo;s missing?</p>
        </div>

        <div>
          <label className="label">The question *</label>
          <textarea
            className={`input min-h-[70px] resize-none ${errors.question ? 'border-red-300 focus:border-red-400' : ''}`}
            placeholder="e.g. Should we open a dedicated Vietnam cross-border lane next quarter?"
            value={decision.question}
            onChange={e => {
              setDecision(p => ({ ...p, question: e.target.value }))
              if (errors.question) setErrors(er => ({ ...er, question: undefined }))
            }}
            aria-invalid={errors.question ? true : undefined}
          />
          {errors.question && <p className="mt-1.5 text-xs text-red-600" role="alert">{errors.question}</p>}
        </div>

        <div>
          <label className="label">Context</label>
          <textarea
            className="input min-h-[70px] resize-none"
            placeholder="Background you want on the table — why now, what's prompted it."
            value={decision.context}
            onChange={e => setDecision(p => ({ ...p, context: e.target.value }))}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Budget" value={decision.budget}
            onChange={v => setDecision(p => ({ ...p, budget: v }))} placeholder="e.g. SGD 500k" />
          <Field label="Timeline" value={decision.timeline}
            onChange={v => setDecision(p => ({ ...p, timeline: v }))} placeholder="e.g. 6 months" />
        </div>

        <div>
          <label className="label">Options on the table</label>
          <p className="text-xs text-muted mb-1.5">One per line. Leave blank and the Scout will frame the options for you.</p>
          <textarea
            className="input min-h-[80px] resize-none"
            placeholder={'Full subsidiary in Ho Chi Minh City\nAsset-light partnership with a local 3PL\nHold and deepen the current market'}
            value={decision.optionsText}
            onChange={e => setDecision(p => ({ ...p, optionsText: e.target.value }))}
          />
        </div>
      </div>

      <button onClick={handleSubmit} className="btn-primary w-full text-lg py-4">
        Convene the board
        <ArrowRight className="w-5 h-5" aria-hidden="true" />
      </button>

      <p className="text-center text-xs text-muted">
        Seven agents evaluate and debate your decision, then return a board memo. A live run takes ~90–240s.
      </p>
    </div>
  )
}

function Field({ label, value, onChange, placeholder, error }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string; error?: string
}) {
  return (
    <div>
      <label className="label">{label}</label>
      <input
        className={`input ${error ? 'border-red-300 focus:border-red-400' : ''}`}
        placeholder={placeholder} value={value}
        onChange={e => onChange(e.target.value)}
        aria-invalid={error ? true : undefined}
      />
      {error && <p className="mt-1.5 text-xs text-red-600" role="alert">{error}</p>}
    </div>
  )
}
