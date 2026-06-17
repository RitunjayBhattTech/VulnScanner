import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useFindings } from '../hooks/useFindings'

const SEV_COLOR: Record<string, string> = {
  critical: '#dc2626', high: '#ea580c', medium: '#ca8a04', low: '#2563eb', informational: '#6b7280'
}

export default function FindingsPage() {
  const [params] = useSearchParams()
  const scanId = params.get('scan_id') ?? undefined

  if (!scanId) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div>
          <h1 style={{ color: 'white', fontSize: '24px', fontWeight: 700 }}>Findings</h1>
          <p style={{ color: '#64748b', fontSize: '14px', marginTop: '4px' }}>Select a scan to view its findings</p>
        </div>
        <div style={{ background: '#0f1629', border: '1px solid #1e2a45', borderRadius: '12px', padding: '48px 24px', textAlign: 'center' }}>
          <div style={{ fontSize: '40px', marginBottom: '16px' }}>◈</div>
          <div style={{ color: '#94a3b8', fontSize: '16px', fontWeight: 500, marginBottom: '8px' }}>No scan selected</div>
          <div style={{ color: '#64748b', fontSize: '14px', marginBottom: '20px' }}>Go to Scans, open a completed scan, and findings will appear here.</div>
          <a href="/scans" style={{ padding: '8px 20px', background: '#3b82f6', color: 'white', borderRadius: '8px', fontSize: '14px', fontWeight: 600, textDecoration: 'none' }}>
            View All Scans →
          </a>
        </div>
      </div>
    )
  }
  const [filter, setFilter] = useState('all')
  const { findings, loading } = useFindings(scanId)
  const safe = Array.isArray(findings) ? findings : []
  const sevs = ['critical', 'high', 'medium', 'low', 'informational']
  const counts = sevs.reduce<Record<string, number>>((a, s) => ({ ...a, [s]: safe.filter(f => f.severity?.toLowerCase() === s).length }), {})
  const filtered = filter === 'all' ? safe : safe.filter(f => f.severity?.toLowerCase() === filter)

  if (loading) return <div style={{ color: '#64748b', textAlign: 'center', padding: '80px 0' }}>Loading findings...</div>

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h1 style={{ color: 'white', fontSize: '24px', fontWeight: 700 }}>Findings</h1>
        <p style={{ color: '#64748b', fontSize: '14px', marginTop: '4px' }}>{safe.length} total findings</p>
      </div>
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {['all', ...sevs].map(s => {
          const cnt = s === 'all' ? safe.length : counts[s]
          if (s !== 'all' && !cnt) return null
          const active = filter === s
          const col = s === 'all' ? '#3b82f6' : SEV_COLOR[s]
          return (
            <button key={s} onClick={() => setFilter(s)} style={{
              padding: '6px 14px', borderRadius: '8px', fontSize: '13px', fontWeight: 500,
              border: active ? `1px solid ${col}` : '1px solid #1e2a45',
              background: active ? col + '33' : 'transparent',
              color: active ? col : '#64748b', cursor: 'pointer', textTransform: 'capitalize',
            }}>
              {s} ({cnt})
            </button>
          )
        })}
      </div>
      {filtered.length === 0 ? (
        <div style={{ background: '#0f1629', border: '1px solid #1e2a45', borderRadius: '12px', padding: '64px 24px', textAlign: 'center', color: '#64748b', fontSize: '14px' }}>
          No findings match this filter
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {filtered.map((f, i) => {
            const c = SEV_COLOR[f.severity?.toLowerCase()] ?? '#6b7280'
            return (
              <div key={f.id ?? i} style={{ background: '#0f1629', border: `1px solid ${c}44`, borderRadius: '10px', padding: '14px 16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ background: c + '22', color: c, border: `1px solid ${c}66`, padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase' }}>{f.severity}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ color: 'white', fontSize: '14px', fontWeight: 500 }}>{f.title}</div>
                  <div style={{ color: '#64748b', fontSize: '12px', fontFamily: 'monospace' }}>{f.affected_component}</div>
                </div>
                <span style={{ color: '#64748b', fontSize: '12px' }}>{f.scanner_source}</span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}