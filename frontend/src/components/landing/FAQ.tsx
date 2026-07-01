'use client'

import { useState } from 'react'
import { Plus, Minus } from 'lucide-react'

/* Copy is editable placeholder — refine against real product behaviour. */
const ITEMS = [
  {
    q: 'What exactly do I get at the end?',
    a: 'A board-ready memo on the decision you brought: a clear recommendation (proceed, hold, or conditional), the reasoning, the dissent behind it, what inputs are still missing, and a phased plan to act on.',
  },
  {
    q: 'How is the council different from one chatbot?',
    a: 'Each agent has a distinct mandate and scoring lens, and they actively debate where they disagree. You see the conflicts and how they were resolved — not a single averaged opinion.',
  },
  {
    q: 'Do I need a technical background to use it?',
    a: 'No. You describe your business and the decision in plain language. FounderOS adapts to your company context and its saved history — no jargon required.',
  },
  {
    q: 'How long does an analysis take?',
    a: 'Most runs complete in a few minutes. You can watch the agents work and the consensus form in real time before the plan is generated.',
  },
  {
    q: 'Is my company information kept private?',
    a: 'Your company context and decision history are used only to inform your recommendations, and persist in your own company vault. (Placeholder — confirm against the actual data and privacy policy before launch.)',
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
