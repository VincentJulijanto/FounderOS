import Link from 'next/link'

/* Footer links are placeholders — wire to real routes/pages as they exist. */
const COLUMNS = [
  {
    heading: 'Product',
    links: [
      { label: 'Features', href: '#features' },
      { label: 'How it works', href: '#how-it-works' },
      { label: 'Open the Studio', href: '/studio' },
    ],
  },
  {
    heading: 'Resources',
    links: [
      { label: 'FAQ', href: '#faq' },
      { label: 'Documentation', href: '#' },
      { label: 'Changelog', href: '#' },
    ],
  },
  {
    heading: 'Company',
    links: [
      { label: 'About', href: '#' },
      { label: 'Privacy', href: '#' },
      { label: 'Terms', href: '#' },
    ],
  },
]

export default function Footer() {
  return (
    <footer className="border-t border-white/5">
      <div className="max-w-6xl mx-auto px-6 py-14 grid gap-10 md:grid-cols-[1.5fr_1fr_1fr_1fr]">
        {/* Brand */}
        <div>
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 bg-gradient-to-br from-brand-500 to-accent-500 rounded-lg flex items-center justify-center text-white font-bold text-sm">
              F
            </span>
            <span className="font-semibold text-lg text-gray-100">FounderOS</span>
          </div>
          <p className="mt-4 text-sm text-gray-500 max-w-xs">
            A society of AI agents that scouts, debates, and builds your startup
            execution plan from scratch.
          </p>
        </div>

        {/* Link columns */}
        {COLUMNS.map((col) => (
          <nav key={col.heading} aria-label={col.heading}>
            <h2 className="text-sm font-semibold text-gray-200">{col.heading}</h2>
            <ul className="mt-4 space-y-2.5">
              {col.links.map((l) => (
                <li key={l.label}>
                  {l.href.startsWith('/') ? (
                    <Link
                      href={l.href}
                      className="text-sm text-gray-500 hover:text-gray-200 transition-colors"
                    >
                      {l.label}
                    </Link>
                  ) : (
                    <a
                      href={l.href}
                      className="text-sm text-gray-500 hover:text-gray-200 transition-colors"
                    >
                      {l.label}
                    </a>
                  )}
                </li>
              ))}
            </ul>
          </nav>
        ))}
      </div>

      <div className="border-t border-white/5">
        <div className="max-w-6xl mx-auto px-6 py-6 text-xs text-gray-600">
          &copy; {/* PLACEHOLDER year */} 2026 FounderOS. All rights reserved.
        </div>
      </div>
    </footer>
  )
}
