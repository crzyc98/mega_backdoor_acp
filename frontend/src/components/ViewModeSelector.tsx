/**
 * View mode selector for heatmap visualization.
 */

import type { ViewMode } from '../types'

interface ViewModeSelectorProps {
  value: ViewMode
  onChange: (mode: ViewMode) => void
}

const VIEW_MODES: { id: ViewMode; label: string; description: string }[] = [
  { id: 'PASS_FAIL', label: 'Pass/Fail', description: 'Simple pass or fail status' },
  { id: 'MARGIN', label: 'Margin', description: 'Distance from threshold' },
  { id: 'RISK_ZONE', label: 'Risk Zone', description: 'Highlight borderline scenarios' },
]

export default function ViewModeSelector({ value, onChange }: ViewModeSelectorProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-gray-600">View:</span>
      <div className="flex gap-1">
        {VIEW_MODES.map((mode) => (
          <button
            key={mode.id}
            onClick={() => onChange(mode.id)}
            className={`
              px-3 py-1.5 text-sm font-medium rounded-md transition-colors
              ${value === mode.id
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }
            `}
            title={mode.description}
          >
            {mode.label}
          </button>
        ))}
      </div>
    </div>
  )
}
