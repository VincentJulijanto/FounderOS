import { Quote } from 'lucide-react'

/**
 * PLACEHOLDER testimonials — fictional names, roles, and quotes.
 * Replace with real, attributed quotes (with permission) before launch.
 */
const QUOTES = [
  {
    quote:
      'It felt like having a founding team in the room. The skeptic agent caught a pricing flaw I would have shipped.',
    name: 'Placeholder Name',
    role: 'Solo founder, productivity tools',
    initials: 'PN',
  },
  {
    quote:
      'I went from a vague interest to a ranked shortlist and a 30-day plan in one afternoon. The debate is what sold me.',
    name: 'Placeholder Name',
    role: 'First-time founder, EdTech',
    initials: 'PN',
  },
  {
    quote:
      'The plan was specific to my budget and skills, not generic advice. I started building the MVP the same week.',
    name: 'Placeholder Name',
    role: 'Indie maker, creator economy',
    initials: 'PN',
  },
]

export default function Testimonials() {
  return (
    <section className="max-w-6xl mx-auto px-6 py-24 md:py-28">
      <div className="max-w-2xl">
        <h2 className="text-3xl md:text-[2.5rem] font-semibold tracking-[-0.02em] leading-[1.12] text-graphite">
          What people say
        </h2>
        <p className="mt-5 text-muted text-lg leading-relaxed">
          {/* PLACEHOLDER — quotes below are illustrative and not yet real. */}
          Early reactions from founders who ran their idea through the council.
        </p>
      </div>

      <div className="mt-14 grid md:grid-cols-3 gap-6">
        {QUOTES.map((t, i) => (
          <figure key={i} className="card-light p-7 flex flex-col">
            <Quote className="w-6 h-6 text-accent-600" aria-hidden="true" />
            <blockquote className="mt-4 flex-1 text-graphite leading-relaxed">
              {t.quote}
            </blockquote>
            <figcaption className="mt-6 flex items-center gap-3">
              <span
                aria-hidden="true"
                className="w-9 h-9 rounded-full bg-brand-500/12 text-brand-600 flex items-center justify-center text-sm font-semibold"
              >
                {t.initials}
              </span>
              <span>
                <span className="block text-sm font-medium text-graphite">{t.name}</span>
                <span className="block text-xs text-muted">{t.role}</span>
              </span>
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
  )
}
