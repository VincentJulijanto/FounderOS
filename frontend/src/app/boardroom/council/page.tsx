'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, Users, Loader2, AlertTriangle, Hammer } from 'lucide-react'
import Logo from '@/components/Logo'
import AuthChip from '@/components/AuthChip'
import CouncilBrief from '@/components/CouncilBrief'
import FeatureLoop from '@/components/FeatureLoop'
import ErrorBoundary from '@/components/ErrorBoundary'
import type { CouncilBriefResponse, FeatureLoopResponse, FeedbackTheme } from '@/lib/types'

const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

const COMPANIES = [
  { id: 'harborline-logistics', label: 'Harborline Logistics' },
  { id: 'lumen-skincare', label: 'Lumen Skincare' },
]

type Status = 'idle' | 'loading' | 'done' | 'error'

export default function CouncilPage() {
  const [companyId, setCompanyId] = useState(COMPANIES[0].id)
  const [status, setStatus] = useState<Status>('idle')
  const [result, setResult] = useState<CouncilBriefResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loopStatus, setLoopStatus] = useState<Status>('idle')
  const [loopResult, setLoopResult] = useState<FeatureLoopResponse | null>(null)
  const [loopError, setLoopError] = useState<string | null>(null)
  const [loopTheme, setLoopTheme] = useState<string | null>(null)

  const runLoop = async (theme: FeedbackTheme) => {
    setLoopStatus('loading')
    setLoopError(null)
    setLoopResult(null)
    setLoopTheme(theme.theme)

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 300_000) // up to ~5 deep calls live

    try {
      const res = await fetch(`${API_URL}/api/feature-loop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: companyId,
          theme,
          feedback_notes_read: result?.feedback_notes_read ?? 0,
        }),
        signal: controller.signal,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'The delivery loop could not run.')
      }
      setLoopResult(await res.json())
      setLoopStatus('done')
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        setLoopError('Request timed out. The loop took too long — try again.')
      } else {
        setLoopError(err instanceof Error ? err.message : 'Something went wrong.')
      }
      setLoopStatus('error')
    } finally {
      clearTimeout(timeoutId)
    }
  }

  const runCouncil = async () => {
    setStatus('loading')
    setError(null)
    setResult(null)
    setLoopStatus('idle')
    setLoopResult(null)
    setLoopError(null)

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 120_000) // 2 min for the lighter council

    try {
      const res = await fetch(`${API_URL}/api/council-brief`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_id: companyId }),
        signal: controller.signal,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'The council could not run.')
      }
      setResult(await res.json())
      setStatus('done')
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        setError('Request timed out. The council took too long — try again.')
      } else {
        setError(err instanceof Error ? err.message : 'Something went wrong.')
      }
      setStatus('error')
    } finally {
      clearTimeout(timeoutId)
    }
  }

  return (
    <main className="min-h-screen">
      <header className="bg-canvas/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link
            href="/"
            className="rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
            aria-label="FounderOS home"
          >
            <Logo idSuffix="council-nav" size={32} />
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/boardroom" className="text-sm text-muted hover:text-graphite transition-colors flex items-center gap-1.5">
              <ArrowLeft className="w-4 h-4" aria-hidden="true" />
              Board room
            </Link>
            <AuthChip />
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-12">

        {/* Hero */}
        <div className="mb-10">
          <div className="flex items-center gap-2.5 mb-4">
            <span className="w-9 h-9 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-400">
              <Users className="w-5 h-5" aria-hidden="true" />
            </span>
            <h1 className="text-2xl font-semibold text-graphite">Feedback Intelligence Council</h1>
          </div>
          <p className="text-muted max-w-2xl leading-relaxed">
            A three-agent mini-council reads your company&rsquo;s feedback vault and returns a ranked
            product brief. The Analyst clusters themes, the Skeptic challenges the ranking for bias
            and scope creep, and the Chair synthesises — accepting, reframing, or overriding each
            objection. From there, any theme can be sent into the delivery loop: a Senior SWE drafts
            the build spec and a QA Engineer reviews it for bugs, leaks, and breach vectors —
            iterating until it is safe to release.
          </p>
        </div>

        {/* Agent Society callout — council + delivery loop */}
        <div className="card mb-8 grid gap-6 sm:grid-cols-3 lg:grid-cols-5">
          {[
            { label: 'Analyst', desc: 'Clusters feedback → ranked themes; gates the loop on signal strength' },
            { label: 'Skeptic', desc: 'Challenges each theme for bias, scope creep, misalignment' },
            { label: 'Chair', desc: 'Accepts / reframes / overrides — writes the final brief' },
            { label: 'Senior SWE', desc: 'Turns a validated theme into a build spec; fixes what QA finds' },
            { label: 'QA Engineer', desc: 'Hunts bugs, leaks, breach vectors — nothing ships until it passes' },
          ].map(({ label, desc }) => (
            <div key={label}>
              <p className="text-sm font-semibold text-graphite mb-0.5">{label}</p>
              <p className="text-xs text-muted">{desc}</p>
            </div>
          ))}
        </div>

        {/* Input */}
        <div className="card mb-8 space-y-5">
          <h2 className="text-base font-semibold">Run the council</h2>

          <div>
            <label className="block text-sm font-medium text-graphite mb-1.5" htmlFor="company-picker">
              Company
            </label>
            <select
              id="company-picker"
              value={companyId}
              onChange={(e) => setCompanyId(e.target.value)}
              className="w-full max-w-xs rounded-lg border border-hairline bg-surface px-3 py-2 text-sm text-graphite focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              {COMPANIES.map((c) => (
                <option key={c.id} value={c.id}>{c.label}</option>
              ))}
            </select>
            <p className="mt-1.5 text-xs text-muted">
              The council reads feedback notes from this company&rsquo;s vault (type: feedback).
            </p>
          </div>

          <button
            className="btn-primary"
            onClick={runCouncil}
            disabled={status === 'loading'}
            aria-busy={status === 'loading'}
          >
            {status === 'loading' ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                Council deliberating…
              </>
            ) : (
              <>
                <Users className="w-4 h-4" aria-hidden="true" />
                Convene the council
              </>
            )}
          </button>
        </div>

        {/* Loading state */}
        {status === 'loading' && (
          <div className="card text-center py-12 space-y-4">
            <Loader2 className="w-8 h-8 animate-spin text-brand-400 mx-auto" aria-hidden="true" />
            <div>
              <p className="text-sm font-medium text-graphite">Council at work</p>
              <p className="text-xs text-muted mt-1">
                Analyst → Skeptic → Chair — three agents deliberating
              </p>
            </div>
          </div>
        )}

        {/* Error */}
        {status === 'error' && error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 flex items-center gap-2" role="alert">
            <AlertTriangle className="w-5 h-5 shrink-0" aria-hidden="true" />
            {error}
          </div>
        )}

        {/* Results */}
        {status === 'done' && result && (
          <ErrorBoundary>
            <CouncilBrief data={result} />
          </ErrorBoundary>
        )}

        {/* Delivery loop — send a council theme to build */}
        {status === 'done' && result && result.themes.length > 0 && (
          <div className="mt-12 space-y-8">
            <div className="card space-y-4">
              <div>
                <h2 className="text-base font-semibold flex items-center gap-2">
                  <Hammer className="w-4 h-4 text-brand-400" aria-hidden="true" />
                  Build from this brief
                </h2>
                <p className="text-sm text-muted mt-1">
                  Send a theme into the delivery loop: the Data Analyst gates on signal strength,
                  the Senior SWE writes the build spec, and QA iterates on it until it is safe to release.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                {result.themes.map((t) => (
                  <button
                    key={t.theme}
                    className="btn-secondary"
                    onClick={() => runLoop(t)}
                    disabled={loopStatus === 'loading'}
                  >
                    {loopStatus === 'loading' && loopTheme === t.theme ? (
                      <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                    ) : (
                      <Hammer className="w-4 h-4" aria-hidden="true" />
                    )}
                    {t.theme}
                  </button>
                ))}
              </div>
            </div>

            {loopStatus === 'loading' && (
              <div className="card text-center py-12 space-y-4">
                <Loader2 className="w-8 h-8 animate-spin text-brand-400 mx-auto" aria-hidden="true" />
                <div>
                  <p className="text-sm font-medium text-graphite">Delivery loop running</p>
                  <p className="text-xs text-muted mt-1">
                    Analyst gate → SWE builds → QA reviews → fixes until it passes
                  </p>
                </div>
              </div>
            )}

            {loopStatus === 'error' && loopError && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 flex items-center gap-2" role="alert">
                <AlertTriangle className="w-5 h-5 shrink-0" aria-hidden="true" />
                {loopError}
              </div>
            )}

            {loopStatus === 'done' && loopResult && (
              <ErrorBoundary>
                <FeatureLoop data={loopResult} />
              </ErrorBoundary>
            )}
          </div>
        )}
      </div>
    </main>
  )
}
