/**
 * Export page for downloading analysis results in CSV or PDF format.
 */

import { useState, useEffect } from 'react'
import { useWorkspace } from '../hooks/useWorkspace'
import runService from '../services/runService'
import exportService, { ExportFormat } from '../services/exportService'
import LoadingSpinner from '../components/LoadingSpinner'
import type { Run } from '../types'

export default function Export() {
  const { activeWorkspace } = useWorkspace()

  const [runs, setRuns] = useState<Run[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [exporting, setExporting] = useState<ExportFormat | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Load runs on mount
  useEffect(() => {
    if (!activeWorkspace) return

    setLoading(true)
    runService
      .list(activeWorkspace.id)
      .then((response) => {
        const completed = response.items.filter((r) => r.status === 'COMPLETED')
        setRuns(completed)
        if (completed.length > 0) {
          setSelectedRunId(completed[0].id)
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

  const handleExport = async (format: ExportFormat) => {
    if (!activeWorkspace || !selectedRunId) return

    setExporting(format)
    setError(null)
    setSuccess(null)

    try {
      await exportService.download(activeWorkspace.id, selectedRunId, format)
      setSuccess(`${format.toUpperCase()} export downloaded successfully`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed')
    } finally {
      setExporting(null)
    }
  }

  const selectedRun = runs.find((r) => r.id === selectedRunId)

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
          Please upload census data and run analysis before exporting.
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
        <h3 className="mt-4 text-lg font-medium text-blue-800">No Analysis Results</h3>
        <p className="mt-2 text-sm text-blue-700">
          Please run an analysis in the Analysis tab before exporting results.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Run selector */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Analysis Run</h2>

        <select
          value={selectedRunId || ''}
          onChange={(e) => setSelectedRunId(e.target.value)}
          className="w-full md:w-96 px-3 py-2 border border-gray-300 rounded-md text-sm"
        >
          {runs.map((run) => (
            <option key={run.id} value={run.id}>
              {run.name || `Run ${run.seed}`} - {new Date(run.created_at).toLocaleString()}
            </option>
          ))}
        </select>

        {selectedRun && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Seed</p>
                <p className="font-medium">{selectedRun.seed}</p>
              </div>
              <div>
                <p className="text-gray-500">Adoption Rates</p>
                <p className="font-medium">
                  {selectedRun.adoption_rates.length} values
                </p>
              </div>
              <div>
                <p className="text-gray-500">Contribution Rates</p>
                <p className="font-medium">
                  {selectedRun.contribution_rates.length} values
                </p>
              </div>
              <div>
                <p className="text-gray-500">Created</p>
                <p className="font-medium">
                  {new Date(selectedRun.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {success && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-600">{success}</p>
        </div>
      )}

      {/* Export options */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Export Format</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* CSV Export */}
          <div className="border border-gray-200 rounded-lg p-4 hover:border-green-300 transition-colors">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg
                  className="w-6 h-6 text-green-600"
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
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-gray-900">CSV Export</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Download grid results as a CSV file. Includes adoption rates,
                  contribution rates, ACP values, margins, and pass/fail status.
                </p>
                <p className="mt-2 text-xs text-gray-400">
                  Best for: data analysis, spreadsheet integration, further processing
                </p>
                <button
                  onClick={() => handleExport('csv')}
                  disabled={!selectedRunId || exporting !== null}
                  className="mt-3 px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {exporting === 'csv' ? (
                    <>
                      <LoadingSpinner size="sm" />
                      Exporting...
                    </>
                  ) : (
                    <>
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                        />
                      </svg>
                      Download CSV
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* PDF Export */}
          <div className="border border-gray-200 rounded-lg p-4 hover:border-red-300 transition-colors">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <svg
                  className="w-6 h-6 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-gray-900">PDF Report</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Generate a comprehensive PDF report with census summary,
                  analysis results table, and audit metadata.
                </p>
                <p className="mt-2 text-xs text-gray-400">
                  Best for: presentations, documentation, compliance records
                </p>
                <button
                  onClick={() => handleExport('pdf')}
                  disabled={!selectedRunId || exporting !== null}
                  className="mt-3 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {exporting === 'pdf' ? (
                    <>
                      <LoadingSpinner size="sm" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                        />
                      </svg>
                      Download PDF
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Export info */}
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Export Information</h3>
        <ul className="text-xs text-gray-500 space-y-1">
          <li>
            All exports include audit metadata (timestamp, system version, census details)
          </li>
          <li>
            CSV files can be opened in Excel, Google Sheets, or any spreadsheet application
          </li>
          <li>PDF reports include up to 50 scenarios; use CSV for complete data</li>
          <li>
            Files are generated on-demand and are not stored on the server
          </li>
        </ul>
      </div>
    </div>
  )
}
