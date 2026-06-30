/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Dark surfaces + text (the Studio)
        ink: '#0B0C14',      // page base
        surface: '#161A26',  // raised cards / panels
        paper: '#F4F5FA',    // primary text on dark

        // Light surfaces + text (the Marketing page). Additive — does not
        // affect the dark studio, which never references these.
        canvas: '#F7F5F1',   // warm paper background
        hairline: '#ECEAE4', // light card border
        graphite: '#14151A', // solid ink headline / text on light
        muted: '#6B6B72',    // secondary copy on light

        // Brand primary = Violet. Retires the old sky-blue to kill the
        // generic-SaaS-blue feel. 400 = violet-soft, 500 = violet-primary.
        brand: {
          300: '#C9BEFA',
          400: '#A78BFA', // violet soft
          500: '#7C6FF0', // violet primary
          600: '#6A5CE0',
          700: '#574AC2',
          800: '#3D3590',
          900: '#29245E',
          950: '#18142F',
        },

        // Accent = Gold. Used sparingly — primary CTAs, success, the plan reveal.
        accent: {
          300: '#F0CE8E',
          400: '#E9BD6C',
          500: '#E0A845', // gold
          600: '#C8902F', // gold darkened for contrast on light surfaces
          700: '#9E6E22',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
