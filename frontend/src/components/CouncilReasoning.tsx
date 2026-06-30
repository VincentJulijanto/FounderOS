'use client'

import { Check, AlertTriangle } from 'lucide-react'
import type { AgentOutput } from '@/app/studio/page'
import { iconFor } from '@/components/agentRoster'

interface Props {
  outputs: AgentOutput[]
}

/**
 * Beat 5 — attributes the recommendation back to the council. Renders each
 * agent's findings and concerns from agent_outputs (already in the payload).
 */
export default function CouncilReasoning({ outputs }: Props) {
  if (!outputs?.length) return null

  return (
    <section aria-labelledby="council-reasoning">
      <h2 id="council-reasoning" className="text-2xl font-semibold tracking-[-0.01em] mb-1">
        How the council reasoned
      </h2>
      <p className="text-sm text-muted mb-5">
        Every score traces back to an agent. Here is what each one concluded.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {outputs.map((a) => {
          const Icon = iconFor(a.agent_name)
          return (
            <article key={a.agent_name} className="card !p-5">
              <header className="flex items-center gap-3 mb-3">
                <span className="w-9 h-9 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-600">
                  <Icon className="w-4 h-4" aria-hidden="true" />
                </span>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-graphite truncate">{a.agent_name}</h3>
                  <p className="text-xs text-muted truncate">{a.role}</p>
                </div>
                {a.score != null && (
                  <span className="badge bg-brand-500/10 text-brand-700 font-mono">
                    {a.score}/10
                  </span>
                )}
              </header>

              {a.analysis && (
                <p className="text-sm text-graphite/80 leading-relaxed mb-3">{a.analysis}</p>
              )}

              {a.key_findings?.length > 0 && (
                <ul className="space-y-1.5 mb-3">
                  {a.key_findings.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-graphite/80">
                      <Check className="w-3.5 h-3.5 mt-0.5 shrink-0 text-brand-600" aria-hidden="true" />
                      {f}
                    </li>
                  ))}
                </ul>
              )}

              {a.concerns?.length > 0 && (
                <ul className="space-y-1.5">
                  {a.concerns.map((c, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-muted">
                      <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0 text-accent-600" aria-hidden="true" />
                      {c}
                    </li>
                  ))}
                </ul>
              )}
            </article>
          )
        })}
      </div>
    </section>
  )
}
