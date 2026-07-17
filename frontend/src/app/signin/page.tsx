'use client'

import { useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { Mail, ArrowRight, CheckCircle2, AlertTriangle, Lock } from 'lucide-react'
import Logo from '@/components/Logo'
import { createClient } from '@/lib/supabase/client'

// idle: form shown. loading: request in flight. error: message shown, form stays.
// sent: magic-link email dispatched. check-email: sign-up / reset email dispatched.
type State = 'idle' | 'loading' | 'error' | 'sent' | 'check-email'
type Mode = 'signin' | 'signup'

const MIN_PASSWORD = 6 // Supabase project default; surfaced client-side below.

function SignInForm() {
  const params = useSearchParams()
  const redirect = params.get('redirect') || '/boardroom'
  const [mode, setMode] = useState<Mode>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [state, setState] = useState<State>(params.get('error') ? 'error' : 'idle')
  const [message, setMessage] = useState('')

  const busy = state === 'loading'
  const callbackUrl = () =>
    `${window.location.origin}/auth/callback?next=${encodeURIComponent(redirect)}`

  const fail = (err: unknown, fallback: string) => {
    setMessage(err instanceof Error ? err.message : fallback)
    setState('error')
  }

  // Email + password: sign in, or create account (confirm-email flow).
  const submitPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (busy) return
    if (!email.trim()) return
    if (password.length < MIN_PASSWORD) {
      setMessage(`Password must be at least ${MIN_PASSWORD} characters.`)
      setState('error')
      return
    }
    setState('loading')
    try {
      const supabase = createClient()
      if (mode === 'signup') {
        const { data, error } = await supabase.auth.signUp({
          email: email.trim(),
          password,
          options: { emailRedirectTo: callbackUrl() },
        })
        if (error) throw error
        // Confirm-email off: signUp returns a live session, so land them in.
        // Confirm-email on: no session yet, show the check-email state.
        if (data.session) {
          window.location.assign(redirect)
        } else {
          setState('check-email')
        }
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        })
        if (error) throw error
        // Session cookie is set; go where they were headed.
        window.location.assign(redirect)
      }
    } catch (err) {
      fail(err, mode === 'signup' ? 'Could not create the account.' : 'Could not sign in.')
    }
  }

  // Secondary path: passwordless magic link (unchanged behaviour).
  const sendLink = async () => {
    if (busy) return
    if (!email.trim()) {
      setMessage('Enter your email first, then request a link.')
      setState('error')
      return
    }
    setState('loading')
    try {
      const supabase = createClient()
      const { error } = await supabase.auth.signInWithOtp({
        email: email.trim(),
        options: { emailRedirectTo: callbackUrl() },
      })
      if (error) throw error
      setState('sent')
    } catch (err) {
      fail(err, 'Could not send the sign-in link.')
    }
  }

  const forgotPassword = async () => {
    if (busy) return
    if (!email.trim()) {
      setMessage('Enter your email first, then reset your password.')
      setState('error')
      return
    }
    setState('loading')
    try {
      const supabase = createClient()
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: `${window.location.origin}/auth/reset`,
      })
      if (error) throw error
      setState('check-email')
    } catch (err) {
      fail(err, 'Could not send the reset link.')
    }
  }

  const switchMode = (next: Mode) => {
    setMode(next)
    setState('idle')
    setMessage('')
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-6 bg-canvas">
      <div className="w-full max-w-sm">
        <div className="flex justify-center mb-8">
          <Logo idSuffix="signin" size={40} />
        </div>

        <div className="card">
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
          ) : state === 'check-email' ? (
            <div className="flex items-start gap-3 rounded-xl border border-hairline bg-canvas p-4">
              <CheckCircle2 className="w-5 h-5 text-brand-600 shrink-0 mt-0.5" aria-hidden="true" />
              <div>
                <p className="text-sm font-medium text-graphite">Check your email</p>
                <p className="text-sm text-muted mt-0.5">
                  We sent a link to {email}. Open it to continue, then come back to sign in.
                </p>
              </div>
            </div>
          ) : (
            <>
              <h1 className="text-xl font-semibold text-graphite">
                {mode === 'signup' ? 'Create your FounderOS account' : 'Sign in to FounderOS'}
              </h1>
              <p className="text-sm text-muted mt-1 mb-5">
                {mode === 'signup'
                  ? 'Use your email and a password. We will email you a confirmation link.'
                  : 'Use your email and password, or request a one-time sign-in link.'}
              </p>

              <div
                className="grid grid-cols-2 gap-1 p-1 rounded-full border border-hairline mb-5"
                role="tablist"
                aria-label="Sign in or create account"
              >
                {(['signin', 'signup'] as Mode[]).map((m) => (
                  <button
                    key={m}
                    type="button"
                    role="tab"
                    aria-selected={mode === m}
                    onClick={() => switchMode(m)}
                    className={`text-sm font-medium py-1.5 rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
                      mode === m ? 'bg-graphite text-canvas' : 'text-muted hover:text-graphite'
                    }`}
                  >
                    {m === 'signin' ? 'Sign in' : 'Create account'}
                  </button>
                ))}
              </div>

              <form onSubmit={submitPassword} className="space-y-4">
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

                <div>
                  <div className="flex items-center justify-between">
                    <label className="label mb-2" htmlFor="password">Password</label>
                    {mode === 'signin' && (
                      <button
                        type="button"
                        onClick={forgotPassword}
                        className="text-xs text-muted hover:text-graphite transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
                      >
                        Forgot password?
                      </button>
                    )}
                  </div>
                  <input
                    id="password"
                    type="password"
                    autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                    className="input"
                    placeholder={mode === 'signup' ? 'Create a password' : 'Your password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    minLength={MIN_PASSWORD}
                    required
                  />
                  {mode === 'signup' && (
                    <p className="text-xs text-muted mt-1.5">At least {MIN_PASSWORD} characters.</p>
                  )}
                </div>

                {state === 'error' && (
                  <div className="flex items-center gap-2 text-sm text-red-700" role="alert">
                    <AlertTriangle className="w-4 h-4 shrink-0" aria-hidden="true" />
                    {message || 'Something went wrong. Try again.'}
                  </div>
                )}

                <button type="submit" className="btn-primary w-full" disabled={busy} aria-busy={busy}>
                  <Lock className="w-4 h-4" aria-hidden="true" />
                  {busy
                    ? mode === 'signup'
                      ? 'Creating account...'
                      : 'Signing in...'
                    : mode === 'signup'
                      ? 'Create account'
                      : 'Sign in'}
                  {!busy && <ArrowRight className="w-4 h-4" aria-hidden="true" />}
                </button>
              </form>

              <div className="flex items-center gap-3 my-5">
                <div className="h-px flex-1 bg-hairline" />
                <span className="text-xs text-muted">or</span>
                <div className="h-px flex-1 bg-hairline" />
              </div>

              <button
                type="button"
                onClick={sendLink}
                className="btn-secondary w-full"
                disabled={busy}
                aria-busy={busy}
              >
                <Mail className="w-4 h-4" aria-hidden="true" />
                Email me a link instead
              </button>
            </>
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
