/**
 * FounderOS frontend contract mirror.
 *
 * The TypeScript mirror of `backend/models.py` (the frozen Phase 0 contract in
 * `docs/architecture.md`). Lane A owns `models.py`; Lane B mirrors it here. If a
 * field changes, it changes in `models.py` first, then here.
 *
 * The evaluator contract: in = { company_id, profile?, decision }, out = a
 * BoardResponse (agent-society envelope + the BoardRecommendation memo).
 */

// ── Input: company + one decision ────────────────────────────────────────────

export interface Financials {
  revenue_band: string
  margin?: string | null
  cash_position?: string | null
}

// Backend enforces max lengths (Pydantic Field caps) — mirror them in any input UI.
export const PROFILE_LIMITS = {
  company_name: 100, sector: 200, stage: 100, business_model: 200, size_band: 50,
} as const
export const DECISION_LIMITS = { question: 500, context: 2000 } as const
/** company_id must match ^[a-z0-9][a-z0-9\-_]{0,49}$ (validated server-side). */
export const COMPANY_ID_MAX = 50

export interface CompanyProfile {
  company_name: string    // ≤100 chars (server-enforced)
  sector: string          // ≤200 · e.g. "regional logistics", "D2C skincare"
  stage: string           // ≤100 · e.g. "early-revenue", "scaling", "mature"
  business_model: string  // ≤200 · e.g. "B2B SaaS", "marketplace", "retail"
  size_band: string       // ≤50 · e.g. "1–10", "11–50", "51–200" employees
  financials: Financials
}

export interface Constraints {
  budget?: string | null
  timeline?: string | null
}

export interface Decision {
  question: string        // ≤500 chars (server-enforced)
  context?: string | null // background the operator wants on the table
  constraints: Constraints
  /** Alternative approaches to THIS one decision; Scout frames them if empty. */
  options?: string[] | null
}

export interface AnalyzeRequest {
  company_id: string
  profile?: CompanyProfile | null // if omitted, hydrated from the vault
  decision: Decision
}

// ── Agent-society envelope (carried over unchanged in shape) ──────────────────

export interface AgentOutput {
  agent_name: string      // canonical string: scout · trend · finance · … · venture_partner
  role: string
  analysis: string
  score: number | null    // 0–10
  key_findings: string[]
  concerns: string[]
  recommendations: string[]
  raw_data?: Record<string, unknown>
}

export interface ConflictPoint {
  topic: string
  agent_a: string
  agent_a_position: string
  agent_b: string
  agent_b_position: string
  severity: string        // "low" | "medium" | "high"
  resolved?: boolean
}

export interface DebateRound {
  round_number: number
  conflicts_identified: ConflictPoint[]
  revised_positions: Record<string, string>
  resolution_achieved: boolean
  moderator_summary: string
}

export interface ConsensusReport {
  /** Resolution rate — a measure of agreement, NOT decision quality. */
  consensus_score: number
  label: string
  total_conflicts: number
  resolved_conflicts: number
  unresolved_conflicts: ConflictPoint[]
  rounds_used: number
  summary: string
}

// ── Board memo (the evaluator output) ────────────────────────────────────────

export type Verdict = 'proceed' | 'hold' | 'conditional'
export type Confidence = 'low' | 'medium' | 'high'

export interface OptionAssessment {
  option: string
  assessment: string
  verdict?: string | null // e.g. "favoured", "viable", "avoid"
}

export interface Dissent {
  agent: string           // canonical agent-name string
  position: string        // the objection that did NOT get resolved
}

export interface Phase {
  name: string            // e.g. "Validate", "Pilot", "Scale"
  objective: string
  actions: string[]
  timeframe?: string | null
}

export interface ExecutionPlan {
  phases: Phase[]
}

export interface BoardRecommendation {
  recommendation: Verdict
  confidence: Confidence
  rationale: string
  missing_inputs: string[]
  options_assessed: OptionAssessment[]
  dissent: Dissent[]
  what_would_change_this_call: string
  execution_plan: ExecutionPlan
  financial_view: string
  risks: string[]
  disclaimer: string
}

export interface BoardResponse {
  response_id: string
  company_id: string
  agent_outputs: AgentOutput[]
  debate_rounds: DebateRound[]
  consensus: ConsensusReport | null
  recommendation: BoardRecommendation // the memo
  mcp_used: boolean
  mcp_sources: string[]
  /** True when the backend ran on mock fixtures (no API key). */
  mock_mode?: boolean
  /** Vault notes that informed this run (provenance; _-prefixed = identity, not memory). */
  used_paths?: string[]
  created_at?: string
}

// ── Feedback (the outcome loop → vault write-back) ────────────────────────────

export interface FeedbackRequest {
  response_id: string
  outcome?: string | null
  notes?: string | null
}
