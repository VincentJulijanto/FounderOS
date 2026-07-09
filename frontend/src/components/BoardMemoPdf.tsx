import React from 'react'
import {
  Document,
  Page,
  View,
  Text,
  StyleSheet,
} from '@react-pdf/renderer'
import type { BoardResponse } from '@/lib/types'
import { labelFor, roleFor } from '@/components/agentRoster'
import { cleanProse, consultedDecisionNotes, humanizeNotePath } from '@/lib/planMarkdown'

/** Dedupe + word-boundary-truncate note names, capped at 2 + "and N more". */
const formatConsulted = (paths: string[]): string => {
  const names = Array.from(new Set(paths.map(humanizeNotePath)))
  const short = (s: string) => (s.length > 48 ? s.slice(0, 48).replace(/\s+\S*$/, '') + '…' : s)
  const shown = names.slice(0, 2).map(short)
  const more = names.length - shown.length
  return shown.join(' · ') + (more > 0 ? ` and ${more} more` : '')
}

interface Props {
  response: BoardResponse
  companyName?: string
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

const s = StyleSheet.create({
  page: {
    backgroundColor: C.pageBg,
    paddingHorizontal: 32,
    paddingVertical: 28,
    fontFamily: 'Helvetica',
    fontSize: 10,
    color: C.text,
    lineHeight: 1.5,
  },
  brandBar: {
    height: 6,
    backgroundColor: C.brand,
    borderRadius: 3,
    marginBottom: 18,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    marginBottom: 16,
  },
  headerLeft: { flex: 1, paddingRight: 12 },
  docTitle: { fontSize: 16, fontFamily: 'Helvetica-Bold', color: C.text },
  docSubtitle: { fontSize: 10, color: C.muted, marginTop: 2 },
  docQuestion: { fontSize: 11, fontFamily: 'Helvetica-Bold', color: C.text, marginTop: 4 },
  docMeta: { fontSize: 9, color: C.muted, marginTop: 4 },
  headerRight: { alignItems: 'flex-end' },
  dateText: { fontSize: 9, color: C.muted },
  mockBadge: {
    marginTop: 4,
    border: 1,
    borderColor: C.border,
    borderRadius: 4,
    padding: '3 7',
    fontSize: 9,
    color: C.muted,
    backgroundColor: '#FAFAF8',
  },
  divider: { borderTop: 1, borderTopColor: C.border, marginBottom: 16 },
  card: {
    backgroundColor: C.cardBg,
    border: 1,
    borderColor: C.border,
    borderRadius: 6,
    padding: '12 14',
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 8,
    fontFamily: 'Helvetica-Bold',
    textTransform: 'uppercase',
    letterSpacing: 0.7,
    color: C.muted,
    marginBottom: 8,
    marginTop: 0,
  },
  sectionHint: { fontSize: 8, color: C.muted, marginTop: -5, marginBottom: 8 },
  bodyText: { fontSize: 10, color: C.text, lineHeight: 1.5 },
  bulletRow: { flexDirection: 'row', marginBottom: 3 },
  bulletDot: { width: 12, fontSize: 10, color: C.text },
  bulletText: { flex: 1, fontSize: 10, color: C.text, lineHeight: 1.5 },
  agentHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  agentName: { fontSize: 11, fontFamily: 'Helvetica-Bold', color: C.text },
  agentRole: { fontSize: 9, color: C.muted },
  scoreBadge: {
    backgroundColor: '#F4F3FF',
    borderRadius: 4,
    padding: '2 7',
    fontSize: 10,
    fontFamily: 'Helvetica-Bold',
    color: '#4338CA',
  },
  subLabel: { fontSize: 9, fontFamily: 'Helvetica-Bold', color: C.muted, marginBottom: 2 },
  phaseLabel: { fontSize: 10, fontFamily: 'Helvetica-Bold', color: C.text, marginBottom: 2 },
  phaseTime: { fontSize: 10, color: C.muted },
  disclaimer: { fontSize: 9, color: C.muted, fontFamily: 'Helvetica-Oblique', lineHeight: 1.5, marginTop: 4 },
})

export default function BoardMemoPdfDoc({ response, companyName, question }: Props) {
  const rec = response.recommendation
  const vs = verdictStyle(rec.recommendation)
  const exportDate = new Date().toLocaleDateString('en-GB', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
  const consulted = consultedDecisionNotes(response.used_paths)

  return (
    <Document title="FounderOS Board Memo" producer="FounderOS" creator="FounderOS">
      <Page size="A4" style={s.page}>

        {/* Brand bar */}
        <View style={s.brandBar} />

        {/* Header */}
        <View style={s.headerRow}>
          <View style={s.headerLeft}>
            <Text style={s.docTitle}>FounderOS Board Memo</Text>
            <Text style={s.docSubtitle}>{companyName || response.company_id}</Text>
            {question ? <Text style={s.docQuestion}>&ldquo;{question}&rdquo;</Text> : null}
            {consulted.length > 0 ? (
              <Text style={s.docMeta}>
                Board memory consulted: {consulted.length} prior decision{consulted.length === 1 ? '' : 's'} — {formatConsulted(consulted)}
              </Text>
            ) : null}
          </View>
          <View style={s.headerRight}>
            <Text style={s.dateText}>{exportDate}</Text>
            {response.mock_mode ? (
              <View style={s.mockBadge}><Text>Sample data — mock run, not live</Text></View>
            ) : null}
          </View>
        </View>

        <View style={s.divider} />

        {/* The Call */}
        <View style={{ ...s.card, borderLeftWidth: 3, borderLeftColor: vs.bg }} wrap={false}>
          <Text style={s.sectionTitle}>The Call</Text>
          <View style={{ flexDirection: 'row', gap: 6, marginBottom: 8, flexWrap: 'wrap' }}>
            <View style={{ backgroundColor: vs.bg, borderRadius: 4, padding: '2 8', border: 1, borderColor: vs.border }}>
              <Text style={{ fontSize: 10, fontFamily: 'Helvetica-Bold', color: vs.text }}>{cap(rec.recommendation)}</Text>
            </View>
            <View style={{ backgroundColor: '#F4F3FF', borderRadius: 4, padding: '2 8', border: 1, borderColor: '#C7D2FE' }}>
              <Text style={{ fontSize: 10, color: '#4338CA' }}>{cap(rec.confidence)} confidence</Text>
            </View>
          </View>
          {rec.rationale ? <Text style={s.bodyText}>{cleanProse(rec.rationale)}</Text> : null}
        </View>

        {/* Options Assessed */}
        {rec.options_assessed?.length > 0 ? (
          <View>
            <View wrap={false}>
              <Text style={s.sectionTitle}>Options Assessed</Text>
              <Text style={s.sectionHint}>The board weighed {rec.options_assessed.length} option{rec.options_assessed.length === 1 ? '' : 's'} against the call above</Text>
              <OptionCard o={rec.options_assessed[0]} />
            </View>
            {rec.options_assessed.slice(1).map((o, i) => (
              <OptionCard key={i} o={o} />
            ))}
            <View style={{ height: 4 }} />
          </View>
        ) : null}

        {/* Execution Plan */}
        {rec.execution_plan?.phases?.length > 0 ? (
          <View style={s.card}>
            <Text style={s.sectionTitle}>Execution Plan</Text>
            <Text style={s.sectionHint}>The recommended path, phased</Text>
            {rec.execution_plan.phases.map((ph, i) => (
              <View key={i} style={{ marginBottom: i < rec.execution_plan.phases.length - 1 ? 10 : 0 }} wrap={false}>
                <View style={{ flexDirection: 'row', marginBottom: 2 }}>
                  <Text style={s.phaseLabel}>Phase {i + 1}: {ph.name}</Text>
                  {ph.timeframe ? <Text style={s.phaseTime}> ({ph.timeframe})</Text> : null}
                </View>
                {ph.objective ? <Text style={{ fontSize: 9, color: C.muted, marginBottom: 4 }}>{cleanProse(ph.objective)}</Text> : null}
                {ph.actions?.map((a, j) => (
                  <View key={j} style={s.bulletRow}>
                    <Text style={s.bulletDot}>•</Text>
                    <Text style={s.bulletText}>{cleanProse(a)}</Text>
                  </View>
                ))}
              </View>
            ))}
          </View>
        ) : null}

        {/* Dissent on Record */}
        <View style={s.card} wrap={false}>
          <Text style={s.sectionTitle}>Dissent on Record</Text>
          <Text style={s.sectionHint}>Objections that did not resolve — on the record</Text>
          {rec.dissent?.length > 0 ? (
            rec.dissent.map((d, i) => (
              <View key={i} style={{ marginBottom: i < rec.dissent.length - 1 ? 6 : 0, padding: '6 10', backgroundColor: '#FFF7ED', border: 1, borderColor: '#FED7AA', borderRadius: 4 }}>
                <Text>
                  <Text style={{ fontFamily: 'Helvetica-Bold', fontSize: 10, color: '#92400E' }}>{labelFor(d.agent)}</Text>
                  <Text style={{ fontSize: 10, color: C.text }}> — {cleanProse(d.position)}</Text>
                </Text>
              </View>
            ))
          ) : (
            <Text style={{ fontSize: 10, color: C.muted, fontFamily: 'Helvetica-Oblique' }}>No dissent recorded.</Text>
          )}
        </View>

        {/* Trust Posture */}
        {(rec.what_would_change_this_call || rec.financial_view || rec.missing_inputs?.length > 0 || rec.risks?.length > 0) ? (
          <View>
            <View wrap={false}>
              <Text style={s.sectionTitle}>Trust Posture</Text>
              <Text style={s.sectionHint}>What the board doesn&apos;t know, and what would change its mind</Text>
              {rec.what_would_change_this_call ? (
                <View style={s.card}>
                  <Text style={{ ...s.sectionTitle, marginBottom: 4 }}>What would change this call</Text>
                  <Text style={s.bodyText}>{cleanProse(rec.what_would_change_this_call)}</Text>
                </View>
              ) : null}
            </View>
            {rec.financial_view ? (
              <View style={s.card} wrap={false}>
                <Text style={{ ...s.sectionTitle, marginBottom: 4 }}>Financial view</Text>
                <Text style={s.bodyText}>{cleanProse(rec.financial_view)}</Text>
              </View>
            ) : null}
            {rec.missing_inputs?.length > 0 ? (
              <View style={s.card} wrap={false}>
                <Text style={{ ...s.sectionTitle, marginBottom: 4 }}>Missing inputs</Text>
                {rec.missing_inputs.map((m, i) => (
                  <View key={i} style={s.bulletRow}>
                    <Text style={s.bulletDot}>•</Text>
                    <Text style={s.bulletText}>{cleanProse(m)}</Text>
                  </View>
                ))}
              </View>
            ) : null}
            {rec.risks?.length > 0 ? (
              <View style={s.card} wrap={false}>
                <Text style={{ ...s.sectionTitle, marginBottom: 4 }}>Risks</Text>
                {rec.risks.map((r, i) => (
                  <View key={i} style={s.bulletRow}>
                    <Text style={s.bulletDot}>•</Text>
                    <Text style={s.bulletText}>{cleanProse(r)}</Text>
                  </View>
                ))}
              </View>
            ) : null}
            <View style={{ height: 4 }} />
          </View>
        ) : null}

        {/* How the Board Reasoned */}
        {response.agent_outputs?.length > 0 ? (
          <View>
            <View wrap={false}>
              <Text style={s.sectionTitle}>How the Board Reasoned</Text>
              <Text style={s.sectionHint}>Each agent&apos;s independent read before debate</Text>
              <AgentCard a={response.agent_outputs[0]} />
              {response.agent_outputs.length === 1 ? <DisclaimerBlock text={rec.disclaimer} /> : null}
            </View>
            {response.agent_outputs.slice(1, -1).map((a, i) => (
              <AgentCard key={i} a={a} />
            ))}
            {response.agent_outputs.length > 1 ? (
              <View wrap={false}>
                <AgentCard a={response.agent_outputs[response.agent_outputs.length - 1]} />
                <DisclaimerBlock text={rec.disclaimer} />
              </View>
            ) : null}
          </View>
        ) : (
          <DisclaimerBlock text={rec.disclaimer} />
        )}

      </Page>
    </Document>
  )
}

function AgentCard({ a }: { a: BoardResponse['agent_outputs'][number] }) {
  return (
    <View style={s.card} wrap={false}>
      <View style={s.agentHeader}>
        <View>
          <Text style={s.agentName}>{labelFor(a.agent_name)}</Text>
          <Text style={s.agentRole}>{roleFor(a.agent_name)}</Text>
        </View>
        {a.score != null ? (
          <View style={s.scoreBadge}><Text>{a.score}/10</Text></View>
        ) : null}
      </View>
      {a.analysis ? <Text style={{ ...s.bodyText, marginBottom: 6 }}>{cleanProse(a.analysis)}</Text> : null}
      {a.key_findings?.length > 0 ? (
        <View style={{ marginBottom: 4 }}>
          <Text style={s.subLabel}>Key findings</Text>
          {a.key_findings.map((f, j) => (
            <View key={j} style={s.bulletRow}>
              <Text style={s.bulletDot}>•</Text>
              <Text style={s.bulletText}>{cleanProse(f)}</Text>
            </View>
          ))}
        </View>
      ) : null}
      {a.concerns?.length > 0 ? (
        <View>
          <Text style={s.subLabel}>Concerns</Text>
          {a.concerns.map((c, j) => (
            <View key={j} style={s.bulletRow}>
              <Text style={s.bulletDot}>•</Text>
              <Text style={s.bulletText}>{cleanProse(c)}</Text>
            </View>
          ))}
        </View>
      ) : null}
    </View>
  )
}

function DisclaimerBlock({ text }: { text?: string }) {
  if (!text) return null
  return (
    <>
      <View style={s.divider} />
      <Text style={s.disclaimer}>{text}</Text>
    </>
  )
}

function OptionCard({ o }: { o: BoardResponse['recommendation']['options_assessed'][number] }) {
  const ov = o.verdict
    ? verdictStyle(o.verdict === 'favoured' ? 'proceed' : o.verdict === 'avoid' ? 'hold' : 'conditional')
    : null
  return (
    <View style={{ ...s.card, marginBottom: 6 }} wrap={false}>
      <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 4, gap: 6 }}>
        <Text style={{ fontFamily: 'Helvetica-Bold', fontSize: 10, color: C.text }}>{o.option}</Text>
        {o.verdict && ov ? (
          <View style={{ backgroundColor: ov.bg, borderRadius: 3, padding: '1 5', border: 1, borderColor: ov.border }}>
            <Text style={{ fontSize: 8, fontFamily: 'Helvetica-Bold', color: ov.text }}>{cap(o.verdict)}</Text>
          </View>
        ) : null}
      </View>
      {o.assessment ? <Text style={s.bodyText}>{cleanProse(o.assessment)}</Text> : null}
    </View>
  )
}
