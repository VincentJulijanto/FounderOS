import Link from 'next/link'
import { ArrowRight, PlayCircle } from 'lucide-react'
import AgentActivityMockup from './AgentActivityMockup'

export default function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* Soft brand/accent background wash */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            'radial-gradient(60% 50% at 15% 0%, rgba(14,165,233,0.14), transparent 70%), radial-gradient(50% 50% at 90% 10%, rgba(139,92,246,0.14), transparent 70%)',
        }}
      />

      <div className="max-w-6xl mx-auto px-6 pt-16 pb-20 md:pt-24 md:pb-28 grid lg:grid-cols-2 gap-12 lg:gap-8 items-center">
        {/* Left: copy */}
        <div className="animate-fade-in">
          <span className="badge bg-accent-500/15 text-accent-300 border border-accent-500/30">
            AI Venture Studio
          </span>

          <h1 className="mt-5 text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.05] tracking-tight text-gray-100">
            Build ventures with
            <span className="block bg-gradient-to-r from-brand-400 to-accent-400 bg-clip-text text-transparent">
              a society of AI agents
            </span>
          </h1>

          <p className="mt-6 text-lg text-gray-400 max-w-xl leading-relaxed">
            FounderOS runs seven specialized agents that scout opportunities, debate
            the trade-offs, and hand you a complete, execution-ready startup plan —
            tailored to your skills, budget, and time.
          </p>

          {/* CTAs */}
          <div className="mt-8 flex flex-col sm:flex-row gap-3">
            <Link href="/studio" className="btn-primary">
              Open the Studio
              <ArrowRight className="w-4 h-4" aria-hidden="true" />
            </Link>
            <a href="#how-it-works" className="btn-outline">
              <PlayCircle className="w-4 h-4" aria-hidden="true" />
              See how it works
            </a>
          </div>

          {/* Social proof row */}
          <div className="mt-10 flex items-center gap-4">
            {/* PLACEHOLDER: decorative avatar stand-ins, not real users */}
            <div className="flex -space-x-2" aria-hidden="true">
              {['from-brand-500 to-brand-700', 'from-accent-500 to-accent-600', 'from-brand-400 to-accent-500', 'from-accent-400 to-brand-500'].map(
                (g, i) => (
                  <span
                    key={i}
                    className={`w-9 h-9 rounded-full bg-gradient-to-br ${g} ring-2 ring-gray-950`}
                  />
                ),
              )}
            </div>
            <p className="text-sm text-gray-400">
              {/* PLACEHOLDER STAT — replace with a real, verified number */}
              <span className="font-semibold text-gray-200">1,200+ founders</span> have
              run their idea through the agents
            </p>
          </div>
        </div>

        {/* Right: floating product-UI mockup */}
        <div className="relative lg:pl-8">
          <div
            aria-hidden="true"
            className="absolute -inset-4 -z-10 rounded-3xl bg-gradient-to-br from-brand-500/10 to-accent-500/10 blur-2xl"
          />
          <AgentActivityMockup />
        </div>
      </div>
    </section>
  )
}
