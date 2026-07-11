import {
  Telescope,
  Radar,
  TrendingUp,
  Wallet,
  Rocket,
  ShieldQuestion,
  Puzzle,
  Handshake,
  Bot,
  type LucideIcon,
} from 'lucide-react'

export interface AgentMeta {
  /**
   * Canonical name — must match the backend `agent_name` EXACTLY. This is the
   * join key for agent_outputs, debate positions, and dissent. It is the string
   * scout · research · trend · finance · growth · skeptic · capability · venture_partner.
   */
  name: string
  /** Human-facing display name (e.g. venture_partner → "Chair"). */
  label: string
  /** Short label for compact tiles. */
  short: string
  /** Distinct line glyph (lucide). No emoji. */
  Icon: LucideIcon
  /** One-line role, present tense (used in the "meet your board" preview). */
  role: string
  /** Working status line shown while the agent runs. */
  status: string
  /** Per-agent identity tint for the live tile border/background. */
  tone: string
}

/**
 * The canonical 8-agent board. Single source of truth for icons, labels, and
 * tints across the intake preview and the debate view. Keyed on the canonical
 * backend strings; `label` carries the human-facing name (venture_partner is the
 * board's "Chair"). `capability` is the rebuilt `founder_fit` — organisational
 * readiness, not a person's skills. `research` (Market Intelligence) runs after
 * Scout and before the analysts. Order mirrors the pipeline.
 */
export const ROSTER: AgentMeta[] = [
  {
    name: 'scout',
    label: 'Opportunity Scout',
    short: 'Scout',
    Icon: Telescope,
    role: 'Frames the options on the table for this decision.',
    status: 'Framing the options...',
    tone: 'border-brand-700/60 bg-brand-950/40',
  },
  {
    name: 'research',
    label: 'Market Intelligence',
    short: 'Research',
    Icon: Radar,
    role: 'Gathers cited market data before the analysts weigh in.',
    status: 'Gathering market intelligence...',
    tone: 'border-sky-700/60 bg-sky-950/30',
  },
  {
    name: 'trend',
    label: 'Trend Analyst',
    short: 'Trend',
    Icon: TrendingUp,
    role: 'Reads market and demand signals for this decision.',
    status: 'Reading market signals...',
    tone: 'border-emerald-700/60 bg-emerald-950/30',
  },
  {
    name: 'finance',
    label: 'Finance Agent',
    short: 'Finance',
    Icon: Wallet,
    role: "Models the decision against the company's economics.",
    status: 'Modelling the economics...',
    tone: 'border-accent-600/60 bg-accent-700/10',
  },
  {
    name: 'growth',
    label: 'Growth Agent',
    short: 'Growth',
    Icon: Rocket,
    role: 'Maps how the company executes and goes to market.',
    status: 'Mapping execution...',
    tone: 'border-violet-700/60 bg-brand-950/40',
  },
  {
    name: 'skeptic',
    label: 'Skeptic',
    short: 'Skeptic',
    Icon: ShieldQuestion,
    role: "Attacks the decision's weakest assumptions and failure modes.",
    status: 'Attacking the assumptions...',
    tone: 'border-rose-700/60 bg-rose-950/30',
  },
  {
    name: 'capability',
    label: 'Capability Agent',
    short: 'Capability',
    Icon: Puzzle,
    role: "Scores the organisation's readiness to execute.",
    status: 'Scoring organisational readiness...',
    tone: 'border-teal-700/60 bg-teal-950/30',
  },
  {
    name: 'venture_partner',
    label: 'Chair',
    short: 'Chair',
    Icon: Handshake,
    role: 'Synthesises the debate into the board memo.',
    status: 'Writing the board memo...',
    tone: 'border-accent-500/60 bg-accent-700/10',
  },
]

const BY_NAME: Record<string, AgentMeta> = Object.fromEntries(
  ROSTER.map((a) => [a.name, a]),
)

/** Resolve an agent's glyph by canonical name, with a neutral fallback. */
export const iconFor = (name: string): LucideIcon => BY_NAME[name]?.Icon ?? Bot

/** Resolve an agent's display label by canonical name (falls back to the raw name). */
export const labelFor = (name: string): string => BY_NAME[name]?.label ?? name

/** Resolve an agent's one-line role by canonical name. */
export const roleFor = (name: string): string => BY_NAME[name]?.role ?? ''
