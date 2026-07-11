/** @type {import('next').NextConfig} */
const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

// When the auth gate is on, the browser must reach Supabase (magic-link + session
// calls hit its /auth/v1 endpoints). Add ONLY its origin to connect-src, and ONLY
// when AUTH_ENABLED, so the CSP is byte-identical to today when the gate is off.
const authEnabled = process.env.NEXT_PUBLIC_AUTH_ENABLED === 'true'
let supabaseOrigin = ''
try {
  if (authEnabled && process.env.NEXT_PUBLIC_SUPABASE_URL) {
    supabaseOrigin = new URL(process.env.NEXT_PUBLIC_SUPABASE_URL).origin
  }
} catch {
  supabaseOrigin = ''
}
const connectSrc = ["'self'", apiBase, supabaseOrigin].filter(Boolean).join(' ')

const nextConfig = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
              "style-src 'self' 'unsafe-inline'",
              `connect-src ${connectSrc}`,
              "img-src 'self' data:",
              "font-src 'self'",
            ].join('; '),
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig
