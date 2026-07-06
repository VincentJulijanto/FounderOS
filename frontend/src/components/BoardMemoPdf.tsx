import type { BoardResponse } from '@/lib/types'
import { labelFor, roleFor } from '@/components/agentRoster'
import { cleanProse, consultedDecisionNotes, humanizeNotePath } from '@/lib/planMarkdown'

interface Props {
  response: BoardResponse
  /** Company DISPLAY name (picker label) — falls back to the company_id slug. */
  companyName?: string
  /** The decision question the board was convened on. */
  question?: string
}

const C = {
  pageBg: '#F7F5F1',
  cardBg: '#ffffff',
  border: '#ECEAE4',
  text: '#14151A',
  muted: '#6B6B72',
  brand: '#7C6FF0',
  proceed: { bg: '#F0FDF4', border: '#DCFCE7', text: '#166534' },
  hold: { bg: '#FFF1F2', border: '#FECDD3', text: '#9F1239' },
  conditional: { bg: '#FFF7ED', border: '#FED7AA', text: '#92400E' },
} as const

const verdictStyle = (v: string) => {
  if (v === 'proceed') return C.proceed
  if (v === 'hold') return C.hold
  return C.conditional
}

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

const card: React.CSSProperties = {
  background: C.cardBg,
  border: `1px solid ${C.border}`,
  borderRadius: 8,
  padding: '16px 20px',
  marginBottom: 12,
  pageBreakInside: 'avoid',
}

const sectionTitle: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 600,
  textTransform: 'uppercase' as const,
  letterSpacing: '0.07em',
  color: C.muted,
  marginBottom: 12,
  marginTop: 0,
}

const bullet: React.CSSProperties = {
  margin: '3px 0',
  paddingLeft: 16,
  color: C.text,
  fontSize: 13,
  lineHeight: 1.5,
}

export default function BoardMemoPdf({ response, companyName, question }: Props) {
  const rec = response.recommendation
  const vs = verdictStyle(rec.recommendation)
  const exportDate = new Date().toLocaleDateString('en-GB', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
  // Decision notes only — _profile.md is identity, not memory (same rule as on screen).
  const consulted = consultedDecisionNotes(response.used_paths)

  return (
    <div style={{ background: C.pageBg, padding: 32, fontFamily: 'system-ui, -apple-system, sans-serif', color: C.text, fontSize: 14, lineHeight: 1.6 }}>

      {/* Top brand bar */}
      <div style={{ height: 8, background: C.brand, borderRadius: 4, marginBottom: 24 }} />

      {/* Document header */}
      <div style={{ display: 'table', width: '100%', marginBottom: 24 }}>
        <div style={{ display: 'table-row' }}>
          <div style={{ display: 'table-cell', verticalAlign: 'bottom' }}>
            <div style={{ fontSize: 20, fontWeight: 700, color: C.text }}>FounderOS Board Memo</div>
            <div style={{ fontSize: 13, color: C.muted, marginTop: 2 }}>{companyName || response.company_id}</div>
            {question && (
              <div style={{ fontSize: 14, fontWeight: 500, color: C.text, marginTop: 6 }}>&ldquo;{question}&rdquo;</div>
            )}
            {consulted.length > 0 && (
              <div style={{ fontSize: 11, color: C.muted, marginTop: 6 }}>
                Board memory consulted: {consulted.length} prior decision{consulted.length === 1 ? '' : 's'} —{' '}
                {consulted.map(humanizeNotePath).join(' · ')}
              </div>
            )}
          </div>
          <div style={{ display: 'table-cell', verticalAlign: 'bottom', textAlign: 'right', fontSize: 12, color: C.muted }}>
            {exportDate}
            {response.mock_mode && (
              <div style={{ marginTop: 6, display: 'inline-block', border: `1px solid ${C.border}`, borderRadius: 6, padding: '3px 10px', fontSize: 11, color: C.muted, background: '#FAFAF8' }}>
                Sample data — mock fixtures, not a live board run
              </div>
            )}
          </div>
        </div>
      </div>

      <hr style={{ border: 'none', borderTop: `1px solid ${C.border}`, marginBottom: 24 }} />

      {/* The Call */}
      <div style={{ ...card, borderLeft: `4px solid ${vs.bg}` }}>
        <p style={sectionTitle}>The Call</p>
        <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' as const }}>
          <span style={{ background: vs.bg, color: vs.text, border: `1px solid ${vs.border}`, borderRadius: 6, padding: '3px 10px', fontSize: 13, fontWeight: 600 }}>
            {cap(rec.recommendation)}
          </span>
          <span style={{ background: '#F4F3FF', color: '#4338CA', border: '1px solid #C7D2FE', borderRadius: 6, padding: '3px 10px', fontSize: 13, fontWeight: 500 }}>
            {cap(rec.confidence)} confidence
          </span>
        </div>
        {rec.rationale && (
          <p style={{ margin: 0, fontSize: 14, color: C.text, lineHeight: 1.6 }}>{cleanProse(rec.rationale)}</p>
        )}
      </div>

      {/* Options Assessed */}
      {rec.options_assessed?.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <p style={sectionTitle}>Options Assessed</p>
          <div style={{ display: 'table', width: '100%', borderSpacing: '6px 0' }}>
            <div style={{ display: 'table-row' }}>
              {rec.options_assessed.map((o, i) => {
                const ov = o.verdict
                  ? verdictStyle(o.verdict === 'favoured' ? 'proceed' : o.verdict === 'avoid' ? 'hold' : 'conditional')
                  : null
                return (
                  <div key={i} style={{ display: 'table-cell', width: '50%', verticalAlign: 'top', paddingRight: i % 2 === 0 ? 8 : 0 }}>
                    <div style={{ ...card, marginBottom: 6 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6, gap: 8 }}>
                        <span style={{ fontWeight: 600, fontSize: 13, color: C.text, flex: 1 }}>{o.option}</span>
                        {o.verdict && ov && (
                          <span style={{ background: ov.bg, color: ov.text, borderRadius: 4, padding: '2px 7px', fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap' as const }}>
                            {cap(o.verdict)}
                          </span>
                        )}
                      </div>
                      {o.assessment && <p style={{ margin: 0, fontSize: 13, color: C.text, lineHeight: 1.5 }}>{cleanProse(o.assessment)}</p>}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Execution Plan */}
      {rec.execution_plan?.phases?.length > 0 && (
        <div style={{ ...card }}>
          <p style={sectionTitle}>Execution Plan</p>
          {rec.execution_plan.phases.map((ph, i) => (
            <div key={i} style={{ marginBottom: i < rec.execution_plan.phases.length - 1 ? 14 : 0, pageBreakInside: 'avoid' }}>
              <div style={{ fontWeight: 600, fontSize: 13, color: C.text, marginBottom: 3 }}>
                Phase {i + 1}: {ph.name}
                {ph.timeframe && <span style={{ fontWeight: 400, color: C.muted, marginLeft: 6 }}>({ph.timeframe})</span>}
              </div>
              {ph.objective && <p style={{ margin: '2px 0 6px', fontSize: 13, color: C.muted }}>{cleanProse(ph.objective)}</p>}
              {ph.actions?.map((a, j) => (
                <div key={j} style={bullet}>• {cleanProse(a)}</div>
              ))}
            </div>
          ))}
        </div>
      )}

      {/* Dissent on Record */}
      <div style={{ ...card }}>
        <p style={sectionTitle}>Dissent on Record</p>
        {rec.dissent?.length > 0 ? (
          rec.dissent.map((d, i) => (
            <div key={i} style={{ marginBottom: i < rec.dissent.length - 1 ? 8 : 0, padding: '8px 12px', background: '#FFF7ED', border: '1px solid #FED7AA', borderRadius: 6 }}>
              <span style={{ fontWeight: 600, fontSize: 13, color: '#92400E' }}>{labelFor(d.agent)}</span>
              <span style={{ color: C.text, fontSize: 13 }}> — {cleanProse(d.position)}</span>
            </div>
          ))
        ) : (
          <p style={{ margin: 0, color: C.muted, fontSize: 13, fontStyle: 'italic' }}>No dissent recorded.</p>
        )}
      </div>

      {/* Trust Posture — 2-column */}
      <div style={{ marginBottom: 12 }}>
        <p style={sectionTitle}>Trust Posture</p>
        <div style={{ display: 'table', width: '100%', borderSpacing: 0 }}>
          <div style={{ display: 'table-row' }}>
            {/* Left col */}
            <div style={{ display: 'table-cell', width: '50%', verticalAlign: 'top', paddingRight: 8 }}>
              {rec.what_would_change_this_call && (
                <div style={{ ...card }}>
                  <p style={{ ...sectionTitle, marginBottom: 6 }}>What would change this call</p>
                  <p style={{ margin: 0, fontSize: 13, color: C.text, lineHeight: 1.5 }}>{cleanProse(rec.what_would_change_this_call)}</p>
                </div>
              )}
              {rec.missing_inputs?.length > 0 && (
                <div style={{ ...card }}>
                  <p style={{ ...sectionTitle, marginBottom: 6 }}>Missing inputs</p>
                  {rec.missing_inputs.map((m, i) => (
                    <div key={i} style={bullet}>• {cleanProse(m)}</div>
                  ))}
                </div>
              )}
            </div>
            {/* Right col */}
            <div style={{ display: 'table-cell', width: '50%', verticalAlign: 'top' }}>
              {rec.financial_view && (
                <div style={{ ...card }}>
                  <p style={{ ...sectionTitle, marginBottom: 6 }}>Financial view</p>
                  <p style={{ margin: 0, fontSize: 13, color: C.text, lineHeight: 1.5 }}>{cleanProse(rec.financial_view)}</p>
                </div>
              )}
              {rec.risks?.length > 0 && (
                <div style={{ ...card }}>
                  <p style={{ ...sectionTitle, marginBottom: 6 }}>Risks</p>
                  {rec.risks.map((r, i) => (
                    <div key={i} style={bullet}>• {cleanProse(r)}</div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* How the Board Reasoned */}
      {response.agent_outputs?.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <p style={sectionTitle}>How the Board Reasoned</p>
          {response.agent_outputs.map((a, i) => (
            <div key={i} style={{ ...card }}>
              <div style={{ display: 'table', width: '100%', marginBottom: 8 }}>
                <div style={{ display: 'table-row' }}>
                  <div style={{ display: 'table-cell', verticalAlign: 'top' }}>
                    <div style={{ fontWeight: 700, fontSize: 14, color: C.text }}>{labelFor(a.agent_name)}</div>
                    <div style={{ fontSize: 12, color: C.muted }}>{roleFor(a.agent_name)}</div>
                  </div>
                  {a.score != null && (
                    <div style={{ display: 'table-cell', verticalAlign: 'top', textAlign: 'right' }}>
                      <span style={{ background: '#F4F3FF', color: '#4338CA', borderRadius: 6, padding: '3px 10px', fontSize: 13, fontWeight: 600 }}>
                        {a.score}/10
                      </span>
                    </div>
                  )}
                </div>
              </div>
              {a.analysis && <p style={{ margin: '0 0 8px', fontSize: 13, color: C.text, lineHeight: 1.5 }}>{cleanProse(a.analysis)}</p>}
              {a.key_findings?.length > 0 && (
                <div style={{ marginBottom: 6 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: C.muted, marginBottom: 3 }}>Key findings</div>
                  {a.key_findings.map((f, j) => <div key={j} style={bullet}>• {cleanProse(f)}</div>)}
                </div>
              )}
              {a.concerns?.length > 0 && (
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: C.muted, marginBottom: 3 }}>Concerns</div>
                  {a.concerns.map((c, j) => <div key={j} style={bullet}>• {cleanProse(c)}</div>)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Disclaimer */}
      {rec.disclaimer && (
        <>
          <hr style={{ border: 'none', borderTop: `1px solid ${C.border}`, marginBottom: 16 }} />
          <p style={{ margin: 0, fontSize: 12, color: C.muted, fontStyle: 'italic', lineHeight: 1.5 }}>{rec.disclaimer}</p>
        </>
      )}
    </div>
  )
}
