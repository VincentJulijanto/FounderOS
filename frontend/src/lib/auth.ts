/**
 * Thin auth gate config. The whole feature is behind ONE flag so the demo can
 * run exactly as before. When NEXT_PUBLIC_AUTH_ENABLED is anything other than
 * the string "true", every auth path is inert: no login UI, no session checks,
 * middleware passes everything through.
 *
 * Read as a plain string compare (not a truthy coercion) so an unset var, "",
 * "false", or "0" all mean OFF.
 */
export const AUTH_ENABLED = process.env.NEXT_PUBLIC_AUTH_ENABLED === 'true'

/** The only route the gate protects this pass. Landing + everything else stay public. */
export const PROTECTED_PREFIXES = ['/boardroom']
