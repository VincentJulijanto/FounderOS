import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

/**
 * Magic-link callback. Supabase redirects here with a `code`; we exchange it for
 * a session (cookies) and forward to the originally requested page (default
 * /boardroom). On failure, back to /signin with an error flag.
 */
export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const next = searchParams.get('next') || '/boardroom'

  if (code) {
    const supabase = createClient()
    const { error } = await supabase.auth.exchangeCodeForSession(code)
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`)
    }
  }

  return NextResponse.redirect(`${origin}/signin?error=auth`)
}
