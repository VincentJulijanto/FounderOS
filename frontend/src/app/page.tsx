'use client'

import { useState } from 'react'
import ProfileForm from '@/components/ProfileForm'
import AgentDebate from '@/components/AgentDebate'
import StartupCard from '@/components/StartupCard'
import ExecutionPlan from '@/components/ExecutionPlan'

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
      <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-brand-500 to-accent-500 rounded-lg flex items-center justify-center text-white font-bold text-sm">
              F
            </div>
            <span className="font-semibold text-lg">FounderOS</span>
            <span className="badge bg-accent-500/20 text-accent-500 border border-accent-500/30">
              AI Venture Studio
            </span>
          </div>
          <nav className="flex items-center gap-2 text-sm text-gray-500">
            {(['input', 'analyzing', 'debating', 'results'] as Phase[]).map((p, i) => (
              <div key={p} className="flex items-center gap-2">
                {i > 0 && <span className="text-gray-700">→</span>}
                <span className={phase === p ? 'text-brand-400 font-medium' : ''}>
                  {PHASE_LABELS[p]}
                </span>
              </div>
            ))}
          </nav>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-6 py-12">

        {/* Hero — only on input phase */}
        {phase === 'input' && (
          <div className="text-center mb-12 animate-fade-in">
            <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-brand-400 to-accent-400 bg-clip-text text-transparent">
              Your AI Venture Studio
            </h1>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              A society of 7 specialized AI agents will scout, debate, and build
              your complete startup execution plan — tailored to your skills and budget.
            </p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/30 border border-red-700 rounded-xl text-red-300">
            ⚠️ {error}
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
        {phase === 'results' && recommendation && (
          <div className="space-y-8 animate-fade-in">
            {/* Final Memo */}
            <div className="card border-brand-800 bg-gradient-to-br from-brand-950/50 to-gray-900">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-2xl">📋</span>
                <h2 className="text-xl font-bold">Venture Partner Memo</h2>
              </div>
              <p className="text-gray-300 leading-relaxed">{recommendation.final_memo}</p>
            </div>

            {/* Top Ideas */}
            <div>
              <h2 className="text-2xl font-bold mb-4">Top Startup Opportunities</h2>
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

            {/* Execution Plan for selected idea */}
            {recommendation.execution_plan && (
              <ExecutionPlan plan={recommendation.execution_plan} />
            )}

            {/* Restart */}
            <div className="text-center pt-4">
              <button
                className="btn-secondary"
                onClick={() => { setPhase('input'); setRecommendation(null) }}
              >
                ← Start Over with New Profile
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
