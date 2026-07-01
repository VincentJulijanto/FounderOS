'use client'

import { useState } from 'react'
import { ChevronDown, UserCog, Search, Scale, FileText } from 'lucide-react'

const STEPS = [
  {
    icon: UserCog,
    title: 'Bring a decision',
    body: 'Tell FounderOS the call you are weighing and your company context — sector, stage, model, and the numbers that matter. The council pulls the rest from your saved history.',
  },
  {
    icon: Search,
    title: 'The council convenes',
    body: 'The Scout frames the options on the table; Trend, Finance, Growth, and Capability agents pressure each one across their dimensions in parallel.',
  },
  {
    icon: Scale,
    title: 'Debate to consensus',
    body: 'Agents identify where they disagree and argue it out over rounds. A moderator tracks conflicts until the council converges — and what stays unresolved becomes the dissent on record.',
  },
  {
    icon: FileText,
    title: 'Get your board memo',
    body: 'The Chair weighs the debate into a clear recommendation — proceed, hold, or conditional — with the dissent, what is still missing, and a phased plan.',
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
          From one decision to a board-ready memo in four steps.
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
            <span className="text-sm font-medium text-graphite">Options assessed</span>
            <span className="text-xs font-mono text-muted">3 options assessed</span>
          </div>

          {/* Ranked ideas — PLACEHOLDER illustrative data */}
          <ul className="mt-4 space-y-3">
            {[
              { rank: 1, name: 'Enter Indonesia (pilot first)', score: 'High', w: '84%' },
              { rank: 2, name: 'Deepen in the home market', score: 'Medium', w: '76%' },
              { rank: 3, name: 'Acquire a regional competitor', score: 'Low', w: '69%' },
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
            Recommended: <span className="text-graphite font-medium">Enter Indonesia (pilot first)</span> — board memo ready
          </div>
        </div>
      </div>
    </section>
  )
}
