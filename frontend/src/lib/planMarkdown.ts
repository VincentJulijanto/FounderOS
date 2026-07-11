import type { BoardResponse } from '@/lib/types'
import { labelFor } from '@/components/agentRoster'

export interface MemoMeta {
  /** Company DISPLAY name (picker label) — falls back to the company_id slug. */
  companyName?: string
  /** The decision question the board was convened on. */
  question?: string
}

/**
 * Strip markdown emphasis the LLM emits in prose — display surfaces render raw
 * text, so `*could*` shows its asterisks on screen and in the PDF. PAIRED
 * markers only; unpaired asterisks are data, not markup. The .md export is NOT
 * sanitized — emphasis is legitimate markdown there.
 *
 *   cleanProse('board *could* smooth')   → 'board could smooth'
 *   cleanProse('a **hard** threshold')   → 'a hard threshold'
 *   cleanProse('`spot` lanes')           → 'spot lanes'
 *   cleanProse('5*10 grid, 2*3 too')     → unchanged (mid-word asterisks)
 *   cleanProse('see footnote*')          → unchanged (unpaired)
 */
export function cleanProse(text: string): string {
  return stripMockMarkers(text)
    .replace(/\*\*([^*\n]+?)\*\*/g, '$1')
    // italic: opening * at start/after space or "(", closing * before space/punct/end
    .replace(/(^|[\s(])\*([^*\n]+?)\*(?=$|[\s).,;:!?])/g, '$1$2')
    .replace(/`([^`\n]+)`/g, '$1')
}

/**
 * Remove mock-mode provenance markers before display. Keyless demo mode tags
 * synthetic sources with "[MOCK]" and cites mock.<host>.example.com URLs (see the
 * Research agent fixture); those are payload honesty, not something to show the
 * operator. The response payload keeps them intact — this strips at the surface.
 * Also tidies parens/separators emptied by the removal.
 *
 *   stripMockMarkers('CBRE Q3 2025 [MOCK]')                 → 'CBRE Q3 2025'
 *   stripMockMarkers('rate: 4.0/kg (Statista [MOCK])')      → 'rate: 4.0/kg (Statista)'
 *   stripMockMarkers('see https://mock.x.example.com/a b')  → 'see  b'
 */
export function stripMockMarkers(text: string): string {
  return text
    .replace(/https?:\/\/mock\.[^\s,)]*\.example\.com[^\s,)]*/gi, '')
    .replace(/\s*\[MOCK\]/gi, '')
    .replace(/\(\s*\)/g, '')       // parens emptied by the strip
    .replace(/[ \t]{2,}/g, ' ')    // collapse runs of spaces the strip left behind
    .trim()
}

/**
 * The DECISION notes that informed a run: _-prefixed paths (e.g. _profile.md)
 * are identity context that rides along on every read — memory they are not.
 */
export function consultedDecisionNotes(usedPaths?: string[]): string[] {
  return (usedPaths ?? []).filter((p) => !p.startsWith('_'))
}

/** "2026-07-02-should-we-scale-the-lane-0a82cbc3.md" → "Should we scale the lane" */
export function humanizeNotePath(path: string): string {
  const name = path
    .replace(/\.md$/, '')
    .replace(/^\d{4}-\d{2}-\d{2}-/, '')   // date prefix
    .replace(/-[0-9a-f]{8}$/, '')          // decision_id suffix
    .replace(/-/g, ' ')
    .trim()
  return name.charAt(0).toUpperCase() + name.slice(1)
}

/**
 * Serialize a BoardResponse into a portable board-memo Markdown document.
 * Pure client-side — reads only data already in the payload. Mirrors the memo
 * the operator sees on screen: the call → options → dissent → trust posture →
 * execution plan → how the board reasoned.
 */
export function memoToMarkdown(res: BoardResponse, meta?: MemoMeta): string {
  const rec = res.recommendation
  const lines: string[] = []

  lines.push(`# Board memo — ${meta?.companyName || res.company_id}`)
  if (meta?.question) lines.push(`\n> ${meta.question}`)
  if (res.created_at) lines.push(`\n_${res.created_at.slice(0, 10)}_`)
  const consulted = consultedDecisionNotes(res.used_paths)
  if (consulted.length) {
    lines.push(
      `\n_Board memory consulted: ${consulted.length} prior decision${consulted.length === 1 ? '' : 's'}` +
      ` — ${consulted.map(humanizeNotePath).join(' · ')}_`
    )
  }
  lines.push(`\n**Recommendation: ${cap(rec.recommendation)}** · ${rec.confidence} confidence`)
  if (rec.rationale) lines.push(`\n${rec.rationale}`)

  if (rec.options_assessed?.length) {
    lines.push(`\n## Options assessed`)
    for (const o of rec.options_assessed) {
      lines.push(`\n### ${o.option}${o.verdict ? ` — _${o.verdict}_` : ''}`)
      if (o.assessment) lines.push(o.assessment)
    }
  }

  if (rec.dissent?.length) {
    lines.push(`\n## Dissent on record`)
    rec.dissent.forEach((d) => lines.push(`- **${labelFor(d.agent)}:** ${d.position}`))
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

  if (rec.execution_plan?.phases?.length) {
    lines.push(`\n## Execution plan`)
    rec.execution_plan.phases.forEach((ph, i) => {
      lines.push(`\n### Phase ${i + 1}: ${ph.name}${ph.timeframe ? ` (${ph.timeframe})` : ''}`)
      if (ph.objective) lines.push(ph.objective)
      ph.actions?.forEach((a) => lines.push(`- ${a}`))
    })
  }

  // Council reasoning — attribute the memo back to the board.
  if (res.agent_outputs?.length) {
    lines.push(`\n## How the board reasoned`)
    for (const a of res.agent_outputs) {
      lines.push(`\n### ${labelFor(a.agent_name)}${a.score != null ? ` — ${a.score}/10` : ''}`)
      // Strip mock markers only (not full cleanProse) — emphasis is legit markdown here.
      if (a.analysis) lines.push(stripMockMarkers(a.analysis))
      if (a.key_findings?.length) {
        lines.push(`\n**Key findings**`)
        a.key_findings.forEach((f) => lines.push(`- ${stripMockMarkers(f)}`))
      }
      if (a.concerns?.length) {
        lines.push(`\n**Concerns**`)
        a.concerns.forEach((c) => lines.push(`- ${stripMockMarkers(c)}`))
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
