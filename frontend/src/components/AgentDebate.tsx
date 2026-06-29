'use client'

import { useEffect, useState } from 'react'
import type { AgentOutput, DebateRound, ConsensusReport } from '@/app/studio/page'

interface Props {
  phase: 'analyzing' | 'debating'
  agentOutputs?: AgentOutput[]
  debateRounds?: DebateRound[]
  debateSummary?: string
  consensus?: ConsensusReport | null
  onContinue?: () => void
}

// Consensus = resolution rate, NOT idea quality. Colour by agreement level only.
const consensusTone = (score: number) =>
  score >= 8 ? 'border-green-700 bg-green-950/40 text-green-300'
    : score >= 5 ? 'border-yellow-700 bg-yellow-950/40 text-yellow-300'
    : 'border-red-800 bg-red-950/40 text-red-300'

// Canonical agent roster — icon + colour per agent. This is the real 7-agent
// line-up the backend runs; the live status/scores come from agentOutputs.
const ROSTER = [
  { name: 'Opportunity Scout', icon: '🔭', role: 'Scouting market gaps...', color: 'border-blue-700 bg-blue-950/40' },
  { name: 'Trend Analyst', icon: '📈', role: 'Analysing market demand...', color: 'border-green-700 bg-green-950/40' },
  { name: 'Finance Agent', icon: '💰', role: 'Running financial models...', color: 'border-yellow-700 bg-yellow-950/40' },
  { name: 'Growth Agent', icon: '🚀', role: 'Building acquisition strategy...', color: 'border-purple-700 bg-purple-950/40' },
  { name: 'Skeptic Agent', icon: '🎯', role: 'Challenging assumptions...', color: 'border-red-700 bg-red-950/40' },
  { name: 'Founder-Fit Agent', icon: '🧩', role: 'Scoring founder–opportunity fit...', color: 'border-teal-700 bg-teal-950/40' },
  { name: 'Venture Partner', icon: '🤝', role: 'Synthesising recommendation...', color: 'border-orange-700 bg-orange-950/40' },
]

const ICONS: Record<string, string> = Object.fromEntries(ROSTER.map(a => [a.name, a.icon]))
const iconFor = (name: string) => ICONS[name] ?? '🤖'

const SEVERITY_STYLE: Record<string, string> = {
  high: 'border-red-800 bg-red-950/30',
  medium: 'border-yellow-800 bg-yellow-950/30',
  low: 'border-gray-700 bg-gray-800/50',
}

export default function AgentDebate({ phase, agentOutputs, debateRounds, debateSummary, consensus, onContinue }: Props) {
  const [visibleAgents, setVisibleAgents] = useState<number[]>([])
  const [currentStatus, setCurrentStatus] = useState('Initialising agent society...')

  // Reveal the roster one-by-one while the backend is working.
  useEffect(() => {
    ROSTER.forEach((_, i) => {
      setTimeout(() => {
        setVisibleAgents(prev => (prev.includes(i) ? prev : [...prev, i]))
        setCurrentStatus(ROSTER[i].role)
      }, i * 400)
    })
  }, [])

  useEffect(() => {
    if (phase === 'debating') {
      const rounds = debateRounds?.length ?? 0
      setCurrentStatus(rounds > 0
        ? `Debate complete — ${rounds} round${rounds === 1 ? '' : 's'} of conflict resolution.`
        : 'Consensus reached — agents agreed without debate.')
    }
  }, [phase, debateRounds])

  const rounds = debateRounds ?? []

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">

      {/* Status */}
      <div className="card text-center py-6">
        <div className="flex items-center justify-center gap-3 mb-2">
          <div className="flex gap-1">
            {[0, 1, 2].map(i => (
              <div
                key={i}
                className="w-2 h-2 rounded-full bg-brand-400 animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
          <span className="text-brand-400 font-medium">{currentStatus}</span>
        </div>
        <p className="text-sm text-gray-500">
          {phase === 'analyzing'
            ? 'Agents are independently analysing your profile...'
            : 'Debate protocol complete — review how the agents reasoned about your profile.'}
        </p>
      </div>

      {/* Agent Grid — the live roster (real status once outputs arrive) */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {ROSTER.map((agent, i) => {
          const output = agentOutputs?.find(o => o.agent_name === agent.name)
          const done = phase === 'debating'
          return (
            <div
              key={agent.name}
              className={`agent-bubble ${agent.color} transition-all duration-500 ${
                visibleAgents.includes(i) || done ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
              }`}
            >
              <span className="text-2xl">{agent.icon}</span>
              <div className="min-w-0">
                <div className="text-sm font-semibold flex items-center gap-2">
                  {agent.name}
                  {done && output?.score != null && (
                    <span className="badge bg-brand-500/20 text-brand-400 border border-brand-600/30">
                      {output.score}/10
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-400 mt-0.5 truncate">
                  {done ? (
                    output ? `✓ ${output.role}` : 'No output'
                  ) : visibleAgents.includes(i) ? (
                    <span className="flex items-center gap-1">
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                      {agent.role}
                    </span>
                  ) : 'Waiting...'}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Debate Stream — driven entirely by real backend data */}
      {phase === 'debating' && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="text-red-400 text-lg">⚡</span>
              <h3 className="font-semibold">
                {rounds.length > 0
                  ? `Debate — ${rounds.length} round${rounds.length === 1 ? '' : 's'}`
                  : 'Consensus'}
              </h3>
            </div>
            {consensus && (
              <span
                className={`badge border ${consensusTone(consensus.consensus_score)}`}
                title="Severity-weighted share of conflicts resolved — a measure of agreement, not idea quality."
              >
                {consensus.label} · {consensus.consensus_score}/10
              </span>
            )}
          </div>

          {/* Consensus meter — resolution rate, not a quality score */}
          {consensus && consensus.total_conflicts > 0 && (
            <div className="text-xs text-gray-400">
              {consensus.resolved_conflicts} of {consensus.total_conflicts} conflict
              {consensus.total_conflicts === 1 ? '' : 's'} resolved over {consensus.rounds_used} round
              {consensus.rounds_used === 1 ? '' : 's'}.
            </div>
          )}

          {rounds.length === 0 && (
            <p className="text-sm text-gray-400 p-3 rounded-lg border border-green-800 bg-green-950/30">
              {debateSummary || 'All agents reached consensus without debate.'}
            </p>
          )}

          {rounds.map(round => (
            <div key={round.round_number} className="space-y-3 border-t border-gray-800 pt-3 first:border-0 first:pt-0">
              <div className="flex items-center gap-2 text-sm">
                <span className="font-semibold">Round {round.round_number}</span>
                <span className={`badge border ${
                  round.resolution_achieved
                    ? 'border-green-700 bg-green-950/40 text-green-400'
                    : 'border-yellow-700 bg-yellow-950/40 text-yellow-400'
                }`}>
                  {round.resolution_achieved ? 'Resolved' : 'Ongoing'}
                </span>
              </div>

              {/* Conflicts in this round */}
              {round.conflicts_identified.map((c, ci) => (
                <div key={ci} className={`p-3 rounded-lg border text-sm ${SEVERITY_STYLE[c.severity] ?? SEVERITY_STYLE.low}`}>
                  <div className="font-medium text-gray-300 mb-1 flex items-center gap-2">
                    <span>{c.topic} <span className="text-xs text-gray-500">({c.severity})</span></span>
                    <span className={`badge border text-xs ${
                      c.resolved
                        ? 'border-green-700 bg-green-950/40 text-green-400'
                        : 'border-yellow-700 bg-yellow-950/40 text-yellow-400'
                    }`}>
                      {c.resolved ? 'resolved' : 'open'}
                    </span>
                  </div>
                  <div className="text-gray-400">
                    <span className="font-medium">{iconFor(c.agent_a)} {c.agent_a}:</span> {c.agent_a_position}
                  </div>
                  <div className="text-gray-400">
                    <span className="font-medium">{iconFor(c.agent_b)} {c.agent_b}:</span> {c.agent_b_position}
                  </div>
                </div>
              ))}

              {/* Revised positions (rebuttals) */}
              {Object.entries(round.revised_positions).map(([agent, stance]) => (
                <div key={agent} className="p-3 rounded-lg border border-purple-800 bg-purple-950/30 text-sm">
                  <span className="font-medium text-gray-300">{iconFor(agent)} {agent} revised: </span>
                  <span className="text-gray-400">{stance}</span>
                </div>
              ))}

              {round.moderator_summary && (
                <div className="p-3 rounded-lg border border-blue-800 bg-blue-950/30 text-sm">
                  <span className="font-medium text-gray-300">🧑‍⚖️ Moderator: </span>
                  <span className="text-gray-400">{round.moderator_summary}</span>
                </div>
              )}
            </div>
          ))}

          {/* Unresolved conflicts surfaced (not hidden) */}
          {consensus && consensus.unresolved_conflicts.length > 0 && (
            <div className="p-3 rounded-lg border border-yellow-800 bg-yellow-950/20 text-sm">
              <div className="font-medium text-yellow-300 mb-2">
                ⚠ Unresolved — surfaced for your judgement
              </div>
              <ul className="space-y-1 text-gray-400">
                {consensus.unresolved_conflicts.map((c, i) => (
                  <li key={i}>
                    <span className="text-gray-300">{c.topic}</span>{' '}
                    <span className="text-xs text-gray-500">({c.severity})</span> —{' '}
                    {iconFor(c.agent_a)} {c.agent_a} vs {iconFor(c.agent_b)} {c.agent_b}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Consensus summary + advance */}
          {debateSummary && rounds.length > 0 && (
            <div className="p-3 rounded-lg border border-green-800 bg-green-950/30 text-sm text-gray-300 whitespace-pre-line">
              <span className="font-medium">Consensus: </span>{debateSummary}
            </div>
          )}

          {onContinue && (
            <button onClick={onContinue} className="btn-primary w-full">
              See your startup plan →
            </button>
          )}
        </div>
      )}
    </div>
  )
}
