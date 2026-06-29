import { Users, MessagesSquare, FileCheck2 } from 'lucide-react'

const FEATURES = [
  {
    icon: Users,
    title: 'A society of specialists',
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
    <section id="features" className="max-w-6xl mx-auto px-6 py-20 md:py-28 scroll-mt-24">
      <div className="max-w-2xl">
        <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-gray-100">
          One idea in, a full team&rsquo;s thinking out
        </h2>
        <p className="mt-4 text-gray-400 text-lg">
          FounderOS replaces the blank page with a coordinated panel of agents that
          do the analysis a founding team would.
        </p>
      </div>

      <div className="mt-12 grid md:grid-cols-3 gap-6">
        {FEATURES.map((f) => {
          const Icon = f.icon
          return (
            <article
              key={f.title}
              className="glass p-7 hover:border-white/20 transition-colors"
            >
              <span className="inline-flex w-12 h-12 rounded-xl bg-gradient-to-br from-brand-500/20 to-accent-500/20 border border-white/10 items-center justify-center text-brand-300">
                <Icon className="w-6 h-6" aria-hidden="true" />
              </span>
              <h3 className="mt-5 text-lg font-semibold text-gray-100">{f.title}</h3>
              <p className="mt-2 text-sm text-gray-400 leading-relaxed">{f.body}</p>
            </article>
          )
        })}
      </div>
    </section>
  )
}
