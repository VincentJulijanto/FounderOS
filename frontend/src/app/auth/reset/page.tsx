'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { Lock, ArrowRight, CheckCircle2, AlertTriangle } from 'lucide-react'
import Logo from '@/components/Logo'
import { createClient } from '@/lib/supabase/client'

// verifying: exchanging the recovery code for a session on mount.
// ready: session established, show the new-password form.
// loading: updateUser in flight. done: password changed. error/invalid: dead link.
type State = 'verifying' | 'ready' | 'loading' | 'done' | 'error' | 'invalid'

const MIN_PASSWORD = 6

function ResetForm() {
  const params = useSearchParams()
  const [state, setState] = useState<State>('verifying')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')

  // Supabase's recovery link lands here with a `code` (PKCE). Exchange it for a
  // session so updateUser can set the new password. Same-browser only, by design.
  useEffect(() => {
    const supabase = createClient()
    const run = async () => {
      const code = params.get('code')
      if (code) {
        const { error } = await supabase.auth.exchangeCodeForSession(code)
        setState(error ? 'invalid' : 'ready')
        return
      }
      // detectSessionInUrl may have already established the recovery session.
      const { data } = await supabase.auth.getSession()
      setState(data.session ? 'ready' : 'invalid')
    }
    run()
  }, [params])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (state === 'loading') return
    if (password.length < MIN_PASSWORD) {
      setMessage(`Password must be at least ${MIN_PASSWORD} characters.`)
      setState('error')
      return
    }
    setState('loading')
    try {
      const { error } = await createClient().auth.updateUser({ password })
      if (error) throw error
      setState('done')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Could not update the password.')
      setState('error')
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-6 bg-canvas">
      <div className="w-full max-w-sm">
        <div className="flex justify-center mb-8">
          <Logo idSuffix="reset" size={40} />
        </div>

        <div className="card">
          {state === 'verifying' ? (
            <p className="text-sm text-muted">Verifying your reset link...</p>
          ) : state === 'invalid' ? (
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-700 shrink-0 mt-0.5" aria-hidden="true" />
              <div>
                <p className="text-sm font-medium text-graphite">This reset link is invalid or expired</p>
                <p className="text-sm text-muted mt-0.5">
                  Request a new one from the <a href="/signin" className="underline">sign-in page</a>.
                </p>
              </div>
            </div>
          ) : state === 'done' ? (
            <div className="flex items-start gap-3 rounded-xl border border-hairline bg-canvas p-4">
              <CheckCircle2 className="w-5 h-5 text-brand-600 shrink-0 mt-0.5" aria-hidden="true" />
              <div>
                <p className="text-sm font-medium text-graphite">Password updated</p>
                <p className="text-sm text-muted mt-0.5">
                  You can now <a href="/signin" className="underline">sign in</a> with your new password.
                </p>
              </div>
            </div>
          ) : (
            <>
              <h1 className="text-xl font-semibold text-graphite">Set a new password</h1>
              <p className="text-sm text-muted mt-1 mb-6">
                Choose a new password for your FounderOS account.
              </p>
              <form onSubmit={submit} className="space-y-4">
                <div>
                  <label className="label" htmlFor="password">New password</label>
                  <input
                    id="password"
                    type="password"
                    autoComplete="new-password"
                    className="input"
                    placeholder="New password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    minLength={MIN_PASSWORD}
                    required
                  />
                  <p className="text-xs text-muted mt-1.5">At least {MIN_PASSWORD} characters.</p>
                </div>

                {state === 'error' && (
                  <div className="flex items-center gap-2 text-sm text-red-700" role="alert">
                    <AlertTriangle className="w-4 h-4 shrink-0" aria-hidden="true" />
                    {message || 'Something went wrong. Try again.'}
                  </div>
                )}

                <button
                  type="submit"
                  className="btn-primary w-full"
                  disabled={state === 'loading'}
                  aria-busy={state === 'loading'}
                >
                  <Lock className="w-4 h-4" aria-hidden="true" />
                  {state === 'loading' ? 'Updating...' : 'Update password'}
                  {state !== 'loading' && <ArrowRight className="w-4 h-4" aria-hidden="true" />}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </main>
  )
}

export default function ResetPage() {
  return (
    <Suspense fallback={null}>
      <ResetForm />
    </Suspense>
  )
}
