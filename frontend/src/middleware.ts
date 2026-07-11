import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'
import { AUTH_ENABLED } from '@/lib/auth'

/**
 * Thin gate. Protects ONLY /boardroom. Landing, /signin, and the auth callback
 * stay public. When AUTH_ENABLED is off, this returns immediately and the app
 * behaves exactly as today (no session work, no redirects).
 */
export async function middleware(request: NextRequest) {
  if (!AUTH_ENABLED) return NextResponse.next()

  let response = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          response = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options),
          )
        },
      },
    },
  )

  // Do not run code between createServerClient and getUser — refreshes the session.
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    const url = request.nextUrl.clone()
    url.pathname = '/signin'
    url.searchParams.set('redirect', request.nextUrl.pathname)
    return NextResponse.redirect(url)
  }

  return response
}

// Run only on the gated route (and its subpaths). Everything else is public.
export const config = {
  matcher: ['/boardroom/:path*', '/boardroom'],
}
