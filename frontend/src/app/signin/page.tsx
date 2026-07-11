'use client'

import { useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { Mail, ArrowRight, CheckCircle2, AlertTriangle } from 'lucide-react'
import Logo from '@/components/Logo'
import { createClient } from '@/lib/supabase/client'

type State = 'idle' | 'sent' | 'error'

function SignInForm() {
  const params = useSearchParams()
  const redirect = params.get('redirect') || '/boardroom'
  const [email, setEmail] = useState('')
  const [state, setState] = useState<State>(params.get('error') ? 'error' : 'idle')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  const sendLink = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || busy) return
    setBusy(true)
    setState('idle')
    try {
      const supabase = createClient()
      const next = `${window.location.origin}/auth/callback?next=${encodeURIComponent(redirect)}`
      const { error } = await supabase.auth.signInWithOtp({
        email: email.trim(),
        options: { emailRedirectTo: next },
      })
      if (error) throw error
      setState('sent')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Could not send the sign-in link.')
      setState('error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-6 bg-canvas">
      <div className="w-full max-w-sm">
        <div className="flex justify-center mb-8">
          <Logo idSuffix="signin" size={40} />
        </div>

        <div className="card">
          <h1 className="text-xl font-semibold text-graphite">Sign in to FounderOS</h1>
          <p className="text-sm text-muted mt-1 mb-6">
            Enter your email and we will send you a sign-in link. No password needed.
          </p>

          {state === 'sent' ? (
            <div className="flex items-start gap-3 rounded-xl border border-hairline bg-canvas p-4">
              <CheckCircle2 className="w-5 h-5 text-brand-600 shrink-0 mt-0.5" aria-hidden="true" />
              <div>
                <p className="text-sm font-medium text-graphite">Check your email</p>
                <p className="text-sm text-muted mt-0.5">
                  We sent a sign-in link to {email}. Open it on this device to continue.
                </p>
              </div>
            </div>
          ) : (
            <form onSubmit={sendLink} className="space-y-4">
              <div>
                <label className="label" htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  className="input"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              {state === 'error' && (
                <div className="flex items-center gap-2 text-sm text-red-700" role="alert">
                  <AlertTriangle className="w-4 h-4 shrink-0" aria-hidden="true" />
                  {message || 'Something went wrong. Try again.'}
                </div>
              )}

              <button type="submit" className="btn-primary w-full" disabled={busy} aria-busy={busy}>
                <Mail className="w-4 h-4" aria-hidden="true" />
                {busy ? 'Sending link...' : 'Send sign-in link'}
                {!busy && <ArrowRight className="w-4 h-4" aria-hidden="true" />}
              </button>
            </form>
          )}
        </div>

        <p className="text-center text-xs text-muted mt-6">
          An AI board for your business decisions.
        </p>
      </div>
    </main>
  )
}

export default function SignInPage() {
  return (
    <Suspense fallback={null}>
      <SignInForm />
    </Suspense>
  )
}
