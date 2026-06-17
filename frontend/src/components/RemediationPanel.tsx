interface Props {
  remediation?: string | null
}

export default function RemediationPanel({ remediation }: Props) {
  if (!remediation) return null

  return (
    <div className="bg-[#0a0e1a] border border-green-900/50 rounded-lg p-4 mt-3">
      <div className="text-xs font-medium text-green-400 uppercase tracking-wider mb-2 flex items-center gap-2">
        <span>✓</span> Remediation Guidance
      </div>
      <pre className="text-slate-300 text-xs leading-relaxed whitespace-pre-wrap font-sans">
        {remediation}
      </pre>
    </div>
  )
}