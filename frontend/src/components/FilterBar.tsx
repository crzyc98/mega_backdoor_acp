/**
 * Filter bar component for employee impact view.
 */

import type { ConstraintStatus } from '../types'

interface FilterBarProps {
  searchTerm: string
  onSearchChange: (value: string) => void
  constraintFilter: ConstraintStatus | 'ALL'
  onConstraintChange: (value: ConstraintStatus | 'ALL') => void
}

const CONSTRAINT_OPTIONS: { value: ConstraintStatus | 'ALL'; label: string }[] = [
  { value: 'ALL', label: 'All Constraints' },
  { value: 'Unconstrained', label: 'Unconstrained' },
  { value: 'At §415(c) Limit', label: 'At §415(c) Limit' },
  { value: 'Reduced', label: 'Reduced' },
  { value: 'Not Selected', label: 'Not Selected' },
]

export default function FilterBar({
  searchTerm,
  onSearchChange,
  constraintFilter,
  onConstraintChange,
}: FilterBarProps) {
  return (
    <div className="flex flex-wrap gap-3 items-center">
      {/* Search */}
      <div className="relative">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search by employee ID..."
          className="w-64 px-3 py-1.5 pl-9 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <svg
          className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>

      {/* Constraint filter */}
      <select
        value={constraintFilter}
        onChange={(e) => onConstraintChange(e.target.value as ConstraintStatus | 'ALL')}
        className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        {CONSTRAINT_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  )
}
