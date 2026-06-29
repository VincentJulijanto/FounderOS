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
    <section className="max-w-6xl mx-auto px-6 py-20 md:py-28">
      <div className="max-w-2xl">
        <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-gray-100">
          What people say
        </h2>
        <p className="mt-4 text-gray-400 text-lg">
          {/* PLACEHOLDER — quotes below are illustrative and not yet real. */}
          Early reactions from founders who ran their idea through the agents.
        </p>
      </div>

      <div className="mt-12 grid md:grid-cols-3 gap-6">
        {QUOTES.map((t, i) => (
          <figure key={i} className="glass p-7 flex flex-col">
            <Quote className="w-7 h-7 text-brand-400/60" aria-hidden="true" />
            <blockquote className="mt-4 flex-1 text-gray-300 leading-relaxed">
              {t.quote}
            </blockquote>
            <figcaption className="mt-6 flex items-center gap-3">
              <span
                aria-hidden="true"
                className="w-10 h-10 rounded-full bg-gradient-to-br from-brand-500 to-accent-500 flex items-center justify-center text-sm font-semibold text-white"
              >
                {t.initials}
              </span>
              <span>
                <span className="block text-sm font-medium text-gray-200">{t.name}</span>
                <span className="block text-xs text-gray-500">{t.role}</span>
              </span>
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
  )
}
