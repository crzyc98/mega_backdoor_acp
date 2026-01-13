/**
 * StepValidation - Validation review step of the import wizard.
 * Displays color-coded validation status for each row with error details.
 */

import { useState, useCallback } from 'react'
import LoadingSpinner from '../LoadingSpinner'
import importWizardService from '../../services/importWizardService'
import type {
  ValidationResult,
  PreviewRowList,
  RowStatus,
  ValidationIssue,
} from '../../types/importWizard'

interface StepValidationProps {
  sessionId: string
  validationResult: ValidationResult | null
  previewRows: PreviewRowList | null
  onContinue: () => void
  onBack: () => void
  loading: boolean
  error: string | null
}

function getStatusColor(status: RowStatus): string {
  switch (status) {
    case 'valid':
      return 'bg-green-100 border-green-200 text-green-800'
    case 'warning':
      return 'bg-yellow-100 border-yellow-200 text-yellow-800'
    case 'error':
      return 'bg-red-100 border-red-200 text-red-800'
    default:
      return 'bg-gray-100 border-gray-200 text-gray-800'
  }
}

function getStatusIcon(status: RowStatus) {
  switch (status) {
    case 'valid':
      return (
        <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      )
    case 'warning':
      return (
        <svg className="w-4 h-4 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
      )
    case 'error':
      return (
        <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      )
    default:
      return null
  }
}

export default function StepValidation({
  sessionId,
  validationResult,
  previewRows: initialPreviewRows,
  onContinue,
  onBack,
  loading,
  error,
}: StepValidationProps) {
  const [previewRows, setPreviewRows] = useState(initialPreviewRows)
  const [statusFilter, setStatusFilter] = useState<RowStatus | 'all'>('all')
  const [expandedRow, setExpandedRow] = useState<number | null>(null)
  const [loadingMore, setLoadingMore] = useState(false)

  const summary = validationResult?.summary

  // Filter rows by status
  const handleFilterChange = useCallback(async (status: RowStatus | 'all') => {
    setStatusFilter(status)
    if (!sessionId) return

    setLoadingMore(true)
    try {
      const rows = await importWizardService.getPreviewRows(sessionId, {
        status: status === 'all' ? undefined : status,
        limit: 100,
      })
      setPreviewRows(rows)
    } catch {
      // Keep existing rows on error
    } finally {
      setLoadingMore(false)
    }
  }, [sessionId])

  // Check if import can proceed
  const canProceed = summary ? summary.error_count === 0 : false

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-base font-medium text-gray-900">
          Validation Results
        </h3>
        <p className="text-sm text-gray-500">
          Review the validation status of your data. Errors must be fixed before importing.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">
              {summary.total_rows.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500">Total Rows</div>
          </div>
          <div className="bg-green-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-green-600">
              {summary.valid_count.toLocaleString()}
            </div>
            <div className="text-xs text-green-700">Valid</div>
          </div>
          <div className="bg-yellow-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-yellow-600">
              {summary.warning_count.toLocaleString()}
            </div>
            <div className="text-xs text-yellow-700">Warnings</div>
          </div>
          <div className="bg-red-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-red-600">
              {summary.error_count.toLocaleString()}
            </div>
            <div className="text-xs text-red-700">Errors</div>
          </div>
        </div>
      )}

      {/* Filter buttons */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-500">Filter:</span>
        {(['all', 'valid', 'warning', 'error'] as const).map((status) => (
          <button
            key={status}
            onClick={() => handleFilterChange(status)}
            className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${
              statusFilter === status
                ? status === 'all'
                  ? 'bg-gray-900 text-white'
                  : status === 'valid'
                    ? 'bg-green-600 text-white'
                    : status === 'warning'
                      ? 'bg-yellow-500 text-white'
                      : 'bg-red-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
            disabled={loadingMore}
          >
            {status === 'all' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1)}
          </button>
        ))}
        {loadingMore && <LoadingSpinner size="sm" />}
      </div>

      {/* Preview rows table */}
      {previewRows && (
        <div className="bg-gray-50 rounded-lg overflow-hidden">
          <div className="max-h-96 overflow-y-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-100 sticky top-0">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-600 w-16">
                    Row
                  </th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600 w-24">
                    Status
                  </th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">
                    Issues
                  </th>
                </tr>
              </thead>
              <tbody>
                {previewRows.items.map((row) => (
                  <>
                    <tr
                      key={row.row_number}
                      className={`cursor-pointer hover:bg-gray-100 ${
                        expandedRow === row.row_number ? 'bg-gray-100' : 'bg-white'
                      }`}
                      onClick={() =>
                        setExpandedRow(
                          expandedRow === row.row_number ? null : row.row_number
                        )
                      }
                    >
                      <td className="px-3 py-2 text-gray-900 font-mono">
                        {row.row_number}
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                            row.status
                          )}`}
                        >
                          {getStatusIcon(row.status)}
                          {row.status}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-gray-600">
                        {row.issues.length === 0 ? (
                          <span className="text-gray-400">No issues</span>
                        ) : (
                          <span>
                            {row.issues.length} issue
                            {row.issues.length !== 1 ? 's' : ''}
                          </span>
                        )}
                      </td>
                    </tr>
                    {expandedRow === row.row_number && row.issues.length > 0 && (
                      <tr>
                        <td colSpan={3} className="bg-gray-50 px-3 py-2">
                          <div className="space-y-2 ml-4">
                            {row.issues.map((issue: ValidationIssue) => (
                              <div
                                key={issue.id}
                                className={`p-2 rounded border ${
                                  issue.severity === 'error'
                                    ? 'bg-red-50 border-red-200'
                                    : issue.severity === 'warning'
                                      ? 'bg-yellow-50 border-yellow-200'
                                      : 'bg-blue-50 border-blue-200'
                                }`}
                              >
                                <div className="flex items-start gap-2">
                                  <span
                                    className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                                      issue.severity === 'error'
                                        ? 'bg-red-100 text-red-800'
                                        : issue.severity === 'warning'
                                          ? 'bg-yellow-100 text-yellow-800'
                                          : 'bg-blue-100 text-blue-800'
                                    }`}
                                  >
                                    {issue.field_name}
                                  </span>
                                  <span className="text-xs text-gray-900">
                                    {issue.message}
                                  </span>
                                </div>
                                {issue.raw_value && (
                                  <div className="mt-1 text-xs text-gray-500">
                                    Value: <code className="bg-gray-100 px-1 rounded">{issue.raw_value}</code>
                                  </div>
                                )}
                                {issue.suggestion && (
                                  <div className="mt-1 text-xs text-gray-600">
                                    Suggestion: {issue.suggestion}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>

          {previewRows.total > previewRows.items.length && (
            <div className="px-3 py-2 bg-gray-100 text-center text-xs text-gray-500">
              Showing {previewRows.items.length} of {previewRows.total} rows
            </div>
          )}
        </div>
      )}

      {/* Error blocking message */}
      {summary && summary.error_count > 0 && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-start gap-3">
            <svg
              className="w-5 h-5 text-red-500 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <h4 className="text-sm font-medium text-red-800">
                Import blocked by errors
              </h4>
              <p className="mt-1 text-sm text-red-700">
                {summary.error_count} row{summary.error_count !== 1 ? 's have' : ' has'} errors
                that must be fixed in your source CSV before importing.
              </p>
              {/* T049: Jump to first error button */}
              <button
                type="button"
                onClick={async () => {
                  await handleFilterChange('error')
                  // Find first error row and expand it
                  if (previewRows?.items) {
                    const firstError = previewRows.items.find((r) => r.status === 'error')
                    if (firstError) {
                      setExpandedRow(firstError.row_number)
                    }
                  }
                }}
                className="mt-2 text-sm font-medium text-red-700 hover:text-red-900 underline"
              >
                Show errors
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={onBack}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          disabled={loading}
        >
          Back
        </button>

        <button
          type="button"
          onClick={onContinue}
          disabled={!canProceed || loading}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {loading ? (
            <>
              <LoadingSpinner size="sm" />
              Loading...
            </>
          ) : (
            'Continue'
          )}
        </button>
      </div>
    </div>
  )
}
