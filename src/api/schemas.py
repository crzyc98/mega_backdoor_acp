"""
Pydantic Schemas for API Request/Response Models.

These schemas match the OpenAPI specification in contracts/openapi.yaml.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# HCE Mode type
HCEMode = Literal["explicit", "compensation_threshold"]


# Census Schemas
class CensusCreate(BaseModel):
    """Request model for census creation (form data fields)."""
    plan_year: int = Field(..., ge=2020, le=2100, description="Plan year for analysis")
    name: str = Field(..., max_length=255, description="Name for the census")
    client_name: str | None = Field(None, max_length=255, description="Optional client/organization name")
    hce_mode: HCEMode = Field("explicit", description="HCE determination method")
    column_mapping: str | None = Field(None, description="JSON string mapping source columns to target fields")


class CensusUpdateRequest(BaseModel):
    """Request model for updating census metadata."""
    name: str | None = Field(None, max_length=255, description="Updated census name")
    client_name: str | None = Field(None, max_length=255, description="Updated client name")


class CensusSummary(BaseModel):
    """Summary view of a census."""
    id: str
    name: str
    client_name: str | None = None
    plan_year: int
    hce_mode: HCEMode = "explicit"
    participant_count: int
    hce_count: int
    nhce_count: int
    upload_timestamp: datetime | None = None


class Census(CensusSummary):
    """Full census details."""
    upload_timestamp: datetime
    avg_compensation: float | None = None
    avg_deferral_rate: float | None = None
    version: str


class ImportMetadataResponse(BaseModel):
    """Response model for import metadata."""
    id: str
    census_id: str
    source_filename: str
    column_mapping: dict[str, str]
    row_count: int
    created_at: datetime


class CensusDetail(Census):
    """Census with import metadata and analysis info."""
    import_metadata: ImportMetadataResponse | None = None
    has_analyses: bool = False


class CensusListResponse(BaseModel):
    """Response model for census list endpoint."""
    items: list[CensusSummary]
    total: int
    limit: int
    offset: int


class ColumnMappingDetection(BaseModel):
    """Response model for column mapping detection."""
    source_columns: list[str]
    suggested_mapping: dict[str, str]
    required_fields: list[str]
    missing_fields: list[str]


class HCEThresholdsResponse(BaseModel):
    """Response model for HCE thresholds."""
    thresholds: dict[str, int]


class ParticipantResponse(BaseModel):
    """Response model for a participant."""
    id: str
    internal_id: str
    is_hce: bool
    compensation: float
    deferral_rate: float
    match_rate: float
    after_tax_rate: float


class ParticipantListResponse(BaseModel):
    """Response model for participant list endpoint."""
    items: list[ParticipantResponse]
    total: int
    limit: int
    offset: int


class CensusValidationErrorDetail(BaseModel):
    """Detail of a census validation error."""
    field: str | None = None
    message: str
    row: int | None = None


class CensusValidationError(BaseModel):
    """Response model for census validation errors."""
    detail: str
    errors: list[CensusValidationErrorDetail]


# Analysis Request Schemas
class SingleScenarioRequest(BaseModel):
    """Request model for single scenario analysis."""
    adoption_rate: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of HCEs adopting mega-backdoor (0-100)"
    )
    contribution_rate: float = Field(
        ...,
        ge=0,
        le=15,
        description="Mega-backdoor contribution rate as % of compensation (0-15)"
    )
    seed: int | None = Field(
        None,
        description="Random seed for HCE selection (auto-generated if omitted)"
    )


class GridScenarioRequest(BaseModel):
    """Request model for grid scenario analysis."""
    adoption_rates: list[float] = Field(
        ...,
        min_length=2,
        max_length=20,
        description="List of adoption rates to test (0-100)"
    )
    contribution_rates: list[float] = Field(
        ...,
        min_length=2,
        max_length=20,
        description="List of contribution rates to test (0-15)"
    )
    seed: int | None = Field(
        None,
        description="Random seed for HCE selection (shared across all scenarios)"
    )
    name: str | None = Field(
        None,
        max_length=255,
        description="Optional name for the grid analysis"
    )


# Analysis Result Schemas
class AnalysisResult(BaseModel):
    """Result of a single scenario analysis."""
    id: str
    census_id: str
    grid_analysis_id: str | None = None
    adoption_rate: float
    contribution_rate: float
    seed: int
    nhce_acp: float
    hce_acp: float
    threshold: float
    margin: float
    result: Literal["PASS", "FAIL"]
    limiting_test: Literal["1.25x", "+2.0"]
    run_timestamp: datetime
    version: str


class AnalysisResultListResponse(BaseModel):
    """Response model for analysis results list endpoint."""
    items: list[AnalysisResult]
    total: int


class GridSummary(BaseModel):
    """Summary statistics for a grid analysis."""
    total_scenarios: int
    pass_count: int
    fail_count: int
    pass_rate: float


class GridAnalysisResult(BaseModel):
    """Result of a grid scenario analysis."""
    id: str
    census_id: str
    name: str | None = None
    adoption_rates: list[float]
    contribution_rates: list[float]
    seed: int
    results: list[AnalysisResult]
    summary: GridSummary
    created_timestamp: datetime
    version: str


# Error Schemas
class ValidationErrorDetail(BaseModel):
    """Detail of a validation error."""
    loc: list[str]
    msg: str
    type: str


class ValidationError(BaseModel):
    """Response model for validation errors."""
    detail: list[ValidationErrorDetail]


class Error(BaseModel):
    """Response model for general errors."""
    error: str
    message: str


# Health Check Schema
class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = "healthy"
    version: str


# ============================================================================
# CSV Import Wizard Schemas (Feature 003-csv-import-wizard)
# ============================================================================

# Type aliases for wizard
WizardStep = Literal["upload", "map", "validate", "preview", "confirm", "completed"]
Severity = Literal["error", "warning", "info"]
DuplicateResolution = Literal["replace", "skip"]


# Import Session Schemas
class ImportSessionCreate(BaseModel):
    """Request model for creating an import session (file uploaded separately)."""
    pass  # File is uploaded via multipart/form-data


class ImportSession(BaseModel):
    """Response model for an import session."""
    id: str
    current_step: WizardStep
    created_at: datetime
    updated_at: datetime | None = None
    expires_at: datetime
    original_filename: str | None = None
    file_size_bytes: int | None = None
    row_count: int | None = None


class ImportSessionDetail(ImportSession):
    """Detailed import session with additional fields."""
    headers: list[str] | None = None
    column_mapping: dict[str, str] | None = None
    validation_summary: "ValidationSummary | None" = None
    duplicate_resolution: dict[str, DuplicateResolution] | None = None


class ImportSessionList(BaseModel):
    """Response model for listing import sessions."""
    items: list[ImportSession]
    total: int


# File Preview Schemas
class FilePreview(BaseModel):
    """Response model for CSV file preview."""
    headers: list[str]
    sample_rows: list[list[str]]
    total_rows: int
    detected_delimiter: str | None = None
    detected_encoding: str | None = None


# Column Mapping Schemas
class ColumnMappingSuggestion(BaseModel):
    """Response model for auto-suggested column mappings."""
    suggested_mapping: dict[str, str]
    required_fields: list[str]
    missing_fields: list[str]
    confidence_scores: dict[str, float]


class ColumnMappingRequest(BaseModel):
    """Request model for setting column mapping."""
    mapping: dict[str, str] = Field(
        ...,
        description="Map of target_field to source_column"
    )


# Validation Schemas
class ValidationSummary(BaseModel):
    """Summary of validation results."""
    total_rows: int
    error_count: int
    warning_count: int
    info_count: int
    valid_count: int


class ValidationResult(BaseModel):
    """Response model for validation run."""
    session_id: str
    summary: ValidationSummary
    completed_at: datetime
    duration_seconds: float | None = None


class ValidationIssue(BaseModel):
    """Individual validation issue."""
    id: str
    row_number: int
    field_name: str
    source_column: str | None = None
    severity: Severity
    issue_code: str
    message: str
    suggestion: str | None = None
    raw_value: str | None = None
    related_row: int | None = None


class ValidationIssueList(BaseModel):
    """Response model for listing validation issues."""
    items: list[ValidationIssue]
    total: int
    limit: int
    offset: int


# Import Preview Schemas
class ImportPreview(BaseModel):
    """Response model for pre-commit import preview."""
    total_rows: int
    import_count: int
    reject_count: int
    warning_count: int
    replace_count: int | None = None
    skip_count: int | None = None


class PreviewRow(BaseModel):
    """Individual row in import preview."""
    row_number: int
    status: Literal["import", "reject", "warning"]
    data: dict[str, str]
    issues: list[ValidationIssue] | None = None


class PreviewRowList(BaseModel):
    """Response model for listing preview rows."""
    items: list[PreviewRow]
    total: int
    limit: int
    offset: int


# Duplicate Resolution Schemas
class DuplicateResolutionRequest(BaseModel):
    """Request model for setting duplicate resolution."""
    resolutions: dict[str, DuplicateResolution] = Field(
        default_factory=dict,
        description="Map of SSN hash to resolution action"
    )
    apply_to_all: DuplicateResolution | None = Field(
        None,
        description="Apply same resolution to all duplicates"
    )


# Import Execution Schemas
class ImportExecuteRequest(BaseModel):
    """Request model for executing import."""
    census_name: str = Field(..., max_length=255)
    plan_year: int = Field(..., ge=2020, le=2100)
    client_name: str | None = Field(None, max_length=255)
    save_mapping_profile: bool = False
    mapping_profile_name: str | None = Field(None, max_length=255)


class ImportResultSummary(BaseModel):
    """Summary of import execution results."""
    total_rows: int
    imported_count: int
    rejected_count: int
    warning_count: int
    replaced_count: int
    skipped_count: int


class ImportResult(BaseModel):
    """Response model for import execution."""
    import_log_id: str
    census_id: str
    summary: ImportResultSummary
    completed_at: datetime
    duration_seconds: float | None = None


# Import Log Schemas
class ImportLog(BaseModel):
    """Response model for an import log."""
    id: str
    census_id: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    original_filename: str
    total_rows: int
    imported_count: int
    rejected_count: int
    warning_count: int
    replaced_count: int
    skipped_count: int


class ImportLogDetail(ImportLog):
    """Detailed import log with column mapping and results."""
    column_mapping_used: dict[str, str]
    detailed_results: list[PreviewRow] | None = None


class ImportLogList(BaseModel):
    """Response model for listing import logs."""
    items: list[ImportLog]
    total: int
    limit: int
    offset: int


# Mapping Profile Schemas
class MappingProfileCreate(BaseModel):
    """Request model for creating a mapping profile."""
    name: str = Field(..., max_length=255)
    description: str | None = None
    column_mapping: dict[str, str]
    expected_headers: list[str] | None = None


class MappingProfileUpdate(BaseModel):
    """Request model for updating a mapping profile."""
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    column_mapping: dict[str, str] | None = None


class MappingProfile(BaseModel):
    """Response model for a mapping profile."""
    id: str
    name: str
    description: str | None = None
    column_mapping: dict[str, str]
    expected_headers: list[str] | None = None
    created_at: datetime
    updated_at: datetime | None = None


class MappingProfileList(BaseModel):
    """Response model for listing mapping profiles."""
    items: list[MappingProfile]
    total: int


class ProfileApplyResult(BaseModel):
    """Response model for applying a mapping profile."""
    session_id: str
    profile_id: str
    applied_mappings: dict[str, str]
    unmatched_fields: list[str]
    success: bool
