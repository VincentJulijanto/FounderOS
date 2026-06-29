'use client'

import { useState } from 'react'
import { ChevronDown, UserCog, Search, Scale, FileText } from 'lucide-react'

const STEPS = [
  {
    icon: UserCog,
    title: 'Share your profile',
    body: 'Tell FounderOS your skills, budget, weekly hours, and goals. That context anchors every agent so recommendations fit you — not a generic founder.',
  },
  {
    icon: Search,
    title: 'Agents scout & analyze',
    body: 'The Scout surfaces market gaps; Trend, Finance, Growth, and Founder-Fit agents score each opportunity across their dimensions in parallel.',
  },
  {
    icon: Scale,
    title: 'Debate to consensus',
    body: 'Agents identify where they disagree and argue it out over rounds. A moderator tracks conflicts until the panel converges on a consensus.',
  },
  {
    icon: FileText,
    title: 'Get your execution plan',
    body: 'The Venture Partner synthesizes everything into a ranked shortlist plus a full plan: lean canvas, MVP scope, 30-day roadmap, and outreach copy.',
  },
]

export default function HowItWorks() {
  const [open, setOpen] = useState(0)

  return (
    <section
      id="how-it-works"
      className="max-w-6xl mx-auto px-6 py-20 md:py-28 scroll-mt-24"
    >
      <div className="max-w-2xl">
        <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-gray-100">
          How the model works
        </h2>
        <p className="mt-4 text-gray-400 text-lg">
          From a short profile to a defensible plan in four steps.
        </p>
      </div>

      <div className="mt-12 grid lg:grid-cols-2 gap-10 lg:gap-12 items-start">
        {/* Accordion */}
        <div className="divide-y divide-white/5 rounded-2xl border border-white/10 bg-white/[0.02]">
          {STEPS.map((s, i) => {
            const Icon = s.icon
            const isOpen = open === i
            return (
              <div key={s.title}>
                <h3>
                  <button
                    type="button"
                    onClick={() => setOpen(isOpen ? -1 : i)}
                    aria-expanded={isOpen}
                    className="w-full flex items-center gap-4 px-5 py-4 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded-2xl"
                  >
                    <span className="inline-flex w-9 h-9 shrink-0 rounded-lg bg-gradient-to-br from-brand-500/20 to-accent-500/20 border border-white/10 items-center justify-center text-brand-300">
                      <Icon className="w-4 h-4" aria-hidden="true" />
                    </span>
                    <span className="flex-1 font-medium text-gray-100">{s.title}</span>
                    <ChevronDown
                      className={`w-5 h-5 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
                      aria-hidden="true"
                    />
                  </button>
                </h3>
                {isOpen && (
                  <div className="px-5 pb-5 pl-[4.5rem] text-sm text-gray-400 leading-relaxed">
                    {s.body}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Dashboard-style mockup */}
        <div className="glass p-6">
          <div className="flex items-center justify-between pb-4 border-b border-white/10">
            <span className="text-sm font-medium text-gray-200">Venture pipeline</span>
            <span className="text-xs font-mono text-gray-500">3 ideas ranked</span>
          </div>

          {/* Ranked ideas — PLACEHOLDER illustrative data */}
          <ul className="mt-4 space-y-3">
            {[
              { rank: 1, name: 'Niche B2B onboarding tool', score: 8.4, w: '84%' },
              { rank: 2, name: 'Creator analytics dashboard', score: 7.6, w: '76%' },
              { rank: 3, name: 'Local services marketplace', score: 6.9, w: '69%' },
            ].map((idea) => (
              <li
                key={idea.rank}
                className="rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="w-6 h-6 shrink-0 rounded-md bg-white/5 border border-white/10 flex items-center justify-center text-xs font-mono text-gray-300">
                      {idea.rank}
                    </span>
                    <span className="text-sm text-gray-200 truncate">{idea.name}</span>
                  </div>
                  <span className="text-sm font-mono text-brand-300">{idea.score}</span>
                </div>
                <div className="mt-2 score-bar">
                  <div
                    className="score-fill bg-gradient-to-r from-brand-500 to-accent-500"
                    style={{ width: idea.w }}
                  />
                </div>
              </li>
            ))}
          </ul>

          <div className="mt-4 rounded-xl bg-gradient-to-r from-brand-500/10 to-accent-500/10 border border-white/10 px-4 py-3 text-xs text-gray-400">
            Recommended: <span className="text-gray-200 font-medium">Niche B2B onboarding tool</span> — execution plan ready
          </div>
        </div>
      </div>
    </section>
  )
}
