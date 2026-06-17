import type { SeverityLevel } from '../types'
import { SEVERITY_COLORS } from '../types'

interface Props {
  severity: string
  size?: 'sm' | 'md'
}

export default function SeverityBadge({ severity, size = 'sm' }: Props) {
  const key = severity?.toLowerCase() as SeverityLevel
  const colors = SEVERITY_COLORS[key] ?? SEVERITY_COLORS.informational
  const padding = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm'

  return (
    <span
      className={`inline-flex items-center rounded font-bold uppercase ${padding}`}
      style={{
        backgroundColor: colors.bg + '33',
        color: colors.bg,
        border: `1px solid ${colors.border}`,
      }}
    >
      {severity || 'unknown'}
    </span>
  )
}