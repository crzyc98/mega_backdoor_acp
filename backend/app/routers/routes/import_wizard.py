"""
Import Wizard API Routes.

Provides endpoints for the CSV import wizard workflow including:
- Session management
- File upload and preview
- Column mapping suggestions
- Validation
- Duplicate resolution
- Import execution
- Mapping profiles
- Import logs
"""

from __future__ import annotations

import io
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile

from app.models.census import CensusSummary as CensusSummaryModel
from app.storage.workspace_storage import get_workspace_storage

from app.routers.schemas import (
    ColumnMappingRequest,
    ColumnMappingSuggestion,
    DateFormatDetectionResponse,
    DateFormatOptionResponse,
    DateFormatPreviewResponse,
    DateFormatRequest,
    DateSampleResponse,
    DuplicateResolutionRequest,
    FilePreview,
    ImportExecuteRequest,
    ImportLog as ImportLogSchema,
    ImportLogDetail,
    ImportLogList,
    ImportPreview,
    ImportResult,
    ImportSession as ImportSessionSchema,
    ImportSessionDetail,
    ImportSessionList,
    MappingProfile as MappingProfileSchema,
    MappingProfileCreate,
    MappingProfileList,
    MappingProfileUpdate,
    ProfileApplyResult,
    PreviewRow,
    PreviewRowList,
    ValidationIssue as ValidationIssueSchema,
    ValidationIssueList,
    ValidationResult,
    ValidationSummary,
)
from app.services.field_mappings import REQUIRED_FIELDS, suggest_mapping, validate_mapping
from app.services.import_wizard import (
    create_session,
    detect_in_file_duplicates,
    is_session_expired,
    parse_csv_file,
    parse_csv_preview,
    validate_file,
)
from app.services.date_parser import (
    detect_date_format,
    get_date_column_values,
    preview_date_format,
)
from app.storage.database import get_db
from app.storage.models import ImportSession, MappingProfile, ImportLog
from app.storage.repository import (
    ImportSessionRepository,
    MappingProfileRepository,
    ValidationIssueRepository,
    ImportLogRepository,
)


router = APIRouter(prefix="/import", tags=["Import Wizard"])

# Workspace-scoped router for session creation
workspace_router = APIRouter(tags=["Import Wizard"])

# Maximum file size (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# Temp directory for uploaded files
UPLOAD_DIR = Path(tempfile.gettempdir()) / "acp_imports"


def get_workspace_id_from_header(
    x_workspace_id: str = Header(..., alias="X-Workspace-ID")
) -> str:
    """Extract workspace ID from request header."""
    return x_workspace_id


def get_session_repo(
    workspace_id: str = Depends(get_workspace_id_from_header),
) -> ImportSessionRepository:
    """Dependency for ImportSessionRepository."""
    conn = get_db(workspace_id)
    return ImportSessionRepository(conn)


def get_profile_repo(
    workspace_id: str = Depends(get_workspace_id_from_header),
) -> MappingProfileRepository:
    """Dependency for MappingProfileRepository."""
    conn = get_db(workspace_id)
    return MappingProfileRepository(conn)


def get_issue_repo(
    workspace_id: str = Depends(get_workspace_id_from_header),
) -> ValidationIssueRepository:
    """Dependency for ValidationIssueRepository."""
    conn = get_db(workspace_id)
    return ValidationIssueRepository(conn)


def get_log_repo(
    workspace_id: str = Depends(get_workspace_id_from_header),
) -> ImportLogRepository:
    """Dependency for ImportLogRepository."""
    conn = get_db(workspace_id)
    return ImportLogRepository(conn)


def ensure_upload_dir():
    """Ensure upload directory exists."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_session_or_404(
    session_id: str,
    repo: ImportSessionRepository,
) -> ImportSession:
    """Get session or raise 404."""
    session = repo.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Import session not found")
    if is_session_expired(session):
        raise HTTPException(status_code=410, detail="Import session has expired")
    return session


# ============================================================================
# Import Session Endpoints
# ============================================================================


@router.post("/sessions", status_code=201, response_model=ImportSessionSchema)
async def create_import_session(
    file: UploadFile = File(...),
    workspace_id: str = Depends(get_workspace_id_from_header),
    repo: ImportSessionRepository = Depends(get_session_repo),
) -> ImportSessionSchema:
    """
    Create a new import session with uploaded CSV file.

    Accepts a CSV file upload and creates a new wizard session.
    Returns session details with file preview information.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith((".csv", ".xlsx")):
        raise HTTPException(status_code=400, detail="File must be a CSV or XLSX")

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds 50MB limit"
        )

    # Parse file preview
    try:
        headers, sample_rows, total_rows, delimiter, encoding = parse_csv_preview(
            content,
            filename=file.filename,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    # Create session
    session = create_session(
        original_filename=file.filename,
        file_size_bytes=file_size,
    )
    session.headers = headers
    session.row_count = total_rows
    session.workspace_id = workspace_id  # CRITICAL: Set workspace_id for census storage

    # Save file to temp directory
    ensure_upload_dir()
    ext = Path(file.filename).suffix.lower() if file.filename else ".csv"
    file_path = UPLOAD_DIR / f"{session.id}{ext}"
    with open(file_path, "wb") as f:
        f.write(content)
    session.file_reference = str(file_path)

    # Save session
    repo.save(session)

    return ImportSessionSchema(
        id=session.id,
        current_step=session.current_step,
        created_at=session.created_at,
        updated_at=session.updated_at,
        expires_at=session.expires_at,
        original_filename=session.original_filename,
        file_size_bytes=session.file_size_bytes,
        row_count=session.row_count,
    )


# T009: Workspace-scoped session creation endpoint
@workspace_router.post(
    "/workspaces/{workspace_id}/import/sessions",
    status_code=201,
    response_model=ImportSessionSchema,
)
async def create_workspace_import_session(
    workspace_id: str,
    file: UploadFile = File(...),
) -> ImportSessionSchema:
    """
    Create a new import session for a specific workspace.

    T009: Workspace-scoped session creation with workspace_id association.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith((".csv", ".xlsx")):
        raise HTTPException(status_code=400, detail="File must be a CSV or XLSX")

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds 50MB limit"
        )

    # Check for empty file or headers-only
    if file_size == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Parse file preview
    try:
        headers, sample_rows, total_rows, delimiter, encoding = parse_csv_preview(
            content,
            filename=file.filename,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    # Check for headers-only file
    if total_rows == 0:
        raise HTTPException(status_code=400, detail="File contains only headers, no data rows")

    # Get database connection using path workspace_id
    conn = get_db(workspace_id)
    repo = ImportSessionRepository(conn)

    # Create session with workspace association
    session = create_session(
        original_filename=file.filename,
        file_size_bytes=file_size,
    )
    session.workspace_id = workspace_id
    session.headers = headers
    session.row_count = total_rows

    # Save file to temp directory
    ensure_upload_dir()
    ext = Path(file.filename).suffix.lower() if file.filename else ".csv"
    file_path = UPLOAD_DIR / f"{session.id}{ext}"
    with open(file_path, "wb") as f:
        f.write(content)
    session.file_reference = str(file_path)

    # Save session
    repo.save(session)

    return ImportSessionSchema(
        id=session.id,
        current_step=session.current_step,
        created_at=session.created_at,
        updated_at=session.updated_at,
        expires_at=session.expires_at,
        original_filename=session.original_filename,
        file_size_bytes=session.file_size_bytes,
        row_count=session.row_count,
    )


@router.get("/sessions/{session_id}", response_model=ImportSessionDetail)
async def get_import_session(
    session_id: str,
    repo: ImportSessionRepository = Depends(get_session_repo),
    issue_repo: ValidationIssueRepository = Depends(get_issue_repo),
) -> ImportSessionDetail:
    """Get import session details."""
    session = get_session_or_404(session_id, repo)

    # Get validation summary if available
    validation_summary = None
    if session.validation_results:
        summary = issue_repo.get_summary(session_id)
        issues, total = issue_repo.get_by_session(session_id, limit=0)
        valid_count = (session.row_count or 0) - summary.get("error", 0)
        validation_summary = ValidationSummary(
            total_rows=session.row_count or 0,
            error_count=summary.get("error", 0),
            warning_count=summary.get("warning", 0),
            info_count=summary.get("info", 0),
            valid_count=max(0, valid_count),
        )

    return ImportSessionDetail(
        id=session.id,
        current_step=session.current_step,
        created_at=session.created_at,
        updated_at=session.updated_at,
        expires_at=session.expires_at,
        original_filename=session.original_filename,
        file_size_bytes=session.file_size_bytes,
        row_count=session.row_count,
        headers=session.headers,
        column_mapping=session.column_mapping,
        validation_summary=validation_summary,
        duplicate_resolution=session.duplicate_resolution,
    )


@router.get("/sessions", response_model=ImportSessionList)
async def list_import_sessions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    repo: ImportSessionRepository = Depends(get_session_repo),
) -> ImportSessionList:
    """List active import sessions."""
    sessions, total = repo.list(include_expired=False, limit=limit, offset=offset)

    return ImportSessionList(
        items=[
            ImportSessionSchema(
                id=s.id,
                current_step=s.current_step,
                created_at=s.created_at,
                updated_at=s.updated_at,
                expires_at=s.expires_at,
                original_filename=s.original_filename,
                file_size_bytes=s.file_size_bytes,
                row_count=s.row_count,
            )
            for s in sessions
        ],
        total=total,
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_import_session(
    session_id: str,
    repo: ImportSessionRepository = Depends(get_session_repo),
) -> None:
    """Delete an import session."""
    session = repo.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Import session not found")

    # Delete uploaded file if exists
    if session.file_reference:
        file_path = Path(session.file_reference)
        if file_path.exists():
            file_path.unlink()

    repo.delete(session_id)


# ============================================================================
# File Preview and Mapping Endpoints
# ============================================================================


@router.get("/sessions/{session_id}/preview", response_model=FilePreview)
async def get_file_preview(
    session_id: str,
    repo: ImportSessionRepository = Depends(get_session_repo),
) -> FilePreview:
    """Get file headers and sample rows for preview."""
    session = get_session_or_404(session_id, repo)

    if not session.file_reference:
        raise HTTPException(status_code=400, detail="No file uploaded for this session")

    file_path = Path(session.file_reference)
    if not file_path.exists():
        raise HTTPException(status_code=410, detail="Uploaded file no longer available")

    with open(file_path, "rb") as f:
        content = f.read()

    headers, sample_rows, total_rows, delimiter, encoding = parse_csv_preview(
        content,
        filename=session.original_filename or file_path.name,
    )

    return FilePreview(
        headers=headers,
        sample_rows=sample_rows,
        total_rows=total_rows,
        detected_delimiter=delimiter,
        detected_encoding=encoding,
    )


@router.get("/sessions/{session_id}/mapping/suggest", response_model=ColumnMappingSuggestion)
async def suggest_column_mapping(
    session_id: str,
    repo: ImportSessionRepository = Depends(get_session_repo),
) -> ColumnMappingSuggestion:
    """Get auto-suggested column mappings based on header names."""
    session = get_session_or_404(session_id, repo)

    if not session.headers:
        raise HTTPException(status_code=400, detail="No file headers available")

    mapping, confidence_scores, missing_fields = suggest_mapping(session.headers)

    return ColumnMappingSuggestion(
        suggested_mapping=mapping,
        required_fields=REQUIRED_FIELDS,
        missing_fields=missing_fields,
        confidence_scores=confidence_scores,
    )


@router.put("/sessions/{session_id}/mapping", response_model=ImportSessionSchema)
async def set_column_mapping(
    session_id: str,
    request: ColumnMappingRequest,
    repo: ImportSessionRepository = Depends(get_session_repo),
) -> ImportSessionSchema:
    """Set column mapping for the import session."""
    session = get_session_or_404(session_id, repo)

    # Validate all required fields are mapped
    is_valid, missing = validate_mapping(request.mapping)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required field mappings: {', '.join(missing)}"
        )

    # Update session
    session.column_mapping = request.mapping
    session.current_step = "validate"
    repo.update(session)

    return ImportSessionSchema(
        id=session.id,
        current_step=session.current_step,
        created_at=session.created_at,
        updated_at=session.updated_at,
        expires_at=session.expires_at,
        original_filename=session.original_filename,
        file_size_bytes=session.file_size_bytes,
        row_count=session.row_count,
    )


# ============================================================================
# Date Format Endpoints (T020-T023)
# ============================================================================


@router.get("/sessions/{session_id}/date-format/detect", response_model=DateFormatDetectionResponse)
async def detect_session_date_format(
    session_id: str,
    repo: ImportSessionRepository = Depends(get_session_repo),
) -> DateFormatDetectionResponse:
    """
    T020: Auto-detect date format from sample data in the uploaded file.

    Returns recommended format and all candidate formats with success rates.
    """
    session = get_session_or_404(session_id, repo)

    if not session.column_mapping:
        raise HTTPException(status_code=400, detail="Column mapping must be set before date format detection")

    if not session.file_reference:
        raise HTTPException(status_code=400, detail="No file uploaded")

    file_path = Path(session.file_reference)
    if not file_path.exists():
        raise HTTPException(status_code=410, detail="Uploaded file no longer available")

    # Parse file and get date samples
    with open(file_path, "rb") as f:
        content = f.read()

    df = parse_csv_file(
        content,
        filename=session.original_filename or file_path.name,
    )
    sample_values = get_date_column_values(df, session.column_mapping)

    if not sample_values:
        raise HTTPException(status_code=400, detail="No date values found in mapped columns")

    # Detect format
    detection = detect_date_format(sample_values)

    return DateFormatDetectionResponse(
        recommended_format=detection.recommended_format,
        formats=[
            DateFormatOptionResponse(
                format=opt.format,
                label=opt.label,
                success_rate=opt.success_rate,
                recommended=opt.recommended,
            )
            for opt in detection.formats
        ],
    )


@router.get("/sessions/{session_id}/date-format/preview", response_model=DateFormatPreviewResponse)
async def preview_session_date_format(
    session_id: str,
    format: str = Query(..., description="Date format string to preview"),
    repo: ImportSessionRepository = Depends(get_session_repo),
) -> DateFormatPreviewResponse:
    """
    T022: Preview how a specific date format parses sample values.

    Returns parsed samples with success/failure status for each.
    """
    session = get_session_or_404(session_id, repo)

    if not session.column_mapping:
        raise HTTPException(status_code=400, detail="Column mapping must be set before date format preview")

    if not session.file_reference:
        raise HTTPException(status_code=400, detail="No file uploaded")

    file_path = Path(session.file_reference)
    if not file_path.exists():
        raise HTTPException(status_code=410, detail="Uploaded file no longer available")

    # Parse file and get date samples
    with open(file_path, "rb") as f:
        content = f.read()

    df = parse_csv_file(
        content,
        filename=session.original_filename or file_path.name,
    )
    sample_values = get_date_column_values(df, session.column_mapping)

    # Preview format
    preview = preview_date_format(sample_values, format)

    return DateFormatPreviewResponse(
        format=preview.format,
        format_label=preview.format_label,
        samples=[
            DateSampleResponse(
                raw_value=s.raw_value,
                parsed_date=s.parsed_date,
                display_date=s.display_date,
                valid=s.valid,
                error=s.error,
            )
            for s in preview.samples
        ],
        success_rate=preview.success_rate,
    )


@router.put("/sessions/{session_id}/date-format", response_model=ImportSessionSchema)
async def set_session_date_format(
    session_id: str,
    request: DateFormatRequest,
    repo: ImportSessionRepository = Depends(get_session_repo),
) -> ImportSessionSchema:
    """
    T023: Set the date format for parsing dates in the import session.

    Updates session and advances to validation step.
    """
    session = get_session_or_404(session_id, repo)

    if not session.column_mapping:
        raise HTTPException(status_code=400, detail="Column mapping must be set before date format")

    # Update session with date format
    session.date_format = request.date_format
    session.current_step = "validate"
    repo.update(session)

    return ImportSessionSchema(
        id=session.id,
        current_step=session.current_step,
        created_at=session.created_at,
        updated_at=session.updated_at,
        expires_at=session.expires_at,
        original_filename=session.original_filename,
        file_size_bytes=session.file_size_bytes,
        row_count=session.row_count,
    )


# ============================================================================
# Validation Endpoints
# ============================================================================


@router.post("/sessions/{session_id}/validate", response_model=ValidationResult)
async def run_validation(
    session_id: str,
    repo: ImportSessionRepository = Depends(get_session_repo),
    issue_repo: ValidationIssueRepository = Depends(get_issue_repo),
) -> ValidationResult:
    """Run validation on the mapped data."""
    session = get_session_or_404(session_id, repo)

    if not session.column_mapping:
        raise HTTPException(status_code=400, detail="Column mapping must be set before validation")

    if not session.file_reference:
        raise HTTPException(status_code=400, detail="No file uploaded")

    file_path = Path(session.file_reference)
    if not file_path.exists():
        raise HTTPException(status_code=410, detail="Uploaded file no longer available")

    # Clear previous validation issues
    issue_repo.delete_by_session(session_id)

    # Parse and validate file
    start_time = datetime.utcnow()

    with open(file_path, "rb") as f:
        content = f.read()

    df = parse_csv_file(
        content,
        filename=session.original_filename or file_path.name,
    )
    issues, error_count, warning_count, info_count = validate_file(
        df, session.column_mapping, session_id
    )

    # Detect in-file duplicates
    ssn_col = session.column_mapping.get("ssn")
    if ssn_col:
        dup_issues = detect_in_file_duplicates(df, ssn_col, session_id)
        issues.extend(dup_issues)
        error_count += len(dup_issues)

    # Save issues
    issue_repo.bulk_insert(issues)

    # Update session
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    valid_count = (session.row_count or 0) - error_count
    session.validation_results = {
        "error_count": error_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "valid_count": max(0, valid_count),
    }
    session.current_step = "preview"
    repo.update(session)

    return ValidationResult(
        session_id=session_id,
        summary=ValidationSummary(
            total_rows=session.row_count or 0,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            valid_count=max(0, valid_count),
        ),
        completed_at=end_time,
        duration_seconds=duration,
    )


@router.get("/sessions/{session_id}/validation-issues", response_model=ValidationIssueList)
async def get_validation_issues(
    session_id: str,
    severity: Literal["error", "warning", "info"] | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    repo: ImportSessionRepository = Depends(get_session_repo),
    issue_repo: ValidationIssueRepository = Depends(get_issue_repo),
) -> ValidationIssueList:
    """Get validation issues for a session with optional severity filter."""
    session = get_session_or_404(session_id, repo)

    issues, total = issue_repo.get_by_session(session_id, severity, limit, offset)

    return ValidationIssueList(
        items=[
            ValidationIssueSchema(
                id=i.id,
                row_number=i.row_number,
                field_name=i.field_name,
                source_column=i.source_column,
                severity=i.severity,
                issue_code=i.issue_code,
                message=i.message,
                suggestion=i.suggestion,
                raw_value=i.raw_value,
                related_row=i.related_row,
            )
            for i in issues
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/sessions/{session_id}/preview-rows", response_model=PreviewRowList)
async def get_preview_rows(
    session_id: str,
    status: Literal["valid", "warning", "error"] | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: ImportSessionRepository = Depends(get_session_repo),
    issue_repo: ValidationIssueRepository = Depends(get_issue_repo),
) -> PreviewRowList:
    """
    T030: Get preview rows with validation status for each row.

    Returns rows with color-coded status (valid/warning/error) and associated issues.
    """
    session = get_session_or_404(session_id, repo)

    if not session.file_reference:
        raise HTTPException(status_code=400, detail="No file uploaded")

    file_path = Path(session.file_reference)
    if not file_path.exists():
        raise HTTPException(status_code=410, detail="Uploaded file no longer available")

    # Parse file
    with open(file_path, "rb") as f:
        content = f.read()

    df = parse_csv_file(
        content,
        filename=session.original_filename or file_path.name,
    )

    # Get all issues for this session
    all_issues, total_issues = issue_repo.get_by_session(session_id, limit=10000)

    # Group issues by row number
    issues_by_row: dict[int, list] = {}
    for issue in all_issues:
        if issue.row_number not in issues_by_row:
            issues_by_row[issue.row_number] = []
        issues_by_row[issue.row_number].append(issue)

    # Determine status for each row
    def get_row_status(row_num: int) -> str:
        row_issues = issues_by_row.get(row_num, [])
        if any(i.severity == "error" for i in row_issues):
            return "error"
        if any(i.severity == "warning" for i in row_issues):
            return "warning"
        return "valid"

    # Build preview rows
    preview_rows = []
    valid_count = 0
    warning_count = 0
    error_count = 0

    for row_num, row in enumerate(df.to_dict("records"), start=1):
        row_status = get_row_status(row_num)

        # Count by status
        if row_status == "valid":
            valid_count += 1
        elif row_status == "warning":
            warning_count += 1
        else:
            error_count += 1

        # Filter by status if requested
        if status and row_status != status:
            continue

        # Build issue list for this row
        row_issues = issues_by_row.get(row_num, [])

        preview_rows.append({
            "row_number": row_num,
            "status": row_status,
            "original_values": row,
            "mapped_values": {},  # TODO: Apply mapping
            "parsed_dates": {},  # TODO: Parse dates
            "issues": [
                ValidationIssueSchema(
                    id=i.id,
                    row_number=i.row_number,
                    field_name=i.field_name,
                    source_column=i.source_column,
                    severity=i.severity,
                    issue_code=i.issue_code,
                    message=i.message,
                    suggestion=i.suggestion,
                    raw_value=i.raw_value,
                    related_row=i.related_row,
                )
                for i in row_issues
            ],
        })

    # Apply pagination
    total_filtered = len(preview_rows)
    preview_rows = preview_rows[offset:offset + limit]

    return PreviewRowList(
        items=[
            PreviewRow(
                row_number=r["row_number"],
                status=r["status"],
                data=r["original_values"],
                issues=r["issues"] if r["issues"] else None,
            )
            for r in preview_rows
        ],
        total=total_filtered,
        valid_count=valid_count,
        warning_count=warning_count,
        error_count=error_count,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# Duplicate Resolution Endpoints
# ============================================================================


@router.put("/sessions/{session_id}/duplicate-resolution", response_model=ImportSessionSchema)
async def set_duplicate_resolution(
    session_id: str,
    request: DuplicateResolutionRequest,
    repo: ImportSessionRepository = Depends(get_session_repo),
) -> ImportSessionSchema:
    """Set duplicate resolution strategy for existing record conflicts."""
    session = get_session_or_404(session_id, repo)

    # Build resolution map
    resolution = request.resolutions.copy() if request.resolutions else {}

    # Apply to all if specified
    if request.apply_to_all:
        # In a real implementation, we'd get all duplicate SSN hashes
        # For now, just store the apply_to_all preference
        resolution["_apply_to_all"] = request.apply_to_all

    session.duplicate_resolution = resolution
    repo.update(session)

    return ImportSessionSchema(
        id=session.id,
        current_step=session.current_step,
        created_at=session.created_at,
        updated_at=session.updated_at,
        expires_at=session.expires_at,
        original_filename=session.original_filename,
        file_size_bytes=session.file_size_bytes,
        row_count=session.row_count,
    )


# ============================================================================
# Import Preview and Execution Endpoints
# ============================================================================


@router.get("/sessions/{session_id}/preview-import", response_model=ImportPreview)
async def get_import_preview(
    session_id: str,
    repo: ImportSessionRepository = Depends(get_session_repo),
    issue_repo: ValidationIssueRepository = Depends(get_issue_repo),
) -> ImportPreview:
    """Get pre-commit import preview with categorized counts."""
    session = get_session_or_404(session_id, repo)

    summary = issue_repo.get_summary(session_id)
    total_rows = session.row_count or 0
    error_count = summary.get("error", 0)
    warning_count = summary.get("warning", 0)

    # Calculate counts
    # Rows with errors will be rejected
    reject_count = error_count
    import_count = total_rows - reject_count

    # Count replace/skip from duplicate resolution
    replace_count = 0
    skip_count = 0
    if session.duplicate_resolution:
        for key, action in session.duplicate_resolution.items():
            if key == "_apply_to_all":
                continue
            if action == "replace":
                replace_count += 1
            elif action == "skip":
                skip_count += 1
                import_count -= 1

    return ImportPreview(
        total_rows=total_rows,
        import_count=max(0, import_count),
        reject_count=reject_count,
        warning_count=warning_count,
        replace_count=replace_count if replace_count > 0 else None,
        skip_count=skip_count if skip_count > 0 else None,
    )


@router.post("/sessions/{session_id}/execute", response_model=ImportResult)
async def execute_import(
    session_id: str,
    request: ImportExecuteRequest,
    repo: ImportSessionRepository = Depends(get_session_repo),
    log_repo: ImportLogRepository = Depends(get_log_repo),
    issue_repo: ValidationIssueRepository = Depends(get_issue_repo),
) -> ImportResult:
    """Execute the import and create census records."""
    session = get_session_or_404(session_id, repo)

    if not session.column_mapping:
        raise HTTPException(status_code=400, detail="Column mapping must be set")

    if not session.validation_results:
        raise HTTPException(status_code=400, detail="Validation must be run first")

    # Get validation summary
    summary = issue_repo.get_summary(session_id)
    total_rows = session.row_count or 0
    error_count = summary.get("error", 0)
    warning_count = summary.get("warning", 0)

    # Create import log
    start_time = datetime.utcnow()

    import_log = ImportLog(
        id=str(uuid.uuid4()),
        session_id=session_id,
        original_filename=session.original_filename or "unknown.csv",
        total_rows=total_rows,
        column_mapping_used=session.column_mapping,
        created_at=start_time,
    )

    # Calculate counts
    imported_count = total_rows - error_count
    rejected_count = error_count

    # Create census from imported data
    census_id = ""
    if session.workspace_id and session.file_reference and imported_count > 0:
        try:
            import pandas as pd
            import hashlib

            # Read the uploaded file (CSV or XLSX)
            csv_path = Path(session.file_reference)
            if csv_path.exists():
                file_bytes = csv_path.read_bytes()
                df = parse_csv_file(
                    file_bytes,
                    filename=session.original_filename or csv_path.name,
                )

                # Apply column mapping to transform raw data
                mapping = session.column_mapping or {}

                # DEBUG: Log mapping and columns for troubleshooting
                print(f"DEBUG import_wizard: Column mapping = {mapping}")
                print(f"DEBUG import_wizard: DataFrame columns = {list(df.columns)}")
                for field, col in mapping.items():
                    if col and col not in df.columns:
                        print(f"DEBUG import_wizard: WARNING - mapped column '{col}' for field '{field}' NOT FOUND in DataFrame!")
                    elif col:
                        print(f"DEBUG import_wizard: OK - '{field}' -> '{col}' (sample: {df[col].iloc[0] if len(df) > 0 else 'empty'})")

                # Create processed dataframe with expected columns
                processed_df = pd.DataFrame()

                def get_numeric(col: str | None) -> pd.Series:
                    if not col or col not in df.columns:
                        if col:
                            print(f"DEBUG get_numeric: Column '{col}' not found in df.columns")
                        return pd.Series([0] * len(df))
                    cleaned = (
                        df[col]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        .str.replace(r"^\((.*)\)$", r"-\1", regex=True)
                        .str.replace("$", "", regex=False)
                        .str.replace(",", "", regex=False)
                        .str.replace("%", "", regex=False)
                        .str.replace(" ", "", regex=False)
                    )
                    return pd.to_numeric(cleaned, errors="coerce").fillna(0)

                # Generate internal_id from SSN (hashed)
                ssn_col = mapping.get("ssn")
                if ssn_col and ssn_col in df.columns:
                    census_salt = str(uuid4())[:8]
                    processed_df["internal_id"] = df[ssn_col].fillna("").astype(str).apply(
                        lambda x: hashlib.sha256(f"{x}{census_salt}".encode()).hexdigest()[:16]
                    )
                else:
                    processed_df["internal_id"] = [f"p{i}" for i in range(len(df))]
                    census_salt = str(uuid4())[:8]

                # Map compensation (convert to cents)
                comp_col = mapping.get("compensation")
                comp_values = get_numeric(comp_col)
                processed_df["compensation"] = comp_values
                processed_df["compensation_cents"] = (comp_values * 100).round().astype(int)

                # Map date fields (critical for ACP exclusion logic)
                def get_date(col: str | None) -> pd.Series:
                    """Parse date column, returning ISO format strings or empty."""
                    if not col or col not in df.columns:
                        return pd.Series([""] * len(df))
                    return df[col].fillna("").astype(str).str.strip()

                dob_col = mapping.get("dob")
                processed_df["dob"] = get_date(dob_col)

                hire_date_col = mapping.get("hire_date")
                processed_df["hire_date"] = get_date(hire_date_col)

                termination_date_col = mapping.get("termination_date")
                processed_df["termination_date"] = get_date(termination_date_col)

                # Determine HCE status - use explicit column if mapped, else compensation threshold
                hce_col = mapping.get("hce_status")
                if hce_col and hce_col in df.columns:
                    # Parse HCE status from column (Y/N, True/False, 1/0, Yes/No)
                    hce_values = df[hce_col].fillna("").astype(str).str.strip().str.upper()
                    processed_df["is_hce"] = hce_values.isin(["Y", "YES", "TRUE", "1", "HCE"])
                else:
                    # Fall back to compensation threshold
                    hce_threshold = 155000 if request.plan_year >= 2024 else 150000
                    processed_df["is_hce"] = processed_df["compensation"] >= hce_threshold

                # Map contribution columns (convert to cents)
                pre_tax_col = mapping.get("employee_pre_tax")
                pre_tax_values = get_numeric(pre_tax_col)
                processed_df["pre_tax_cents"] = (pre_tax_values * 100).round().astype(int)

                after_tax_col = mapping.get("employee_after_tax")
                after_tax_values = get_numeric(after_tax_col)
                processed_df["after_tax_cents"] = (after_tax_values * 100).round().astype(int)

                roth_col = mapping.get("employee_roth")
                roth_values = get_numeric(roth_col)
                processed_df["roth_cents"] = (roth_values * 100).round().astype(int)

                match_col = mapping.get("employer_match")
                match_values = get_numeric(match_col)
                processed_df["match_cents"] = (match_values * 100).round().astype(int)

                non_elective_col = mapping.get("employer_non_elective")
                non_elective_values = get_numeric(non_elective_col)
                processed_df["non_elective_cents"] = (non_elective_values * 100).round().astype(int)

                # Calculate deferral_rate (pre_tax / compensation)
                processed_df["deferral_rate"] = 0.0
                mask = processed_df["compensation"] > 0
                if mask.any():
                    processed_df.loc[mask, "deferral_rate"] = (
                        pre_tax_values.loc[mask] / processed_df.loc[mask, "compensation"]
                    )

                # Calculate match_rate and after_tax_rate
                processed_df["match_rate"] = 0.0
                processed_df["after_tax_rate"] = 0.0
                if mask.any():
                    processed_df.loc[mask, "match_rate"] = (
                        match_values.loc[mask] / processed_df.loc[mask, "compensation"]
                    )
                    processed_df.loc[mask, "after_tax_rate"] = (
                        after_tax_values.loc[mask] / processed_df.loc[mask, "compensation"]
                    )

                # Calculate statistics
                participant_count = len(processed_df)
                hce_count = int(processed_df["is_hce"].sum())
                nhce_count = participant_count - hce_count
                avg_compensation = float(processed_df["compensation"].mean()) if participant_count > 0 else 0.0
                avg_deferral = float(processed_df["deferral_rate"].mean()) * 100 if participant_count > 0 else 0.0

                # Create census ID and timestamp
                census_id = str(uuid4())
                upload_timestamp = datetime.utcnow()

                # CRITICAL: Save to DuckDB for analysis routes to read
                from app.storage.models import Census as CensusModel, Participant as ParticipantModel
                from app.storage.repository import CensusRepository, ParticipantRepository
                from app.storage.database import get_db

                # Get database connection for this workspace
                db_conn = get_db(session.workspace_id)

                # Create Census record in DuckDB
                census_model = CensusModel(
                    id=census_id,
                    name=request.census_name,
                    client_name=None,
                    plan_year=request.plan_year,
                    hce_mode="explicit" if hce_col else "compensation_threshold",
                    upload_timestamp=upload_timestamp,
                    participant_count=participant_count,
                    hce_count=hce_count,
                    nhce_count=nhce_count,
                    avg_compensation_cents=int(avg_compensation * 100),
                    avg_deferral_rate=avg_deferral,
                    salt=census_salt,
                    version="1.0.0",
                )
                census_repo = CensusRepository(db_conn)
                census_repo.save(census_model)

                # Create Participant records in DuckDB
                from datetime import date as date_type, datetime as datetime_type

                # Get the date format from session (set by user in wizard)
                date_format = session.date_format or "%Y-%m-%d"

                def parse_date_str(date_str: str) -> date_type | None:
                    """Parse date string to date object using session's date format."""
                    if not date_str or not date_str.strip():
                        return None
                    date_str = date_str.strip()
                    # Try the user-selected format first
                    try:
                        return datetime_type.strptime(date_str, date_format).date()
                    except ValueError:
                        pass
                    # Fall back to ISO format
                    try:
                        return date_type.fromisoformat(date_str)
                    except ValueError:
                        pass
                    # Try common US formats as fallback
                    for fmt in ["%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%Y/%m/%d"]:
                        try:
                            return datetime_type.strptime(date_str, fmt).date()
                        except ValueError:
                            continue
                    return None

                participant_models = []
                for idx, row in processed_df.iterrows():
                    # Parse dates - convert strings to date objects
                    dob_str = str(row.get("dob", "")).strip()
                    hire_str = str(row.get("hire_date", "")).strip()
                    term_str = str(row.get("termination_date", "")).strip()

                    participant_model = ParticipantModel(
                        id=str(uuid4()),
                        census_id=census_id,
                        internal_id=str(row["internal_id"]),
                        is_hce=bool(row["is_hce"]),
                        compensation_cents=int(row["compensation_cents"]),
                        deferral_rate=float(row["deferral_rate"]) * 100,  # Convert to percentage
                        match_rate=float(row["match_rate"]) * 100,
                        after_tax_rate=float(row["after_tax_rate"]) * 100,
                        dob=parse_date_str(dob_str),
                        hire_date=parse_date_str(hire_str),
                        termination_date=parse_date_str(term_str),
                    )
                    participant_models.append(participant_model)

                participant_repo = ParticipantRepository(db_conn)
                participant_repo.bulk_insert(participant_models)

                # Set census_id on import log
                import_log.census_id = census_id
        except Exception as e:
            # Re-raise with more context
            import traceback
            print(f"ERROR: Failed to save census: {e}")
            print(f"  workspace_id: {session.workspace_id}")
            print(f"  file_reference: {session.file_reference}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Census save failed: {str(e)}")

    # Update log with results
    import_log.imported_count = imported_count
    import_log.rejected_count = rejected_count
    import_log.warning_count = warning_count
    import_log.completed_at = datetime.utcnow()

    log_repo.save(import_log)

    # Update session
    session.current_step = "completed"
    session.import_result_id = import_log.id
    repo.update(session)

    duration = (import_log.completed_at - start_time).total_seconds()

    return ImportResult(
        import_log_id=import_log.id,
        census_id=census_id,  # From workspace file storage, not import_log
        summary={
            "total_rows": total_rows,
            "imported_count": imported_count,
            "rejected_count": rejected_count,
            "warning_count": warning_count,
            "replaced_count": import_log.replaced_count,
            "skipped_count": import_log.skipped_count,
        },
        completed_at=import_log.completed_at,
        duration_seconds=duration,
    )


# ============================================================================
# Import Log Endpoints
# ============================================================================


@router.get("/logs", response_model=ImportLogList)
async def list_import_logs(
    census_id: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    repo: ImportLogRepository = Depends(get_log_repo),
) -> ImportLogList:
    """List import logs with optional filtering."""
    logs, total = repo.list(census_id=census_id, limit=limit, offset=offset)

    return ImportLogList(
        items=[
            ImportLogSchema(
                id=log.id,
                census_id=log.census_id,
                created_at=log.created_at,
                completed_at=log.completed_at,
                original_filename=log.original_filename,
                total_rows=log.total_rows,
                imported_count=log.imported_count,
                rejected_count=log.rejected_count,
                warning_count=log.warning_count,
                replaced_count=log.replaced_count,
                skipped_count=log.skipped_count,
            )
            for log in logs
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/logs/{log_id}", response_model=ImportLogDetail)
async def get_import_log(
    log_id: str,
    repo: ImportLogRepository = Depends(get_log_repo),
) -> ImportLogDetail:
    """Get import log details."""
    log = repo.get(log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Import log not found")

    return ImportLogDetail(
        id=log.id,
        census_id=log.census_id,
        created_at=log.created_at,
        completed_at=log.completed_at,
        original_filename=log.original_filename,
        total_rows=log.total_rows,
        imported_count=log.imported_count,
        rejected_count=log.rejected_count,
        warning_count=log.warning_count,
        replaced_count=log.replaced_count,
        skipped_count=log.skipped_count,
        column_mapping_used=log.column_mapping_used,
        detailed_results=None,  # TODO: Convert to PreviewRow list
    )


@router.delete("/logs/{log_id}", status_code=204)
async def delete_import_log(
    log_id: str,
    repo: ImportLogRepository = Depends(get_log_repo),
) -> None:
    """Soft delete an import log."""
    if not repo.soft_delete(log_id):
        raise HTTPException(status_code=404, detail="Import log not found")


# ============================================================================
# Mapping Profile Endpoints
# ============================================================================


@router.post("/mapping-profiles", status_code=201, response_model=MappingProfileSchema)
async def create_mapping_profile(
    request: MappingProfileCreate,
    repo: MappingProfileRepository = Depends(get_profile_repo),
) -> MappingProfileSchema:
    """Create a new mapping profile."""
    # Check for duplicate name
    existing = repo.get_by_name(request.name)
    if existing:
        raise HTTPException(status_code=409, detail="Profile with this name already exists")

    profile = MappingProfile(
        id=str(uuid.uuid4()),
        name=request.name,
        description=request.description,
        column_mapping=request.column_mapping,
        expected_headers=request.expected_headers,
        created_at=datetime.utcnow(),
    )

    repo.save(profile)

    return MappingProfileSchema(
        id=profile.id,
        name=profile.name,
        description=profile.description,
        column_mapping=profile.column_mapping,
        expected_headers=profile.expected_headers,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("/mapping-profiles", response_model=MappingProfileList)
async def list_mapping_profiles(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    repo: MappingProfileRepository = Depends(get_profile_repo),
) -> MappingProfileList:
    """List mapping profiles."""
    profiles, total = repo.list(limit=limit, offset=offset)

    return MappingProfileList(
        items=[
            MappingProfileSchema(
                id=p.id,
                name=p.name,
                description=p.description,
                column_mapping=p.column_mapping,
                expected_headers=p.expected_headers,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in profiles
        ],
        total=total,
    )


@router.get("/mapping-profiles/{profile_id}", response_model=MappingProfileSchema)
async def get_mapping_profile(
    profile_id: str,
    repo: MappingProfileRepository = Depends(get_profile_repo),
) -> MappingProfileSchema:
    """Get a mapping profile by ID."""
    profile = repo.get(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Mapping profile not found")

    return MappingProfileSchema(
        id=profile.id,
        name=profile.name,
        description=profile.description,
        column_mapping=profile.column_mapping,
        expected_headers=profile.expected_headers,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.put("/mapping-profiles/{profile_id}", response_model=MappingProfileSchema)
async def update_mapping_profile(
    profile_id: str,
    request: MappingProfileUpdate,
    repo: MappingProfileRepository = Depends(get_profile_repo),
) -> MappingProfileSchema:
    """Update a mapping profile."""
    profile = repo.get(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Mapping profile not found")

    if request.name is not None:
        profile.name = request.name
    if request.description is not None:
        profile.description = request.description
    if request.column_mapping is not None:
        profile.column_mapping = request.column_mapping

    repo.update(profile)

    return MappingProfileSchema(
        id=profile.id,
        name=profile.name,
        description=profile.description,
        column_mapping=profile.column_mapping,
        expected_headers=profile.expected_headers,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.delete("/mapping-profiles/{profile_id}", status_code=204)
async def delete_mapping_profile(
    profile_id: str,
    repo: MappingProfileRepository = Depends(get_profile_repo),
) -> None:
    """Delete a mapping profile."""
    if not repo.delete(profile_id):
        raise HTTPException(status_code=404, detail="Mapping profile not found")


@router.post("/mapping-profiles/{profile_id}/apply", response_model=ProfileApplyResult)
async def apply_mapping_profile(
    profile_id: str,
    session_id: str = Query(..., description="Session ID to apply profile to"),
    profile_repo: MappingProfileRepository = Depends(get_profile_repo),
    session_repo: ImportSessionRepository = Depends(get_session_repo),
) -> ProfileApplyResult:
    """Apply a mapping profile to an import session."""
    profile = profile_repo.get(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Mapping profile not found")

    session = get_session_or_404(session_id, session_repo)

    if not session.headers:
        raise HTTPException(status_code=400, detail="Session has no file headers")

    # Determine which mappings can be applied
    applied_mappings = {}
    unmatched_fields = []

    for field, source_column in profile.column_mapping.items():
        if source_column in session.headers:
            applied_mappings[field] = source_column
        else:
            unmatched_fields.append(field)

    # Update session with applied mappings
    session.column_mapping = applied_mappings
    session_repo.update(session)

    return ProfileApplyResult(
        session_id=session_id,
        profile_id=profile_id,
        applied_mappings=applied_mappings,
        unmatched_fields=unmatched_fields,
        success=len(unmatched_fields) == 0,
    )


# ============================================================================
# Workspace-Scoped Mapping Profile Endpoints (T037-T041)
# ============================================================================


@workspace_router.get(
    "/workspaces/{workspace_id}/import/mapping-profiles",
    response_model=MappingProfileList,
)
async def list_workspace_mapping_profiles(
    workspace_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> MappingProfileList:
    """T037: List mapping profiles for a specific workspace."""
    conn = get_db(workspace_id)
    repo = MappingProfileRepository(conn)
    profiles, total = repo.list_by_workspace(workspace_id, limit=limit, offset=offset)

    return MappingProfileList(
        items=[
            MappingProfileSchema(
                id=p.id,
                name=p.name,
                description=p.description,
                column_mapping=p.column_mapping,
                expected_headers=p.expected_headers,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in profiles
        ],
        total=total,
    )


@workspace_router.post(
    "/workspaces/{workspace_id}/import/mapping-profiles",
    status_code=201,
    response_model=MappingProfileSchema,
)
async def create_workspace_mapping_profile(
    workspace_id: str,
    request: MappingProfileCreate,
) -> MappingProfileSchema:
    """T038: Create a new mapping profile for a specific workspace."""
    conn = get_db(workspace_id)
    repo = MappingProfileRepository(conn)
    # Check for duplicate name in workspace
    existing = repo.get_by_name(request.name, workspace_id=workspace_id)
    if existing:
        raise HTTPException(status_code=409, detail="Profile with this name already exists in workspace")

    profile = MappingProfile(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        name=request.name,
        description=request.description,
        column_mapping=request.column_mapping,
        expected_headers=request.expected_headers,
        created_at=datetime.utcnow(),
    )

    repo.save(profile)

    return MappingProfileSchema(
        id=profile.id,
        name=profile.name,
        description=profile.description,
        column_mapping=profile.column_mapping,
        expected_headers=profile.expected_headers,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@workspace_router.put(
    "/workspaces/{workspace_id}/import/mapping-profiles/{profile_id}",
    response_model=MappingProfileSchema,
)
async def update_workspace_mapping_profile(
    workspace_id: str,
    profile_id: str,
    request: MappingProfileUpdate,
) -> MappingProfileSchema:
    """T039: Update a mapping profile in a specific workspace."""
    conn = get_db(workspace_id)
    repo = MappingProfileRepository(conn)
    profile = repo.get(profile_id)
    if profile is None or profile.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Mapping profile not found in workspace")

    if request.name is not None:
        profile.name = request.name
    if request.description is not None:
        profile.description = request.description
    if request.column_mapping is not None:
        profile.column_mapping = request.column_mapping

    repo.update(profile)

    return MappingProfileSchema(
        id=profile.id,
        name=profile.name,
        description=profile.description,
        column_mapping=profile.column_mapping,
        expected_headers=profile.expected_headers,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@workspace_router.delete(
    "/workspaces/{workspace_id}/import/mapping-profiles/{profile_id}",
    status_code=204,
)
async def delete_workspace_mapping_profile(
    workspace_id: str,
    profile_id: str,
) -> None:
    """T040: Delete a mapping profile from a specific workspace."""
    conn = get_db(workspace_id)
    repo = MappingProfileRepository(conn)
    profile = repo.get(profile_id)
    if profile is None or profile.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Mapping profile not found in workspace")

    if not repo.delete(profile_id):
        raise HTTPException(status_code=404, detail="Mapping profile not found")


@router.post("/sessions/{session_id}/apply-profile", response_model=ProfileApplyResult)
async def apply_profile_to_session(
    session_id: str,
    profile_id: str = Query(..., description="Profile ID to apply"),
    profile_repo: MappingProfileRepository = Depends(get_profile_repo),
    session_repo: ImportSessionRepository = Depends(get_session_repo),
) -> ProfileApplyResult:
    """T041: Apply a mapping profile to an import session."""
    profile = profile_repo.get(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Mapping profile not found")

    session = get_session_or_404(session_id, session_repo)

    if not session.headers:
        raise HTTPException(status_code=400, detail="Session has no file headers")

    # Determine which mappings can be applied
    applied_mappings = {}
    unmatched_fields = []

    for field, source_column in profile.column_mapping.items():
        if source_column in session.headers:
            applied_mappings[field] = source_column
        else:
            unmatched_fields.append(field)

    # Update session with applied mappings
    session.column_mapping = applied_mappings

    # Apply date format from profile if present
    if profile.date_format:
        session.date_format = profile.date_format

    session_repo.update(session)

    return ProfileApplyResult(
        session_id=session_id,
        profile_id=profile_id,
        applied_mappings=applied_mappings,
        unmatched_fields=unmatched_fields,
        success=len(unmatched_fields) == 0,
    )
