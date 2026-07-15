'use client'

import {
  BarChart3,
  Wrench,
  Bug,
  CheckCircle2,
  XCircle,
  Rocket,
  PauseCircle,
  Filter,
  ShieldAlert,
  Sparkles,
} from 'lucide-react'
import type { CouncilTurn, FeatureLoopResponse, QAIssue } from '@/lib/types'

interface Props {
  data: FeatureLoopResponse
}

// ── Agent display metadata for the loop turns ────────────────────────────────

const LOOP_AGENTS: Record<string, { label: string; Icon: React.ElementType; color: string; bg: string }> = {
  feedback_analyst: {
    label: 'Data Analyst',
    Icon: BarChart3,
    color: 'text-sky-400',
    bg: 'border-sky-700/50 bg-sky-950/30',
  },
  senior_swe: {
    label: 'Senior SWE',
    Icon: Wrench,
    color: 'text-accent-400',
    bg: 'border-accent-500/50 bg-accent-700/10',
  },
  qa_engineer: {
    label: 'QA Engineer',
    Icon: Bug,
    color: 'text-rose-400',
    bg: 'border-rose-700/50 bg-rose-950/25',
  },
}

const STATUS_META: Record<FeatureLoopResponse['status'], { label: string; desc: string; Icon: React.ElementType; classes: string }> = {
  released: {
    label: 'Released',
    desc: 'QA passed — the feature cleared the loop and a release note was written to the vault.',
    Icon: Rocket,
    classes: 'border-brand-500/50 bg-brand-500/10 text-brand-400',
  },
  held: {
    label: 'Held — open issues',
    desc: 'QA still failing at the round cap. Nothing ships until the open issues are resolved.',
    Icon: PauseCircle,
    classes: 'border-rose-700/50 bg-rose-950/25 text-rose-400',
  },
  insufficient_signal: {
    label: 'Not built — insufficient signal',
    desc: 'The Data Analyst gate stopped the loop: the feedback does not yet represent enough users.',
    Icon: Filter,
    classes: 'border-hairline bg-surface text-muted',
  },
}

const SEVERITY_CLASSES: Record<QAIssue['severity'], string> = {
  high: 'text-rose-400 bg-rose-950/40 border-rose-700/40',
  medium: 'text-accent-400 bg-accent-700/10 border-accent-600/30',
  low: 'text-muted bg-surface border-hairline',
}

function LoopTurn({ turn, index }: { turn: CouncilTurn; index: number }) {
  const meta = LOOP_AGENTS[turn.agent] ?? {
    label: turn.agent, Icon: Sparkles, color: 'text-muted', bg: 'border-hairline bg-surface',
  }
  const { Icon, label, color, bg } = meta

  return (
    <div className={`rounded-xl border p-5 ${bg}`}>
      <div className="flex items-start gap-3">
        <span className={`mt-0.5 ${color}`} aria-hidden="true">
          <Icon className="w-5 h-5" />
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-graphite mb-1">{label}</p>
          <p className="text-sm text-graphite leading-relaxed whitespace-pre-line">{turn.message}</p>
          {turn.challenges.length > 0 && (
            <ul className="mt-3 space-y-1">
              {turn.challenges.map((c, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-rose-300">
                  <XCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-500" aria-hidden="true" />
                  {c}
                </li>
              ))}
            </ul>
          )}
        </div>
        <span className="text-xs text-muted shrink-0">Turn {index + 1}</span>
      </div>
    </div>
  )
}

function SpecList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null
  return (
    <div>
      <p className="text-xs text-muted uppercase tracking-wider font-medium mb-1.5">{title}</p>
      <ul className="space-y-1">
        {items.map((s, i) => (
          <li key={i} className="text-sm text-graphite leading-relaxed flex items-start gap-2">
            <span className="text-muted mt-0.5 shrink-0">·</span>
            {s}
          </li>
        ))}
      </ul>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export default function FeatureLoop({ data }: Props) {
  const { theme, gate, loop_dialogue, build_spec, qa_rounds, status, release_note_path } = data
  const statusMeta = STATUS_META[status]
  const StatusIcon = statusMeta.Icon

  return (
    <div className="space-y-8 animate-fade-in">

      {/* Status banner */}
      <div className={`rounded-xl border p-5 flex items-start gap-3 ${statusMeta.classes}`}>
        <StatusIcon className="w-5 h-5 shrink-0 mt-0.5" aria-hidden="true" />
        <div>
          <p className="text-base font-semibold">{statusMeta.label}</p>
          <p className="text-sm mt-0.5 opacity-90">{statusMeta.desc}</p>
          <p className="text-xs mt-1.5 opacity-75">
            Theme: {theme.theme}
            {qa_rounds.length > 0 && <> · {qa_rounds.length} QA {qa_rounds.length === 1 ? 'round' : 'rounds'}</>}
            {release_note_path && <> · vault note: {release_note_path}</>}
          </p>
        </div>
      </div>

      {/* Loop dialogue — turns repeat agents, so keys are positional */}
      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted mb-4">
          Delivery Loop
        </h2>
        <div className="space-y-3">
          {loop_dialogue.map((turn, i) => (
            <LoopTurn key={i} turn={turn} index={i} />
          ))}
        </div>
      </section>

      {/* QA rounds timeline */}
      {qa_rounds.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted mb-3">
            QA Rounds
          </h2>
          <div className="card space-y-4">
            {qa_rounds.map((r) => (
              <div key={r.round} className="flex items-start gap-3">
                {r.verdict === 'pass' ? (
                  <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5 text-brand-400" aria-hidden="true" />
                ) : (
                  <ShieldAlert className="w-5 h-5 shrink-0 mt-0.5 text-rose-400" aria-hidden="true" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-graphite">
                    Round {r.round}: {r.verdict === 'pass' ? 'Pass' : `Fail — ${r.issues.length} ${r.issues.length === 1 ? 'issue' : 'issues'}`}
                  </p>
                  {r.issues.length > 0 && (
                    <ul className="mt-2 space-y-2">
                      {r.issues.map((issue, i) => (
                        <li key={i} className="text-sm">
                          <span className="flex items-center gap-1.5 flex-wrap">
                            <span className={`text-xs px-1.5 py-0.5 rounded border font-medium ${SEVERITY_CLASSES[issue.severity]}`}>
                              {issue.severity}
                            </span>
                            <span className="text-xs px-1.5 py-0.5 rounded border text-muted bg-surface border-hairline">
                              {issue.category}
                            </span>
                            {issue.location && <span className="text-xs text-muted">{issue.location}</span>}
                          </span>
                          <p className="text-graphite mt-1 leading-relaxed">{issue.description}</p>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Final build spec */}
      {build_spec && (
        <section>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted mb-3">
            {status === 'released' ? 'Released Build Spec' : 'Build Spec (latest revision)'}
          </h2>
          <div className="card space-y-5">
            <div>
              <p className="text-base font-semibold text-graphite">{build_spec.feature_name}</p>
              <p className="text-sm text-muted mt-1 leading-relaxed">{build_spec.problem}</p>
            </div>
            <SpecList title="Scope" items={build_spec.scope} />
            <SpecList title="Out of scope" items={build_spec.out_of_scope} />
            <SpecList title="Data touched" items={build_spec.data_touched} />
            <SpecList title="Implementation steps" items={build_spec.implementation_steps} />
            <SpecList title="Security considerations" items={build_spec.security_considerations} />
            <SpecList title="QA verified" items={build_spec.test_notes} />
          </div>
        </section>
      )}

      {/* Gate rationale when nothing was built */}
      {status === 'insufficient_signal' && (
        <p className="text-sm text-muted leading-relaxed">{gate.rationale}</p>
      )}
    </div>
  )
}
