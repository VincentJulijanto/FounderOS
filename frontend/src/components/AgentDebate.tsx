'use client'

import { useEffect, useState } from 'react'
import { Gavel, AlertTriangle, Check, ArrowRight } from 'lucide-react'
import type { AgentOutput, DebateRound, ConsensusReport } from '@/lib/types'
import { ROSTER, iconFor, labelFor, roleFor } from '@/components/agentRoster'

interface Props {
  phase: 'analyzing' | 'debating'
  /** The response has arrived — compress any staging still pending (mock/fast runs). */
  responseReady?: boolean
  agentOutputs?: AgentOutput[]
  debateRounds?: DebateRound[]
  debateSummary?: string
  consensus?: ConsensusReport | null
  onContinue?: () => void
}

const SKEPTIC = 'skeptic' // canonical agent-name string

/**
 * The pipeline shape the wait state walks (mirrors graph.py):
 * scout → four analysts in parallel → skeptic → debate → chair.
 * Durations pace a ~110s typical live run (validated runs land 90–140s, and
 * the analysts finish in ~10s), reaching the chair by ~80s so even a fast run
 * shows every stage; the last stage holds until the response actually arrives.
 * Once it has (responseReady), remaining stages play compressed so mock/fast
 * runs still show the pass without faking slowness.
 */
const STAGES: { agents: string[]; status: string; secs: number }[] = [
  { agents: ['scout'], status: 'The Scout is framing the options on the table...', secs: 10 },
  { agents: ['trend', 'finance', 'growth', 'capability'], status: 'Four analysts are reading the decision in parallel...', secs: 30 },
  { agents: ['skeptic'], status: 'The Skeptic is attacking the assumptions...', secs: 25 },
  { agents: [], status: 'The board is debating the conflicts...', secs: 15 },
  { agents: ['venture_partner'], status: 'The Chair is writing the board memo...', secs: 15 },
]
const COMPRESSED_STAGE_MS = 450

type TileState = 'queued' | 'working' | 'done'

// Consensus = resolution rate, NOT idea quality. Status colours only (not brand gold).
const consensusTone = (score: number) =>
  score >= 8 ? 'border-green-200 bg-green-50 text-green-700'
    : score >= 5 ? 'border-amber-200 bg-amber-50 text-amber-700'
    : 'border-red-200 bg-red-50 text-red-700'

// One readable turn in the debate transcript.
interface Turn {
  key: string
  speaker: string
  role: string
  text: string
  kind: 'argument' | 'rebuttal' | 'moderator'
  topic?: string
  isChallenge: boolean // the Skeptic pushing back — the one gold moment
}

// Flatten the structured rounds into a paced, readable sequence of speaker turns.
function buildTurns(rounds: DebateRound[]): Turn[] {
  const turns: Turn[] = []
  rounds.forEach((round, ri) => {
    round.conflicts_identified.forEach((c, ci) => {
      turns.push({
        key: `r${ri}-c${ci}-a`, speaker: c.agent_a, role: roleFor(c.agent_a),
        text: c.agent_a_position, kind: 'argument', topic: c.topic,
        isChallenge: c.agent_a === SKEPTIC,
      })
      turns.push({
        key: `r${ri}-c${ci}-b`, speaker: c.agent_b, role: roleFor(c.agent_b),
        text: c.agent_b_position, kind: 'argument', topic: c.topic,
        isChallenge: c.agent_b === SKEPTIC,
      })
    })
    Object.entries(round.revised_positions).forEach(([agent, stance], i) => {
      turns.push({
        key: `r${ri}-rev${i}`, speaker: agent, role: roleFor(agent),
        text: stance, kind: 'rebuttal', isChallenge: false,
      })
    })
    if (round.moderator_summary) {
      turns.push({
        key: `r${ri}-mod`, speaker: 'Moderator', role: 'Tracks conflicts toward consensus',
        text: round.moderator_summary, kind: 'moderator', isChallenge: false,
      })
    }
  })
  return turns
}

export default function AgentDebate({ phase, responseReady, agentOutputs, debateRounds, debateSummary, consensus, onContinue }: Props) {
  const [stageIdx, setStageIdx] = useState(0)
  const [elapsed, setElapsed] = useState(0)
  const [revealed, setRevealed] = useState(0)

  // Advance the pipeline stages while the board works. Each advance is a single
  // timeout whose cleanup runs on any phase/stage/readiness change, so no timer
  // ever outlives the real data — the status can't be overwritten after arrival.
  useEffect(() => {
    if (phase !== 'analyzing' || stageIdx >= STAGES.length - 1) return
    const ms = responseReady ? COMPRESSED_STAGE_MS : STAGES[stageIdx].secs * 1000
    const id = setTimeout(() => setStageIdx(i => Math.min(i + 1, STAGES.length - 1)), ms)
    return () => clearTimeout(id)
  }, [phase, stageIdx, responseReady])

  // Elapsed-time counter for the wait.
  useEffect(() => {
    if (phase !== 'analyzing') return
    const id = setInterval(() => setElapsed(e => e + 1), 1000)
    return () => clearInterval(id)
  }, [phase])

  // Status is derived, not stored — once phase flips, the stage copy is inert.
  const rounds = debateRounds ?? []
  const currentStatus = phase === 'analyzing'
    ? STAGES[stageIdx].status
    : rounds.length > 0
      ? `Debate complete — ${rounds.length} round${rounds.length === 1 ? '' : 's'} of conflict resolution.`
      : 'Consensus reached — the board agreed without debate.'

  const tileState = (name: string): TileState => {
    if (phase === 'debating') return 'done'
    const idx = STAGES.findIndex(s => s.agents.includes(name))
    if (idx < stageIdx) return 'done'
    if (idx === stageIdx) return 'working'
    return 'queued'
  }

  const turns = buildTurns(rounds)

  // Beat 4 — pace the transcript: reveal one turn at a time.
  useEffect(() => {
    if (phase !== 'debating' || turns.length === 0) return
    setRevealed(1)
    const id = setInterval(() => {
      setRevealed(r => {
        if (r >= turns.length) { clearInterval(id); return r }
        return r + 1
      })
    }, 700)
    return () => clearInterval(id)
  }, [phase, turns.length])

  return (
    <div className="max-w-3xl mx-auto space-y-6">

      {/* Status — Beat 3: "Council convening" */}
      <div className="card text-center py-6">
        <div className="flex items-center justify-center gap-3 mb-2">
          {phase === 'analyzing' && (
            <div className="flex gap-1">
              {[0, 1, 2].map(i => (
                <div
                  key={i}
                  className="w-2 h-2 rounded-full bg-brand-500 animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
          )}
          <span className="text-graphite font-medium">{currentStatus}</span>
        </div>
        <p className="text-sm text-muted">
          {phase === 'analyzing'
            ? 'The board is convening — each agent evaluates your decision independently.'
            : 'Here is how the board reasoned about your decision.'}
        </p>
        {phase === 'analyzing' && (
          <p className="text-xs text-muted mt-2 font-mono tabular-nums">
            {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, '0')} elapsed
            <span className="font-sans"> · a live run typically takes 2–4 min</span>
          </p>
        )}
      </div>

      {/* Board roster — tiles progress queued → working → done down the pipeline;
          the Chair anchors its own full-width row (synthesis). */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {ROSTER.map((agent) => {
          const output = agentOutputs?.find(o => o.agent_name === agent.name)
          const state = tileState(agent.name)
          const hasData = phase === 'debating'
          const Icon = agent.Icon
          return (
            <div
              key={agent.name}
              className={`agent-bubble bg-white border-hairline transition-all duration-500 ${
                agent.name === 'venture_partner' ? 'col-span-2 md:col-span-3' : ''
              } ${state === 'queued' ? 'opacity-60' : 'opacity-100'}`}
            >
              <span className="shrink-0 w-9 h-9 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-600">
                <Icon className="w-4 h-4" aria-hidden="true" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-sm font-semibold text-graphite">{agent.label}</span>
                  {hasData && output?.score != null ? (
                    <span className="badge bg-brand-500/10 text-brand-700 font-mono shrink-0">
                      {output.score}/10
                    </span>
                  ) : state === 'done' ? (
                    <Check className="w-3.5 h-3.5 mt-0.5 shrink-0 text-brand-600" aria-hidden="true" />
                  ) : null}
                </div>
                <div className="text-xs text-muted mt-0.5">
                  {hasData ? (
                    output ? (
                      <span className="flex items-start gap-1">
                        <Check className="w-3 h-3 mt-0.5 shrink-0 text-brand-600" aria-hidden="true" />
                        <span className="line-clamp-2">{agent.role}</span>
                      </span>
                    ) : 'No output'
                  ) : state === 'working' ? (
                    <span className="flex items-start gap-1.5">
                      <span className="mt-1 inline-block w-1.5 h-1.5 shrink-0 rounded-full bg-brand-500 animate-pulse" />
                      <span className="line-clamp-2">{agent.status}</span>
                    </span>
                  ) : state === 'done' ? (
                    <span className="line-clamp-2">Done — {agent.role.toLowerCase()}</span>
                  ) : (
                    'Queued'
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Beat 4 — the debate as a readable transcript */}
      {phase === 'debating' && (
        <div className="space-y-5">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-2xl font-semibold tracking-[-0.01em]">The debate</h3>
            {consensus && (consensus.total_conflicts > 0 && consensus.resolved_conflicts === 0 ? (
              // Nothing resolved: an honest state, not a score. A red 0/10 reads
              // as "broken" when the real story is disagreement kept on record.
              <span
                className="badge border border-amber-200 bg-amber-50 text-amber-700"
                title="No conflicts resolved — the disagreement is preserved as dissent in the memo."
              >
                Contested — dissent recorded
              </span>
            ) : (
              <span
                className={`badge border ${consensusTone(consensus.consensus_score)}`}
                title="Severity-weighted share of conflicts resolved — a measure of agreement, not idea quality."
              >
                {consensus.label} · {consensus.consensus_score}/10
              </span>
            ))}
          </div>

          {consensus && consensus.total_conflicts > 0 && (
            <p className="text-sm text-muted">
              {consensus.resolved_conflicts} of {consensus.total_conflicts} conflict
              {consensus.total_conflicts === 1 ? '' : 's'} resolved over {consensus.rounds_used} round
              {consensus.rounds_used === 1 ? '' : 's'}.
            </p>
          )}

          {turns.length === 0 && (
            <div className="card text-sm text-graphite/80">
              {debateSummary || 'All agents reached consensus without debate.'}
            </div>
          )}

          {/* Transcript */}
          <div className="space-y-5">
            {turns.slice(0, revealed).map((turn) => {
              const Icon = turn.kind === 'moderator' ? Gavel : iconFor(turn.speaker)

              // The one gold-accented moment: the Skeptic's challenge.
              if (turn.isChallenge) {
                return (
                  <div
                    key={turn.key}
                    className="animate-slide-up rounded-2xl border border-accent-600/40 bg-accent-500/[0.07] p-5"
                  >
                    <div className="flex items-center gap-2.5 mb-2">
                      <span className="w-9 h-9 rounded-lg bg-accent-500/15 flex items-center justify-center text-accent-700">
                        <Icon className="w-4 h-4" aria-hidden="true" />
                      </span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-graphite">{labelFor(turn.speaker)}</span>
                          <span className="badge bg-accent-500/20 text-accent-700 uppercase tracking-wide text-[10px]">
                            Challenge
                          </span>
                        </div>
                        {turn.topic && <div className="text-xs text-muted">on {turn.topic}</div>}
                      </div>
                    </div>
                    <p className="text-graphite/90 leading-relaxed">{turn.text}</p>
                  </div>
                )
              }

              if (turn.kind === 'moderator') {
                return (
                  <div key={turn.key} className="animate-slide-up flex items-start gap-3 pl-1">
                    <span className="mt-0.5 shrink-0 w-7 h-7 rounded-lg bg-graphite/[0.05] flex items-center justify-center text-muted">
                      <Icon className="w-3.5 h-3.5" aria-hidden="true" />
                    </span>
                    <p className="text-sm text-muted italic leading-relaxed">
                      <span className="font-medium not-italic text-graphite/70">Moderator — </span>
                      {turn.text}
                    </p>
                  </div>
                )
              }

              // Regular argument / rebuttal turn
              return (
                <div key={turn.key} className="animate-slide-up flex items-start gap-3">
                  <span className="mt-0.5 shrink-0 w-9 h-9 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-600">
                    <Icon className="w-4 h-4" aria-hidden="true" />
                  </span>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-baseline gap-x-2">
                      <span className="text-sm font-semibold text-graphite">{labelFor(turn.speaker)}</span>
                      {turn.role && <span className="text-xs text-muted">{turn.role}</span>}
                      {turn.kind === 'rebuttal' && (
                        <span className="badge bg-brand-500/10 text-brand-700 text-[10px]">revised</span>
                      )}
                      {turn.topic && turn.kind === 'argument' && (
                        <span className="text-xs text-muted">on {turn.topic}</span>
                      )}
                    </div>
                    <p className="mt-1 text-graphite/85 leading-relaxed">{turn.text}</p>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Unresolved conflicts surfaced (not hidden) */}
          {revealed >= turns.length && consensus && consensus.unresolved_conflicts.length > 0 && (
            <div className="card !p-4 border-amber-200 bg-amber-50/60">
              <div className="font-medium text-amber-700 mb-2 inline-flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" aria-hidden="true" />
                Unresolved — surfaced for your judgement
              </div>
              <ul className="space-y-1 text-sm text-graphite/80">
                {consensus.unresolved_conflicts.map((c, i) => (
                  <li key={i}>
                    <span className="font-medium">{c.topic}</span>{' '}
                    <span className="text-xs text-muted">({c.severity})</span> — {labelFor(c.agent_a)} vs {labelFor(c.agent_b)}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Consensus summary */}
          {revealed >= turns.length && debateSummary && turns.length > 0 && (
            <div className="card text-sm text-graphite/80 whitespace-pre-line">
              <span className="font-medium text-graphite">Consensus — </span>{debateSummary}
            </div>
          )}

          {onContinue && (
            <button onClick={onContinue} className="btn-primary w-full">
              See the board memo
              <ArrowRight className="w-4 h-4" aria-hidden="true" />
            </button>
          )}
        </div>
      )}
    </div>
  )
}
