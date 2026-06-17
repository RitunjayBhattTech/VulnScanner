import { useScans } from '../hooks/useScans'
import { SEVERITY_COLORS } from '../types'

export default function Dashboard() {
  const { scans, loading } = useScans()

  const total = scans.length
  const totalFindings = scans.reduce((s, sc) => s + (sc.total_findings ?? 0), 0)
  const critical = scans.reduce((s, sc) => s + (sc.critical_count ?? 0), 0)
  const high = scans.reduce((s, sc) => s + (sc.high_count ?? 0), 0)

  if (loading) return <div className="text-slate-500 text-sm">Loading stats...</div>

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {[
        { label: 'Total Scans',    value: total,         color: '#3b82f6' },
        { label: 'Total Findings', value: totalFindings,  color: '#94a3b8' },
        { label: 'Critical',       value: critical,       color: SEVERITY_COLORS.critical.bg },
        { label: 'High',           value: high,           color: SEVERITY_COLORS.high.bg },
      ].map(stat => (
        <div key={stat.label} className="bg-[#0f1629] border border-[#1e2a45] rounded-xl p-5">
          <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-2">
            {stat.label}
          </div>
          <div className="text-3xl font-bold" style={{ color: stat.color }}>
            {stat.value}
          </div>
        </div>
      ))}
    </div>
  )
}