interface LogoProps {
  /** Pixel size of the council mark. Default 40. */
  size?: number
  /** Render the "FounderOS" wordmark beside the mark. Default true. */
  withWordmark?: boolean
  /** Unique suffix for the gradient id — required when more than one Logo
   *  renders on the same page so the SVG gradients don't collide. */
  idSuffix?: string
  className?: string
}

/**
 * The FounderOS council mark: a central node linked to six surrounding nodes —
 * the eight-agent council. Violet-to-gold gradient on the nodes, violet links.
 */
export default function Logo({
  size = 40,
  withWordmark = true,
  idSuffix = 'default',
  className = '',
}: LogoProps) {
  const gradientId = `fos-${idSuffix}`
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 64 64"
        role="img"
        aria-label="FounderOS"
        className="shrink-0"
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#A78BFA" />
            <stop offset="1" stopColor="#E0A845" />
          </linearGradient>
        </defs>
        <g stroke="#7C6FF0" strokeWidth="1.2" opacity="0.55">
          <line x1="32" y1="32" x2="54" y2="32" />
          <line x1="32" y1="32" x2="43" y2="51" />
          <line x1="32" y1="32" x2="21" y2="51" />
          <line x1="32" y1="32" x2="10" y2="32" />
          <line x1="32" y1="32" x2="21" y2="13" />
          <line x1="32" y1="32" x2="43" y2="13" />
        </g>
        <g fill={`url(#${gradientId})`}>
          <circle cx="54" cy="32" r="3.5" />
          <circle cx="43" cy="51" r="3.5" />
          <circle cx="21" cy="51" r="3.5" />
          <circle cx="10" cy="32" r="3.5" />
          <circle cx="21" cy="13" r="3.5" />
          <circle cx="43" cy="13" r="3.5" />
          <circle cx="32" cy="32" r="5.5" />
        </g>
      </svg>
      {withWordmark && (
        // Inherits the surrounding text colour: paper on a dark surface,
        // graphite on the light marketing page.
        <span className="font-semibold text-lg tracking-tight">FounderOS</span>
      )}
    </span>
  )
}
