import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const SEV: Record<string, { bg: string; color: string; border: string }> = {
  critical:      { bg: '#dc262622', color: '#f87171', border: '#dc2626' },
  high:          { bg: '#ea580c22', color: '#fb923c', border: '#ea580c' },
  medium:        { bg: '#ca8a0422', color: '#fbbf24', border: '#ca8a04' },
  low:           { bg: '#2563eb22', color: '#60a5fa', border: '#2563eb' },
  informational: { bg: '#6b728022', color: '#9ca3af', border: '#6b7280' },
}

function SevBadge({ s }: { s: string }) {
  const c = SEV[s?.toLowerCase()] ?? SEV.informational
  return (
    <span style={{ background: c.bg, color: c.color, border: `1px solid ${c.border}`, padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase' as const }}>
      {s}
    </span>
  )
}

function FindingCard({ f, i }: { f: any; i: number }) {
  const [open, setOpen] = useState(false)
  const c = SEV[f.severity?.toLowerCase()] ?? SEV.informational
  return (
    <div style={{ border: `1px solid ${c.border}44`, borderRadius: '10px', overflow: 'hidden', background: c.bg + '44' }}>
      <button onClick={() => setOpen(o => !o)} style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '12px', padding: '14px 16px', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left' as const }}>
        <span style={{ color: '#475569', fontSize: '12px', fontFamily: 'monospace', minWidth: '28px' }}>#{i}</span>
        <SevBadge s={f.severity} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ color: 'white', fontWeight: 500, fontSize: '14px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{f.title}</div>
          <div style={{ color: '#64748b', fontSize: '12px', fontFamily: 'monospace', marginTop: '2px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.affected_component}</div>
        </div>
        {f.delta_status === 'new' && <span style={{ padding: '2px 8px', borderRadius: '4px', background: '#14532d33', color: '#4ade80', border: '1px solid #166534', fontSize: '11px', fontWeight: 600 }}>NEW</span>}
        <span style={{ color: '#475569', fontSize: '14px' }}>{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div style={{ padding: '0 16px 16px', display: 'flex', flexDirection: 'column', gap: '16px', borderTop: '1px solid #ffffff11' }}>
          <div>
            <div style={{ color: '#64748b', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>Description</div>
            <p style={{ color: '#cbd5e1', fontSize: '14px', lineHeight: 1.6 }}>{f.description}</p>
          </div>
          {f.evidence && (
            <div>
              <div style={{ color: '#64748b', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>Evidence</div>
              <pre style={{ background: '#0a0e1a', border: '1px solid #1e2a45', borderRadius: '8px', padding: '12px', color: '#4ade80', fontSize: '12px', overflowX: 'auto', whiteSpace: 'pre-wrap' as const }}>
                {f.evidence.slice(0, 500)}
              </pre>
            </div>
          )}
          {f.ai_triage_notes && (
            <div>
              <div style={{ color: '#3b82f6', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>◆ AI Triage Analysis</div>
              <p style={{ color: '#cbd5e1', fontSize: '14px', lineHeight: 1.6, fontStyle: 'italic' }}>{f.ai_triage_notes}</p>
            </div>
          )}
          {f.cve_ids?.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {f.cve_ids.map((cve: string) => (
                <a key={cve} href={`https://nvd.nist.gov/vuln/detail/${cve}`} target="_blank" rel="noopener noreferrer"
                  style={{ padding: '2px 8px', borderRadius: '4px', background: '#7f1d1d33', color: '#f87171', border: '1px solid #991b1b', fontSize: '12px', fontFamily: 'monospace' }}>
                  {cve} ↗
                </a>
              ))}
            </div>
          )}
          {f.ai_remediation && (
            <div style={{ background: '#0a0e1a', border: '1px solid #14532d55', borderRadius: '8px', padding: '16px' }}>
              <div style={{ color: '#4ade80', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>✓ Remediation</div>
              <pre style={{ color: '#cbd5e1', fontSize: '13px', lineHeight: 1.6, whiteSpace: 'pre-wrap' as const, fontFamily: 'inherit' }}>{f.ai_remediation}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const PHASES = [
  [10,  'Initialising scan...'],
  [30,  'Running port discovery...'],
  [60,  'Crawling web surface...'],
  [120, 'Running vulnerability detection...'],
  [999, 'AI is analysing findings...'],
] as const

const getStatusStyle = (status: string) => {
  const m: Record<string, any> = {
    completed: { background: '#14532d33', color: '#4ade80', border: '1px solid #166534' },
    running:   { background: '#1e3a5f33', color: '#60a5fa', border: '1px solid #1e40af' },
    pending:   { background: '#78350f33', color: '#fbbf24', border: '1px solid #92400e' },
    failed:    { background: '#7f1d1d33', color: '#f87171', border: '1px solid #991b1b' },
  }
  return m[status] || m.pending
}

export default function ScanPage() {
  const { scanId } = useParams()
  const [params] = useSearchParams()
  const isDemo = params.get('demo') === 'true'

  const [scan, setScan] = useState<any>(null)
  const [findings, setFindings] = useState<any[]>([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const startRef = useRef(Date.now())
  const [elapsed, setElapsed] = useState(0)
  const pollRef = useRef<ReturnType<typeof setInterval>>()

  const load = useCallback(async () => {
    if (!scanId && scanId !== 'demo') return
    try {
      if (isDemo) {
        const [s, f] = await Promise.all([
          fetch(`${API}/api/demo/scan`).then(r => r.json()),
          fetch(`${API}/api/demo/findings`).then(r => r.json()),
        ])
        setScan(s); setFindings(Array.isArray(f) ? f : []); setLoading(false); return
      }
      const s = await fetch(`${API}/api/scans/${scanId}`).then(r => r.json())
      setScan(s)
      if (s.status === 'completed' || s.status === 'failed') {
        const f = await fetch(`${API}/api/findings?scan_id=${scanId}`).then(r => r.json())
        setFindings(Array.isArray(f) ? f : (f.findings ?? []))
        clearInterval(pollRef.current)
      }
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }, [scanId, isDemo])

  useEffect(() => {
    load()
    pollRef.current = setInterval(() => {
      load()
      setElapsed(Math.floor((Date.now() - startRef.current) / 1000))
    }, 3000)
    return () => clearInterval(pollRef.current)
  }, [load])

  if (loading) return <div style={{ color: '#64748b', textAlign: 'center', padding: '80px 0' }}>Loading scan...</div>
  if (!scan && !loading) return <div style={{ color: '#f87171', textAlign: 'center', padding: '80px 0' }}>Scan not found.</div>

  const phase = PHASES.find(([t]) => elapsed < t)?.[1] ?? PHASES[PHASES.length - 1][1]
  const sevs = ['critical', 'high', 'medium', 'low', 'informational']
  const counts = sevs.reduce<Record<string, number>>((a, s) => ({ ...a, [s]: findings.filter(f => f.severity?.toLowerCase() === s).length }), {})
  const filtered = filter === 'all' ? findings : findings.filter(f => f.severity?.toLowerCase() === filter)
  const currentScan = scan || {}

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {isDemo && (
        <div style={{ background: '#78350f33', border: '1px solid #854d0e', borderRadius: '10px', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ color: '#fbbf24', fontSize: '18px' }}>⚠</span>
          <span style={{ color: '#fcd34d', fontSize: '14px', fontWeight: 500 }}>DEMO MODE — Simulated data for demonstration purposes only</span>
        </div>
      )}

      <div style={{ background: '#0f1629', border: '1px solid #1e2a45', borderRadius: '12px', padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px' }}>
          <div>
            <div style={{ color: '#475569', fontSize: '11px', fontFamily: 'monospace', marginBottom: '4px' }}>{currentScan.id}</div>
            <h1 style={{ color: 'white', fontSize: '20px', fontWeight: 700 }}>{currentScan.target}</h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '8px' }}>
              <span style={{ ...getStatusStyle(currentScan.status), padding: '3px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: 600 }}>{currentScan.status?.toUpperCase()}</span>
              <span style={{ color: '#64748b', fontSize: '13px' }}>{currentScan.created_at ? new Date(currentScan.created_at).toLocaleString() : ''}</span>
            </div>
          </div>
          {currentScan.status === 'completed' && (
            <a href={`${API}/api/reports/${currentScan.id}/pdf`} target="_blank" rel="noopener noreferrer"
              style={{ padding: '8px 16px', background: '#3b82f6', color: 'white', borderRadius: '8px', fontSize: '13px', fontWeight: 600, textDecoration: 'none', whiteSpace: 'nowrap' }}>
              ↓ Download PDF
            </a>
          )}
        </div>
        {currentScan.status === 'completed' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px', marginTop: '20px' }}>
            {[['Critical', currentScan.critical_count ?? 0, '#dc2626'], ['High', currentScan.high_count ?? 0, '#ea580c'], ['Medium', currentScan.medium_count ?? 0, '#ca8a04'], ['Low', currentScan.low_count ?? 0, '#2563eb'], ['Info', currentScan.info_count ?? 0, '#6b7280']].map(([l, v, c]) => (
              <div key={l as string} style={{ background: '#1a2238', borderRadius: '8px', padding: '12px', textAlign: 'center' }}>
                <div style={{ color: c as string, fontSize: '28px', fontWeight: 700 }}>{v as number}</div>
                <div style={{ color: '#64748b', fontSize: '12px', marginTop: '2px' }}>{l}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {(currentScan.status === 'running' || currentScan.status === 'pending') && (
        <div style={{ background: '#0f1629', border: '1px solid #1e3a5f', borderRadius: '12px', padding: '48px 24px', textAlign: 'center' }}>
          <div style={{ width: '48px', height: '48px', border: '4px solid #1e3a5f', borderTop: '4px solid #3b82f6', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
          <div style={{ color: 'white', fontWeight: 500, fontSize: '16px' }}>{phase}</div>
          <div style={{ color: '#64748b', fontSize: '13px', marginTop: '4px' }}>Elapsed: {elapsed}s</div>
          <div style={{ width: '200px', height: '4px', background: '#1a2238', borderRadius: '2px', margin: '16px auto 0', overflow: 'hidden' }}>
            <div style={{ height: '100%', background: '#3b82f6', borderRadius: '2px', width: `${Math.min((elapsed / 300) * 100, 92)}%`, transition: 'width 1s ease' }} />
          </div>
        </div>
      )}

      {currentScan.summary && (
        <div style={{ background: '#0f1629', border: '1px solid #1e2a45', borderRadius: '12px', padding: '24px' }}>
          <div style={{ color: '#3b82f6', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>◆ AI Executive Summary</div>
          <p style={{ color: '#cbd5e1', fontSize: '14px', lineHeight: 1.7 }}>{currentScan.summary}</p>
        </div>
      )}

      {findings.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h2 style={{ color: 'white', fontSize: '16px', fontWeight: 600 }}>Findings ({findings.length})</h2>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {['all', ...sevs].map(s => {
                const cnt = s === 'all' ? findings.length : counts[s]
                if (s !== 'all' && !cnt) return null
                const active = filter === s
                const col = s === 'all' ? '#3b82f6' : (SEV[s]?.color ?? '#9ca3af')
                return (
                  <button key={s} onClick={() => setFilter(s)} style={{
                    padding: '5px 12px', borderRadius: '6px', fontSize: '12px', fontWeight: 500,
                    border: active ? `1px solid ${col}` : '1px solid #1e2a45',
                    background: active ? col + '33' : 'transparent',
                    color: active ? col : '#64748b', cursor: 'pointer', textTransform: 'capitalize',
                  }}>
                    {s} ({cnt})
                  </button>
                )
              })}
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {filtered.map((f, i) => <FindingCard key={f.id ?? i} f={f} i={i + 1} />)}
          </div>
        </div>
      )}

      {currentScan.status === 'completed' && findings.length === 0 && (
        <div style={{ background: '#0f1629', border: '1px solid #1e2a45', borderRadius: '12px', padding: '64px 24px', textAlign: 'center' }}>
          <div style={{ fontSize: '40px', marginBottom: '12px' }}>✓</div>
          <div style={{ color: 'white', fontWeight: 500, fontSize: '16px' }}>No findings detected</div>
          <div style={{ color: '#64748b', fontSize: '14px', marginTop: '4px' }}>The target passed all security checks</div>
        </div>
      )}
    </div>
  )
}