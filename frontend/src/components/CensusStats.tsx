/**
 * Census statistics display component.
 */

import type { CensusSummary } from '../types'

interface CensusStatsProps {
  summary: CensusSummary
}

export default function CensusStats({ summary }: CensusStatsProps) {
  const formatCurrency = (value: number | undefined) => {
    if (value === undefined) return 'N/A'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(value)
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    })
  }

  const stats = [
    {
      label: 'Total Participants',
      value: summary.participant_count.toLocaleString(),
      color: 'bg-blue-50 text-blue-700',
    },
    {
      label: 'HCE Count',
      value: summary.hce_count.toLocaleString(),
      color: 'bg-purple-50 text-purple-700',
    },
    {
      label: 'NHCE Count',
      value: summary.nhce_count.toLocaleString(),
      color: 'bg-green-50 text-green-700',
    },
    {
      label: 'Avg Compensation',
      value: formatCurrency(summary.avg_compensation),
      color: 'bg-amber-50 text-amber-700',
    },
  ]

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Census Statistics</h3>
        <span className="text-sm text-gray-500">
          Plan Year: {summary.plan_year}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className={`rounded-lg p-4 ${stat.color}`}
          >
            <p className="text-sm font-medium opacity-80">{stat.label}</p>
            <p className="text-2xl font-bold mt-1">{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="text-xs text-gray-400">
        Uploaded: {formatDate(summary.upload_timestamp)}
      </div>
    </div>
  )
}
