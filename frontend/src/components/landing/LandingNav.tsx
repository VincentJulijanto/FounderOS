'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Menu, X } from 'lucide-react'

const LINKS = [
  { label: 'Features', href: '#features' },
  { label: 'How it works', href: '#how-it-works' },
  { label: 'FAQ', href: '#faq' },
]

export default function LandingNav() {
  const [open, setOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 border-b border-white/5 bg-gray-950/70 backdrop-blur">
      <nav
        className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between"
        aria-label="Primary"
      >
        {/* Logo → home */}
        <Link
          href="/"
          className="flex items-center gap-3 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          aria-label="FounderOS home"
        >
          <span className="w-8 h-8 bg-gradient-to-br from-brand-500 to-accent-500 rounded-lg flex items-center justify-center text-white font-bold text-sm">
            F
          </span>
          <span className="font-semibold text-lg text-gray-100">FounderOS</span>
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-8 text-sm text-gray-400">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="hover:text-gray-100 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
            >
              {l.label}
            </a>
          ))}
        </div>

        {/* Desktop CTA */}
        <div className="hidden md:flex items-center gap-3">
          <Link href="/studio" className="btn-primary !px-5 !py-2 text-sm">
            Open the Studio
          </Link>
        </div>

        {/* Mobile toggle */}
        <button
          type="button"
          className="md:hidden p-2 -mr-2 text-gray-300 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
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
        <div id="mobile-menu" className="md:hidden border-t border-white/5 px-6 py-4 space-y-3">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className="block text-gray-300 hover:text-gray-100 transition-colors"
            >
              {l.label}
            </a>
          ))}
          <Link
            href="/studio"
            onClick={() => setOpen(false)}
            className="btn-primary w-full !py-2 text-sm"
          >
            Open the Studio
          </Link>
        </div>
      )}
    </header>
  )
}
