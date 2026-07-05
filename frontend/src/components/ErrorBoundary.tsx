'use client'

import React from 'react'
import { AlertTriangle } from 'lucide-react'

interface Props {
  children: React.ReactNode
  fallback?: React.ReactNode
}

interface State {
  hasError: boolean
  message: string
}

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, message: '' }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message || 'An unexpected error occurred.' }
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="card border-red-200 bg-red-50/50 p-6 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold text-red-700">Something went wrong rendering the board memo.</p>
            <p className="text-xs text-red-600/80 mt-1">
              Try refreshing the page. If the issue persists, download the raw memo instead.
            </p>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
