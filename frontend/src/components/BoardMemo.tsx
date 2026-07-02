'use client'

import {
  CheckCircle2, PauseCircle, AlertCircle, ListChecks, Scale,
  HelpCircle, ShieldAlert, Wallet, Map as MapIcon,
} from 'lucide-react'
import type { BoardRecommendation, Verdict } from '@/lib/types'
import { labelFor } from '@/components/agentRoster'

interface Props {
  rec: BoardRecommendation
}

const VERDICT: Record<Verdict, { label: string; Icon: typeof CheckCircle2; tone: string }> = {
  proceed:     { label: 'Proceed',     Icon: CheckCircle2, tone: 'border-green-200 bg-green-50 text-green-700' },
  hold:        { label: 'Hold',        Icon: PauseCircle,  tone: 'border-red-200 bg-red-50 text-red-700' },
  conditional: { label: 'Conditional', Icon: AlertCircle,  tone: 'border-amber-200 bg-amber-50 text-amber-700' },
}

const optionVerdictTone = (v?: string | null) => {
  const s = (v ?? '').toLowerCase()
  if (s.includes('favour') || s.includes('favor') || s.includes('recommend')) return 'bg-green-50 text-green-700 border-green-200'
  if (s.includes('avoid') || s.includes('reject')) return 'bg-red-50 text-red-700 border-red-200'
  return 'bg-brand-500/10 text-brand-700 border-brand-500/20'
}

export default function BoardMemo({ rec }: Props) {
  const v = VERDICT[rec.recommendation] ?? VERDICT.conditional
  const VIcon = v.Icon

  return (
    <div className="space-y-8">

      {/* The call */}
      <div className="card">
        <div className="flex flex-wrap items-center gap-3 mb-3">
          <span className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-semibold ${v.tone}`}>
            <VIcon className="w-4 h-4" aria-hidden="true" />
            {v.label}
          </span>
          <span className="badge bg-graphite/[0.05] text-graphite/70 uppercase tracking-wide text-[11px]">
            {rec.confidence} confidence
          </span>
        </div>
        <p className="text-graphite/85 leading-relaxed">{rec.rationale}</p>
      </div>

      {/* Options assessed */}
      {rec.options_assessed.length > 0 && (
        <Section title="Options assessed" Icon={Scale}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {rec.options_assessed.map((o, i) => (
              <article key={i} className="card !p-5">
                <div className="flex items-start justify-between gap-3 mb-2">
                  <h3 className="text-sm font-semibold text-graphite">{o.option}</h3>
                  {o.verdict && (
                    <span className={`badge border shrink-0 ${optionVerdictTone(o.verdict)}`}>{o.verdict}</span>
                  )}
                </div>
                <p className="text-sm text-graphite/80 leading-relaxed">{o.assessment}</p>
              </article>
            ))}
          </div>
        </Section>
      )}

      {/* Execution plan (phased) */}
      {rec.execution_plan?.phases?.length > 0 && (
        <Section title="Execution plan" Icon={MapIcon}>
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
                {ph.objective && <p className="text-sm text-graphite/80 mb-2">{ph.objective}</p>}
                {ph.actions?.length > 0 && (
                  <ul className="space-y-1">
                    {ph.actions.map((a, j) => (
                      <li key={j} className="flex items-start gap-2 text-sm text-graphite/80">
                        <span className="mt-1.5 w-1 h-1 rounded-full bg-brand-500 shrink-0" aria-hidden="true" />
                        {a}
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ol>
        </Section>
      )}

      {/* Dissent on record — a feature of the output, not a failure. Always
          rendered: an empty record is itself part of the trust posture. */}
      <Section title="Dissent on record" Icon={ShieldAlert}>
        {rec.dissent.length > 0 ? (
          <>
            <p className="text-sm text-muted -mt-2 mb-3">Objections that did not get resolved — surfaced, not buried.</p>
            <ul className="space-y-2">
              {rec.dissent.map((d, i) => (
                <li key={i} className="card !p-4 border-amber-200 bg-amber-50/50">
                  <span className="text-sm font-semibold text-graphite">{labelFor(d.agent)}</span>
                  <span className="text-sm text-graphite/80"> — {d.position}</span>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p className="card !p-4 text-sm text-muted -mt-1">
            No dissent recorded — the board aligned on this call.
          </p>
        )}
      </Section>

      {/* Trust posture — what would change the call, what's missing, the risks */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {rec.what_would_change_this_call && (
          <div className="card !p-5">
            <SubHead Icon={HelpCircle} title="What would change this call" />
            <p className="text-sm text-graphite/80 leading-relaxed">{rec.what_would_change_this_call}</p>
          </div>
        )}
        {rec.financial_view && (
          <div className="card !p-5">
            <SubHead Icon={Wallet} title="Financial view" />
            <p className="text-sm text-graphite/80 leading-relaxed">{rec.financial_view}</p>
          </div>
        )}
        {rec.missing_inputs.length > 0 && (
          <div className="card !p-5">
            <SubHead Icon={ListChecks} title="Missing inputs" />
            <ul className="space-y-1.5">
              {rec.missing_inputs.map((m, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-graphite/80">
                  <span className="mt-1.5 w-1 h-1 rounded-full bg-muted shrink-0" aria-hidden="true" />{m}
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
                  <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0 text-accent-600" aria-hidden="true" />{r}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Disclaimer — advisory, not fiduciary */}
      {rec.disclaimer && (
        <p className="text-xs text-muted italic border-t border-hairline pt-4">{rec.disclaimer}</p>
      )}
    </div>
  )
}

function Section({ title, Icon, children }: { title: string; Icon: typeof CheckCircle2; children: React.ReactNode }) {
  return (
    <section>
      <div className="flex items-center gap-2.5 mb-4">
        <span className="w-8 h-8 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-600">
          <Icon className="w-4 h-4" aria-hidden="true" />
        </span>
        <h2 className="text-xl font-semibold tracking-[-0.01em]">{title}</h2>
      </div>
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
