/**
 * Employee impact page with drill-down into individual employee contributions.
 */

import { useState, useEffect, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useWorkspace } from '../hooks/useWorkspace'
import runService, { RunDetail } from '../services/runService'
import employeeService from '../services/employeeService'
import DataTable, { Column } from '../components/DataTable'
import ConstraintBadge from '../components/ConstraintBadge'
import EmployeeTypeToggle from '../components/EmployeeTypeToggle'
import FilterBar from '../components/FilterBar'
import LoadingSpinner from '../components/LoadingSpinner'
import type { EmployeeImpact as EmployeeImpactType, EmployeeImpactView, ConstraintStatus, Run } from '../types'

type EmployeeFilter = 'HCE' | 'NHCE' | 'ALL'

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

function formatPercentage(value: number | null): string {
  if (value === null) return 'N/A'
  return `${value.toFixed(2)}%`
}

function formatSignedPercentage(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

// Format rate for display - handles both fraction (0.25) and percentage (25) formats
function formatRateForDisplay(rate: number): string {
  // If rate > 1, it's already a percentage; otherwise it's a fraction
  const pct = rate > 1 ? rate : rate * 100
  return `${pct.toFixed(0)}%`
}

export default function EmployeeImpact() {
  const { activeWorkspace } = useWorkspace()
  const [searchParams] = useSearchParams()

  const [runs, setRuns] = useState<Run[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [selectedRun, setSelectedRun] = useState<RunDetail | null>(null)
  const [impactData, setImpactData] = useState<EmployeeImpactView | null>(null)

  const [adoptionRate, setAdoptionRate] = useState<number | null>(null)
  const [contributionRate, setContributionRate] = useState<number | null>(null)

  const [loading, setLoading] = useState(false)
  const [loadingImpact, setLoadingImpact] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [employeeFilter, setEmployeeFilter] = useState<EmployeeFilter>('ALL')
  const [searchTerm, setSearchTerm] = useState('')
  const [constraintFilter, setConstraintFilter] = useState<ConstraintStatus | 'ALL'>('ALL')

  // Check for scenario context from URL params
  useEffect(() => {
    const adoption = searchParams.get('adoption_rate')
    const contribution = searchParams.get('contribution_rate')
    const runId = searchParams.get('run_id')

    if (adoption) setAdoptionRate(parseFloat(adoption))
    if (contribution) setContributionRate(parseFloat(contribution))
    if (runId) setSelectedRunId(runId)
  }, [searchParams])

  // Load runs on mount
  useEffect(() => {
    if (!activeWorkspace) return

    setLoading(true)
    runService
      .list(activeWorkspace.id)
      .then((response) => {
        setRuns(response.items.filter((r) => r.status === 'COMPLETED'))
        // Auto-select first completed run if none selected
        if (!selectedRunId && response.items.length > 0) {
          const firstCompleted = response.items.find((r) => r.status === 'COMPLETED')
          if (firstCompleted) {
            setSelectedRunId(firstCompleted.id)
          }
        }
      })
      .catch((err) => {
        console.error('Failed to load runs:', err)
        setError('Failed to load analysis runs')
      })
      .finally(() => {
        setLoading(false)
      })
  }, [activeWorkspace])

  // Load selected run details
  useEffect(() => {
    if (!activeWorkspace || !selectedRunId) return

    runService
      .get(activeWorkspace.id, selectedRunId)
      .then((runDetail) => {
        setSelectedRun(runDetail)
        // Set default rates if not already set
        if (adoptionRate === null && runDetail.adoption_rates.length > 0) {
          setAdoptionRate(runDetail.adoption_rates[runDetail.adoption_rates.length - 1])
        }
        if (contributionRate === null && runDetail.contribution_rates.length > 0) {
          setContributionRate(runDetail.contribution_rates[0])
        }
      })
      .catch((err) => {
        console.error('Failed to load run details:', err)
      })
  }, [activeWorkspace, selectedRunId])

  // Load employee impact data when rates are selected
  useEffect(() => {
    if (!activeWorkspace || !selectedRunId || adoptionRate === null || contributionRate === null) {
      return
    }

    setLoadingImpact(true)
    setError(null)

    employeeService
      .getImpact(activeWorkspace.id, selectedRunId, adoptionRate, contributionRate)
      .then((data) => {
        setImpactData(data)
      })
      .catch((err) => {
        console.error('Failed to load employee impact:', err)
        setError(err instanceof Error ? err.message : 'Failed to load employee impact data')
      })
      .finally(() => {
        setLoadingImpact(false)
      })
  }, [activeWorkspace, selectedRunId, adoptionRate, contributionRate])

  // Filter employees
  const filteredEmployees = useMemo(() => {
    if (!impactData) return []

    let employees: EmployeeImpactType[] = []

    if (employeeFilter === 'ALL') {
      employees = [...impactData.hce_employees, ...impactData.nhce_employees]
    } else if (employeeFilter === 'HCE') {
      employees = impactData.hce_employees
    } else {
      employees = impactData.nhce_employees
    }

    // Apply search filter
    if (searchTerm) {
      employees = employees.filter((e) =>
        e.employee_id.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Apply constraint filter
    if (constraintFilter !== 'ALL') {
      employees = employees.filter((e) => e.constraint_status === constraintFilter)
    }

    return employees
  }, [impactData, employeeFilter, searchTerm, constraintFilter])

  // Table columns
  const columns: Column<EmployeeImpactType>[] = [
    {
      key: 'employee_id',
      header: 'Employee ID',
      render: (row) => <span className="font-mono text-sm">{row.employee_id}</span>,
    },
    {
      key: 'is_hce',
      header: 'Type',
      align: 'center',
      render: (row) => (
        <span
          className={`
            px-2 py-0.5 rounded-full text-xs font-medium
            ${row.is_hce ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'}
          `}
        >
          {row.is_hce ? 'HCE' : 'NHCE'}
        </span>
      ),
    },
    {
      key: 'compensation',
      header: 'Compensation',
      align: 'right',
      render: (row) => formatCurrency(row.compensation),
    },
    {
      key: 'deferral_amount',
      header: 'Deferral',
      align: 'right',
      render: (row) => formatCurrency(row.deferral_amount),
    },
    {
      key: 'match_amount',
      header: 'Match',
      align: 'right',
      render: (row) => formatCurrency(row.match_amount),
    },
    {
      key: 'mega_backdoor_amount',
      header: 'Mega Backdoor',
      align: 'right',
      render: (row) => (
        <span className={row.mega_backdoor_amount > 0 ? 'font-semibold text-green-600' : ''}>
          {formatCurrency(row.mega_backdoor_amount)}
        </span>
      ),
    },
    {
      key: 'available_room',
      header: '§415(c) Room',
      align: 'right',
      render: (row) => (
        <span className={row.available_room < 0 ? 'text-red-600' : ''}>
          {formatCurrency(row.available_room)}
        </span>
      ),
    },
    {
      key: 'individual_acp',
      header: 'ACP',
      align: 'right',
      render: (row) => formatPercentage(row.individual_acp),
    },
    {
      key: 'constraint_status',
      header: 'Constraint',
      render: (row) => <ConstraintBadge status={row.constraint_status} />,
    },
  ]

  if (!activeWorkspace?.has_census) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
        <svg
          className="mx-auto h-12 w-12 text-yellow-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <h3 className="mt-4 text-lg font-medium text-yellow-800">Census Required</h3>
        <p className="mt-2 text-sm text-yellow-700">
          Please upload census data and run analysis before viewing employee impact.
        </p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (runs.length === 0) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
        <svg
          className="mx-auto h-12 w-12 text-blue-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <h3 className="mt-4 text-lg font-medium text-blue-800">Analysis Required</h3>
        <p className="mt-2 text-sm text-blue-700">
          Please run a grid analysis in the Analysis tab before viewing employee impact.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Scenario selector */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Scenario</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Run selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Analysis Run
            </label>
            <select
              value={selectedRunId || ''}
              onChange={(e) => {
                setSelectedRunId(e.target.value)
                setImpactData(null)
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              {runs.map((run) => (
                <option key={run.id} value={run.id}>
                  {run.name || `Run ${run.seed}`} ({new Date(run.created_at).toLocaleDateString()})
                </option>
              ))}
            </select>
          </div>

          {/* Adoption rate selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Adoption Rate
            </label>
            <select
              value={adoptionRate ?? ''}
              onChange={(e) => {
                setAdoptionRate(parseFloat(e.target.value))
                setImpactData(null)
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              disabled={!selectedRun}
            >
              {selectedRun?.adoption_rates.map((rate) => (
                <option key={rate} value={rate}>
                  {formatRateForDisplay(rate)}
                </option>
              ))}
            </select>
          </div>

          {/* Contribution rate selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contribution Rate
            </label>
            <select
              value={contributionRate ?? ''}
              onChange={(e) => {
                setContributionRate(parseFloat(e.target.value))
                setImpactData(null)
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              disabled={!selectedRun}
            >
              {selectedRun?.contribution_rates.map((rate) => (
                <option key={rate} value={rate}>
                  {formatRateForDisplay(rate)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Summary cards */}
      {impactData && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="bg-purple-50 rounded-lg p-4">
            <p className="text-sm text-purple-600 mb-1">HCE Count</p>
            <p className="text-2xl font-bold text-purple-700">{impactData.hce_summary.total_count}</p>
            <p className="text-xs text-purple-500 mt-1">
              {impactData.hce_summary.at_limit_count} at limit
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">NHCE Count</p>
            <p className="text-2xl font-bold text-gray-700">{impactData.nhce_summary.total_count}</p>
          </div>
          <div className="bg-amber-50 rounded-lg p-4">
            <p className="text-sm text-amber-700 mb-1">Excluded Employees</p>
            <p className="text-2xl font-bold text-amber-800">{impactData.excluded_count}</p>
            {impactData.exclusion_breakdown && impactData.excluded_count > 0 && (
              <div className="text-xs text-amber-600 mt-1 space-y-0.5">
                {impactData.exclusion_breakdown.terminated_before_entry_count > 0 && (
                  <p>{impactData.exclusion_breakdown.terminated_before_entry_count} termed before entry</p>
                )}
                {impactData.exclusion_breakdown.not_eligible_during_year_count > 0 && (
                  <p>{impactData.exclusion_breakdown.not_eligible_during_year_count} not eligible</p>
                )}
              </div>
            )}
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <p className="text-sm text-green-600 mb-1">Total Mega Backdoor</p>
            <p className="text-2xl font-bold text-green-700">
              {formatCurrency(impactData.hce_summary.total_mega_backdoor || 0)}
            </p>
          </div>
          <div className="bg-blue-50 rounded-lg p-4">
            <p className="text-sm text-blue-600 mb-1">§415(c) Limit</p>
            <p className="text-2xl font-bold text-blue-700">
              {formatCurrency(impactData.section_415c_limit)}
            </p>
            <p className="text-xs text-blue-500 mt-1">
              Plan year {impactData.plan_year}
            </p>
          </div>
        </div>
      )}

      {impactData?.scenario && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Compliance Card</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-500">NHCE ACP</span>
                <span className="font-medium">{formatPercentage(impactData.scenario.nhce_acp)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">HCE ACP</span>
                <span className="font-medium">{formatPercentage(impactData.scenario.hce_acp)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Limit 1.25x</span>
                <span className="font-medium">{formatPercentage(impactData.scenario.limit_125 ?? null)}</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-500">Limit +2.0%</span>
                <span className="font-medium">{formatPercentage(impactData.scenario.limit_2pct_uncapped ?? null)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Cap 2x</span>
                <span className="font-medium">{formatPercentage(impactData.scenario.cap_2x ?? null)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Capped +2.0%</span>
                <span className="font-medium">{formatPercentage(impactData.scenario.limit_2pct_capped ?? null)}</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-500">Effective Limit</span>
                <span className="font-medium">
                  {formatPercentage(
                    impactData.scenario.effective_limit ?? impactData.scenario.max_allowed_acp ?? null
                  )}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Binding Rule</span>
                <span className="font-medium">{impactData.scenario.binding_rule ?? 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Margin</span>
                <span className="font-medium">{formatSignedPercentage(impactData.scenario.margin)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Employee table */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Employee Details</h2>

          {impactData && (
            <EmployeeTypeToggle
              value={employeeFilter}
              onChange={setEmployeeFilter}
              hceCount={impactData.hce_summary.total_count}
              nhceCount={impactData.nhce_summary.total_count}
            />
          )}
        </div>

        {impactData && (
          <div className="mb-4">
            <FilterBar
              searchTerm={searchTerm}
              onSearchChange={setSearchTerm}
              constraintFilter={constraintFilter}
              onConstraintChange={setConstraintFilter}
            />
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {loadingImpact ? (
          <div className="py-12">
            <LoadingSpinner size="md" />
          </div>
        ) : impactData ? (
          <DataTable
            data={filteredEmployees}
            columns={columns}
            keyField="employee_id"
            pageSize={15}
            emptyMessage="No employees match the current filters"
          />
        ) : (
          <div className="text-center py-8 text-gray-500">
            Select a scenario to view employee impact details
          </div>
        )}
      </div>
    </div>
  )
}
