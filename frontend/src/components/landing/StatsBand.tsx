/**
 * Stats band. All figures are PLACEHOLDERS — replace with real, verified
 * numbers before launch. "7 agents" is the only value tied to the actual
 * product (the backend runs a 7-agent roster).
 */
const STATS = [
  { value: '7', label: 'specialized agents per analysis', verified: true },
  { value: '4', label: 'debate rounds to reach consensus', verified: false },
  { value: '30-day', label: 'execution roadmap with every plan', verified: false },
]

export default function StatsBand() {
  return (
    <section className="relative overflow-hidden border-y border-white/5">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            'linear-gradient(90deg, rgba(14,165,233,0.06), rgba(139,92,246,0.06))',
        }}
      />
      <div className="max-w-6xl mx-auto px-6 py-16 grid sm:grid-cols-3 gap-10 text-center">
        {STATS.map((s) => (
          <div key={s.label}>
            <p className="text-4xl md:text-5xl font-bold tracking-tight bg-gradient-to-r from-brand-400 to-accent-400 bg-clip-text text-transparent">
              {s.value}
            </p>
            <p className="mt-3 text-sm text-gray-400 max-w-[16rem] mx-auto">
              {s.label}
              {!s.verified && (
                <span className="block mt-1 text-xs text-gray-600">(placeholder)</span>
              )}
            </p>
          </div>
        ))}
      </div>
    </section>
  )
}
