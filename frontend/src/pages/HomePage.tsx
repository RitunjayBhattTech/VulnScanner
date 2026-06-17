import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { useScans } from '../hooks/useScans'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const CARD = { background: '#0f1629', border: '1px solid #1e2a45', borderRadius: '12px' }
const INPUT = { background: '#1a2238', border: '1px solid #1e2a45', borderRadius: '8px', color: 'white', padding: '8px 12px', fontSize: '14px', width: '100%', outline: 'none' }
const LABEL = { color: '#94a3b8', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase' as const, letterSpacing: '0.05em', display: 'block', marginBottom: '6px' }
const BTN = { background: '#3b82f6', color: 'white', border: 'none', borderRadius: '8px', padding: '10px 20px', fontSize: '14px', fontWeight: 600, cursor: 'pointer', width: '100%' }
const BTND = { background: '#1e3a5f', color: '#64748b', border: 'none', borderRadius: '8px', padding: '10px 20px', fontSize: '14px', fontWeight: 600, cursor: 'not-allowed', width: '100%' }

const STATUS: Record<string, any> = {
  completed: { background: '#14532d33', color: '#4ade80', border: '1px solid #166534' },
  running:   { background: '#1e3a5f33', color: '#60a5fa', border: '1px solid #1e40af' },
  pending:   { background: '#78350f33', color: '#fbbf24', border: '1px solid #92400e' },
  failed:    { background: '#7f1d1d33', color: '#f87171', border: '1px solid #991b1b' },
}

function StatCard({ l, v, c }: { l: string; v: number; c: string }) {
  return (
    <div style={{ ...CARD, padding: '20px' }}>
      <div style={{ color: '#64748b', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>{l}</div>
      <div style={{ color: c, fontSize: '32px', fontWeight: 700, lineHeight: 1 }}>{v}</div>
    </div>
  )
}

export default function HomePage() {
  const navigate = useNavigate()
  const { scans, loading } = useScans()
  const safe = Array.isArray(scans) ? scans : []

  const [target, setTarget] = useState('')
  const [scope, setScope] = useState('')
  const [st, setSt] = useState({ port: true, web: true, headers: true, ssl: true, semgrep: false })
  const [auth, setAuth] = useState(false)
  const [err, setErr] = useState('')
  const [sub, setSub] = useState(false)

  const total = safe.reduce((s, sc) => s + (sc.total_findings ?? 0), 0)
  const critical = safe.reduce((s, sc) => s + (sc.critical_count ?? 0), 0)
  const high = safe.reduce((s, sc) => s + (sc.high_count ?? 0), 0)
  const medium = safe.reduce((s, sc) => s + (sc.medium_count ?? 0), 0)
  const low = safe.reduce((s, sc) => s + (sc.low_count ?? 0), 0)
  const chartData = [
    { name: 'Critical', count: critical }, { name: 'High', count: high },
    { name: 'Medium', count: medium }, { name: 'Low', count: low },
  ]
  const COLORS = ['#dc2626', '#ea580c', '#ca8a04', '#2563eb']

  async function submitScan(e: React.FormEvent) {
    e.preventDefault()
    if (!auth) { setErr('You must confirm authorisation.'); return }
    if (!target.trim()) { setErr('Target URL/IP is required.'); return }
    if (!scope.trim()) { setErr('Scope is required.'); return }
    const selected = Object.entries(st).filter(([,v]) => v).map(([k]) => k)
    if (!selected.length) { setErr('Select at least one scan type.'); return }
    setErr(''); setSub(true)
    try {
      const res = await fetch(`${API}/api/scans`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: target.trim(), scope: scope.trim().split('\n').map(s => s.trim()).filter(Boolean), scan_types: selected, authorisation_confirmed: true })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed')
      navigate(`/scans/${data.id}`)
    } catch (e: any) { setErr(e.message) } finally { setSub(false) }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ color: 'white', fontSize: '24px', fontWeight: 700 }}>Security Dashboard</h1>
          <p style={{ color: '#64748b', fontSize: '14px', marginTop: '4px' }}>AI-powered vulnerability assessment platform</p>
        </div>
        <button onClick={() => navigate('/scans/demo?demo=true')}
          style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid #854d0e', background: '#78350f33', color: '#fbbf24', fontSize: '13px', fontWeight: 500, cursor: 'pointer' }}>
          ⚡ View Demo
        </button>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <StatCard l="Total Scans" v={safe.length} c="#3b82f6" />
        <StatCard l="Total Findings" v={total} c="#94a3b8" />
        <StatCard l="Critical" v={critical} c="#dc2626" />
        <StatCard l="High" v={high} c="#ea580c" />
      </div>

      {/* Chart + Form */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div style={{ ...CARD, padding: '24px' }}>
          <h2 style={{ color: 'white', fontSize: '15px', fontWeight: 600, marginBottom: '20px' }}>Findings by Severity</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData} barSize={36}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2a45" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip contentStyle={{ background: '#0f1629', border: '1px solid #1e2a45', borderRadius: '8px', color: '#e2e8f0' }} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {chartData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div style={{ ...CARD, padding: '24px' }}>
          <h2 style={{ color: 'white', fontSize: '15px', fontWeight: 600, marginBottom: '20px' }}>New Security Scan</h2>
          <form onSubmit={submitScan} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={LABEL}>Target URL / IP</label>
              <input value={target} onChange={e => setTarget(e.target.value)} placeholder="https://example.com" style={INPUT} />
            </div>
            <div>
              <label style={LABEL}>Scope (one per line)</label>
              <textarea value={scope} onChange={e => setScope(e.target.value)} placeholder="example.com" rows={2} style={{ ...INPUT, resize: 'none' }} />
            </div>
            <div>
              <label style={LABEL}>Scan Types</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {Object.entries(st).map(([type, checked]) => (
                  <label key={type} style={{
                    display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', borderRadius: '8px', cursor: 'pointer', fontSize: '13px', fontWeight: 500,
                    border: checked ? '1px solid #3b82f6' : '1px solid #1e2a45', background: checked ? '#1e3a5f55' : 'transparent',
                    color: checked ? '#60a5fa' : '#94a3b8', transition: 'all 0.15s',
                  }}>
                    <input type="checkbox" checked={checked} onChange={e => setSt(p => ({ ...p, [type]: e.target.checked }))} style={{ display: 'none' }} />
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </label>
                ))}
              </div>
            </div>
            <label style={{
              display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px', borderRadius: '8px', cursor: 'pointer',
              border: auth ? '1px solid #166534' : '1px solid #1e2a45', background: auth ? '#14532d22' : 'transparent', transition: 'all 0.15s',
            }}>
              <input type="checkbox" checked={auth} onChange={e => setAuth(e.target.checked)} style={{ marginTop: '2px', accentColor: '#22c55e' }} />
              <span style={{ color: '#cbd5e1', fontSize: '13px', lineHeight: 1.5 }}>
                <strong style={{ color: 'white' }}>Legal Acknowledgement: </strong>
                I confirm I have written authorisation from the system owner.
              </span>
            </label>
            {err && <div style={{ background: '#7f1d1d22', border: '1px solid #991b1b', borderRadius: '8px', padding: '10px 12px', color: '#f87171', fontSize: '13px' }}>{err}</div>}
            <button type="submit" disabled={!auth || sub} style={auth && !sub ? BTN : BTND}>
              {sub ? '⟳ Starting...' : '▶ Start Scan'}
            </button>
          </form>
        </div>
      </div>

      {/* Table */}
      <div style={{ ...CARD, padding: '24px' }}>
        <h2 style={{ color: 'white', fontSize: '15px', fontWeight: 600, marginBottom: '20px' }}>All Scans</h2>
        {loading ? (
          <div style={{ color: '#64748b', textAlign: 'center', padding: '48px 0' }}>Loading...</div>
        ) : safe.length === 0 ? (
          <div style={{ color: '#64748b', textAlign: 'center', padding: '48px 0', fontSize: '14px' }}>No scans yet.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1e2a45' }}>
                {['Target', 'Status', 'Findings', 'Date', ''].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '0 0 12px', color: '#64748b', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {safe.slice(0, 10).map(scan => (
                <tr key={scan.id} style={{ borderBottom: '1px solid #0f1629' }}>
                  <td style={{ padding: '12px 0', color: '#94a3b8', fontFamily: 'monospace', fontSize: '13px' }}>{scan.target}</td>
                  <td style={{ padding: '12px 8px 12px 0' }}>
                    <span style={{ ...(STATUS[scan.status] || STATUS.pending), padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>{scan.status?.toUpperCase()}</span>
                  </td>
                  <td style={{ padding: '12px 0' }}>
                    <div style={{ display: 'flex', gap: '8px', fontSize: '12px' }}>
                      {(scan.critical_count ?? 0) > 0 && <span style={{ color: '#dc2626', fontWeight: 600 }}>C:{scan.critical_count}</span>}
                      {(scan.high_count ?? 0) > 0 && <span style={{ color: '#ea580c', fontWeight: 600 }}>H:{scan.high_count}</span>}
                      {(scan.medium_count ?? 0) > 0 && <span style={{ color: '#ca8a04', fontWeight: 600 }}>M:{scan.medium_count}</span>}
                    </div>
                  </td>
                  <td style={{ padding: '12px 0', color: '#64748b', fontSize: '13px' }}>{new Date(scan.created_at).toLocaleDateString()}</td>
                  <td style={{ padding: '12px 0' }}>
                    <button onClick={() => navigate(`/scans/${scan.id}`)} style={{ padding: '4px 12px', borderRadius: '6px', background: '#1a2238', border: '1px solid #1e2a45', color: '#60a5fa', fontSize: '12px', cursor: 'pointer' }}>View →</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}