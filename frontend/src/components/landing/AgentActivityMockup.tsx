import { Telescope, TrendingUp, Wallet, Rocket, Target, Check, Loader2 } from 'lucide-react'

/**
 * Light product-UI mockup for the marketing hero. White card, hairline border,
 * soft shadow — no dark glass. Mirrors the studio's "agent society" surface but
 * presentational only. All values are illustrative PLACEHOLDERS.
 */

const AGENTS = [
  { name: 'Opportunity Scout', icon: Telescope, status: 'done', note: 'Framed 4 options' },
  { name: 'Trend Analyst', icon: TrendingUp, status: 'done', note: 'Demand scored' },
  { name: 'Finance Agent', icon: Wallet, status: 'running', note: 'Modelling unit economics' },
  { name: 'Growth Agent', icon: Rocket, status: 'queued', note: 'Acquisition plan' },
  { name: 'Skeptic Agent', icon: Target, status: 'queued', note: 'Stress-testing' },
] as const

const statusStyles: Record<string, string> = {
  done: 'text-brand-700 bg-brand-500/10',
  running: 'text-accent-700 bg-accent-500/15',
  queued: 'text-muted bg-graphite/[0.04]',
}

export default function AgentActivityMockup() {
  return (
    <div
      className="card-light p-5"
      role="img"
      aria-label="Illustration of the FounderOS agent council evaluating a business decision in real time"
    >
      {/* Window chrome */}
      <div className="flex items-center justify-between pb-4 border-b border-hairline">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-graphite/10" />
          <span className="w-2.5 h-2.5 rounded-full bg-graphite/10" />
          <span className="w-2.5 h-2.5 rounded-full bg-graphite/10" />
        </div>
        <span className="text-xs font-mono text-muted">agent council · live</span>
      </div>

      {/* Agent rows */}
      <ul className="mt-4 space-y-2.5">
        {AGENTS.map((a) => {
          const Icon = a.icon
          return (
            <li
              key={a.name}
              className="flex items-center gap-3 rounded-xl border border-hairline bg-canvas/60 px-3 py-2.5"
            >
              <span className="w-8 h-8 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-600">
                <Icon className="w-4 h-4" aria-hidden="true" />
              </span>
              <span className="flex-1 min-w-0">
                <span className="block text-sm font-medium text-graphite truncate">{a.name}</span>
                <span className="block text-xs text-muted truncate">{a.note}</span>
              </span>
              <span className={`badge ${statusStyles[a.status]} gap-1`}>
                {a.status === 'done' && <Check className="w-3 h-3" aria-hidden="true" />}
                {a.status === 'running' && (
                  <Loader2 className="w-3 h-3 animate-spin" aria-hidden="true" />
                )}
                {a.status}
              </span>
            </li>
          )
        })}
      </ul>

      {/* Consensus footer */}
      <div className="mt-4 flex items-center justify-between rounded-xl border border-hairline bg-canvas/60 px-4 py-3">
        <span className="text-xs text-muted">Confidence</span>
        <span className="text-sm font-mono font-semibold text-accent-700">Medium</span>
      </div>
    </div>
  )
}
