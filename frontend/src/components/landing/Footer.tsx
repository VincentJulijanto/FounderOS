import Link from 'next/link'
import Logo from '@/components/Logo'

/* Footer links are placeholders — wire to real routes/pages as they exist. */
const COLUMNS = [
  {
    heading: 'Product',
    links: [
      { label: 'Features', href: '#features' },
      { label: 'How it works', href: '#how-it-works' },
      { label: 'Enter the boardroom', href: '/boardroom' },
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
    <footer className="border-t border-hairline">
      <div className="max-w-6xl mx-auto px-6 py-16 grid gap-12 md:grid-cols-[1.5fr_1fr_1fr_1fr]">
        {/* Brand */}
        <div>
          <Logo idSuffix="footer" size={30} />
          <p className="mt-4 text-sm text-muted max-w-xs leading-relaxed">
            An AI board for business decisions: a council of agents that
            pressure-tests the call you bring, debates the trade-offs, and hands
            you a board-ready memo.
          </p>
        </div>

        {/* Link columns */}
        {COLUMNS.map((col) => (
          <nav key={col.heading} aria-label={col.heading}>
            <h2 className="text-sm font-semibold text-graphite">{col.heading}</h2>
            <ul className="mt-4 space-y-2.5">
              {col.links.map((l) => (
                <li key={l.label}>
                  {l.href.startsWith('/') ? (
                    <Link href={l.href} className="text-sm text-muted hover:text-graphite transition-colors">
                      {l.label}
                    </Link>
                  ) : (
                    <a href={l.href} className="text-sm text-muted hover:text-graphite transition-colors">
                      {l.label}
                    </a>
                  )}
                </li>
              ))}
            </ul>
          </nav>
        ))}
      </div>

      <div className="max-w-6xl mx-auto px-6 pb-10 text-xs text-muted/80">
        &copy; {/* PLACEHOLDER year */} 2026 FounderOS. All rights reserved.
      </div>
    </footer>
  )
}
