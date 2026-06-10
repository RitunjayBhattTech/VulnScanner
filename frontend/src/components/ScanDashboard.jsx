import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getScans } from '../api'

export default function ScanDashboard() {
  const [scans, setScans] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const fetchScans = async () => {
    try {
      setError(null)
      const data = await getScans()
      setScans(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchScans()
    const interval = setInterval(fetchScans, 5000) // Auto-refresh every 5s
    return () => clearInterval(interval)
  }, [])

  // Compute stats
  const totalScans = scans.length
  const totalFindings = scans.reduce((sum, s) => sum + (s.finding_count || 0), 0)
  const totalChains = scans.reduce((sum, s) => sum + (s.chain_count || 0), 0)
  const runningScans = scans.filter(s => s.status === 'running').length
  const failedScans = scans.filter(s => s.status === 'failed').length

  // Severity counts from last completed scan (simplified - in production would be a dedicated API)
  const severityCounts = { critical: 0, high: 0, medium: 0, low: 0, info: 0 }

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>Dashboard</h1>

      {error && <div className="error">{error}</div>}

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{totalScans}</div>
          <div className="stat-label">Total Scans</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{totalFindings}</div>
          <div className="stat-label">Total Findings</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{totalChains}</div>
          <div className="stat-label">Attack Chains</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: runningScans > 0 ? '#58a6ff' : '#8b949e' }}>
            {runningScans}
          </div>
          <div className="stat-label">Running</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: failedScans > 0 ? '#f85149' : '#8b949e' }}>
            {failedScans}
          </div>
          <div className="stat-label">Failed</div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">
          Recent Scans <span className="badge">{scans.length} total</span>
        </div>

        {loading ? (
          <div className="loading">
            <div className="loading-spinner" />
            Loading scans...
          </div>
        ) : scans.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: '#8b949e' }}>
            <p style={{ fontSize: 18, marginBottom: 8 }}>No scans yet</p>
            <button className="btn btn-primary" onClick={() => navigate('/new-scan')}>
              Launch your first scan
            </button>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Target</th>
                  <th>Profile</th>
                  <th>Status</th>
                  <th>Findings</th>
                  <th>Chains</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {scans.map(scan => (
                  <tr
                    key={scan.id}
                    onClick={() => navigate(`/scans/${scan.id}`)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td>#{scan.id}</td>
                    <td><code>{scan.target_scope}</code></td>
                    <td>{scan.profile}</td>
                    <td>
                      <span className={`status-badge status-${scan.status}`}>
                        {scan.status}
                      </span>
                    </td>
                    <td>{scan.finding_count || 0}</td>
                    <td>{scan.chain_count || 0}</td>
                    <td>{scan.created_at ? new Date(scan.created_at).toLocaleString() : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}