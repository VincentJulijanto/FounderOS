import {
  Telescope,
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
  /** Canonical name — must match the backend agent_name exactly. */
  name: string
  /** Short label for compact tiles. */
  short: string
  /** Distinct line glyph (lucide). No emoji. */
  Icon: LucideIcon
  /** One-line role, present tense (used in the "meet your council" preview). */
  role: string
  /** Working status line shown while the agent runs. */
  status: string
  /** Per-agent identity tint for the live tile border/background. */
  tone: string
}

/**
 * The canonical 7-agent council. Single source of truth for icons, roles, and
 * tints across ProfileForm (preview) and AgentDebate (live + debate attribution).
 */
export const ROSTER: AgentMeta[] = [
  {
    name: 'Opportunity Scout',
    short: 'Scout',
    Icon: Telescope,
    role: 'Hunts for underserved market gaps worth building in.',
    status: 'Scouting market gaps...',
    tone: 'border-brand-700/60 bg-brand-950/40',
  },
  {
    name: 'Trend Analyst',
    short: 'Trend',
    Icon: TrendingUp,
    role: 'Reads demand signals and timing for each opportunity.',
    status: 'Analysing market demand...',
    tone: 'border-emerald-700/60 bg-emerald-950/30',
  },
  {
    name: 'Finance Agent',
    short: 'Finance',
    Icon: Wallet,
    role: 'Models unit economics against your budget.',
    status: 'Running financial models...',
    tone: 'border-accent-600/60 bg-accent-700/10',
  },
  {
    name: 'Growth Agent',
    short: 'Growth',
    Icon: Rocket,
    role: 'Maps how the first customers are won.',
    status: 'Building acquisition strategy...',
    tone: 'border-violet-700/60 bg-brand-950/40',
  },
  {
    name: 'Skeptic Agent',
    short: 'Skeptic',
    Icon: ShieldQuestion,
    role: 'Attacks the weakest assumptions before you do.',
    status: 'Challenging assumptions...',
    tone: 'border-rose-700/60 bg-rose-950/30',
  },
  {
    name: 'Founder-Fit Agent',
    short: 'Founder-Fit',
    Icon: Puzzle,
    role: 'Scores each idea against your skills and time.',
    status: 'Scoring founder–opportunity fit...',
    tone: 'border-teal-700/60 bg-teal-950/30',
  },
  {
    name: 'Venture Partner',
    short: 'Partner',
    Icon: Handshake,
    role: 'Synthesises the council into one recommendation.',
    status: 'Synthesising recommendation...',
    tone: 'border-accent-500/60 bg-accent-700/10',
  },
]

const BY_NAME: Record<string, AgentMeta> = Object.fromEntries(
  ROSTER.map((a) => [a.name, a]),
)

/** Resolve an agent's glyph by name, with a neutral fallback. */
export const iconFor = (name: string): LucideIcon => BY_NAME[name]?.Icon ?? Bot
