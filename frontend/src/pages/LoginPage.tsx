import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [isRegister, setIsRegister] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [form, setForm] = useState({
    email: '', username: '', password: '', confirmPassword: ''
  })

  const update = (k: string, v: string) => setForm(p => ({ ...p, [k]: v }))

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (isRegister && form.password !== form.confirmPassword) {
      setError('Passwords do not match')
      return
    }

    setLoading(true)
    try {
      const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login'
      const body = isRegister
        ? { email: form.email, username: form.username, password: form.password }
        : { email: form.email, password: form.password }

      const res = await fetch(`${API}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Authentication failed')

      login(data)
      navigate('/')
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const inputStyle: React.CSSProperties = {
    width: '100%',
    background: '#1a2238',
    border: '1px solid #1e2a45',
    borderRadius: '8px',
    padding: '10px 14px',
    color: 'white',
    fontSize: '14px',
    outline: 'none',
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0a0e1a',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
    }}>
      <div style={{ width: '100%', maxWidth: '420px' }}>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <div style={{
            width: '56px', height: '56px',
            background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
            borderRadius: '16px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 16px',
            fontSize: '24px', fontWeight: 700, color: 'white',
          }}>V</div>
          <div style={{ color: 'white', fontSize: '22px', fontWeight: 700 }}>VulnAI Scanner</div>
          <div style={{ color: '#64748b', fontSize: '13px', marginTop: '4px' }}>
            AI-powered vulnerability assessment
          </div>
        </div>

        {/* Card */}
        <div style={{
          background: '#0f1629',
          border: '1px solid #1e2a45',
          borderRadius: '16px',
          padding: '32px',
        }}>
          {/* Tab switcher */}
          <div style={{
            display: 'flex',
            background: '#1a2238',
            borderRadius: '10px',
            padding: '4px',
            marginBottom: '28px',
          }}>
            {['Login', 'Register'].map((tab, i) => (
              <button
                key={tab}
                onClick={() => { setIsRegister(i === 1); setError('') }}
                style={{
                  flex: 1, padding: '8px',
                  borderRadius: '8px', border: 'none',
                  background: (i === 1) === isRegister ? '#3b82f6' : 'transparent',
                  color: (i === 1) === isRegister ? 'white' : '#64748b',
                  fontSize: '14px', fontWeight: 500, cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >{tab}</button>
            ))}
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ color: '#94a3b8', fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Email
              </label>
              <input
                type="email"
                value={form.email}
                onChange={e => update('email', e.target.value)}
                placeholder="you@example.com"
                required
                style={inputStyle}
              />
            </div>

            {isRegister && (
              <div>
                <label style={{ color: '#94a3b8', fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Username
                </label>
                <input
                  type="text"
                  value={form.username}
                  onChange={e => update('username', e.target.value)}
                  placeholder="johndoe"
                  required={isRegister}
                  style={inputStyle}
                />
              </div>
            )}

            <div>
              <label style={{ color: '#94a3b8', fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Password
              </label>
              <input
                type="password"
                value={form.password}
                onChange={e => update('password', e.target.value)}
                placeholder="••••••••"
                required
                style={inputStyle}
              />
            </div>

            {isRegister && (
              <div>
                <label style={{ color: '#94a3b8', fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Confirm Password
                </label>
                <input
                  type="password"
                  value={form.confirmPassword}
                  onChange={e => update('confirmPassword', e.target.value)}
                  placeholder="••••••••"
                  required={isRegister}
                  style={inputStyle}
                />
              </div>
            )}

            {error && (
              <div style={{
                background: '#7f1d1d22',
                border: '1px solid #991b1b',
                borderRadius: '8px',
                padding: '10px 14px',
                color: '#f87171',
                fontSize: '13px',
              }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                padding: '11px',
                background: loading ? '#1e3a5f' : '#3b82f6',
                color: loading ? '#64748b' : 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
                marginTop: '4px',
                transition: 'all 0.15s',
              }}
            >
              {loading ? '⟳ Please wait...' : isRegister ? 'Create Account' : 'Sign In'}
            </button>
          </form>

          {isRegister && (
            <p style={{ color: '#475569', fontSize: '12px', textAlign: 'center', marginTop: '16px', lineHeight: 1.5 }}>
              The first account registered automatically becomes admin.
            </p>
          )}
        </div>

        <p style={{ color: '#334155', fontSize: '12px', textAlign: 'center', marginTop: '24px' }}>
          For authorised security testing only
        </p>
      </div>
    </div>
  )
}