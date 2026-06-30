'use client'

import { useState } from 'react'
import { Plus, Minus } from 'lucide-react'

/* Copy is editable placeholder — refine against real product behaviour. */
const ITEMS = [
  {
    q: 'What exactly do I get at the end?',
    a: 'A ranked shortlist of startup opportunities plus a full execution plan for the recommended one: lean canvas, MVP scope, a 30-day roadmap, marketing and acquisition notes, and outreach templates.',
  },
  {
    q: 'How is the council different from one chatbot?',
    a: 'Each agent has a distinct mandate and scoring lens, and they actively debate where they disagree. You see the conflicts and how they were resolved — not a single averaged opinion.',
  },
  {
    q: 'Do I need a technical background to use it?',
    a: 'No. You describe your skills, budget, and time in plain language. FounderOS adapts its recommendations to your profile, including no-code paths when that fits you better.',
  },
  {
    q: 'How long does an analysis take?',
    a: 'Most runs complete in a few minutes. You can watch the agents work and the consensus form in real time before the plan is generated.',
  },
  {
    q: 'Is my profile information kept private?',
    a: 'Your inputs are used only to generate your recommendation. (Placeholder — confirm against the actual data and privacy policy before launch.)',
  },
]

export default function FAQ() {
  const [open, setOpen] = useState<number | null>(0)

  return (
    <section id="faq" className="max-w-3xl mx-auto px-6 py-24 md:py-28 scroll-mt-24">
      <h2 className="text-3xl md:text-[2.5rem] font-semibold tracking-[-0.02em] leading-[1.12] text-graphite">
        Frequently asked questions
      </h2>

      <dl className="mt-12">
        {ITEMS.map((item, i) => {
          const isOpen = open === i
          return (
            <div key={item.q} className="border-b border-hairline">
              <dt>
                <button
                  type="button"
                  onClick={() => setOpen(isOpen ? null : i)}
                  aria-expanded={isOpen}
                  className="w-full flex items-center gap-4 py-5 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
                >
                  <span className="font-mono text-sm text-brand-500 w-7 shrink-0 tabular-nums">
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span className="flex-1 font-medium text-graphite">{item.q}</span>
                  {isOpen ? (
                    <Minus className="w-5 h-5 text-muted shrink-0" aria-hidden="true" />
                  ) : (
                    <Plus className="w-5 h-5 text-muted shrink-0" aria-hidden="true" />
                  )}
                </button>
              </dt>
              {isOpen && (
                <dd className="pb-5 pl-11 text-sm text-muted leading-relaxed">
                  {item.a}
                </dd>
              )}
            </div>
          )
        })}
      </dl>
    </section>
  )
}
