import type { BoardResponse } from '@/lib/types'

/**
 * Serialize a BoardResponse into a portable board-memo Markdown document.
 * Pure client-side — reads only data already in the payload. Mirrors the memo
 * the operator sees on screen (recommendation → dissent → trust posture → plan).
 */
export function memoToMarkdown(res: BoardResponse): string {
  const rec = res.recommendation
  const lines: string[] = []

  lines.push(`# Board memo — ${res.company_id}`)
  lines.push(`\n**Recommendation: ${cap(rec.recommendation)}** · ${rec.confidence} confidence`)
  if (rec.rationale) lines.push(`\n${rec.rationale}`)

  if (rec.options_assessed?.length) {
    lines.push(`\n## Options assessed`)
    for (const o of rec.options_assessed) {
      lines.push(`\n### ${o.option}${o.verdict ? ` — _${o.verdict}_` : ''}`)
      if (o.assessment) lines.push(o.assessment)
    }
  }

  if (rec.execution_plan?.phases?.length) {
    lines.push(`\n## Execution plan`)
    rec.execution_plan.phases.forEach((ph, i) => {
      lines.push(`\n### Phase ${i + 1}: ${ph.name}${ph.timeframe ? ` (${ph.timeframe})` : ''}`)
      if (ph.objective) lines.push(ph.objective)
      ph.actions?.forEach((a) => lines.push(`- ${a}`))
    })
  }

  if (rec.dissent?.length) {
    lines.push(`\n## Dissent on record`)
    rec.dissent.forEach((d) => lines.push(`- **${d.agent}:** ${d.position}`))
  }

  if (rec.what_would_change_this_call) {
    lines.push(`\n## What would change this call\n\n${rec.what_would_change_this_call}`)
  }
  if (rec.financial_view) lines.push(`\n## Financial view\n\n${rec.financial_view}`)

  if (rec.missing_inputs?.length) {
    lines.push(`\n## Missing inputs`)
    rec.missing_inputs.forEach((m) => lines.push(`- ${m}`))
  }
  if (rec.risks?.length) {
    lines.push(`\n## Risks`)
    rec.risks.forEach((r) => lines.push(`- ${r}`))
  }

  // Council reasoning — attribute the memo back to the board.
  if (res.agent_outputs?.length) {
    lines.push(`\n## How the board reasoned`)
    for (const a of res.agent_outputs) {
      lines.push(`\n### ${a.agent_name}${a.score != null ? ` — ${a.score}/10` : ''}`)
      if (a.analysis) lines.push(a.analysis)
      if (a.key_findings?.length) {
        lines.push(`\n**Key findings**`)
        a.key_findings.forEach((f) => lines.push(`- ${f}`))
      }
      if (a.concerns?.length) {
        lines.push(`\n**Concerns**`)
        a.concerns.forEach((c) => lines.push(`- ${c}`))
      }
    }
  }

  if (rec.disclaimer) lines.push(`\n---\n_${rec.disclaimer}_`)
  return lines.join('\n')
}

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

/** Trigger a client-side download of text as a file. */
export function downloadTextFile(filename: string, text: string): void {
  const blob = new Blob([text], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
