/**
 * StepUpload - File upload step of the import wizard.
 * Provides a file dropzone and displays file preview information.
 */

import FileDropzone from '../FileDropzone'
import LoadingSpinner from '../LoadingSpinner'
import type { FilePreview } from '../../types/importWizard'

interface StepUploadProps {
  onFileSelect: (file: File) => void
  filePreview: FilePreview | null
  loading: boolean
  error: string | null
}

export default function StepUpload({
  onFileSelect,
  filePreview,
  loading,
  error,
}: StepUploadProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-base font-medium text-gray-900 mb-2">
          Upload CSV File
        </h3>
        <p className="text-sm text-gray-500 mb-4">
          Select a CSV file containing your census data. Maximum file size: 50MB.
        </p>

        <FileDropzone
          onFileSelect={onFileSelect}
          disabled={loading}
        />
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-sm text-gray-500">Processing file...</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="flex">
            <svg
              className="h-5 w-5 text-red-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Upload Error</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {filePreview && !loading && (
        <div className="space-y-4">
          {/* T046: Warning for empty or headers-only files */}
          {filePreview.total_rows === 0 && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
              <div className="flex">
                <svg
                  className="h-5 w-5 text-yellow-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-yellow-800">Empty File</h3>
                  <p className="mt-1 text-sm text-yellow-700">
                    This file contains only headers with no data rows. Please upload a file with census data.
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">
              File Preview
            </h4>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Rows:</span>
                <span className="ml-2 font-medium text-gray-900">
                  {filePreview.total_rows.toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Delimiter:</span>
                <span className="ml-2 font-medium text-gray-900">
                  {filePreview.detected_delimiter === ',' ? 'Comma' :
                   filePreview.detected_delimiter === '\t' ? 'Tab' :
                   filePreview.detected_delimiter === ';' ? 'Semicolon' :
                   filePreview.detected_delimiter}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Encoding:</span>
                <span className="ml-2 font-medium text-gray-900">
                  {filePreview.detected_encoding}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">
              Detected Columns ({filePreview.headers.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {filePreview.headers.map((header) => (
                <span
                  key={header}
                  className="px-2 py-1 bg-white border border-gray-200 rounded text-xs text-gray-700"
                >
                  {header}
                </span>
              ))}
            </div>
          </div>

          {filePreview.sample_rows.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4 overflow-hidden">
              <h4 className="text-sm font-medium text-gray-900 mb-3">
                Sample Data (First {filePreview.sample_rows.length} rows)
              </h4>
              <div className="overflow-x-auto">
                <table className="min-w-full text-xs">
                  <thead>
                    <tr className="bg-gray-100">
                      {filePreview.headers.map((header) => (
                        <th
                          key={header}
                          className="px-3 py-2 text-left font-medium text-gray-600 whitespace-nowrap"
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filePreview.sample_rows.slice(0, 5).map((row, rowIndex) => (
                      <tr
                        key={rowIndex}
                        className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                      >
                        {row.map((cell, cellIndex) => (
                          <td
                            key={cellIndex}
                            className="px-3 py-2 text-gray-900 whitespace-nowrap max-w-[200px] truncate"
                            title={cell}
                          >
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
