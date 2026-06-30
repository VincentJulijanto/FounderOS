'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ChevronRight, AlertTriangle, ScrollText, ArrowLeft, Copy, Check, Download } from 'lucide-react'
import Logo from '@/components/Logo'
import ProfileForm from '@/components/ProfileForm'
import AgentDebate from '@/components/AgentDebate'
import StartupCard from '@/components/StartupCard'
import ExecutionPlan from '@/components/ExecutionPlan'
import CouncilReasoning from '@/components/CouncilReasoning'
import { recommendationToMarkdown, downloadTextFile } from '@/lib/planMarkdown'

type Phase = 'input' | 'analyzing' | 'debating' | 'results'

export interface VentureRecommendation {
  recommendation_id: string
  agent_outputs: AgentOutput[]
  debate_rounds: DebateRound[]
  debate_summary: string
  consensus: ConsensusReport | null
  top_ideas: StartupIdea[]
  recommended_idea: StartupIdea
  execution_plan: ExecutionPlanData
  final_memo: string
}

export interface ConsensusReport {
  consensus_score: number
  label: string
  total_conflicts: number
  resolved_conflicts: number
  unresolved_conflicts: ConflictPoint[]
  rounds_used: number
  summary: string
}

export interface AgentOutput {
  agent_name: string
  role: string
  analysis: string
  score: number | null
  key_findings: string[]
  concerns: string[]
  recommendations: string[]
}

export interface DebateRound {
  round_number: number
  conflicts_identified: ConflictPoint[]
  revised_positions: Record<string, string>
  resolution_achieved: boolean
  moderator_summary: string
}

export interface ConflictPoint {
  topic: string
  agent_a: string
  agent_a_position: string
  agent_b: string
  agent_b_position: string
  severity: string
  resolved?: boolean
}

export interface StartupIdea {
  name: string
  tagline: string
  description: string
  target_market: string
  startup_score: number
  feasibility_score: number
  market_attractiveness_score: number
  founder_fit_score: number
  risk_score: number
  revenue_potential: string
  estimated_monthly_revenue: string
  time_to_launch: string
  initial_investment: string
  risk_level: string
}

export interface ExecutionPlanData {
  startup_name: string
  value_proposition: string
  customer_persona: string
  lean_canvas: Record<string, string>
  mvp_scope: string
  landing_page_copy: string
  marketing_strategy: string
  customer_acquisition_plan: string
  elevator_pitch: string
  customer_outreach_templates: Record<string, string>
  thirty_day_roadmap: string[]
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const PHASE_LABELS: Record<Phase, string> = {
  input: 'Your Profile',
  analyzing: 'Agent Society at Work',
  debating: 'Debate in Progress',
  results: 'Your Startup Plan',
}

export default function Home() {
  const [phase, setPhase] = useState<Phase>('input')
  const [recommendation, setRecommendation] = useState<VentureRecommendation | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedIdeaIndex, setSelectedIdeaIndex] = useState(0)
  const [copiedPlan, setCopiedPlan] = useState(false)

  const handleSubmit = async (profileData: Record<string, unknown>) => {
    setPhase('analyzing')
    setError(null)
    setRecommendation(null)

    try {
      const res = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile: profileData }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Analysis failed')
      }

      const data: VentureRecommendation = await res.json()
      // Real data has arrived — drive the debate view from it, then let the
      // user advance to the full plan. (No fake timer-based phase transition.)
      setRecommendation(data)
      setPhase('debating')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setPhase('input')
    }
  }

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="bg-canvas/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link
            href="/"
            className="rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
            aria-label="FounderOS home"
          >
            <Logo idSuffix="studio-nav" size={32} />
          </Link>
          <nav className="hidden sm:flex items-center gap-2 text-sm text-muted" aria-label="Progress">
            {(['input', 'analyzing', 'debating', 'results'] as Phase[]).map((p, i) => (
              <div key={p} className="flex items-center gap-2">
                {i > 0 && <ChevronRight className="w-4 h-4 text-hairline" aria-hidden="true" />}
                <span
                  className={phase === p ? 'text-graphite font-medium' : ''}
                  aria-current={phase === p ? 'step' : undefined}
                >
                  {PHASE_LABELS[p]}
                </span>
              </div>
            ))}
          </nav>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-6 py-12">

        {/* Hero — only on input phase. One outcome line (Beat 1). */}
        {phase === 'input' && (
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-semibold tracking-[-0.02em] leading-[1.12] text-graphite mb-4">
              In a few minutes, a complete startup plan
              <span className="block text-muted font-normal text-2xl md:text-3xl mt-2">
                scouted, debated, and built for you
              </span>
            </h1>
            <p className="text-lg text-muted max-w-2xl mx-auto">
              Seven specialized agents analyse your profile and debate the best path —
              then hand you a ranked shortlist and an execution-ready plan, tailored to
              your skills and budget.
            </p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 flex items-center gap-2" role="alert">
            <AlertTriangle className="w-5 h-5 shrink-0" aria-hidden="true" />
            {error}
          </div>
        )}

        {/* Phase: Input */}
        {phase === 'input' && (
          <ProfileForm onSubmit={handleSubmit} />
        )}

        {/* Phase: Analyzing / Debating */}
        {(phase === 'analyzing' || phase === 'debating') && (
          <AgentDebate
            phase={phase}
            agentOutputs={recommendation?.agent_outputs}
            debateRounds={recommendation?.debate_rounds}
            debateSummary={recommendation?.debate_summary}
            consensus={recommendation?.consensus}
            onContinue={() => setPhase('results')}
          />
        )}

        {/* Phase: Results */}
        {phase === 'results' && recommendation && (() => {
          const selectedIdea =
            recommendation.top_ideas[selectedIdeaIndex] ?? recommendation.recommended_idea

          const copyPlan = () => {
            const md = recommendationToMarkdown(recommendation, selectedIdea)
            navigator.clipboard.writeText(md)
            setCopiedPlan(true)
            setTimeout(() => setCopiedPlan(false), 2000)
          }

          const downloadPlan = () => {
            const md = recommendationToMarkdown(recommendation, selectedIdea)
            const slug = (recommendation.execution_plan?.startup_name ?? selectedIdea.name)
              .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
            downloadTextFile(`founderos-plan-${slug || 'startup'}.md`, md)
          }

          return (
          <div className="space-y-10 animate-fade-in">
            {/* Final Memo — the Venture Partner's synthesis. */}
            <div className="card">
              <div className="flex items-center gap-2.5 mb-3">
                <span className="w-9 h-9 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-600">
                  <ScrollText className="w-5 h-5" aria-hidden="true" />
                </span>
                <h2 className="text-xl font-semibold">Venture Partner Memo</h2>
              </div>
              <p className="text-graphite/80 leading-relaxed">{recommendation.final_memo}</p>
            </div>

            {/* Top Ideas */}
            <div>
              <h2 className="text-2xl font-semibold tracking-[-0.01em] mb-4">Top startup opportunities</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {recommendation.top_ideas.map((idea, i) => (
                  <StartupCard
                    key={idea.name}
                    idea={idea}
                    rank={i + 1}
                    isSelected={selectedIdeaIndex === i}
                    onSelect={() => setSelectedIdeaIndex(i)}
                  />
                ))}
              </div>
            </div>

            {/* Beat 5 — council reasoning, attributed */}
            <CouncilReasoning outputs={recommendation.agent_outputs} />

            {/* Execution Plan for selected idea */}
            {recommendation.execution_plan && (
              <ExecutionPlan plan={recommendation.execution_plan} />
            )}

            {/* Beat 6 — close the loop: export + clear next action */}
            <div className="card flex flex-col sm:flex-row sm:items-center gap-4 sm:justify-between">
              <div>
                <h2 className="text-base font-semibold">Take your plan with you</h2>
                <p className="text-sm text-muted mt-0.5">
                  Next: open the 30-day roadmap above and start Day 1.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <button className="btn-secondary" onClick={copyPlan}>
                  {copiedPlan ? (
                    <><Check className="w-4 h-4 text-brand-600" aria-hidden="true" /> Copied</>
                  ) : (
                    <><Copy className="w-4 h-4" aria-hidden="true" /> Copy plan</>
                  )}
                </button>
                <button className="btn-primary" onClick={downloadPlan}>
                  <Download className="w-4 h-4" aria-hidden="true" />
                  Download .md
                </button>
              </div>
            </div>

            {/* Restart */}
            <div className="text-center pt-2">
              <button
                className="link-quiet mx-auto"
                onClick={() => { setPhase('input'); setRecommendation(null) }}
              >
                <ArrowLeft className="w-4 h-4" aria-hidden="true" />
                Start over with a new profile
              </button>
            </div>
          </div>
          )
        })()}
      </div>
    </main>
  )
}
