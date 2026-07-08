'use client'

import {
  CheckCircle2, PauseCircle, AlertCircle, ListChecks, Scale,
  HelpCircle, ShieldAlert, Wallet, Map as MapIcon,
} from 'lucide-react'
import type { BoardRecommendation, Verdict } from '@/lib/types'
import { labelFor } from '@/components/agentRoster'
import { cleanProse, consultedDecisionNotes, humanizeNotePath } from '@/lib/planMarkdown'

/** Dedupe + word-boundary-truncate note names, capped at 2 + "and N more". */
const formatConsulted = (paths: string[]): string => {
  const names = Array.from(new Set(paths.map(humanizeNotePath)))
  const short = (s: string) => (s.length > 48 ? s.slice(0, 48).replace(/\s+\S*$/, '') + '\u2026' : s)
  const shown = names.slice(0, 2).map(short)
  const more = names.length - shown.length
  return shown.join(' \u00b7 ') + (more > 0 ? ` and ${more} more` : '')
}

interface Props {
  rec: BoardRecommendation
  /** Company DISPLAY name (from the picker's label, never the vault slug). */
  companyName?: string
  /** The decision question the board was convened on. */
  question?: string
  /** Run date (ISO string; rendered as a date). */
  date?: string
  /** True when the response was built from mock fixtures. */
  sampleData?: boolean
  /** Vault provenance — which notes informed this run (_-prefixed = identity). */
  usedPaths?: string[]
}

const VERDICT: Record<Verdict, { label: string; Icon: typeof CheckCircle2; tone: string; text: string }> = {
  proceed:     { label: 'Proceed',     Icon: CheckCircle2, tone: 'border-green-200 bg-green-50 text-green-700', text: 'text-green-700' },
  hold:        { label: 'Hold',        Icon: PauseCircle,  tone: 'border-red-200 bg-red-50 text-red-700', text: 'text-red-700' },
  conditional: { label: 'Conditional', Icon: AlertCircle,  tone: 'border-amber-200 bg-amber-50 text-amber-700', text: 'text-amber-600' },
}

const optionVerdictTone = (v?: string | null) => {
  const s = (v ?? '').toLowerCase()
  if (s.includes('favour') || s.includes('favor') || s.includes('recommend')) return 'bg-green-50 text-green-700 border-green-200'
  if (s.includes('avoid') || s.includes('reject')) return 'bg-red-50 text-red-700 border-red-200'
  return 'bg-brand-500/10 text-brand-700 border-brand-500/20'
}

export default function BoardMemo({ rec, companyName, question, date, sampleData, usedPaths }: Props) {
  const v = VERDICT[rec.recommendation] ?? VERDICT.conditional
  const VIcon = v.Icon
  const dateStr = date
    ? new Date(date).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
    : null
  // Decision notes only — _profile.md rides along on every read as identity,
  // not memory. Cold start (nothing consulted) renders nothing, never "0".
  const consulted = consultedDecisionNotes(usedPaths)

  return (
    <div className="space-y-8">

      {/* The call — a document header, then the verdict at headline scale */}
      <div className="card">
        {(companyName || question || sampleData || consulted.length > 0) && (
          <div className="flex flex-wrap items-start justify-between gap-3 mb-5 pb-5 border-b border-hairline">
            <div className="min-w-0">
              {companyName && (
                <p className="text-sm text-muted">
                  {companyName}{dateStr && <span> · {dateStr}</span>}
                </p>
              )}
              {question && (
                <p className="text-lg font-medium text-graphite mt-1 leading-snug">&ldquo;{question}&rdquo;</p>
              )}
              {consulted.length > 0 && (
                <p
                  className="text-xs text-muted mt-1.5"
                  title={formatConsulted(consulted)}
                >
                  Board memory consulted: {consulted.length} prior decision{consulted.length === 1 ? '' : 's'}
                </p>
              )}
            </div>
            {sampleData && (
              <span className="badge border border-hairline bg-graphite/[0.04] text-muted shrink-0">
                Sample data — live run uses your API key
              </span>
            )}
          </div>
        )}
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 mb-3">
          <span className={`inline-flex items-center gap-2.5 text-4xl md:text-5xl font-semibold tracking-[-0.02em] ${v.text}`}>
            <VIcon className="w-8 h-8 md:w-9 md:h-9" aria-hidden="true" />
            {v.label}
          </span>
          <span className="text-sm text-muted">{rec.confidence} confidence</span>
        </div>
        <p className="text-graphite/85 leading-relaxed">{cleanProse(rec.rationale)}</p>
      </div>

      {/* ── the thread: WHY — the reasoning and the disagreement ── */}
      <ThreadLabel label="Why" text="the reasoning and the disagreement" />
      <p className="text-xs text-muted -mt-8">
        Seven agents read the decision independently and debated it; what did not resolve is
        below — each agent&rsquo;s full read closes the memo.
      </p>

      {/* Dissent on record — a feature of the output, not a failure. Always
          rendered: an empty record is itself part of the trust posture. */}
      <Section title="Dissent on record" Icon={ShieldAlert} hint="Objections that did not resolve — on the record">
        {rec.dissent.length > 0 ? (
          <>
            <ul className="space-y-2">
              {rec.dissent.map((d, i) => {
                const isSkeptic = d.agent === 'skeptic'
                return (
                  <li key={i} className={`card !p-5 ${isSkeptic ? 'border-red-200 bg-red-50/40' : 'border-amber-200 bg-amber-50/50'}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold text-graphite">{labelFor(d.agent)}</span>
                      <span className={`badge border text-[10px] uppercase tracking-wide ${isSkeptic ? 'bg-red-100 text-red-700 border-red-200' : 'bg-amber-100 text-amber-700 border-amber-200'}`}>
                        unresolved
                      </span>
                    </div>
                    <span className="text-sm text-graphite/80">{cleanProse(d.position)}</span>
                  </li>
                )
              })}
            </ul>
          </>
        ) : (
          <p className="card !p-5 text-sm text-muted -mt-1">
            No dissent recorded — the board aligned on this call.
          </p>
        )}
      </Section>

      {/* ── the thread: WHAT — the options and the unknowns ── */}
      <ThreadLabel label="What" text="the options weighed, and what the board doesn&rsquo;t know" />

      {/* Options assessed */}
      {rec.options_assessed.length > 0 && (
        <Section
          title="Options assessed"
          Icon={Scale}
          hint={`The board weighed ${rec.options_assessed.length} option${rec.options_assessed.length === 1 ? '' : 's'} against the call above`}
        >
          {/* 2-up only when content-balanced: exactly two short assessments. */}
          <div className={
            rec.options_assessed.length === 2 && rec.options_assessed.every(o => (o.assessment || '').length <= 260)
              ? 'grid grid-cols-1 md:grid-cols-2 gap-4'
              : 'grid grid-cols-1 gap-4'
          }>
            {rec.options_assessed.map((o, i) => (
              <article key={i} className="card !p-5">
                <div className="flex items-center justify-between gap-3 mb-2">
                  <h3 className="text-sm font-semibold text-graphite">{o.option}</h3>
                  {o.verdict && (
                    <span className={`badge border shrink-0 ${optionVerdictTone(o.verdict)}`}>{o.verdict}</span>
                  )}
                </div>
                <p className="text-sm text-graphite/80 leading-relaxed">{cleanProse(o.assessment)}</p>
              </article>
            ))}
          </div>
        </Section>
      )}

      {/* Trust posture — what would change the call, what's missing, the risks */}
      <div>
        <p className="text-xs text-muted mb-3">What the board doesn&rsquo;t know, and what would change its mind</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {rec.what_would_change_this_call && (
          <div className="card !p-5">
            <SubHead Icon={HelpCircle} title="What would change this call" />
            <p className="text-sm text-graphite/80 leading-relaxed">{cleanProse(rec.what_would_change_this_call)}</p>
          </div>
        )}
        {rec.financial_view && (
          <div className="card !p-5">
            <SubHead Icon={Wallet} title="Financial view" />
            <p className="text-sm text-graphite/80 leading-relaxed">{cleanProse(rec.financial_view)}</p>
          </div>
        )}
        {rec.missing_inputs.length > 0 && (
          <div className="card !p-5">
            <SubHead Icon={ListChecks} title="Missing inputs" />
            <ul className="space-y-1.5">
              {rec.missing_inputs.map((m, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-graphite/80">
                  <span className="mt-1.5 w-1 h-1 rounded-full bg-muted shrink-0" aria-hidden="true" />{cleanProse(m)}
                </li>
              ))}
            </ul>
          </div>
        )}
        {rec.risks.length > 0 && (
          <div className="card !p-5">
            <SubHead Icon={ShieldAlert} title="Risks" />
            <ul className="space-y-1.5">
              {rec.risks.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-muted">
                  <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0 text-accent-600" aria-hidden="true" />{cleanProse(r)}
                </li>
              ))}
            </ul>
          </div>
        )}
        </div>
      </div>

      {/* ── the thread: HOW — the path ── */}
      <ThreadLabel label="How" text="the recommended path" />

      {/* Execution plan (phased) — the appendix: the call and its reservations come first */}
      {rec.execution_plan?.phases?.length > 0 && (
        <Section title="Execution plan" Icon={MapIcon} hint="The recommended path, phased">
          <ol className="space-y-4">
            {rec.execution_plan.phases.map((ph, i) => (
              <li key={i} className="card !p-5">
                <div className="flex items-center gap-3 mb-1.5">
                  <span className="w-7 h-7 rounded-lg bg-brand-500/10 text-brand-700 font-mono text-sm flex items-center justify-center shrink-0">
                    {i + 1}
                  </span>
                  <h3 className="text-sm font-semibold text-graphite">{ph.name}</h3>
                  {ph.timeframe && <span className="text-xs text-muted">{ph.timeframe}</span>}
                </div>
                {ph.objective && <p className="text-sm text-graphite/80 mb-2">{cleanProse(ph.objective)}</p>}
                {ph.actions?.length > 0 && (
                  <ul className="space-y-1">
                    {ph.actions.map((a, j) => (
                      <li key={j} className="flex items-start gap-2 text-sm text-graphite/80">
                        <span className="mt-1.5 w-1 h-1 rounded-full bg-brand-500 shrink-0" aria-hidden="true" />
                        {cleanProse(a)}
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ol>
        </Section>
      )}
    </div>
  )
}

function ThreadLabel({ label, text }: { label: string; text: string }) {
  return (
    <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">
      {label} <span className="font-normal normal-case tracking-normal">— {text}</span>
    </p>
  )
}

function Section({ title, Icon, hint, children }: { title: string; Icon: typeof CheckCircle2; hint?: string; children: React.ReactNode }) {
  return (
    <section>
      <div className={`flex items-center gap-2.5 ${hint ? 'mb-1' : 'mb-4'}`}>
        <span className="w-8 h-8 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-600">
          <Icon className="w-4 h-4" aria-hidden="true" />
        </span>
        <h2 className="text-xl font-semibold tracking-[-0.01em]">{title}</h2>
      </div>
      {hint && <p className="text-xs text-muted mb-4 ml-[42px]">{hint}</p>}
      {children}
    </section>
  )
}

function SubHead({ Icon, title }: { Icon: typeof CheckCircle2; title: string }) {
  return (
    <div className="flex items-center gap-2 mb-2">
      <Icon className="w-4 h-4 text-brand-600" aria-hidden="true" />
      <h3 className="text-sm font-semibold text-graphite">{title}</h3>
    </div>
  )
}
