/** @type {import('next').NextConfig} */
const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

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
              `connect-src 'self' ${apiBase}`,
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
