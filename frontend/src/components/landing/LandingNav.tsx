'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Menu, X, ArrowRight } from 'lucide-react'
import Logo from '@/components/Logo'

const LINKS = [
  { label: 'Features', href: '#features' },
  { label: 'How it works', href: '#how-it-works' },
  { label: 'FAQ', href: '#faq' },
]

export default function LandingNav() {
  const [open, setOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 bg-canvas/80 backdrop-blur">
      <nav
        className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between"
        aria-label="Primary"
      >
        {/* Logo → home (no category pill — descriptor lives in the hero) */}
        <Link
          href="/"
          className="rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          aria-label="FounderOS home"
        >
          <Logo idSuffix="landing-nav" size={30} />
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-9 text-sm text-muted">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="hover:text-graphite transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
            >
              {l.label}
            </a>
          ))}
        </div>

        {/* Desktop CTA — one quiet link */}
        <Link href="/studio" className="hidden md:inline-flex link-quiet text-sm">
          Enter studio
          <ArrowRight className="w-4 h-4" aria-hidden="true" />
        </Link>

        {/* Mobile toggle */}
        <button
          type="button"
          className="md:hidden p-2 -mr-2 text-graphite rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          aria-expanded={open}
          aria-controls="mobile-menu"
          aria-label={open ? 'Close menu' : 'Open menu'}
          onClick={() => setOpen((v) => !v)}
        >
          {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </nav>

      {/* Mobile menu */}
      {open && (
        <div id="mobile-menu" className="md:hidden px-6 pb-5 space-y-4">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className="block text-muted hover:text-graphite transition-colors"
            >
              {l.label}
            </a>
          ))}
          <Link
            href="/studio"
            onClick={() => setOpen(false)}
            className="link-quiet text-sm"
          >
            Enter studio
            <ArrowRight className="w-4 h-4" aria-hidden="true" />
          </Link>
        </div>
      )}
    </header>
  )
}
