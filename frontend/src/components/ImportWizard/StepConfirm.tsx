/**
 * StepConfirm - Final confirmation step of the import wizard.
 * Shows import summary and allows execution with optional profile saving.
 */

import { useState } from 'react'
import LoadingSpinner from '../LoadingSpinner'
import type {
  ImportSession,
  ImportSessionDetail,
  ValidationResult,
} from '../../types/importWizard'

interface StepConfirmProps {
  session: ImportSession | null
  sessionDetail: ImportSessionDetail | null
  validationResult: ValidationResult | null
  onExecute: (censusName: string, planYear: number, saveProfile: boolean, profileName?: string) => void
  onBack: () => void
  loading: boolean
  error: string | null
}

export default function StepConfirm({
  session,
  sessionDetail,
  validationResult,
  onExecute,
  onBack,
  loading,
  error,
}: StepConfirmProps) {
  const [censusName, setCensusName] = useState('')
  const [planYear, setPlanYear] = useState(new Date().getFullYear())
  const [saveProfile, setSaveProfile] = useState(false)
  const [profileName, setProfileName] = useState('')

  const summary = validationResult?.summary || sessionDetail?.validation_summary

  const handleExecute = () => {
    onExecute(censusName, planYear, saveProfile, saveProfile ? profileName : undefined)
  }

  const canExecute = summary
    ? summary.error_count === 0 &&
      censusName.trim().length > 0 &&
      planYear >= 2020 && planYear <= 2100 &&
      (!saveProfile || profileName.trim().length > 0)
    : false

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-base font-medium text-gray-900">
          Confirm Import
        </h3>
        <p className="text-sm text-gray-500">
          Review the import summary and click Import to create census records.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Census details */}
      <div className="bg-gray-50 rounded-lg p-4 space-y-4">
        <h4 className="text-sm font-medium text-gray-900">Census Details</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="census-name" className="block text-sm text-gray-700 mb-1">
              Census Name <span className="text-red-500">*</span>
            </label>
            <input
              id="census-name"
              type="text"
              value={censusName}
              onChange={(e) => setCensusName(e.target.value)}
              placeholder="e.g., Q4 2025 Census"
              className={`w-full px-3 py-2 text-sm border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                censusName.trim().length === 0 ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {censusName.trim().length === 0 && (
              <p className="mt-1 text-xs text-red-500">Census name is required</p>
            )}
          </div>
          <div>
            <label htmlFor="plan-year" className="block text-sm text-gray-700 mb-1">
              Plan Year <span className="text-red-500">*</span>
            </label>
            <input
              id="plan-year"
              type="number"
              value={planYear}
              onChange={(e) => setPlanYear(parseInt(e.target.value) || 2020)}
              min={2020}
              max={2100}
              className={`w-full px-3 py-2 text-sm border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                planYear < 2020 || planYear > 2100 ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {(planYear < 2020 || planYear > 2100) && (
              <p className="mt-1 text-xs text-red-500">Year must be between 2020 and 2100</p>
            )}
          </div>
        </div>
      </div>

      {/* Import summary */}
      <div className="bg-gray-50 rounded-lg p-4 space-y-4">
        <h4 className="text-sm font-medium text-gray-900">Import Summary</h4>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">File:</span>
            <span className="ml-2 font-medium text-gray-900">
              {session?.original_filename || 'Unknown'}
            </span>
          </div>
          <div>
            <span className="text-gray-500">Total Rows:</span>
            <span className="ml-2 font-medium text-gray-900">
              {summary?.total_rows?.toLocaleString() || session?.row_count?.toLocaleString() || '0'}
            </span>
          </div>
        </div>

        {summary && (
          <div className="grid grid-cols-4 gap-4 pt-4 border-t border-gray-200">
            <div className="text-center">
              <div className="text-xl font-bold text-green-600">
                {summary.valid_count.toLocaleString()}
              </div>
              <div className="text-xs text-gray-500">Ready to Import</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-yellow-600">
                {summary.warning_count.toLocaleString()}
              </div>
              <div className="text-xs text-gray-500">With Warnings</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-red-600">
                {summary.error_count.toLocaleString()}
              </div>
              <div className="text-xs text-gray-500">Rejected</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-gray-900">
                {summary.total_rows.toLocaleString()}
              </div>
              <div className="text-xs text-gray-500">Total</div>
            </div>
          </div>
        )}
      </div>

      {/* Column mapping summary */}
      {sessionDetail?.column_mapping && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">
            Column Mapping
          </h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(sessionDetail.column_mapping).map(([field, column]) => (
              <div key={field} className="flex items-center gap-2">
                <span className="text-gray-500">{field}:</span>
                <span className="font-medium text-gray-900">{column}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Date format */}
      {sessionDetail?.date_format && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">
            Date Format
          </h4>
          <code className="text-sm text-gray-700 bg-gray-100 px-2 py-1 rounded">
            {sessionDetail.date_format}
          </code>
        </div>
      )}

      {/* Save profile option */}
      <div className="bg-gray-50 rounded-lg p-4">
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={saveProfile}
            onChange={(e) => setSaveProfile(e.target.checked)}
            className="mt-0.5 text-blue-600 focus:ring-blue-500 rounded"
          />
          <div>
            <span className="text-sm font-medium text-gray-900">
              Save mapping as profile
            </span>
            <p className="text-xs text-gray-500 mt-0.5">
              Save this column mapping configuration for future imports
            </p>
          </div>
        </label>

        {saveProfile && (
          <div className="mt-4 ml-7">
            <label htmlFor="profile-name" className="block text-sm text-gray-700 mb-1">
              Profile Name <span className="text-red-500">*</span>
            </label>
            <input
              id="profile-name"
              type="text"
              value={profileName}
              onChange={(e) => setProfileName(e.target.value)}
              placeholder="e.g., HR Export Format"
              className={`w-full px-3 py-2 text-sm border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                profileName.trim().length === 0 ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {profileName.trim().length === 0 && (
              <p className="mt-1 text-xs text-red-500">
                Enter a profile name to save, or uncheck the box to import without saving.
              </p>
            )}
          </div>
        )}
      </div>

      {/* Warning about warnings */}
      {summary && summary.warning_count > 0 && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex items-start gap-3">
            <svg
              className="w-5 h-5 text-yellow-500 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <h4 className="text-sm font-medium text-yellow-800">
                Rows with warnings will be imported
              </h4>
              <p className="mt-1 text-sm text-yellow-700">
                {summary.warning_count} row{summary.warning_count !== 1 ? 's have' : ' has'} warnings
                but will still be imported. Review the warnings to ensure data quality.
              </p>
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
          onClick={handleExecute}
          disabled={!canExecute || loading}
          className="px-6 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {loading ? (
            <>
              <LoadingSpinner size="sm" />
              Importing...
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
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                />
              </svg>
              Import Census Data
            </>
          )}
        </button>
      </div>
    </div>
  )
}
