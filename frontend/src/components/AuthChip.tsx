'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { LogOut } from 'lucide-react'
import { AUTH_ENABLED } from '@/lib/auth'
import { createClient } from '@/lib/supabase/client'

/**
 * Quiet signed-in chip for the boardroom header: user email + sign out. Renders
 * nothing when the gate is off, so the app is visually identical to today in the
 * demo. Kept minimal and brand-matched (hairline, muted text, no emoji).
 */
export default function AuthChip() {
  const router = useRouter()
  const [email, setEmail] = useState<string | null>(null)

  useEffect(() => {
    if (!AUTH_ENABLED) return
    const supabase = createClient()
    supabase.auth.getUser().then(({ data }) => setEmail(data.user?.email ?? null))
    const { data: sub } = supabase.auth.onAuthStateChange((_e, session) =>
      setEmail(session?.user?.email ?? null),
    )
    return () => sub.subscription.unsubscribe()
  }, [])

  if (!AUTH_ENABLED || !email) return null

  const signOut = async () => {
    await createClient().auth.signOut()
    router.replace('/signin')
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="hidden sm:inline text-muted max-w-[180px] truncate" title={email}>
        {email}
      </span>
      <button
        onClick={signOut}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-hairline text-graphite/80 hover:text-graphite hover:bg-canvas transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
        aria-label="Sign out"
      >
        <LogOut className="w-4 h-4" aria-hidden="true" />
        Sign out
      </button>
    </div>
  )
}
