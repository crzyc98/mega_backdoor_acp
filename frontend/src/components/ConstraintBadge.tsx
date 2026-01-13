/**
 * Badge component for displaying constraint status.
 */

import type { ConstraintStatus } from '../types'

interface ConstraintBadgeProps {
  status: ConstraintStatus
  showLabel?: boolean
}

const STATUS_STYLES: Record<ConstraintStatus, { bg: string; text: string; icon: string }> = {
  'Unconstrained': {
    bg: 'bg-green-100',
    text: 'text-green-700',
    icon: '✓',
  },
  'At §415(c) Limit': {
    bg: 'bg-red-100',
    text: 'text-red-700',
    icon: '⊘',
  },
  'Reduced': {
    bg: 'bg-amber-100',
    text: 'text-amber-700',
    icon: '↓',
  },
  'Not Selected': {
    bg: 'bg-gray-100',
    text: 'text-gray-600',
    icon: '—',
  },
}

export default function ConstraintBadge({
  status,
  showLabel = true,
}: ConstraintBadgeProps) {
  const style = STATUS_STYLES[status] || STATUS_STYLES['Not Selected']

  return (
    <span
      className={`
        inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium
        ${style.bg} ${style.text}
      `}
      title={status}
    >
      <span>{style.icon}</span>
      {showLabel && <span>{status}</span>}
    </span>
  )
}
