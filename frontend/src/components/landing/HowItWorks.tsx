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
    title: 'The council convenes',
    body: 'The Scout surfaces market gaps; Trend, Finance, Growth, and Founder-Fit agents score each opportunity across their dimensions in parallel.',
  },
  {
    icon: Scale,
    title: 'Debate to consensus',
    body: 'Agents identify where they disagree and argue it out over rounds. A moderator tracks conflicts until the council converges on a consensus.',
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
    <section id="how-it-works" className="max-w-6xl mx-auto px-6 py-24 md:py-28 scroll-mt-24">
      <div className="max-w-2xl">
        <h2 className="text-3xl md:text-[2.5rem] font-semibold tracking-[-0.02em] leading-[1.12] text-graphite">
          How the model works
        </h2>
        <p className="mt-5 text-muted text-lg leading-relaxed">
          From a short profile to a defensible plan in four steps.
        </p>
      </div>

      <div className="mt-14 grid lg:grid-cols-2 gap-12 items-start">
        {/* Accordion */}
        <div>
          {STEPS.map((s, i) => {
            const Icon = s.icon
            const isOpen = open === i
            return (
              <div key={s.title} className="border-b border-hairline last:border-0">
                <h3>
                  <button
                    type="button"
                    onClick={() => setOpen(isOpen ? -1 : i)}
                    aria-expanded={isOpen}
                    className="w-full flex items-center gap-4 py-5 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
                  >
                    <span className="inline-flex w-9 h-9 shrink-0 rounded-lg bg-brand-500/10 items-center justify-center text-brand-600">
                      <Icon className="w-4 h-4" aria-hidden="true" />
                    </span>
                    <span className="flex-1 font-medium text-graphite">{s.title}</span>
                    <ChevronDown
                      className={`w-5 h-5 text-muted transition-transform ${isOpen ? 'rotate-180' : ''}`}
                      aria-hidden="true"
                    />
                  </button>
                </h3>
                {isOpen && (
                  <div className="pb-5 pl-[3.25rem] text-sm text-muted leading-relaxed">
                    {s.body}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Light dashboard-style mockup */}
        <div className="card-light p-6">
          <div className="flex items-center justify-between pb-4 border-b border-hairline">
            <span className="text-sm font-medium text-graphite">Venture pipeline</span>
            <span className="text-xs font-mono text-muted">3 ideas ranked</span>
          </div>

          {/* Ranked ideas — PLACEHOLDER illustrative data */}
          <ul className="mt-4 space-y-3">
            {[
              { rank: 1, name: 'Niche B2B onboarding tool', score: 8.4, w: '84%' },
              { rank: 2, name: 'Creator analytics dashboard', score: 7.6, w: '76%' },
              { rank: 3, name: 'Local services marketplace', score: 6.9, w: '69%' },
            ].map((idea) => (
              <li key={idea.rank} className="rounded-xl border border-hairline bg-canvas/60 px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="w-6 h-6 shrink-0 rounded-md bg-graphite/[0.04] border border-hairline flex items-center justify-center text-xs font-mono text-muted">
                      {idea.rank}
                    </span>
                    <span className="text-sm text-graphite truncate">{idea.name}</span>
                  </div>
                  <span className="text-sm font-mono text-brand-600">{idea.score}</span>
                </div>
                <div className="mt-2 h-1.5 rounded-full bg-graphite/[0.06] overflow-hidden">
                  <div className="h-full rounded-full bg-brand-500" style={{ width: idea.w }} />
                </div>
              </li>
            ))}
          </ul>

          <div className="mt-4 rounded-xl border border-accent-600/30 bg-accent-500/[0.07] px-4 py-3 text-xs text-muted">
            Recommended: <span className="text-graphite font-medium">Niche B2B onboarding tool</span> — execution plan ready
          </div>
        </div>
      </div>
    </section>
  )
}
