'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ChevronRight, AlertTriangle, ScrollText, ArrowLeft, Copy, Check, Download, FileDown } from 'lucide-react'
import Logo from '@/components/Logo'
import DecisionIntake from '@/components/DecisionIntake'
import AgentDebate from '@/components/AgentDebate'
import BoardMemo from '@/components/BoardMemo'
import CouncilReasoning from '@/components/CouncilReasoning'
import ErrorBoundary from '@/components/ErrorBoundary'
import { memoToMarkdown, downloadTextFile } from '@/lib/planMarkdown'
import { exportBoardMemoPdf } from '@/lib/exportPdf'
import type { AnalyzeRequest, BoardResponse } from '@/lib/types'

type Phase = 'input' | 'analyzing' | 'debating' | 'results'

const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

const PHASE_LABELS: Record<Phase, string> = {
  input: 'The Decision',
  analyzing: 'Board at Work',
  debating: 'Debate in Progress',
  results: 'Board Memo',
}

// Minimum time the "Board at Work" phase stays on screen, so a mock/fast run
// still shows the pipeline pass instead of flashing past it.
const MIN_WORK_DWELL_MS = 3200

export default function Boardroom() {
  const [phase, setPhase] = useState<Phase>('input')
  const [response, setResponse] = useState<BoardResponse | null>(null)
  const [request, setRequest] = useState<AnalyzeRequest | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [isExporting, setIsExporting] = useState(false)

  const handleSubmit = async (req: AnalyzeRequest) => {
    setPhase('analyzing')
    setError(null)
    setResponse(null)
    setRequest(req)
    const startedAt = Date.now()

    try {
      const res = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'The board could not evaluate this decision.')
      }

      const data: BoardResponse = await res.json()
      // Real data has arrived — the wait state compresses its remaining staging
      // (responseReady), then we advance. Live runs outlast the dwell and switch
      // immediately; mock runs hold ~3s so the phase is visible.
      setResponse(data)
      const wait = Math.max(0, MIN_WORK_DWELL_MS - (Date.now() - startedAt))
      setTimeout(() => setPhase('debating'), wait)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setPhase('input')
    }
  }

  const debateSummary = response?.consensus?.summary

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
            <Logo idSuffix="boardroom-nav" size={32} />
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

        {/* Hero — only on input phase. */}
        {phase === 'input' && (
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-semibold tracking-[-0.02em] leading-[1.12] text-graphite mb-4">
              Bring one decision to the board
              <span className="block text-muted font-normal text-2xl md:text-3xl mt-2">
                evaluated, debated, and returned as a board memo
              </span>
            </h1>
            <p className="text-lg text-muted max-w-2xl mx-auto">
              Seven specialised agents pressure-test your call against what they know about the
              company — is this sound, and what are you missing? — then hand you a board-ready memo
              with the dissent left in.
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
        {phase === 'input' && <DecisionIntake onSubmit={handleSubmit} />}

        {/* Phase: Analyzing / Debating */}
        {(phase === 'analyzing' || phase === 'debating') && (
          <AgentDebate
            phase={phase}
            responseReady={response != null}
            agentOutputs={response?.agent_outputs}
            debateRounds={response?.debate_rounds}
            debateSummary={debateSummary}
            consensus={response?.consensus}
            onContinue={() => setPhase('results')}
          />
        )}

        {/* Phase: Results — the board memo */}
        {phase === 'results' && response && (() => {
          const companyName = request?.profile?.company_name || response.company_id
          const memoMeta = { companyName, question: request?.decision.question }
          const copyMemo = () => {
            navigator.clipboard.writeText(memoToMarkdown(response, memoMeta))
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
          }
          const downloadMemo = () => {
            const slug = response.company_id || 'company'
            downloadTextFile(`founderos-board-memo-${slug}.md`, memoToMarkdown(response, memoMeta))
          }
          const downloadPdf = async () => {
            setIsExporting(true)
            try {
              const slug = response.company_id || 'company'
              await exportBoardMemoPdf(response, companyName, request?.decision.question, `founderos-board-memo-${slug}.pdf`)
            } finally {
              setIsExporting(false)
            }
          }

          return (
            <div className="space-y-10 animate-fade-in">
              {/* The memo header */}
              <div className="flex items-center gap-2.5">
                <span className="w-9 h-9 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-600">
                  <ScrollText className="w-5 h-5" aria-hidden="true" />
                </span>
                <h2 className="text-xl font-semibold">Board memo</h2>
              </div>

              {/* The memo itself */}
              <ErrorBoundary>
                <BoardMemo
                  rec={response.recommendation}
                  companyName={companyName}
                  question={request?.decision.question}
                  date={response.created_at}
                  sampleData={response.mock_mode}
                  usedPaths={response.used_paths}
                />
              </ErrorBoundary>

              {/* How the board reasoned — attributed */}
              <ErrorBoundary>
                <CouncilReasoning outputs={response.agent_outputs} />
              </ErrorBoundary>

              {/* Close the loop: export */}
              <div className="card flex flex-col sm:flex-row sm:items-center gap-4 sm:justify-between">
                <div>
                  <h2 className="text-base font-semibold">Take the memo with you</h2>
                  <p className="text-sm text-muted mt-0.5">
                    The decision is saved to the company&rsquo;s vault — the board will remember it next time.
                  </p>
                </div>
                <div className="flex flex-wrap gap-3">
                  <button className="btn-secondary" onClick={copyMemo}>
                    {copied ? (
                      <><Check className="w-4 h-4 text-brand-600" aria-hidden="true" /> Copied</>
                    ) : (
                      <><Copy className="w-4 h-4" aria-hidden="true" /> Copy memo</>
                    )}
                  </button>
                  <button className="btn-secondary" onClick={downloadPdf} disabled={isExporting} aria-busy={isExporting}>
                    <FileDown className="w-4 h-4" aria-hidden="true" />
                    {isExporting ? 'Exporting…' : 'Export PDF'}
                  </button>
                  <button className="btn-primary" onClick={downloadMemo}>
                    <Download className="w-4 h-4" aria-hidden="true" />
                    Download .md
                  </button>
                </div>
              </div>

              {/* Disclaimer — advisory, not fiduciary; closes the document */}
              {response.recommendation.disclaimer && (
                <p className="text-xs text-muted italic border-t border-hairline pt-4">
                  {response.recommendation.disclaimer}
                </p>
              )}

              {/* Restart */}
              <div className="text-center pt-2">
                <button
                  className="link-quiet mx-auto"
                  onClick={() => { setPhase('input'); setResponse(null) }}
                >
                  <ArrowLeft className="w-4 h-4" aria-hidden="true" />
                  Bring another decision
                </button>
              </div>
            </div>
          )
        })()}
      </div>
    </main>
  )
}
