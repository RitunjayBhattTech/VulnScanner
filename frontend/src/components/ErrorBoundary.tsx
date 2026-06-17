import { Component, type ReactNode } from 'react'

interface Props { children: ReactNode }
interface State { hasError: boolean; error: string }

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: '' }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error: error.message }
  }

  componentDidCatch(error: Error, info: { componentStack: string }) {
    console.error('React error boundary caught:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          background: '#0a0e1a',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '2rem'
        }}>
          <div style={{
            background: '#0f1629',
            border: '1px solid #dc2626',
            borderRadius: '12px',
            padding: '2rem',
            maxWidth: '600px',
            width: '100%'
          }}>
            <div style={{ color: '#dc2626', fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>
              ⚠ Application Error
            </div>
            <div style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '1rem' }}>
              The app crashed with this error:
            </div>
            <pre style={{
              background: '#0a0e1a',
              border: '1px solid #1e2a45',
              borderRadius: '8px',
              padding: '1rem',
              color: '#f87171',
              fontSize: '0.75rem',
              overflowX: 'auto',
              whiteSpace: 'pre-wrap'
            }}>
              {this.state.error}
            </pre>
            <button
              onClick={() => window.location.reload()}
              style={{
                marginTop: '1rem',
                padding: '0.5rem 1.5rem',
                background: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '0.875rem'
              }}
            >
              Reload Page
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}