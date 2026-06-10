import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createScan } from '../api'

export default function NewScan() {
  const navigate = useNavigate()
  const [targetScope, setTargetScope] = useState('')
  const [profile, setProfile] = useState('normal')
  const [authorized, setAuthorized] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    if (!targetScope.trim()) {
      setError('Target scope is required (e.g. 10.0.0.0/24)')
      return
    }
    if (!authorized) {
      setError('You must confirm authorization before launching a scan')
      return
    }

    setSubmitting(true)
    try {
      const result = await createScan(targetScope.trim(), profile, authorized)
      setSuccess(`Scan #${result.id} launched successfully!`)
      setTimeout(() => navigate(`/scans/${result.id}`), 1500)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>New Scan</h1>

      <div className="card" style={{ maxWidth: 600 }}>
        <form onSubmit={handleSubmit}>
          {error && <div className="error">{error}</div>}
          {success && <div className="success">{success}</div>}

          <div className="form-group">
            <label className="form-label">Target Scope</label>
            <input
              className="form-input"
              type="text"
              value={targetScope}
              onChange={e => setTargetScope(e.target.value)}
              placeholder="e.g. 10.0.0.0/24, 192.168.1.1/32"
              disabled={submitting}
            />
            <div style={{ fontSize: 12, color: '#8b949e', marginTop: 4 }}>
              CIDR notation or single IP address
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Scan Profile</label>
            <select
              className="form-select"
              value={profile}
              onChange={e => setProfile(e.target.value)}
              disabled={submitting}
            >
              <option value="stealth">Stealth (slow, low detection)</option>
              <option value="normal">Normal (balanced)</option>
              <option value="aggressive">Aggressive (fast, OS detection)</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-checkbox">
              <input
                type="checkbox"
                checked={authorized}
                onChange={e => setAuthorized(e.target.checked)}
                disabled={submitting}
              />
              I confirm that I am authorized to scan this target scope
            </label>
          </div>

          <div className="form-group" style={{ marginTop: 24 }}>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting || !authorized}
              style={{ width: '100%' }}
            >
              {submitting ? 'Launching...' : '🚀 Launch Scan'}
            </button>
          </div>
        </form>
      </div>

      <div className="card" style={{ maxWidth: 600 }}>
        <div className="card-title">How AI Analysis Works</div>
        <div style={{ fontSize: 14, lineHeight: 1.7, color: '#8b949e' }}>
          <p style={{ marginBottom: 12 }}>
            1. <strong>Nmap</strong> scans the target and produces XML output with open ports, services, and versions.
          </p>
          <p style={{ marginBottom: 12 }}>
            2. <strong>CVE Context</strong> is retrieved from the RAG knowledge base (ChromaDB with 17+ real CVEs).
          </p>
          <p style={{ marginBottom: 12 }}>
            3. <strong>Ollama (Mistral 7B)</strong> analyzes findings and returns structured JSON with:
          </p>
          <ul style={{ marginLeft: 20, marginBottom: 12 }}>
            <li>CVSSv3 scores & severity per finding</li>
            <li>False positive reasoning</li>
            <li>Exploitation notes</li>
            <li>Multi-step attack chains with MITRE ATT&CK IDs</li>
          </ul>
          <p>
            4. Results are stored in PostgreSQL and viewable on the <strong>Scan Detail</strong> page.
          </p>
        </div>
      </div>
    </div>
  )
}