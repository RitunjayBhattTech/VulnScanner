import React from 'react'

function SeverityBadge({ severity }) {
  const sev = (severity || 'info').toLowerCase()
  return <span className={`severity-badge severity-${sev}`}>{sev}</span>
}

export default function FindingsTable({ findings }) {
  if (!findings || findings.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 40, color: '#8b949e' }}>
        No findings found for this scan
      </div>
    )
  }

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>Host</th>
            <th>Port</th>
            <th>Service</th>
            <th>Severity</th>
            <th>CVSS</th>
            <th>FP Reasoning</th>
            <th>Exploitation Notes</th>
          </tr>
        </thead>
        <tbody>
          {findings.map(finding => (
            <tr key={finding.id}>
              <td><code>{finding.host}</code></td>
              <td>{finding.port || '-'}</td>
              <td>{finding.service || '-'}</td>
              <td>
                <SeverityBadge severity={finding.ai_severity} />
              </td>
              <td>
                {finding.ai_cvss_score != null ? (
                  <div>
                    <span style={{ fontWeight: 600 }}>{finding.ai_cvss_score.toFixed(1)}</span>
                    <div className="measure-bar" style={{ width: 60 }}>
                      <div
                        className={`measure-fill ${(finding.ai_severity || 'info').toLowerCase()}`}
                        style={{ width: `${(finding.ai_cvss_score / 10) * 100}%` }}
                      />
                    </div>
                  </div>
                ) : '-'}
              </td>
              <td style={{ maxWidth: 250, fontSize: 13, color: finding.ai_false_positive_reasoning ? '#e1e4e8' : '#8b949e' }}>
                {finding.ai_false_positive_reasoning || '—'}
              </td>
              <td style={{ maxWidth: 250, fontSize: 13 }}>
                {finding.ai_exploitation_notes || '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}