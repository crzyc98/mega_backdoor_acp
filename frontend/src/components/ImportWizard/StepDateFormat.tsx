/**
 * StepDateFormat - Date format selection step of the import wizard.
 * Allows users to select and preview date format parsing.
 */

import { useState, useEffect } from 'react'
import LoadingSpinner from '../LoadingSpinner'
import importWizardService from '../../services/importWizardService'
import type {
  DateFormatDetection,
  DateFormatPreview,
} from '../../types/importWizard'

interface StepDateFormatProps {
  workspaceId: string
  sessionId: string
  detection: DateFormatDetection | null
  onSubmit: (format: string) => void
  onBack: () => void
  loading: boolean
  error: string | null
}

export default function StepDateFormat({
  workspaceId,
  sessionId,
  detection,
  onSubmit,
  onBack,
  loading,
  error,
}: StepDateFormatProps) {
  const [selectedFormat, setSelectedFormat] = useState<string>('')
  const [preview, setPreview] = useState<DateFormatPreview | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)

  // Initialize with recommended format
  useEffect(() => {
    if (detection?.recommended_format) {
      setSelectedFormat(detection.recommended_format)
    }
  }, [detection])

  // Load preview when format changes
  useEffect(() => {
    if (!selectedFormat || !sessionId || !workspaceId) return

    setPreviewLoading(true)
    importWizardService
      .previewDateFormat(workspaceId, sessionId, selectedFormat)
      .then(setPreview)
      .catch(() => setPreview(null))
      .finally(() => setPreviewLoading(false))
  }, [workspaceId, sessionId, selectedFormat])

  const handleFormatChange = (format: string) => {
    setSelectedFormat(format)
  }

  const handleSubmit = () => {
    if (selectedFormat) {
      onSubmit(selectedFormat)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-base font-medium text-gray-900">
          Select Date Format
        </h3>
        <p className="text-sm text-gray-500">
          Choose the date format used in your CSV file. Preview how dates will be parsed.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">
          Available Formats
        </h4>
        <div className="grid gap-2">
          {detection?.formats.map((formatOption) => (
            <label
              key={formatOption.format}
              className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                selectedFormat === formatOption.format
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 bg-white hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-3">
                <input
                  type="radio"
                  name="date-format"
                  value={formatOption.format}
                  checked={selectedFormat === formatOption.format}
                  onChange={() => handleFormatChange(formatOption.format)}
                  className="text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <span className="text-sm font-medium text-gray-900">
                    {formatOption.label}
                  </span>
                  <span className="ml-2 text-xs text-gray-500">
                    ({formatOption.format})
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {formatOption.recommended && (
                  <span className="text-xs px-2 py-0.5 bg-green-100 text-green-800 rounded-full">
                    Recommended
                  </span>
                )}
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    formatOption.success_rate >= 0.9
                      ? 'bg-green-100 text-green-800'
                      : formatOption.success_rate >= 0.5
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                  }`}
                >
                  {Math.round(formatOption.success_rate * 100)}% match
                </span>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Preview section */}
      {selectedFormat && (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-gray-900">
              Date Preview
            </h4>
            {previewLoading && <LoadingSpinner size="sm" />}
          </div>

          {preview && !previewLoading && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Success rate:</span>
                <span
                  className={`text-sm font-medium ${
                    preview.success_rate >= 0.9
                      ? 'text-green-600'
                      : preview.success_rate >= 0.5
                        ? 'text-yellow-600'
                        : 'text-red-600'
                  }`}
                >
                  {Math.round(preview.success_rate * 100)}%
                </span>
              </div>

              <div className="overflow-hidden rounded-lg border border-gray-200">
                <table className="min-w-full text-sm">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">
                        Original Value
                      </th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">
                        Parsed Date
                      </th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.samples.map((sample, index) => (
                      <tr
                        key={index}
                        className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                      >
                        <td className="px-3 py-2 text-gray-900 font-mono">
                          {sample.raw_value}
                        </td>
                        <td className="px-3 py-2 text-gray-900">
                          {sample.display_date || (
                            <span className="text-gray-400 italic">
                              Could not parse
                            </span>
                          )}
                        </td>
                        <td className="px-3 py-2">
                          {sample.valid ? (
                            <span className="inline-flex items-center gap-1 text-green-600">
                              <svg
                                className="w-4 h-4"
                                fill="currentColor"
                                viewBox="0 0 20 20"
                              >
                                <path
                                  fillRule="evenodd"
                                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                  clipRule="evenodd"
                                />
                              </svg>
                              Valid
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-red-600">
                              <svg
                                className="w-4 h-4"
                                fill="currentColor"
                                viewBox="0 0 20 20"
                              >
                                <path
                                  fillRule="evenodd"
                                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                                  clipRule="evenodd"
                                />
                              </svg>
                              {sample.error || 'Invalid'}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
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
          onClick={handleSubmit}
          disabled={!selectedFormat || loading}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {loading ? (
            <>
              <LoadingSpinner size="sm" />
              Validating...
            </>
          ) : (
            'Continue'
          )}
        </button>
      </div>
    </div>
  )
}
