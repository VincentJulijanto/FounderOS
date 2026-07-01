import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import AgentActivityMockup from './AgentActivityMockup'

export default function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* One very subtle violet corner wash for warmth — the only wash on the page */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            'radial-gradient(48% 42% at 88% 0%, rgba(124,111,240,0.08), transparent 70%)',
        }}
      />

      <div className="max-w-6xl mx-auto px-6 pt-20 pb-24 md:pt-28 md:pb-32 grid lg:grid-cols-[1.05fr_0.95fr] gap-14 lg:gap-12 items-center">
        {/* Left: copy */}
        <div>
          <h1 className="text-[2.75rem] sm:text-6xl lg:text-[4.25rem] font-semibold leading-[1.12] tracking-[-0.02em] text-graphite">
            Bring your next big decision to a
            {/* the single violet word — color as punctuation */}
            <span className="text-brand-500"> council</span> of
            {/* thin gold underline accent under one phrase */}
            <span className="relative whitespace-nowrap">
              {' '}AI agents
              <span
                aria-hidden="true"
                className="absolute left-0 -bottom-1 h-[3px] w-full rounded-full bg-accent-600/70"
              />
            </span>
          </h1>

          <p className="mt-7 text-lg text-muted max-w-xl leading-relaxed">
            FounderOS is an AI board for your business. Seven specialized agents
            pressure-test the decision you bring, debate the trade-offs, and hand you
            a board-ready memo — a clear recommendation, the dissent behind it, and
            what you&rsquo;re still missing.
          </p>

          {/* CTAs — solid ink primary, quiet secondary */}
          <div className="mt-9 flex flex-col sm:flex-row sm:items-center gap-4">
            <Link href="/boardroom" className="btn-ink">
              Enter the boardroom
              <ArrowRight className="w-4 h-4" aria-hidden="true" />
            </Link>
            <a href="#how-it-works" className="link-quiet">
              See how it works
            </a>
          </div>

          {/* Social proof row */}
          <div className="mt-12 flex items-center gap-4">
            {/* PLACEHOLDER: decorative avatar stand-ins, not real users */}
            <div className="flex -space-x-2" aria-hidden="true">
              {['bg-brand-400', 'bg-accent-500', 'bg-brand-300', 'bg-accent-400'].map(
                (c, i) => (
                  <span
                    key={i}
                    className={`w-8 h-8 rounded-full ${c} ring-2 ring-canvas`}
                  />
                ),
              )}
            </div>
            <p className="text-sm text-muted">
              {/* PLACEHOLDER STAT — replace with a real, verified number */}
              <span className="font-semibold text-graphite">1,200+ operators</span> have
              pressure-tested a decision with the council
            </p>
          </div>
        </div>

        {/* Right: light product-UI mockup */}
        <div className="lg:pl-4">
          <AgentActivityMockup />
        </div>
      </div>
    </section>
  )
}
