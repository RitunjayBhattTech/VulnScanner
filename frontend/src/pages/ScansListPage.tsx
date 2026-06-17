import { useNavigate } from 'react-router-dom'
import { useScans } from '../hooks/useScans'

const STATUS_STYLE: Record<string, { background: string; color: string; border: string }> = {
  completed: { background: '#14532d33', color: '#4ade80', border: '1px solid #166534' },
  running:   { background: '#1e3a5f33', color: '#60a5fa', border: '1px solid #1e40af' },
  pending:   { background: '#78350f33', color: '#fbbf24', border: '1px solid #92400e' },
  failed:    { background: '#7f1d1d33', color: '#f87171', border: '1px solid #991b1b' },
  cancelled: { background: '#1e1e2e33', color: '#94a3b8', border: '1px solid #334155' },
}

export default function ScansListPage() {
  const navigate = useNavigate()
  const { scans, loading } = useScans()
  const safe = Array.isArray(scans) ? scans : []

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ color: 'white', fontSize: '24px', fontWeight: 700 }}>All Scans</h1>
          <p style={{ color: '#64748b', fontSize: '14px', marginTop: '4px' }}>{safe.length} scans total</p>
        </div>
        <button
          onClick={() => navigate('/')}
          style={{ padding: '8px 16px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}
        >
          + New Scan
        </button>
      </div>

      {/* Scans list */}
      <div style={{ background: '#0f1629', border: '1px solid #1e2a45', borderRadius: '12px', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ color: '#64748b', textAlign: 'center', padding: '64px 24px', fontSize: '14px' }}>
            Loading scans...
          </div>
        ) : safe.length === 0 ? (
          <div style={{ color: '#64748b', textAlign: 'center', padding: '64px 24px', fontSize: '14px' }}>
            No scans yet.{' '}
            <span
              onClick={() => navigate('/')}
              style={{ color: '#3b82f6', cursor: 'pointer', textDecoration: 'underline' }}
            >
              Start your first scan
            </span>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1e2a45', background: '#1a2238' }}>
                {['Target', 'Status', 'Scan Types', 'Findings', 'Date', 'Actions'].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '12px 16px', color: '#64748b', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {safe.map((scan, i) => {
                const st = STATUS_STYLE[scan.status] || STATUS_STYLE.pending
                return (
                  <tr
                    key={scan.id}
                    style={{ borderBottom: i < safe.length - 1 ? '1px solid #1e2a45' : 'none', cursor: 'pointer', transition: 'background 0.15s' }}
                    onMouseEnter={e => (e.currentTarget.style.background = '#1a2238')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                    onClick={() => navigate(`/scans/${scan.id}`)}
                  >
                    <td style={{ padding: '14px 16px', color: '#94a3b8', fontFamily: 'monospace', fontSize: '13px', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {scan.target}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{ ...st, padding: '3px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: 600 }}>
                        {scan.status?.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                        {(scan.scan_types || []).map((t: string) => (
                          <span key={t} style={{ padding: '1px 6px', background: '#1e3a5f44', color: '#60a5fa', border: '1px solid #1e3a5f', borderRadius: '4px', fontSize: '11px' }}>
                            {t}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ display: 'flex', gap: '8px', fontSize: '12px' }}>
                        {(scan.critical_count ?? 0) > 0 && <span style={{ color: '#dc2626', fontWeight: 700 }}>C:{scan.critical_count}</span>}
                        {(scan.high_count ?? 0) > 0 && <span style={{ color: '#ea580c', fontWeight: 700 }}>H:{scan.high_count}</span>}
                        {(scan.medium_count ?? 0) > 0 && <span style={{ color: '#ca8a04', fontWeight: 700 }}>M:{scan.medium_count}</span>}
                        {(scan.low_count ?? 0) > 0 && <span style={{ color: '#2563eb', fontWeight: 700 }}>L:{scan.low_count}</span>}
                        {(scan.info_count ?? 0) > 0 && <span style={{ color: '#6b7280' }}>I:{scan.info_count}</span>}
                        {!(scan.total_findings) && <span style={{ color: '#475569' }}>—</span>}
                      </div>
                    </td>
                    <td style={{ padding: '14px 16px', color: '#64748b', fontSize: '13px', whiteSpace: 'nowrap' }}>
                      {new Date(scan.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' as const })}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          onClick={e => { e.stopPropagation(); navigate(`/scans/${scan.id}`) }}
                          style={{ padding: '5px 12px', background: '#1a2238', border: '1px solid #1e2a45', color: '#60a5fa', borderRadius: '6px', fontSize: '12px', cursor: 'pointer' }}
                        >
                          View →
                        </button>
                        {scan.status === 'completed' && (
                          <a
                            href={`http://localhost:8000/api/reports/${scan.id}/pdf`}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={e => e.stopPropagation()}
                            style={{ padding: '5px 12px', background: '#1a2238', border: '1px solid #1e2a45', color: '#4ade80', borderRadius: '6px', fontSize: '12px', textDecoration: 'none' }}
                          >
                            PDF
                          </a>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}