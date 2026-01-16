/**
 * Import Wizard API service client.
 * Provides methods for all import wizard endpoints.
 */

import api from './api'
import type {
  ImportSession,
  ImportSessionDetail,
  FilePreview,
  ColumnMappingSuggestion,
  ColumnMappingRequest,
  DateFormatDetection,
  DateFormatPreview,
  ValidationResult,
  ValidationIssueList,
  ValidationSeverity,
  PreviewRowList,
  RowStatus,
  ImportExecuteRequest,
  ImportResult,
  MappingProfile,
  MappingProfileList,
  MappingProfileCreate,
  MappingProfileUpdate,
  ProfileApplyResult,
} from '../types/importWizard'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ============================================================================
// Session Management
// ============================================================================

/**
 * Create a new import session by uploading a CSV or XLSX file.
 */
async function createSession(
  workspaceId: string,
  file: File
): Promise<ImportSession> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(
    `${API_BASE}/api/workspaces/${workspaceId}/import/sessions`,
    {
      method: 'POST',
      body: formData,
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
    throw new Error(error.detail || `Upload failed: ${response.status}`)
  }

  return response.json()
}

/**
 * Get import session details.
 */
async function getSession(workspaceId: string, sessionId: string): Promise<ImportSessionDetail> {
  return api.get<ImportSessionDetail>(`/api/import/sessions/${sessionId}`, {
    headers: { 'X-Workspace-ID': workspaceId },
  })
}

/**
 * Delete/cancel an import session.
 */
async function deleteSession(workspaceId: string, sessionId: string): Promise<void> {
  return api.delete(`/api/import/sessions/${sessionId}`, {
    headers: { 'X-Workspace-ID': workspaceId },
  })
}

// ============================================================================
// File Preview
// ============================================================================

/**
 * Get file preview with headers and sample rows.
 */
async function getFilePreview(workspaceId: string, sessionId: string): Promise<FilePreview> {
  return api.get<FilePreview>(`/api/import/sessions/${sessionId}/preview`, {
    headers: { 'X-Workspace-ID': workspaceId },
  })
}

// ============================================================================
// Column Mapping
// ============================================================================

/**
 * Get auto-suggested column mappings with confidence scores.
 */
async function suggestMapping(workspaceId: string, sessionId: string): Promise<ColumnMappingSuggestion> {
  return api.get<ColumnMappingSuggestion>(
    `/api/import/sessions/${sessionId}/mapping/suggest`,
    { headers: { 'X-Workspace-ID': workspaceId } }
  )
}

/**
 * Set column mapping for the session.
 */
async function setMapping(
  workspaceId: string,
  sessionId: string,
  request: ColumnMappingRequest
): Promise<ImportSession> {
  return api.put<ImportSession>(
    `/api/import/sessions/${sessionId}/mapping`,
    request,
    { headers: { 'X-Workspace-ID': workspaceId } }
  )
}

// ============================================================================
// Date Format
// ============================================================================

/**
 * Auto-detect date format from sample data.
 */
async function detectDateFormat(workspaceId: string, sessionId: string): Promise<DateFormatDetection> {
  return api.get<DateFormatDetection>(
    `/api/import/sessions/${sessionId}/date-format/detect`,
    { headers: { 'X-Workspace-ID': workspaceId } }
  )
}

/**
 * Preview date parsing with a specific format.
 */
async function previewDateFormat(
  workspaceId: string,
  sessionId: string,
  format: string
): Promise<DateFormatPreview> {
  const encodedFormat = encodeURIComponent(format)
  return api.get<DateFormatPreview>(
    `/api/import/sessions/${sessionId}/date-format/preview?format=${encodedFormat}`,
    { headers: { 'X-Workspace-ID': workspaceId } }
  )
}

/**
 * Set date format for the session.
 */
async function setDateFormat(
  workspaceId: string,
  sessionId: string,
  dateFormat: string
): Promise<ImportSession> {
  return api.put<ImportSession>(
    `/api/import/sessions/${sessionId}/date-format`,
    { date_format: dateFormat },
    { headers: { 'X-Workspace-ID': workspaceId } }
  )
}

// ============================================================================
// Validation
// ============================================================================

/**
 * Run full validation on mapped data.
 */
async function runValidation(workspaceId: string, sessionId: string): Promise<ValidationResult> {
  return api.post<ValidationResult>(
    `/api/import/sessions/${sessionId}/validate`,
    undefined,
    { headers: { 'X-Workspace-ID': workspaceId } }
  )
}

/**
 * Get validation issues with optional filtering.
 */
async function getValidationIssues(
  workspaceId: string,
  sessionId: string,
  options: {
    severity?: ValidationSeverity
    limit?: number
    offset?: number
  } = {}
): Promise<ValidationIssueList> {
  const params = new URLSearchParams()
  if (options.severity) params.append('severity', options.severity)
  if (options.limit !== undefined) params.append('limit', options.limit.toString())
  if (options.offset !== undefined) params.append('offset', options.offset.toString())

  const query = params.toString()
  const url = `/api/import/sessions/${sessionId}/validation-issues${query ? `?${query}` : ''}`
  return api.get<ValidationIssueList>(url, {
    headers: { 'X-Workspace-ID': workspaceId },
  })
}

/**
 * Get preview rows with validation status.
 */
async function getPreviewRows(
  workspaceId: string,
  sessionId: string,
  options: {
    status?: RowStatus
    limit?: number
    offset?: number
  } = {}
): Promise<PreviewRowList> {
  const params = new URLSearchParams()
  if (options.status) params.append('status', options.status)
  if (options.limit !== undefined) params.append('limit', options.limit.toString())
  if (options.offset !== undefined) params.append('offset', options.offset.toString())

  const query = params.toString()
  const url = `/api/import/sessions/${sessionId}/preview-rows${query ? `?${query}` : ''}`
  return api.get<PreviewRowList>(url, {
    headers: { 'X-Workspace-ID': workspaceId },
  })
}

// ============================================================================
// Import Execution
// ============================================================================

/**
 * Execute the import and create census records.
 */
async function executeImport(
  workspaceId: string,
  sessionId: string,
  request: ImportExecuteRequest
): Promise<ImportResult> {
  return api.post<ImportResult>(
    `/api/import/sessions/${sessionId}/execute`,
    request,
    { headers: { 'X-Workspace-ID': workspaceId } }
  )
}

// ============================================================================
// Mapping Profiles
// ============================================================================

/**
 * List mapping profiles for a workspace.
 */
async function listProfiles(workspaceId: string): Promise<MappingProfileList> {
  return api.get<MappingProfileList>(
    `/api/workspaces/${workspaceId}/import/mapping-profiles`
  )
}

/**
 * Create a new mapping profile for a workspace.
 */
async function createProfile(
  workspaceId: string,
  request: MappingProfileCreate
): Promise<MappingProfile> {
  return api.post<MappingProfile>(
    `/api/workspaces/${workspaceId}/import/mapping-profiles`,
    request
  )
}

/**
 * Update a mapping profile.
 */
async function updateProfile(
  workspaceId: string,
  profileId: string,
  request: MappingProfileUpdate
): Promise<MappingProfile> {
  return api.put<MappingProfile>(
    `/api/workspaces/${workspaceId}/import/mapping-profiles/${profileId}`,
    request
  )
}

/**
 * Delete a mapping profile.
 */
async function deleteProfile(
  workspaceId: string,
  profileId: string
): Promise<void> {
  return api.delete(
    `/api/workspaces/${workspaceId}/import/mapping-profiles/${profileId}`
  )
}

/**
 * Apply a mapping profile to a session.
 */
async function applyProfile(
  workspaceId: string,
  sessionId: string,
  profileId: string
): Promise<ProfileApplyResult> {
  return api.post<ProfileApplyResult>(
    `/api/import/sessions/${sessionId}/apply-profile`,
    { profile_id: profileId },
    { headers: { 'X-Workspace-ID': workspaceId } }
  )
}

// ============================================================================
// Export Service
// ============================================================================

const importWizardService = {
  // Session management
  createSession,
  getSession,
  deleteSession,

  // File preview
  getFilePreview,

  // Column mapping
  suggestMapping,
  setMapping,

  // Date format
  detectDateFormat,
  previewDateFormat,
  setDateFormat,

  // Validation
  runValidation,
  getValidationIssues,
  getPreviewRows,

  // Import execution
  executeImport,

  // Mapping profiles
  listProfiles,
  createProfile,
  updateProfile,
  deleteProfile,
  applyProfile,
}

export default importWizardService

// Named exports for direct imports
export {
  createSession,
  getSession,
  deleteSession,
  getFilePreview,
  suggestMapping,
  setMapping,
  detectDateFormat,
  previewDateFormat,
  setDateFormat,
  runValidation,
  getValidationIssues,
  getPreviewRows,
  executeImport,
  listProfiles as listMappingProfiles,
  createProfile as createMappingProfile,
  updateProfile as updateMappingProfile,
  deleteProfile as deleteMappingProfile,
  applyProfile as applyMappingProfile,
}
