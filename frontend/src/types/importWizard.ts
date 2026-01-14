/**
 * TypeScript interfaces for the CSV Import Wizard feature.
 * Based on OpenAPI spec: specs/009-csv-upload-wizard/contracts/openapi.yaml
 */

// ============================================================================
// Enums and Type Aliases
// ============================================================================

export type WizardStep =
  | 'upload'
  | 'mapping'
  | 'date_format'
  | 'validation'
  | 'preview'
  | 'completed'

export type ValidationSeverity = 'error' | 'warning' | 'info'

export type RowStatus = 'valid' | 'warning' | 'error'

// ============================================================================
// Import Session Types
// ============================================================================

export interface ImportSession {
  id: string
  workspace_id: string
  current_step: WizardStep
  created_at: string
  updated_at: string | null
  expires_at: string
  original_filename: string | null
  file_size_bytes: number | null
  row_count: number | null
  date_format: string | null  // T004: Date format for parsing
}

export interface ImportSessionDetail extends ImportSession {
  headers: string[] | null
  column_mapping: Record<string, string> | null
  date_format: string | null
  validation_summary: ValidationSummary | null
}

// ============================================================================
// File Preview Types
// ============================================================================

export interface FilePreview {
  headers: string[]
  sample_rows: string[][]
  total_rows: number
  detected_delimiter: string
  detected_encoding: string
}

// ============================================================================
// Column Mapping Types
// ============================================================================

export interface ColumnMappingSuggestion {
  suggested_mapping: Record<string, string>
  required_fields: string[]
  missing_fields: string[]
  confidence_scores: Record<string, number>
}

export interface ColumnMappingRequest {
  mapping: Record<string, string>
}

// ============================================================================
// Date Format Types
// ============================================================================

export interface DateFormatOption {
  format: string
  label: string
  success_rate: number
  recommended: boolean
}

export interface DateFormatDetection {
  recommended_format: string
  formats: DateFormatOption[]
}

export interface DateSample {
  raw_value: string
  parsed_date: string | null
  display_date: string | null
  valid: boolean
  error: string | null
}

export interface DateFormatPreview {
  format: string
  format_label: string
  samples: DateSample[]
  success_rate: number
}

// ============================================================================
// Validation Types
// ============================================================================

export interface ValidationSummary {
  total_rows: number
  valid_count: number
  warning_count: number
  error_count: number
  info_count: number
}

export interface ValidationIssue {
  id: string
  row_number: number
  field_name: string
  source_column: string | null
  severity: ValidationSeverity
  issue_code: string
  message: string
  suggestion: string | null
  raw_value: string | null
  related_row: number | null
}

export interface ValidationIssueList {
  items: ValidationIssue[]
  total: number
  limit: number
  offset: number
}

export interface ValidationResult {
  session_id: string
  summary: ValidationSummary
  completed_at: string
  duration_seconds: number
}

// ============================================================================
// Preview Row Types
// ============================================================================

export interface PreviewRow {
  row_number: number
  status: RowStatus
  original_values: Record<string, string>
  mapped_values: Record<string, unknown>
  parsed_dates: Record<string, DateSample>
  issues: ValidationIssue[]
}

export interface PreviewRowList {
  items: PreviewRow[]
  total: number
  valid_count: number
  warning_count: number
  error_count: number
  limit: number
  offset: number
}

// ============================================================================
// Import Execution Types
// ============================================================================

export interface ImportExecuteRequest {
  census_name: string
  plan_year: number
  client_name?: string
  save_mapping_profile?: boolean
  mapping_profile_name?: string
}

export interface ImportResultSummary {
  total_rows: number
  imported_count: number
  rejected_count: number
  warning_count: number
  replaced_count?: number
  skipped_count?: number
}

export interface ImportResult {
  import_log_id: string
  census_id: string
  summary: ImportResultSummary
  completed_at: string
  duration_seconds: number
}

// ============================================================================
// Mapping Profile Types
// ============================================================================

export interface MappingProfile {
  id: string
  workspace_id: string
  name: string
  description: string | null
  column_mapping: Record<string, string>
  date_format: string | null
  expected_headers: string[] | null
  is_default: boolean
  created_at: string
  updated_at: string | null
}

export interface MappingProfileList {
  items: MappingProfile[]
  total: number
}

export interface MappingProfileCreate {
  name: string
  description?: string
  column_mapping: Record<string, string>
  date_format?: string
  expected_headers?: string[]
  is_default?: boolean
}

export interface MappingProfileUpdate {
  name?: string
  description?: string
  column_mapping?: Record<string, string>
  date_format?: string
  is_default?: boolean
}

export interface ProfileApplyResult {
  session_id: string
  profile_id: string
  applied_mappings: Record<string, string>
  unmatched_fields: string[]
  success: boolean
}

// ============================================================================
// Wizard State Types (Frontend-specific)
// ============================================================================

export interface WizardState {
  session: ImportSession | null
  sessionDetail: ImportSessionDetail | null
  filePreview: FilePreview | null
  mappingSuggestion: ColumnMappingSuggestion | null
  dateFormatDetection: DateFormatDetection | null
  validationResult: ValidationResult | null
  previewRows: PreviewRowList | null
  profiles: MappingProfile[]
  loading: boolean
  error: string | null
}

export type WizardAction =
  | { type: 'SET_SESSION'; payload: ImportSession }
  | { type: 'SET_SESSION_DETAIL'; payload: ImportSessionDetail }
  | { type: 'SET_FILE_PREVIEW'; payload: FilePreview }
  | { type: 'SET_MAPPING_SUGGESTION'; payload: ColumnMappingSuggestion }
  | { type: 'SET_DATE_FORMAT_DETECTION'; payload: DateFormatDetection }
  | { type: 'SET_VALIDATION_RESULT'; payload: ValidationResult }
  | { type: 'SET_PREVIEW_ROWS'; payload: PreviewRowList }
  | { type: 'SET_PROFILES'; payload: MappingProfile[] }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'RESET' }
