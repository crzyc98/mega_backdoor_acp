/**
 * Toggle component for switching between HCE and NHCE views.
 */

type EmployeeType = 'HCE' | 'NHCE' | 'ALL'

interface EmployeeTypeToggleProps {
  value: EmployeeType
  onChange: (type: EmployeeType) => void
  hceCount: number
  nhceCount: number
}

export default function EmployeeTypeToggle({
  value,
  onChange,
  hceCount,
  nhceCount,
}: EmployeeTypeToggleProps) {
  const options: { id: EmployeeType; label: string; count: number }[] = [
    { id: 'ALL', label: 'All', count: hceCount + nhceCount },
    { id: 'HCE', label: 'HCE', count: hceCount },
    { id: 'NHCE', label: 'NHCE', count: nhceCount },
  ]

  return (
    <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
      {options.map((opt) => (
        <button
          key={opt.id}
          onClick={() => onChange(opt.id)}
          className={`
            px-3 py-1.5 text-sm font-medium rounded-md transition-colors
            ${value === opt.id
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
            }
          `}
        >
          {opt.label}
          <span className="ml-1 text-xs text-gray-400">({opt.count})</span>
        </button>
      ))}
    </div>
  )
}
