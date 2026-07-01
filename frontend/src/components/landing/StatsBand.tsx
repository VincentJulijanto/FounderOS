/**
 * Stats band. All figures are PLACEHOLDERS — replace with real, verified
 * numbers before launch. "7 agents" is the only value tied to the actual
 * product (the backend runs a 7-agent council).
 */
const STATS = [
  { value: '7', label: 'specialized agents on every decision', verified: true },
  { value: '4', label: 'debate rounds to reach consensus', verified: false },
  { value: '30-day', label: 'phased execution plan with every memo', verified: false },
]

export default function StatsBand() {
  return (
    <section className="max-w-6xl mx-auto px-6 py-20">
      <div className="grid sm:grid-cols-3 gap-12 sm:gap-8 text-center">
        {STATS.map((s) => (
          <div key={s.label}>
            {/* Solid ink numbers — no gradient fill */}
            <p className="text-5xl md:text-6xl font-semibold tracking-[-0.02em] text-graphite tabular-nums">
              {s.value}
            </p>
            <p className="mt-4 text-sm text-muted max-w-[16rem] mx-auto">
              {s.label}
              {!s.verified && (
                <span className="block mt-1 text-xs text-muted/70">(placeholder)</span>
              )}
            </p>
          </div>
        ))}
      </div>
    </section>
  )
}
