"use client"

import { Component, type ReactNode, type ErrorInfo } from "react"

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("App error:", error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="flex min-h-screen flex-col items-center justify-center p-6 bg-gray-50">
          <h1 className="text-xl font-bold text-gray-900">Something went wrong</h1>
          <p className="mt-2 text-sm text-gray-500">
            {this.state.error?.message || "An unexpected error occurred"}
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null })
              window.location.href = "/"
            }}
            className="mt-6 rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white"
          >
            Go Home
          </button>
        </main>
      )
    }
    return this.props.children
  }
}
