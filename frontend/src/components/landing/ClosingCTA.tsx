import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

export default function ClosingCTA() {
  return (
    <section className="max-w-3xl mx-auto px-6 py-24 md:py-32 text-center">
      <h2 className="text-3xl md:text-[2.75rem] font-semibold tracking-[-0.02em] leading-[1.12] text-graphite">
        Put your idea in front of the council
      </h2>
      <p className="mt-5 text-muted text-lg leading-relaxed max-w-xl mx-auto">
        Share your profile and let the council scout, debate, and build your
        execution plan — in minutes.
      </p>
      <div className="mt-9 flex justify-center">
        <Link href="/studio" className="btn-ink">
          Enter the studio
          <ArrowRight className="w-4 h-4" aria-hidden="true" />
        </Link>
      </div>
    </section>
  )
}
