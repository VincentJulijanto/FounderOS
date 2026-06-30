'use client'

import { Check } from 'lucide-react'
import { StartupIdea } from '@/app/studio/page'

interface Props {
  idea: StartupIdea
  rank: number
  isSelected: boolean
  onSelect: () => void
}

const RISK_COLORS = {
  Low: 'text-green-700 bg-green-50 border-green-200',
  Medium: 'text-amber-700 bg-amber-50 border-amber-200',
  High: 'text-red-700 bg-red-50 border-red-200',
}

// Score bars, attributed to the owning agent (Beat 5).
const ScoreBar = ({ label, agent, score }: { label: string; agent: string; score: number }) => (
  <div className="space-y-1">
    <div className="flex justify-between text-xs">
      <span className="text-graphite/80">
        {label} <span className="text-muted">· {agent}</span>
      </span>
      <span className="font-mono text-graphite">{score.toFixed(1)}</span>
    </div>
    <div className="score-bar">
      <div className="score-fill bg-brand-500" style={{ width: `${(score / 10) * 100}%` }} />
    </div>
  </div>
)

export default function StartupCard({ idea, rank, isSelected, onSelect }: Props) {
  return (
    <button
      onClick={onSelect}
      aria-pressed={isSelected}
      className={`card text-left w-full transition-all duration-200 hover:border-graphite/30 ${
        isSelected ? 'border-brand-500 ring-1 ring-brand-500' : ''
      }`}
    >
      {/* Rank badge + risk */}
      <div className="flex items-start justify-between mb-3">
        <div className="w-7 h-7 rounded-full bg-graphite text-canvas flex items-center justify-center text-xs font-semibold">
          {rank}
        </div>
        <span className={`badge border ${RISK_COLORS[idea.risk_level as keyof typeof RISK_COLORS] || RISK_COLORS.Medium}`}>
          {idea.risk_level} risk
        </span>
      </div>

      {/* Name & tagline */}
      <h3 className="font-semibold text-lg mb-1 text-graphite">{idea.name}</h3>
      <p className="text-sm text-brand-600 mb-3">{idea.tagline}</p>
      <p className="text-xs text-muted mb-4 line-clamp-2">{idea.description}</p>

      {/* Key metrics */}
      <div className="grid grid-cols-2 gap-2 mb-4 text-xs">
        {[
          { k: 'Revenue', v: idea.estimated_monthly_revenue },
          { k: 'Launch in', v: idea.time_to_launch },
          { k: 'Investment', v: idea.initial_investment },
          { k: 'Market', v: idea.target_market },
        ].map((m) => (
          <div key={m.k} className="bg-canvas border border-hairline rounded-lg p-2">
            <div className="text-muted">{m.k}</div>
            <div className="text-graphite font-medium truncate">{m.v}</div>
          </div>
        ))}
      </div>

      {/* Score bars — each attributed to the agent that owns it */}
      <div className="space-y-2">
        <ScoreBar label="Overall" agent="Venture Partner" score={idea.startup_score} />
        <ScoreBar label="Feasibility" agent="Finance" score={idea.feasibility_score} />
        <ScoreBar label="Founder fit" agent="Founder-Fit" score={idea.founder_fit_score} />
      </div>

      {isSelected && (
        <div className="mt-4 text-xs text-center text-brand-600 font-medium flex items-center justify-center gap-1.5">
          <Check className="w-3.5 h-3.5" aria-hidden="true" />
          Execution plan shown below
        </div>
      )}
    </button>
  )
}
