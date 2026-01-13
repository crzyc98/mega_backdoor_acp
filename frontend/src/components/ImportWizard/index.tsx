/**
 * ImportWizard - Main container component for the CSV import wizard.
 * Manages wizard state, step navigation, and coordinates sub-components.
 */

import { useState, useCallback, useEffect } from 'react'
import WizardProgress from './WizardProgress'
import StepUpload from './StepUpload'
import StepMapping from './StepMapping'
import StepDateFormat from './StepDateFormat'
import StepValidation from './StepValidation'
import StepConfirm from './StepConfirm'
import importWizardService from '../../services/importWizardService'
import type {
  WizardStep,
  ImportSession,
  ImportSessionDetail,
  FilePreview,
  ColumnMappingSuggestion,
  DateFormatDetection,
  ValidationResult,
  PreviewRowList,
  MappingProfile,
  ImportResult,
} from '../../types/importWizard'

interface ImportWizardProps {
  workspaceId: string
  onComplete?: (result: ImportResult) => void
  onCancel?: () => void
}

export default function ImportWizard({
  workspaceId,
  onComplete,
  onCancel,
}: ImportWizardProps) {
  // Session state
  const [session, setSession] = useState<ImportSession | null>(null)
  const [sessionDetail, setSessionDetail] = useState<ImportSessionDetail | null>(null)

  // Step-specific data
  const [filePreview, setFilePreview] = useState<FilePreview | null>(null)
  const [mappingSuggestion, setMappingSuggestion] = useState<ColumnMappingSuggestion | null>(null)
  const [dateFormatDetection, setDateFormatDetection] = useState<DateFormatDetection | null>(null)
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null)
  const [previewRows, setPreviewRows] = useState<PreviewRowList | null>(null)
  const [profiles, setProfiles] = useState<MappingProfile[]>([])

  // UI state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessionExpired, setSessionExpired] = useState(false)

  // Current step derived from session
  const currentStep: WizardStep = session?.current_step || 'upload'

  // Load profiles on mount
  useEffect(() => {
    importWizardService.listProfiles(workspaceId)
      .then((result) => setProfiles(result.items))
      .catch(() => {
        // Profiles are optional, ignore errors
      })
  }, [workspaceId])

  // T048: Session expiration check
  useEffect(() => {
    if (!session?.expires_at) return

    const checkExpiration = () => {
      const expiresAt = new Date(session.expires_at)
      const now = new Date()
      if (now >= expiresAt) {
        setSessionExpired(true)
        setError('Your import session has expired. Please upload the file again.')
      }
    }

    // Check immediately
    checkExpiration()

    // Check every minute
    const interval = setInterval(checkExpiration, 60000)
    return () => clearInterval(interval)
  }, [session?.expires_at])

  // Handle file upload
  const handleFileUpload = useCallback(async (file: File) => {
    setLoading(true)
    setError(null)

    try {
      const newSession = await importWizardService.createSession(workspaceId, file)
      setSession(newSession)

      // Get file preview
      const preview = await importWizardService.getFilePreview(newSession.id)
      setFilePreview(preview)

      // Get mapping suggestions
      const suggestions = await importWizardService.suggestMapping(newSession.id)
      setMappingSuggestion(suggestions)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload file')
    } finally {
      setLoading(false)
    }
  }, [workspaceId])

  // Handle mapping submission
  const handleMappingSubmit = useCallback(async (mapping: Record<string, string>) => {
    if (!session) return

    setLoading(true)
    setError(null)

    try {
      const updatedSession = await importWizardService.setMapping(session.id, { mapping })
      setSession(updatedSession)

      // Get date format detection
      const detection = await importWizardService.detectDateFormat(session.id)
      setDateFormatDetection(detection)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save mapping')
    } finally {
      setLoading(false)
    }
  }, [session])

  // Handle date format selection
  const handleDateFormatSubmit = useCallback(async (format: string) => {
    if (!session) return

    setLoading(true)
    setError(null)

    try {
      const updatedSession = await importWizardService.setDateFormat(session.id, format)
      setSession(updatedSession)

      // Run validation
      const result = await importWizardService.runValidation(session.id)
      setValidationResult(result)

      // Get preview rows
      const rows = await importWizardService.getPreviewRows(session.id)
      setPreviewRows(rows)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set date format')
    } finally {
      setLoading(false)
    }
  }, [session])

  // Handle validation continue
  const handleValidationContinue = useCallback(async () => {
    if (!session) return

    setLoading(true)
    setError(null)

    try {
      // Refresh session detail
      const detail = await importWizardService.getSession(session.id)
      setSessionDetail(detail)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load session details')
    } finally {
      setLoading(false)
    }
  }, [session])

  // Handle import execution
  const handleImportExecute = useCallback(async (saveProfile: boolean, profileName?: string) => {
    if (!session) return

    setLoading(true)
    setError(null)

    try {
      const result = await importWizardService.executeImport(session.id, {
        save_profile: saveProfile,
        profile_name: profileName,
      })

      onComplete?.(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute import')
    } finally {
      setLoading(false)
    }
  }, [session, onComplete])

  // Handle cancel/back
  const handleCancel = useCallback(async () => {
    if (session) {
      try {
        await importWizardService.deleteSession(session.id)
      } catch {
        // Ignore delete errors
      }
    }
    onCancel?.()
  }, [session, onCancel])

  // Handle navigation to previous step
  const handleBack = useCallback(async (targetStep: WizardStep) => {
    // For now, just allow going back by updating local state
    // The server will re-validate when we re-submit
    if (session) {
      setSession({ ...session, current_step: targetStep })
    }
  }, [session])

  // Handle profile application (T043: Updated for MappingProfileSelector)
  const handleApplyProfile = useCallback(async (profile: MappingProfile) => {
    if (!session) return

    setLoading(true)
    setError(null)

    try {
      const result = await importWizardService.applyProfile(session.id, profile.id)

      // Refresh mapping suggestions with applied mappings
      if (mappingSuggestion) {
        setMappingSuggestion({
          ...mappingSuggestion,
          suggested_mapping: result.applied_mappings,
        })
      }

      // If profile has date format, store it
      if (profile.date_format) {
        setDateFormatDetection((prev) => prev ? {
          ...prev,
          recommended_format: profile.date_format || prev.recommended_format,
        } : prev)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply profile')
    } finally {
      setLoading(false)
    }
  }, [session, mappingSuggestion])

  // Render current step
  const renderStep = () => {
    switch (currentStep) {
      case 'upload':
        return (
          <StepUpload
            onFileSelect={handleFileUpload}
            filePreview={filePreview}
            loading={loading}
            error={error}
          />
        )

      case 'mapping':
        return (
          <StepMapping
            filePreview={filePreview}
            suggestion={mappingSuggestion}
            profiles={profiles}
            workspaceId={workspaceId}
            dateFormat={session?.date_format ?? undefined}
            onSubmit={handleMappingSubmit}
            onApplyProfile={handleApplyProfile}
            onBack={() => handleBack('upload')}
            loading={loading}
            error={error}
          />
        )

      case 'date_format':
        return (
          <StepDateFormat
            sessionId={session?.id || ''}
            detection={dateFormatDetection}
            onSubmit={handleDateFormatSubmit}
            onBack={() => handleBack('mapping')}
            loading={loading}
            error={error}
          />
        )

      case 'validation':
        return (
          <StepValidation
            sessionId={session?.id || ''}
            validationResult={validationResult}
            previewRows={previewRows}
            onContinue={handleValidationContinue}
            onBack={() => handleBack('date_format')}
            loading={loading}
            error={error}
          />
        )

      case 'preview':
        return (
          <StepConfirm
            session={session}
            sessionDetail={sessionDetail}
            validationResult={validationResult}
            onExecute={handleImportExecute}
            onBack={() => handleBack('validation')}
            loading={loading}
            error={error}
          />
        )

      case 'completed':
        return (
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-green-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">
              Import Complete
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              Your census data has been successfully imported.
            </p>
          </div>
        )

      default:
        return null
    }
  }

  // T048: Handle restart after session expiration
  const handleRestartSession = () => {
    setSession(null)
    setSessionDetail(null)
    setFilePreview(null)
    setMappingSuggestion(null)
    setDateFormatDetection(null)
    setValidationResult(null)
    setPreviewRows(null)
    setSessionExpired(false)
    setError(null)
  }

  // T048: Session expired dialog
  if (sessionExpired) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center py-8">
          <svg
            className="mx-auto h-12 w-12 text-yellow-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">
            Session Expired
          </h3>
          <p className="mt-2 text-sm text-gray-500">
            Your import session has expired. Please upload the file again to continue.
          </p>
          <button
            onClick={handleRestartSession}
            className="mt-6 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Start New Import
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">
          Import Census Data
        </h2>
        {currentStep !== 'completed' && (
          <button
            onClick={handleCancel}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Cancel
          </button>
        )}
      </div>

      <WizardProgress
        currentStep={currentStep}
        onStepClick={handleBack}
        allowNavigation={currentStep !== 'upload'}
      />

      {renderStep()}
    </div>
  )
}
