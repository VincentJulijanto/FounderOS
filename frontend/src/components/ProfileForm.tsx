'use client'

import { useState } from 'react'

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

      {/* Agent preview */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-3 mb-8">
        {[
          { icon: '🔭', name: 'Scout' },
          { icon: '📈', name: 'Trend' },
          { icon: '💰', name: 'Finance' },
          { icon: '🚀', name: 'Growth' },
          { icon: '🎯', name: 'Skeptic' },
          { icon: '🤝', name: 'Partner' },
        ].map(agent => (
          <div key={agent.name} className="card text-center py-3 px-2 opacity-60 hover:opacity-100 transition-opacity">
            <div className="text-2xl mb-1">{agent.icon}</div>
            <div className="text-xs text-gray-400">{agent.name}</div>
          </div>
        ))}
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
          <label className="label">What's your goal? *</label>
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
        <h2 className="text-lg font-semibold mb-4">Resources</h2>
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
              <span className="text-brand-400 font-mono font-bold w-20 text-right">
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
              <span className="text-brand-400 font-mono font-bold w-16 text-right">
                {form.weekly_hours}h
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Skills */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-1">Your Skills *</h2>
        <p className="text-sm text-gray-500 mb-4">Select all that apply</p>
        <div className="flex flex-wrap gap-2">
          {SKILL_OPTIONS.map(skill => (
            <button
              key={skill}
              onClick={() => toggleItem('skills', skill)}
              className={`px-3 py-1.5 rounded-full text-sm border transition-all ${
                form.skills.includes(skill)
                  ? 'bg-brand-600 border-brand-500 text-white'
                  : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500'
              }`}
            >
              {skill}
            </button>
          ))}
        </div>
      </div>

      {/* Interests */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-1">Your Interests</h2>
        <p className="text-sm text-gray-500 mb-4">What sectors excite you?</p>
        <div className="flex flex-wrap gap-2">
          {INTEREST_OPTIONS.map(interest => (
            <button
              key={interest}
              onClick={() => toggleItem('interests', interest)}
              className={`px-3 py-1.5 rounded-full text-sm border transition-all ${
                form.interests.includes(interest)
                  ? 'bg-accent-600 border-accent-500 text-white'
                  : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500'
              }`}
            >
              {interest}
            </button>
          ))}
        </div>
      </div>

      {/* Submit */}
      <button onClick={handleSubmit} className="btn-primary w-full text-lg py-4">
        Launch Agent Society →
      </button>

      <p className="text-center text-xs text-gray-600">
        6 AI agents will analyse your profile and debate the best startup for you.
        This typically takes 30–90 seconds.
      </p>
    </div>
  )
}
