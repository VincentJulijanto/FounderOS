import { createBrowserClient } from '@supabase/ssr'

/**
 * Browser-side Supabase client (magic-link sign-in, sign-out, session reads on
 * the client). Reads NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY.
 * Only ever constructed on auth surfaces, which render only when AUTH_ENABLED.
 */
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  )
}
