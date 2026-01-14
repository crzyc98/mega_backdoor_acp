/**
 * Analysis dashboard page with grid parameters and heatmap visualization.
 */

import { useState, useEffect } from 'react'
import { useWorkspace } from '../hooks/useWorkspace'
import runService, { RunDetail } from '../services/runService'
import Heatmap from '../components/Heatmap'
import ViewModeSelector from '../components/ViewModeSelector'
import LoadingSpinner from '../components/LoadingSpinner'
import type { Run, ViewMode, ScenarioResult } from '../types'

// Default rate configurations (as percentages for API)
const DEFAULT_ADOPTION_RATES = [20, 40, 60, 80, 100]
const DEFAULT_CONTRIBUTION_RATES = [2, 4, 6, 8, 10, 12]

// Format rates array for display - handles both fractions and percentages
const formatRatesForDisplay = (rates: number[]): string => {
  // Detect format: if max rate > 1, they're already percentages; otherwise fractions
  const maxRate = Math.max(...rates)
  const areFractions = maxRate <= 1

  return rates.map((r) => {
    const pct = areFractions ? r * 100 : r
    return pct.toFixed(0)
  }).join(', ')
}

export default function AnalysisDashboard() {
  const { activeWorkspace, refreshActiveWorkspace } = useWorkspace()

  const [adoptionRates, setAdoptionRates] = useState<number[]>(DEFAULT_ADOPTION_RATES)
  const [contributionRates, setContributionRates] = useState<number[]>(DEFAULT_CONTRIBUTION_RATES)
  const [adoptionRatesText, setAdoptionRatesText] = useState<string>(
    formatRatesForDisplay(DEFAULT_ADOPTION_RATES)
  )
  const [contributionRatesText, setContributionRatesText] = useState<string>(
    formatRatesForDisplay(DEFAULT_CONTRIBUTION_RATES)
  )
  const [seed, setSeed] = useState<string>('')
  const [viewMode, setViewMode] = useState<ViewMode>('PASS_FAIL')

  const [runs, setRuns] = useState<Run[]>([])
  const [selectedRun, setSelectedRun] = useState<RunDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [runningAnalysis, setRunningAnalysis] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load runs on mount
  useEffect(() => {
    if (!activeWorkspace) return

    setLoading(true)
    runService
      .list(activeWorkspace.id)
      .then((response) => {
        setRuns(response.items)
        // Load latest completed run if exists
        const latestCompleted = response.items.find((r) => r.status === 'COMPLETED')
        if (latestCompleted) {
          loadRun(latestCompleted.id)
        }
      })
      .catch((err) => {
        console.error('Failed to load runs:', err)
      })
      .finally(() => {
        setLoading(false)
      })
  }, [activeWorkspace])

  const loadRun = async (runId: string) => {
    if (!activeWorkspace) return

    try {
      const runDetail = await runService.get(activeWorkspace.id, runId)
      setSelectedRun(runDetail)
      // Restore parameters from run
      setAdoptionRates(runDetail.adoption_rates)
      setContributionRates(runDetail.contribution_rates)
      setAdoptionRatesText(formatRatesForDisplay(runDetail.adoption_rates))
      setContributionRatesText(formatRatesForDisplay(runDetail.contribution_rates))
      setSeed(runDetail.seed.toString())
    } catch (err) {
      console.error('Failed to load run:', err)
    }
  }

  const parseRates = (text: string): number[] => {
    // Parse user input as percentages (e.g., "20, 40, 60" -> [20, 40, 60])
    // API expects percentages and converts to fractions internally
    return text
      .split(',')
      .map((s) => parseFloat(s.trim()))
      .filter((n) => !isNaN(n) && n > 0 && n <= 100)
  }

  const handleRunAnalysis = async () => {
    if (!activeWorkspace) return

    setRunningAnalysis(true)
    setError(null)

    try {
      const run = await runService.create(activeWorkspace.id, {
        adoption_rates: adoptionRates,
        contribution_rates: contributionRates,
        seed: seed ? parseInt(seed, 10) : undefined,
      })

      // Load the completed run
      const runDetail = await runService.get(activeWorkspace.id, run.id)
      setSelectedRun(runDetail)
      setRuns((prev) => [run, ...prev])
      await refreshActiveWorkspace()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run analysis')
    } finally {
      setRunningAnalysis(false)
    }
  }

  const handleCellClick = (scenario: ScenarioResult) => {
    // Could navigate to employee impact view with this scenario context
    console.log('Clicked scenario:', scenario)
  }

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
          Please upload census data in the Upload tab before running analysis.
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

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Analysis Parameters</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Adoption Rates
            </label>
            <input
              type="text"
              value={adoptionRatesText}
              onChange={(e) => setAdoptionRatesText(e.target.value)}
              onBlur={() => {
                const rates = parseRates(adoptionRatesText)
                if (rates.length >= 2) {
                  setAdoptionRates(rates)
                  setAdoptionRatesText(formatRatesForDisplay(rates))
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              placeholder="20, 40, 60, 80, 100"
            />
            <p className="mt-1 text-xs text-gray-400">Comma-separated percentages</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contribution Rates
            </label>
            <input
              type="text"
              value={contributionRatesText}
              onChange={(e) => setContributionRatesText(e.target.value)}
              onBlur={() => {
                const rates = parseRates(contributionRatesText)
                if (rates.length >= 2) {
                  setContributionRates(rates)
                  setContributionRatesText(formatRatesForDisplay(rates))
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              placeholder="2, 4, 6, 8, 10, 12"
            />
            <p className="mt-1 text-xs text-gray-400">Comma-separated percentages</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Random Seed (optional)
            </label>
            <input
              type="number"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              placeholder="Auto-generate"
              min={1}
            />
            <p className="mt-1 text-xs text-gray-400">For reproducible results</p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <button
          onClick={handleRunAnalysis}
          disabled={runningAnalysis || adoptionRates.length < 2 || contributionRates.length < 2}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {runningAnalysis ? (
            <>
              <LoadingSpinner size="sm" />
              Running Analysis...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Run Analysis
            </>
          )}
        </button>
      </div>

      {selectedRun?.results && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Results Heatmap</h2>
              <p className="text-sm text-gray-500">
                {selectedRun.results.summary.total_count} scenarios analyzed (Seed: {selectedRun.seed})
              </p>
            </div>
            <ViewModeSelector value={viewMode} onChange={setViewMode} />
          </div>

          {/* Summary stats */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-green-50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-green-700">
                {selectedRun.results.summary.pass_count}
              </p>
              <p className="text-xs text-green-600">Pass</p>
            </div>
            <div className="bg-amber-50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-amber-700">
                {selectedRun.results.summary.risk_count}
              </p>
              <p className="text-xs text-amber-600">Risk</p>
            </div>
            <div className="bg-red-50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-red-700">
                {selectedRun.results.summary.fail_count}
              </p>
              <p className="text-xs text-red-600">Fail</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-gray-700">
                {selectedRun.results.summary.error_count}
              </p>
              <p className="text-xs text-gray-600">Error</p>
            </div>
          </div>

          <Heatmap
            scenarios={selectedRun.results.scenarios}
            adoptionRates={selectedRun.adoption_rates}
            contributionRates={selectedRun.contribution_rates}
            viewMode={viewMode}
            onCellClick={handleCellClick}
          />
        </div>
      )}

      {/* Run history */}
      {runs.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Previous Runs</h3>
          <div className="space-y-2">
            {runs.slice(0, 5).map((run) => (
              <button
                key={run.id}
                onClick={() => loadRun(run.id)}
                className={`w-full text-left p-3 rounded-lg border transition-colors ${
                  selectedRun?.id === run.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900">
                    {run.name || `Run ${run.seed}`}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      run.status === 'COMPLETED'
                        ? 'bg-green-100 text-green-700'
                        : run.status === 'FAILED'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {run.status}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {new Date(run.created_at).toLocaleString()}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
