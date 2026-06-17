interface Props {
  status?: string | null
}

const CONFIG: Record<string, { label: string; className: string }> = {
  new:       { label: 'NEW',       className: 'bg-green-900/50 text-green-400 border-green-800' },
  fixed:     { label: 'FIXED',     className: 'bg-blue-900/50 text-blue-400 border-blue-800' },
  regressed: { label: 'REGRESSED', className: 'bg-red-900/50 text-red-400 border-red-800' },
  existing:  { label: 'EXISTING',  className: 'bg-gray-900/50 text-gray-400 border-gray-700' },
}

export default function DeltaBadge({ status }: Props) {
  if (!status) return null
  const cfg = CONFIG[status] ?? CONFIG.existing
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium border ${cfg.className}`}>
      {cfg.label}
    </span>
  )
}