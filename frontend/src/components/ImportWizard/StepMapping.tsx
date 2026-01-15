/**
 * StepMapping - Column mapping step of the import wizard.
 * Allows users to map CSV columns to census fields with confidence indicators.
 * T043: Integrated MappingProfileSelector for saved profile management.
 */

import { useState, useEffect } from 'react'
import LoadingSpinner from '../LoadingSpinner'
import { MappingProfileSelector } from '../MappingProfileSelector'
import type {
  FilePreview,
  ColumnMappingSuggestion,
  MappingProfile,
} from '../../types/importWizard'

interface StepMappingProps {
  filePreview: FilePreview | null
  suggestion: ColumnMappingSuggestion | null
  profiles: MappingProfile[]
  workspaceId: string
  dateFormat?: string
  onSubmit: (mapping: Record<string, string>) => void
  onApplyProfile: (profile: MappingProfile) => void
  onBack: () => void
  loading: boolean
  error: string | null
}

// Field metadata for display
const FIELD_METADATA: Record<string, { label: string; required: boolean; description: string }> = {
  ssn: { label: 'SSN', required: true, description: 'Social Security Number (or hashed identifier)' },
  dob: { label: 'Date of Birth', required: false, description: 'Employee date of birth (for ACP eligibility)' },
  hire_date: { label: 'Hire Date', required: false, description: 'Employment start date (for ACP eligibility)' },
  termination_date: { label: 'Termination Date', required: false, description: 'Employment end date (for ACP eligibility)' },
  compensation: { label: 'Compensation', required: true, description: 'Annual compensation amount' },
  employee_pre_tax: { label: 'Pre-Tax Contributions', required: true, description: 'Employee 401(k) deferrals' },
  employee_after_tax: { label: 'After-Tax Contributions', required: true, description: 'Voluntary after-tax contributions' },
  employee_roth: { label: 'Roth Contributions', required: true, description: 'Roth 401(k) contributions' },
  employer_match: { label: 'Employer Match', required: true, description: 'Company matching contributions' },
  employer_non_elective: { label: 'Employer Non-Elective', required: true, description: 'Profit sharing or safe harbor' },
}

function getConfidenceColor(score: number): string {
  if (score >= 0.9) return 'text-green-600'
  if (score >= 0.6) return 'text-yellow-600'
  return 'text-red-600'
}

function getConfidenceBadge(score: number): string {
  if (score >= 0.9) return 'bg-green-100 text-green-800'
  if (score >= 0.6) return 'bg-yellow-100 text-yellow-800'
  return 'bg-red-100 text-red-800'
}

export default function StepMapping({
  filePreview,
  suggestion,
  profiles: _profiles, // eslint-disable-line @typescript-eslint/no-unused-vars
  workspaceId,
  dateFormat,
  onSubmit,
  onApplyProfile,
  onBack,
  loading,
  error,
}: StepMappingProps) {
  const [mapping, setMapping] = useState<Record<string, string>>({})

  // Initialize mapping from suggestion
  useEffect(() => {
    if (suggestion?.suggested_mapping) {
      setMapping(suggestion.suggested_mapping)
    }
  }, [suggestion])

  const handleFieldChange = (field: string, column: string) => {
    setMapping((prev) => ({
      ...prev,
      [field]: column,
    }))
  }

  const handleSubmit = () => {
    onSubmit(mapping)
  }

  const handleApplyProfile = (profile: MappingProfile) => {
    // Apply the profile's column mapping
    if (profile.column_mapping) {
      setMapping(profile.column_mapping)
    }
    onApplyProfile(profile)
  }

  // Get list of all possible columns (including unmapped option)
  const columns = filePreview?.headers || []
  const columnOptions = [
    { value: '', label: '-- Not mapped --' },
    ...columns.map((col) => ({ value: col, label: col })),
  ]

  // Show all fields from FIELD_METADATA, but only require the ones marked as required
  // or those returned by the API as required_fields
  const allFields = Object.keys(FIELD_METADATA)
  const apiRequiredFields = suggestion?.required_fields || []
  const requiredFieldsSet = new Set([
    ...apiRequiredFields,
    ...allFields.filter(f => FIELD_METADATA[f]?.required)
  ])
  const missingRequired = Array.from(requiredFieldsSet).filter((f) => !mapping[f])
  const canSubmit = missingRequired.length === 0

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-base font-medium text-gray-900">
          Map Columns
        </h3>
        <p className="text-sm text-gray-500">
          Match your CSV columns to the required census fields.
        </p>
      </div>

      {/* T043: MappingProfileSelector integration */}
      <MappingProfileSelector
        workspaceId={workspaceId}
        currentMapping={mapping}
        dateFormat={dateFormat}
        onApplyProfile={handleApplyProfile}
      />

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      <div className="bg-gray-50 rounded-lg p-4">
        <div className="grid gap-4">
          {allFields.map((field) => {
            const meta = FIELD_METADATA[field] || {
              label: field.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
              required: false,
              description: '',
            }
            const isRequired = requiredFieldsSet.has(field)
            const currentValue = mapping[field] || ''
            const confidence = suggestion?.confidence_scores?.[field]
            const isMissing = isRequired && !currentValue

            return (
              <div
                key={field}
                className={`flex items-center gap-4 p-3 rounded-lg ${
                  isMissing ? 'bg-red-50 border border-red-200' : 'bg-white border border-gray-200'
                }`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900">
                      {meta.label}
                    </span>
                    {isRequired && (
                      <span className="text-xs text-red-500">*</span>
                    )}
                    {confidence !== undefined && (
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${getConfidenceBadge(confidence)}`}
                      >
                        {Math.round(confidence * 100)}% match
                      </span>
                    )}
                  </div>
                  {meta.description && (
                    <p className="text-xs text-gray-500 mt-0.5">
                      {meta.description}
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <svg
                    className="w-4 h-4 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M14 5l7 7m0 0l-7 7m7-7H3"
                    />
                  </svg>

                  <select
                    value={currentValue}
                    onChange={(e) => handleFieldChange(field, e.target.value)}
                    className={`w-48 text-sm border rounded-md ${
                      isMissing
                        ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                        : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
                    }`}
                    disabled={loading}
                  >
                    {columnOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>

                  {confidence !== undefined && (
                    <span className={`text-xs ${getConfidenceColor(confidence)}`}>
                      {confidence >= 0.9 ? (
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      ) : confidence >= 0.6 ? (
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                      ) : null}
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {missingRequired.length > 0 && (
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <p className="text-sm text-yellow-800">
            <span className="font-medium">Missing required mappings:</span>{' '}
            {missingRequired.map((f) => FIELD_METADATA[f]?.label || f).join(', ')}
          </p>
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
          disabled={!canSubmit || loading}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {loading ? (
            <>
              <LoadingSpinner size="sm" />
              Processing...
            </>
          ) : (
            'Continue'
          )}
        </button>
      </div>
    </div>
  )
}
