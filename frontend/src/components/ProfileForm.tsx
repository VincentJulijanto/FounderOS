'use client'

import { useState } from 'react'
import { ArrowRight } from 'lucide-react'
import { ROSTER } from '@/components/agentRoster'

interface Props {
  onSubmit: (data: Record<string, unknown>) => void
}

const SKILL_OPTIONS = [
  'Python', 'JavaScript/React', 'No-Code Tools', 'Video Editing',
  'Design/Figma', 'Copywriting', 'Social Media', 'Sales', 'Data Analysis',
  'Teaching/Tutoring', 'Photography', 'Marketing', 'Excel/Spreadsheets',
]

const INTEREST_OPTIONS = [
  'EdTech', 'FinTech', 'Health & Wellness', 'Productivity', 'Gaming',
  'Sustainability', 'Fashion', 'Food & Beverage', 'Travel', 'AI/Tech',
  'Creator Economy', 'Real Estate', 'E-commerce', 'Social Impact',
]

export default function ProfileForm({ onSubmit }: Props) {
  const [form, setForm] = useState({
    name: '',
    background: '',
    budget: 500,
    weekly_hours: 10,
    goals: '',
    skills: [] as string[],
    interests: [] as string[],
  })

  const toggleItem = (list: 'skills' | 'interests', item: string) => {
    setForm(prev => ({
      ...prev,
      [list]: prev[list].includes(item)
        ? prev[list].filter(i => i !== item)
        : [...prev[list], item],
    }))
  }

  const handleSubmit = () => {
    if (!form.name || !form.background || !form.goals || form.skills.length === 0) {
      alert('Please fill in all required fields and select at least one skill.')
      return
    }
    onSubmit(form)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8 animate-slide-up">

      {/* Beat 1 — meet your council before you commit */}
      <div className="card">
        <h2 className="text-lg font-semibold">Meet your council</h2>
        <p className="text-sm text-muted mt-0.5 mb-5">
          Seven specialized agents will analyse your brief — here&rsquo;s who&rsquo;s working for you.
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

      {/* Basic Info */}
      <div className="card space-y-4">
        <h2 className="text-lg font-semibold">Tell us about yourself</h2>

        <div>
          <label className="label">Your Name *</label>
          <input
            className="input"
            placeholder="e.g. Alex Tan"
            value={form.name}
            onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
          />
        </div>

        <div>
          <label className="label">Background *</label>
          <input
            className="input"
            placeholder="e.g. NUS Computer Science student, Year 2"
            value={form.background}
            onChange={e => setForm(p => ({ ...p, background: e.target.value }))}
          />
        </div>

        <div>
          <label className="label">What&apos;s your goal? *</label>
          <textarea
            className="input min-h-[80px] resize-none"
            placeholder="e.g. Earn $1,000/month side income within 3 months with minimal upfront investment"
            value={form.goals}
            onChange={e => setForm(p => ({ ...p, goals: e.target.value }))}
          />
        </div>
      </div>

      {/* Budget & Time */}
      <div className="card">
        <h2 className="text-lg font-semibold">Resources</h2>
        <p className="text-sm text-muted mt-0.5 mb-4">
          This is what tailors the council — Finance models against your budget, Founder-Fit against your time.
        </p>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="label">Budget (SGD)</label>
            <div className="flex items-center gap-3">
              <input
                type="range" min="100" max="5000" step="100"
                value={form.budget}
                onChange={e => setForm(p => ({ ...p, budget: Number(e.target.value) }))}
                className="flex-1 accent-brand-500"
              />
              <span className="text-brand-600 font-mono font-semibold w-20 text-right">
                SGD {form.budget.toLocaleString()}
              </span>
            </div>
          </div>
          <div>
            <label className="label">Hours per week</label>
            <div className="flex items-center gap-3">
              <input
                type="range" min="2" max="40" step="1"
                value={form.weekly_hours}
                onChange={e => setForm(p => ({ ...p, weekly_hours: Number(e.target.value) }))}
                className="flex-1 accent-brand-500"
              />
              <span className="text-brand-600 font-mono font-semibold w-16 text-right">
                {form.weekly_hours}h
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Skills */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-1">Your skills *</h2>
        <p className="text-sm text-muted mb-4">Founder-Fit scores every idea against these — select all that apply.</p>
        <div className="flex flex-wrap gap-2">
          {SKILL_OPTIONS.map(skill => (
            <button
              key={skill}
              onClick={() => toggleItem('skills', skill)}
              className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                form.skills.includes(skill)
                  ? 'bg-graphite border-graphite text-canvas'
                  : 'bg-white border-hairline text-muted hover:border-graphite/40'
              }`}
            >
              {skill}
            </button>
          ))}
        </div>
      </div>

      {/* Interests */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-1">Your interests</h2>
        <p className="text-sm text-muted mb-4">What sectors excite you?</p>
        <div className="flex flex-wrap gap-2">
          {INTEREST_OPTIONS.map(interest => (
            <button
              key={interest}
              onClick={() => toggleItem('interests', interest)}
              className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                form.interests.includes(interest)
                  ? 'bg-graphite border-graphite text-canvas'
                  : 'bg-white border-hairline text-muted hover:border-graphite/40'
              }`}
            >
              {interest}
            </button>
          ))}
        </div>
      </div>

      {/* Submit */}
      <button onClick={handleSubmit} className="btn-primary w-full text-lg py-4">
        Launch Agent Society
        <ArrowRight className="w-5 h-5" aria-hidden="true" />
      </button>

      <p className="text-center text-xs text-muted">
        Seven agents will analyse your profile and debate the best startup for you.
        This typically takes 30–90 seconds.
      </p>
    </div>
  )
}
