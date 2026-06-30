import { Users, MessagesSquare, FileCheck2 } from 'lucide-react'

const FEATURES = [
  {
    icon: Users,
    title: 'A council of specialists',
    body: 'Seven agents — Scout, Trend Analyst, Finance, Growth, Skeptic, Founder-Fit, and Venture Partner — each examine your idea from their own angle.',
  },
  {
    icon: MessagesSquare,
    title: 'Structured debate to consensus',
    body: 'Agents surface conflicts and argue them out across rounds, so you get a recommendation that has already survived its toughest critics.',
  },
  {
    icon: FileCheck2,
    title: 'Execution-ready output',
    body: 'Walk away with a lean canvas, MVP scope, 30-day roadmap, and outreach templates — not just a score, but a plan you can act on.',
  },
]

export default function FeatureCards() {
  return (
    <section id="features" className="max-w-6xl mx-auto px-6 py-24 md:py-28 scroll-mt-24">
      <div className="max-w-2xl">
        <h2 className="text-3xl md:text-[2.5rem] font-semibold tracking-[-0.02em] leading-[1.12] text-graphite">
          One idea in, a full team&rsquo;s thinking out
        </h2>
        <p className="mt-5 text-muted text-lg leading-relaxed">
          FounderOS replaces the blank page with a coordinated panel of agents that
          do the analysis a founding team would.
        </p>
      </div>

      <div className="mt-14 grid md:grid-cols-3 gap-6">
        {FEATURES.map((f) => {
          const Icon = f.icon
          return (
            <article key={f.title} className="card-light p-7">
              <span className="inline-flex w-11 h-11 rounded-xl bg-brand-500/10 items-center justify-center text-brand-600">
                <Icon className="w-5 h-5" aria-hidden="true" />
              </span>
              <h3 className="mt-5 text-lg font-semibold text-graphite">{f.title}</h3>
              <p className="mt-2.5 text-sm text-muted leading-relaxed">{f.body}</p>
            </article>
          )
        })}
      </div>
    </section>
  )
}
