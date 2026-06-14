import React, { useState } from 'react';
import type { Finding } from '../types';
import SeverityBadge from './SeverityBadge';
import DeltaBadge from './DeltaBadge';

interface Props {
  finding: Finding;
}

export default function FindingCard({ finding }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [showRemediation, setShowRemediation] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            <SeverityBadge severity={finding.severity} size="sm" />
            {finding.delta_status && <DeltaBadge deltaStatus={finding.delta_status} />}
            {finding.is_false_positive && (
              <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded bg-purple-100 text-purple-700 border border-purple-300">
                FALSE POSITIVE
              </span>
            )}
            <h3 className="text-sm font-medium text-gray-900 truncate">{finding.title}</h3>
          </div>
          <div className="flex items-center space-x-2 ml-4">
            {finding.affected_component && (
              <span className="text-xs text-gray-500 truncate max-w-[200px]">{finding.affected_component}</span>
            )}
            <svg className={`w-4 h-4 text-gray-400 transform transition-transform ${expanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3">
          {/* Description */}
          {finding.description && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Description</h4>
              <p className="text-sm text-gray-700">{finding.description}</p>
            </div>
          )}

          {/* Evidence */}
          {finding.evidence && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Evidence</h4>
              <pre className="bg-gray-900 text-gray-100 p-3 rounded text-xs overflow-x-auto max-h-40">
                {finding.evidence.length > 500 ? finding.evidence.slice(0, 500) + '...' : finding.evidence}
              </pre>
            </div>
          )}

          {/* AI Triage */}
          {finding.ai_triage_notes && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">AI Triage Notes</h4>
              <p className="text-sm text-gray-700">{finding.ai_triage_notes}</p>
            </div>
          )}

          {/* CVE/CWE IDs */}
          {(finding.cve_ids?.length > 0 || finding.cwe_ids?.length > 0) && (
            <div className="flex flex-wrap gap-2">
              {finding.cve_ids?.map((cve) => (
                <a
                  key={cve}
                  href={`https://nvd.nist.gov/vuln/detail/${cve}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:text-blue-800 underline"
                >
                  {cve}
                </a>
              ))}
              {finding.cwe_ids?.map((cwe) => (
                <a
                  key={cwe}
                  href={`https://cwe.mitre.org/data/definitions/${cwe.replace('CWE-', '')}.html`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:text-blue-800 underline"
                >
                  {cwe}
                </a>
              ))}
            </div>
          )}

          {/* Scanner source */}
          {finding.scanner_source && (
            <p className="text-xs text-gray-400">
              Source: {finding.scanner_source} | {new Date(finding.created_at).toLocaleString()}
            </p>
          )}

          {/* Remediation toggle */}
          {finding.ai_remediation && (
            <div>
              <button
                onClick={() => setShowRemediation(!showRemediation)}
                className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
              >
                {showRemediation ? 'Hide Remediation' : 'Show Remediation'}
              </button>
              {showRemediation && (
                <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded">
                  <div className="text-sm text-gray-700 whitespace-pre-wrap">{finding.ai_remediation}</div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}