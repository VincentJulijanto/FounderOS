'use client'

import { useState } from 'react'
import {
  BarChart3,
  ShieldQuestion,
  Handshake,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  XCircle,
  Sparkles,
  AlertTriangle,
} from 'lucide-react'
import type { CouncilBriefResponse, CouncilTurn, FeedbackTheme } from '@/lib/types'

interface Props {
  data: CouncilBriefResponse
}

// ── Agent display metadata for the 3 council agents ──────────────────────────

const COUNCIL_AGENTS: Record<string, { label: string; role: string; Icon: React.ElementType; color: string; bg: string }> = {
  feedback_analyst: {
    label: 'Analyst',
    role: 'Clustered feedback into themes and produced a baseline summary.',
    Icon: BarChart3,
    color: 'text-sky-400',
    bg: 'border-sky-700/50 bg-sky-950/30',
  },
  feedback_skeptic: {
    label: 'Skeptic',
    role: 'Challenged the ranking for survivorship bias, scope creep, and thesis misalignment.',
    Icon: ShieldQuestion,
    color: 'text-rose-400',
    bg: 'border-rose-700/50 bg-rose-950/25',
  },
  feedback_chair: {
    label: 'Chair',
    role: 'Synthesised both sides — accepting, reframing, or overriding each challenge.',
    Icon: Handshake,
    color: 'text-accent-400',
    bg: 'border-accent-500/50 bg-accent-700/10',
  },
}

// ── Sub-components ─────────────────────────────────────────────────────────

function DialogueTurn({ turn, index }: { turn: CouncilTurn; index: number }) {
  const meta = COUNCIL_AGENTS[turn.agent] ?? {
    label: turn.agent,
    role: '',
    Icon: Sparkles,
    color: 'text-muted',
    bg: 'border-hairline bg-surface',
  }
  const { Icon, label, role, color, bg } = meta

  return (
    <div className={`rounded-xl border p-5 ${bg}`}>
      <div className="flex items-start gap-3">
        <span className={`mt-0.5 ${color}`} aria-hidden="true">
          <Icon className="w-5 h-5" />
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-sm font-semibold text-graphite">{label}</span>
            <span className="text-xs text-muted">{role}</span>
          </div>
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

function ThemeRow({ theme, rank }: { theme: FeedbackTheme; rank: number }) {
  const priorityColor = {
    high: 'text-rose-400 bg-rose-950/40 border-rose-700/40',
    medium: 'text-accent-400 bg-accent-700/10 border-accent-600/30',
    low: 'text-muted bg-surface border-hairline',
  }[theme.priority]

  return (
    <div className="flex items-start gap-3 py-3 border-b border-hairline last:border-0">
      <span className="text-xs font-mono text-muted w-5 shrink-0 mt-0.5">{rank}.</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-graphite">{theme.theme}</span>
          <span className={`text-xs px-1.5 py-0.5 rounded border font-medium ${priorityColor}`}>
            {theme.priority}
          </span>
          {!theme.thesis_aligned && (
            <span className="text-xs px-1.5 py-0.5 rounded border text-muted bg-surface border-hairline">
              off-thesis
            </span>
          )}
        </div>
        {theme.representative_quotes.length > 0 && (
          <p className="mt-1 text-xs text-muted italic truncate">
            &ldquo;{theme.representative_quotes[0]}&rdquo;
          </p>
        )}
      </div>
      <span className="text-xs text-muted shrink-0">×{theme.frequency}</span>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────

export default function CouncilBrief({ data }: Props) {
  const [showBaseline, setShowBaseline] = useState(false)

  const { council_dialogue, themes, baseline_comparison, ranked_brief, feedback_notes_read, mock_mode } = data
  const corrections = baseline_comparison.corrections_count

  return (
    <div className="space-y-8 animate-fade-in">

      {/* Mock mode badge */}
      {mock_mode && (
        <div className="flex items-center gap-2 text-xs text-muted border border-hairline rounded-lg px-3 py-2 bg-surface w-fit">
          <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" />
          Sample data — running on mock fixtures (no API key)
        </div>
      )}

      {/* Efficiency gain — the headline metric */}
      <div className="card flex flex-col sm:flex-row sm:items-center gap-6">
        <div className="flex items-center gap-4">
          <span className="text-5xl font-bold text-brand-400 tabular-nums">{corrections}</span>
          <div>
            <p className="text-base font-semibold text-graphite">
              {corrections === 1 ? 'issue' : 'issues'} caught by the council
            </p>
            <p className="text-sm text-muted mt-0.5">
              that a single agent would have reported as valid
            </p>
          </div>
        </div>
        <div className="sm:ml-auto text-sm text-muted">
          {feedback_notes_read} feedback {feedback_notes_read === 1 ? 'note' : 'notes'} read
        </div>
      </div>

      {/* Council dialogue — stable keys on agent name (unique per turn) */}
      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted mb-4">
          Council Dialogue
        </h2>
        <div className="space-y-3">
          {council_dialogue.map((turn, i) => (
            <DialogueTurn key={turn.agent} turn={turn} index={i} />
          ))}
        </div>
      </section>

      {/* Ranked themes — stable keys on theme name */}
      {themes.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted mb-3">
            Ranked Brief
          </h2>
          <div className="card divide-y-0 p-0">
            <div className="px-5 pt-4 pb-2">
              <p className="text-sm text-muted leading-relaxed">{ranked_brief}</p>
            </div>
            <div className="px-5 pb-4">
              {themes.map((t, i) => (
                <ThemeRow key={t.theme} theme={t} rank={i + 1} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Council corrections detail */}
      {baseline_comparison.council_corrections.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted mb-3">
            What the Council Caught
          </h2>
          <div className="card space-y-2">
            {baseline_comparison.council_corrections.map((c, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-brand-400" aria-hidden="true" />
                <span className="text-graphite">{c}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Single-agent baseline — collapsed by default */}
      <section>
        <button
          className="flex items-center gap-2 text-sm text-muted hover:text-graphite transition-colors"
          onClick={() => setShowBaseline((v) => !v)}
          aria-expanded={showBaseline}
        >
          {showBaseline ? (
            <ChevronUp className="w-4 h-4" aria-hidden="true" />
          ) : (
            <ChevronDown className="w-4 h-4" aria-hidden="true" />
          )}
          Single-agent baseline (before the council)
        </button>
        {showBaseline && (
          <div className="mt-3 card border-dashed">
            <p className="text-xs text-muted uppercase tracking-wider font-medium mb-2">
              What a lone agent would have reported
            </p>
            <p className="text-sm text-muted leading-relaxed whitespace-pre-line">
              {baseline_comparison.single_agent_summary}
            </p>
          </div>
        )}
      </section>
    </div>
  )
}
