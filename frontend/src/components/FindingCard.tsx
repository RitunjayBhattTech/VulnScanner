import { useState } from 'react'
import type { Finding } from '../types'
import SeverityBadge from './SeverityBadge'
import DeltaBadge from './DeltaBadge'
import RemediationPanel from './RemediationPanel'

interface Props {
  finding: Finding
  index?: number
}

export default function FindingCard({ finding, index }: Props) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="border border-[#1e2a45] rounded-xl overflow-hidden bg-[#0f1629] hover:border-[#243352] transition-colors">
      <button
        className="w-full text-left p-4 flex items-center gap-4"
        onClick={() => setExpanded(e => !e)}
        type="button"
      >
        {index !== undefined && (
          <span className="text-slate-600 text-xs font-mono w-6 shrink-0">#{index}</span>
        )}
        <SeverityBadge severity={finding.severity} />
        <div className="flex-1 min-w-0">
          <div className="text-white font-medium text-sm truncate">{finding.title}</div>
          <div className="text-slate-400 text-xs font-mono mt-0.5 truncate">
            {finding.affected_component}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <DeltaBadge status={finding.delta_status} />
          {finding.is_false_positive && (
            <span className="px-2 py-0.5 text-xs bg-gray-800 text-gray-400 rounded border border-gray-700">
              FP
            </span>
          )}
          <span className="text-slate-500 text-sm">{expanded ? '▲' : '▼'}</span>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-[#1e2a45] pt-4">
          <div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Description</div>
            <p className="text-slate-300 text-sm leading-relaxed">{finding.description}</p>
          </div>

          {finding.evidence && (
            <div>
              <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Evidence</div>
              <pre className="bg-[#0a0e1a] border border-[#1e2a45] rounded-lg p-3 text-xs text-green-400 font-mono overflow-x-auto whitespace-pre-wrap">
                {finding.evidence.slice(0, 400)}
              </pre>
            </div>
          )}

          {finding.ai_triage_notes && (
            <div>
              <div className="text-xs font-medium text-blue-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                <span>◆</span> AI Triage
              </div>
              <p className="text-slate-300 text-sm leading-relaxed italic">{finding.ai_triage_notes}</p>
            </div>
          )}

          {(finding.cve_ids?.length > 0 || finding.cwe_ids?.length > 0) && (
            <div className="flex flex-wrap gap-2">
              {finding.cve_ids?.map(cve => (
                <a
                  key={cve}
                  href={`https://nvd.nist.gov/vuln/detail/${cve}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-2 py-0.5 text-xs bg-red-900/30 text-red-400 border border-red-800 rounded font-mono hover:bg-red-900/50 transition-colors"
                >
                  {cve} ↗
                </a>
              ))}
              {finding.cwe_ids?.map(cwe => (
                <span key={cwe} className="px-2 py-0.5 text-xs bg-orange-900/30 text-orange-400 border border-orange-800 rounded font-mono">
                  {cwe}
                </span>
              ))}
            </div>
          )}

          <RemediationPanel remediation={finding.ai_remediation} />
        </div>
      )}
    </div>
  )
}