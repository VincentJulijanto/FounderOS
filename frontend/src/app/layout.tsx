import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'FounderOS — AI Board for Operators',
  description: 'A board of AI agents that pressure-tests one business decision and returns a board memo.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-canvas text-graphite min-h-screen`}>
        {children}
      </body>
    </html>
  )
}
