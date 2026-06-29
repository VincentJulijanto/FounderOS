import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

export default function ClosingCTA() {
  return (
    <section className="max-w-6xl mx-auto px-6 pb-24">
      <div className="relative overflow-hidden glass px-8 py-14 md:py-20 text-center">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 -z-10"
          style={{
            background:
              'radial-gradient(60% 80% at 50% 0%, rgba(139,92,246,0.18), transparent 70%), radial-gradient(60% 80% at 50% 100%, rgba(14,165,233,0.16), transparent 70%)',
          }}
        />
        <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-gray-100 max-w-2xl mx-auto">
          Put your idea in front of the agents
        </h2>
        <p className="mt-4 text-gray-400 text-lg max-w-xl mx-auto">
          Share your profile and let the society scout, debate, and build your
          execution plan — in minutes.
        </p>
        <div className="mt-8 flex justify-center">
          <Link href="/studio" className="btn-primary">
            Open the Studio
            <ArrowRight className="w-4 h-4" aria-hidden="true" />
          </Link>
        </div>
      </div>
    </section>
  )
}
