import { Boxes, CircuitBoard, Database, Cloud, Hexagon, Layers } from 'lucide-react'

/**
 * PLACEHOLDER logos. Generic lucide marks standing in for partner / technology
 * logos — swap each for a real brand asset before launch.
 */
const LOGOS = [
  { name: 'Acme Labs', icon: Boxes },
  { name: 'Northwind', icon: CircuitBoard },
  { name: 'DataForge', icon: Database },
  { name: 'Nimbus', icon: Cloud },
  { name: 'Hexel', icon: Hexagon },
  { name: 'Stratify', icon: Layers },
]

export default function TrustStrip() {
  return (
    <section className="max-w-6xl mx-auto px-6 py-12">
      <p className="text-center text-xs uppercase tracking-[0.18em] text-muted">
        Built with a modern AI &amp; data stack
        <span className="ml-2 normal-case tracking-normal text-muted/70">(placeholder logos)</span>
      </p>
      <ul className="mt-8 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-x-6 gap-y-8 items-center">
        {LOGOS.map((l) => {
          const Icon = l.icon
          return (
            <li
              key={l.name}
              className="flex items-center justify-center gap-2 text-muted/70 hover:text-graphite transition-colors"
            >
              <Icon className="w-5 h-5" aria-hidden="true" />
              <span className="text-sm font-medium">{l.name}</span>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
