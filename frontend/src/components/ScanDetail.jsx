import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getScan, getScanFindings, getScanChains } from '../api'
import FindingsTable from './FindingsTable'
import ChainsView from './ChainsView'

export default function ScanDetail() {
  const { scanId } = useParams()
  const navigate = useNavigate()
  const [scan, setScan] = useState(null)
  const [findings, setFindings] = useState([])
  const [chains, setChains] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('findings')

  const fetchData = useCallback(async () => {
    try {
      setError(null)
      const [scanData, findingsData, chainsData] = await Promise.all([
        getScan(Number(scanId)),
        getScanFindings(Number(scanId)),
        getScanChains(Number(scanId)),
      ])
      setScan(scanData)
      setFindings(findingsData)
      setChains(chainsData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [scanId])

  useEffect(() => {
    setLoading(true)
    fetchData()
    // Auto-refresh if scan is still running
    const interval = setInterval(() => {
      if (scan?.status === 'running') fetchData()
    }, 3000)
    return () => clearInterval(interval)
  }, [scanId, scan?.status])

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner" />
        Loading scan #{scanId}...
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <div className="error">{error}</div>
        <button className="btn btn-secondary" onClick={() => navigate('/')}>
          ← Back to Dashboard
        </button>
      </div>
    )
  }

  if (!scan) {
    return (
      <div>
        <div className="error">Scan #{scanId} not found</div>
        <button className="btn btn-secondary" onClick={() => navigate('/')}>
          ← Back to Dashboard
        </button>
      </div>
    )
  }

  // Compute severity breakdown
  const severityCount = { critical: 0, high: 0, medium: 0, low: 0, info: 0 }
  findings.forEach(f => {
    const sev = (f.ai_severity || 'info').toLowerCase()
    if (severityCount[sev] !== undefined) severityCount[sev]++
  })

  return (
    <div>
      <button
        className="btn btn-secondary"
        onClick={() => navigate('/')}
        style={{ marginBottom: 16 }}
      >
        ← Back to Dashboard
      </button>

      <div className="detail-header">
        <h1>Scan #{scan.id}</h1>
        <span className={`status-badge status-${scan.status}`}>{scan.status}</span>
      </div>

      <div className="detail-meta">
        <div className="meta-item">
          <span className="meta-label">Target</span>
          <span className="meta-value"><code>{scan.target_scope}</code></span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Profile</span>
          <span className="meta-value">{scan.profile}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Findings</span>
          <span className="meta-value">{findings.length}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Attack Chains</span>
          <span className="meta-value">{chains.length}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Created</span>
          <span className="meta-value">
            {scan.created_at ? new Date(scan.created_at).toLocaleString() : '-'}
          </span>
        </div>
      </div>

      {/* Severity distribution */}
      <div className="grid-3">
        {Object.entries(severityCount).map(([severity, count]) => (
          <div className="card" key={severity} style={{ textAlign: 'center', marginBottom: 0 }}>
            <div className={`stat-value ${severity}`}>{count}</div>
            <div className="stat-label" style={{ textTransform: 'capitalize' }}>{severity}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="card">
        <div style={{ marginBottom: 16 }}>
          <div className="toggle-group">
            <button
              className={`toggle-btn ${activeTab === 'findings' ? 'active' : ''}`}
              onClick={() => setActiveTab('findings')}
            >
              Findings ({findings.length})
            </button>
            <button
              className={`toggle-btn ${activeTab === 'chains' ? 'active' : ''}`}
              onClick={() => setActiveTab('chains')}
            >
              Attack Chains ({chains.length})
            </button>
          </div>
        </div>

        {activeTab === 'findings' ? (
          <FindingsTable findings={findings} />
        ) : (
          <ChainsView chains={chains} />
        )}
      </div>
    </div>
  )
}