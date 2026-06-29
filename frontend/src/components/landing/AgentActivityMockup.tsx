import { Telescope, TrendingUp, Wallet, Rocket, Target, Check, Loader2 } from 'lucide-react'

/**
 * Lightweight, purely-decorative product-UI mockup for the hero.
 * Mirrors the real FounderOS "agent society" surface (see src/components/AgentDebate.tsx)
 * but is static and presentational — NOT a phone/bank dashboard.
 * All values here are illustrative PLACEHOLDERS.
 */

const AGENTS = [
  { name: 'Opportunity Scout', icon: Telescope, status: 'done', note: 'Found 12 market gaps' },
  { name: 'Trend Analyst', icon: TrendingUp, status: 'done', note: 'Demand scored' },
  { name: 'Finance Agent', icon: Wallet, status: 'running', note: 'Modelling unit economics' },
  { name: 'Growth Agent', icon: Rocket, status: 'queued', note: 'Acquisition plan' },
  { name: 'Skeptic Agent', icon: Target, status: 'queued', note: 'Stress-testing' },
] as const

const statusStyles: Record<string, string> = {
  done: 'text-brand-300 bg-brand-500/10 border-brand-500/30',
  running: 'text-accent-300 bg-accent-500/10 border-accent-500/30',
  queued: 'text-gray-400 bg-white/5 border-white/10',
}

export default function AgentActivityMockup() {
  return (
    <div
      className="glass p-5 shadow-2xl shadow-brand-950/40"
      role="img"
      aria-label="Illustration of the FounderOS agent society analysing a venture in real time"
    >
      {/* Window chrome */}
      <div className="flex items-center justify-between pb-4 border-b border-white/10">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-white/15" />
          <span className="w-2.5 h-2.5 rounded-full bg-white/15" />
          <span className="w-2.5 h-2.5 rounded-full bg-white/15" />
        </div>
        <span className="text-xs font-mono text-gray-500">agent-society · live</span>
      </div>

      {/* Agent rows */}
      <ul className="mt-4 space-y-2.5">
        {AGENTS.map((a) => {
          const Icon = a.icon
          return (
            <li
              key={a.name}
              className="flex items-center gap-3 rounded-xl border border-white/5 bg-white/[0.02] px-3 py-2.5"
            >
              <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500/20 to-accent-500/20 border border-white/10 flex items-center justify-center text-brand-300">
                <Icon className="w-4 h-4" aria-hidden="true" />
              </span>
              <span className="flex-1 min-w-0">
                <span className="block text-sm font-medium text-gray-200 truncate">{a.name}</span>
                <span className="block text-xs text-gray-500 truncate">{a.note}</span>
              </span>
              <span
                className={`badge border ${statusStyles[a.status]} gap-1`}
              >
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
      <div className="mt-4 flex items-center justify-between rounded-xl bg-gradient-to-r from-brand-500/10 to-accent-500/10 border border-white/10 px-4 py-3">
        <span className="text-xs text-gray-400">Consensus forming</span>
        <span className="text-sm font-mono font-semibold bg-gradient-to-r from-brand-300 to-accent-300 bg-clip-text text-transparent">
          7.8 / 10
        </span>
      </div>
    </div>
  )
}
