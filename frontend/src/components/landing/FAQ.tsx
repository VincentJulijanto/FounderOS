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
    q: 'How are the seven agents different from one chatbot?',
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
    <section id="faq" className="max-w-3xl mx-auto px-6 py-20 md:py-28 scroll-mt-24">
      <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-gray-100 text-center">
        Frequently asked questions
      </h2>

      <dl className="mt-12 divide-y divide-white/5 rounded-2xl border border-white/10 bg-white/[0.02]">
        {ITEMS.map((item, i) => {
          const isOpen = open === i
          return (
            <div key={item.q} className="px-5">
              <dt>
                <button
                  type="button"
                  onClick={() => setOpen(isOpen ? null : i)}
                  aria-expanded={isOpen}
                  className="w-full flex items-center gap-4 py-5 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded-lg"
                >
                  <span className="font-mono text-sm text-brand-400 w-6 shrink-0">
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span className="flex-1 font-medium text-gray-100">{item.q}</span>
                  {isOpen ? (
                    <Minus className="w-5 h-5 text-gray-500 shrink-0" aria-hidden="true" />
                  ) : (
                    <Plus className="w-5 h-5 text-gray-500 shrink-0" aria-hidden="true" />
                  )}
                </button>
              </dt>
              {isOpen && (
                <dd className="pb-5 pl-10 text-sm text-gray-400 leading-relaxed">
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
