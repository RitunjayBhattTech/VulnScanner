import React from 'react'

export default function ChainsView({ chains }) {
  if (!chains || chains.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 40, color: '#8b949e' }}>
        <p style={{ fontSize: 16, marginBottom: 8 }}>No attack chains identified</p>
        <p style={{ fontSize: 13 }}>Attack chains are generated when the AI finds multi-step exploitation paths across related findings.</p>
      </div>
    )
  }

  return (
    <div className="chain-list">
      {chains.map(chain => (
        <div className="chain-item" key={chain.id}>
          <div className="chain-item-header">
            <div className="chain-description">{chain.chain_description}</div>
            <span className={`severity-badge severity-${(chain.severity || 'medium').toLowerCase()}`}>
              {chain.severity}
            </span>
          </div>

          <div className="chain-steps">
            {Array.isArray(chain.steps) && chain.steps.length > 0 ? (
              chain.steps.map((step, i) => (
                <span className="chain-step" key={i}>
                  {typeof step === 'string' ? step : step.host || JSON.stringify(step)}
                </span>
              ))
            ) : (
              <span className="chain-step" style={{ color: '#8b949e' }}>No step details</span>
            )}
          </div>

          <div className="chain-meta">
            {chain.likelihood && (
              <span>Likelihood: <strong>{chain.likelihood}</strong></span>
            )}
            {chain.mitre_technique_id && (
              <span>MITRE: <strong>{chain.mitre_technique_id}</strong></span>
            )}
            <span>ID: #{chain.id}</span>
          </div>
        </div>
      ))}
    </div>
  )
}