'use client'

import { StartupIdea } from '@/app/page'

interface Props {
  idea: StartupIdea
  rank: number
  isSelected: boolean
  onSelect: () => void
}

const RISK_COLORS = {
  Low: 'text-green-400 bg-green-950/50 border-green-800',
  Medium: 'text-yellow-400 bg-yellow-950/50 border-yellow-800',
  High: 'text-red-400 bg-red-950/50 border-red-800',
}

const ScoreBar = ({ label, score }: { label: string; score: number }) => {
  const color =
    score >= 7 ? 'bg-green-500' :
    score >= 5 ? 'bg-yellow-500' :
    'bg-red-500'

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-gray-400">
        <span>{label}</span>
        <span className="font-mono">{score.toFixed(1)}</span>
      </div>
      <div className="score-bar">
        <div
          className={`score-fill ${color}`}
          style={{ width: `${(score / 10) * 100}%` }}
        />
      </div>
    </div>
  )
}

export default function StartupCard({ idea, rank, isSelected, onSelect }: Props) {
  const rankColors = ['from-yellow-500 to-orange-500', 'from-gray-400 to-gray-500', 'from-amber-600 to-amber-700']
  const isTop = rank === 1

  return (
    <button
      onClick={onSelect}
      className={`card text-left w-full transition-all duration-200 hover:border-brand-600 ${
        isSelected ? 'border-brand-500 ring-1 ring-brand-500' : ''
      } ${isTop ? 'md:col-span-1' : ''}`}
    >
      {/* Rank badge */}
      <div className="flex items-start justify-between mb-3">
        <div className={`w-7 h-7 rounded-full bg-gradient-to-br ${rankColors[rank - 1]} flex items-center justify-center text-xs font-bold text-white`}>
          {rank}
        </div>
        <span className={`badge border ${RISK_COLORS[idea.risk_level as keyof typeof RISK_COLORS] || RISK_COLORS.Medium}`}>
          {idea.risk_level} Risk
        </span>
      </div>

      {/* Name & tagline */}
      <h3 className="font-bold text-lg mb-1 text-white">{idea.name}</h3>
      <p className="text-sm text-brand-400 mb-3">{idea.tagline}</p>
      <p className="text-xs text-gray-500 mb-4 line-clamp-2">{idea.description}</p>

      {/* Key metrics */}
      <div className="grid grid-cols-2 gap-2 mb-4 text-xs">
        <div className="bg-gray-800 rounded-lg p-2">
          <div className="text-gray-500">Revenue</div>
          <div className="text-green-400 font-medium">{idea.estimated_monthly_revenue}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-2">
          <div className="text-gray-500">Launch in</div>
          <div className="text-blue-400 font-medium">{idea.time_to_launch}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-2">
          <div className="text-gray-500">Investment</div>
          <div className="text-yellow-400 font-medium">{idea.initial_investment}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-2">
          <div className="text-gray-500">Market</div>
          <div className="text-purple-400 font-medium text-xs truncate">{idea.target_market}</div>
        </div>
      </div>

      {/* Score bars */}
      <div className="space-y-2">
        <ScoreBar label="Overall Score" score={idea.startup_score} />
        <ScoreBar label="Feasibility" score={idea.feasibility_score} />
        <ScoreBar label="Founder Fit" score={idea.founder_fit_score} />
      </div>

      {isSelected && (
        <div className="mt-4 text-xs text-center text-brand-400 font-medium">
          ✓ Execution plan shown below
        </div>
      )}
    </button>
  )
}
