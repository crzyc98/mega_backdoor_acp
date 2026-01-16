"""
Data Models for ACP Sensitivity Analyzer.

Dataclass models representing census, participant, and analysis entities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Literal, Any


# Type alias for HCE determination mode
HCEMode = Literal["explicit", "compensation_threshold"]


def _parse_datetime(value: Any) -> datetime | None:
    """Parse datetime from various formats (string or datetime object)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise ValueError(f"Cannot parse datetime from {type(value)}: {value}")


def _parse_date(value: Any) -> date | None:
    """Parse date from various formats (string, date, or datetime object)."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError(f"Cannot parse date from {type(value)}: {value}")


@dataclass
class Census:
    """
    A collection of participant records for a single plan.

    T031: Census dataclass model per data-model.md
    Extended with client_name, hce_mode, and summary statistics.
    """
    id: str
    name: str
    plan_year: int
    upload_timestamp: datetime
    participant_count: int
    hce_count: int
    nhce_count: int
    salt: str
    version: str
    client_name: str | None = None
    hce_mode: HCEMode = "explicit"
    avg_compensation_cents: int | None = None
    avg_deferral_rate: float | None = None

    @property
    def avg_compensation(self) -> float | None:
        """Return average compensation in dollars."""
        if self.avg_compensation_cents is None:
            return None
        return self.avg_compensation_cents / 100

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "name": self.name,
            "client_name": self.client_name,
            "plan_year": self.plan_year,
            "hce_mode": self.hce_mode,
            "upload_timestamp": self.upload_timestamp.isoformat(),
            "participant_count": self.participant_count,
            "hce_count": self.hce_count,
            "nhce_count": self.nhce_count,
            "avg_compensation_cents": self.avg_compensation_cents,
            "avg_deferral_rate": self.avg_deferral_rate,
            "salt": self.salt,
            "version": self.version,
        }

    @classmethod
    def from_row(cls, row: dict) -> "Census":
        """Create Census from database row."""
        return cls(
            id=row["id"],
            name=row["name"],
            client_name=row.get("client_name"),
            plan_year=row["plan_year"],
            hce_mode=row.get("hce_mode", "explicit"),
            upload_timestamp=_parse_datetime(row["upload_timestamp"]),
            participant_count=row["participant_count"],
            hce_count=row["hce_count"],
            nhce_count=row["nhce_count"],
            avg_compensation_cents=row.get("avg_compensation_cents"),
            avg_deferral_rate=row.get("avg_deferral_rate"),
            salt=row["salt"],
            version=row["version"],
        )


@dataclass
class Participant:
    """
    An individual plan participant with ACP-relevant attributes.

    T032: Participant dataclass model per data-model.md
    """
    id: str
    census_id: str
    internal_id: str
    is_hce: bool
    compensation_cents: int
    deferral_rate: float
    match_rate: float
    after_tax_rate: float
    dob: date | None = None
    hire_date: date | None = None
    termination_date: date | None = None
    # Contribution amounts in cents
    employee_pre_tax_cents: int = 0
    employee_after_tax_cents: int = 0
    employee_roth_cents: int = 0
    employer_match_cents: int = 0
    employer_non_elective_cents: int = 0
    # SSN hash for duplicate detection
    ssn_hash: str | None = None

    @property
    def match_cents(self) -> int:
        """Calculate match contribution in cents."""
        return int(self.compensation_cents * self.match_rate / 100)

    @property
    def after_tax_cents(self) -> int:
        """Calculate after-tax contribution in cents."""
        return int(self.compensation_cents * self.after_tax_rate / 100)

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "census_id": self.census_id,
            "internal_id": self.internal_id,
            "is_hce": 1 if self.is_hce else 0,
            "compensation_cents": self.compensation_cents,
            "deferral_rate": self.deferral_rate,
            "match_rate": self.match_rate,
            "after_tax_rate": self.after_tax_rate,
            "dob": self.dob,  # DuckDB accepts date objects directly
            "hire_date": self.hire_date,
            "termination_date": self.termination_date,
            "employee_pre_tax_cents": self.employee_pre_tax_cents,
            "employee_after_tax_cents": self.employee_after_tax_cents,
            "employee_roth_cents": self.employee_roth_cents,
            "employer_match_cents": self.employer_match_cents,
            "employer_non_elective_cents": self.employer_non_elective_cents,
            "ssn_hash": self.ssn_hash,
        }

    def to_calculation_dict(self) -> dict:
        """Convert to dictionary for ACP calculations."""
        return {
            "internal_id": self.internal_id,
            "is_hce": self.is_hce,
            "match_cents": self.match_cents,
            "after_tax_cents": self.after_tax_cents,
            "compensation_cents": self.compensation_cents,
            "deferral_rate": self.deferral_rate,
            "match_rate": self.match_rate,
            "after_tax_rate": self.after_tax_rate,
            "dob": self.dob,
            "hire_date": self.hire_date,
            "termination_date": self.termination_date,
        }

    @classmethod
    def from_row(cls, row: dict) -> "Participant":
        """Create Participant from database row."""
        return cls(
            id=row["id"],
            census_id=row["census_id"],
            internal_id=row["internal_id"],
            is_hce=bool(row["is_hce"]),
            compensation_cents=row["compensation_cents"],
            deferral_rate=row["deferral_rate"],
            match_rate=row["match_rate"],
            after_tax_rate=row["after_tax_rate"],
            dob=_parse_date(row.get("dob")),
            hire_date=_parse_date(row.get("hire_date")),
            termination_date=_parse_date(row.get("termination_date")),
            employee_pre_tax_cents=row.get("employee_pre_tax_cents", 0) or 0,
            employee_after_tax_cents=row.get("employee_after_tax_cents", 0) or 0,
            employee_roth_cents=row.get("employee_roth_cents", 0) or 0,
            employer_match_cents=row.get("employer_match_cents", 0) or 0,
            employer_non_elective_cents=row.get("employer_non_elective_cents", 0) or 0,
            ssn_hash=row.get("ssn_hash"),
        )


@dataclass
class AnalysisResult:
    """
    The outcome of running one scenario against a census.

    T033: AnalysisResult dataclass model per data-model.md
    """
    id: str
    census_id: str
    grid_analysis_id: str | None
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

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "census_id": self.census_id,
            "grid_analysis_id": self.grid_analysis_id,
            "adoption_rate": self.adoption_rate,
            "contribution_rate": self.contribution_rate,
            "seed": self.seed,
            "nhce_acp": self.nhce_acp,
            "hce_acp": self.hce_acp,
            "threshold": self.threshold,
            "margin": self.margin,
            "result": self.result,
            "limiting_test": self.limiting_test,
            "run_timestamp": self.run_timestamp.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_row(cls, row: dict) -> "AnalysisResult":
        """Create AnalysisResult from database row."""
        return cls(
            id=row["id"],
            census_id=row["census_id"],
            grid_analysis_id=row["grid_analysis_id"],
            adoption_rate=row["adoption_rate"],
            contribution_rate=row["contribution_rate"],
            seed=row["seed"],
            nhce_acp=row["nhce_acp"],
            hce_acp=row["hce_acp"],
            threshold=row["threshold"],
            margin=row["margin"],
            result=row["result"],
            limiting_test=row["limiting_test"],
            run_timestamp=_parse_datetime(row["run_timestamp"]),
            version=row["version"],
        )


@dataclass
class GridAnalysis:
    """
    A collection of analysis results across multiple scenarios.

    T055 (Phase 4): GridAnalysis dataclass model per data-model.md
    """
    id: str
    census_id: str
    name: str | None
    created_timestamp: datetime
    seed: int
    adoption_rates: list[float]
    contribution_rates: list[float]
    version: str

    @property
    def scenario_count(self) -> int:
        """Calculate total number of scenarios."""
        return len(self.adoption_rates) * len(self.contribution_rates)

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        import json
        return {
            "id": self.id,
            "census_id": self.census_id,
            "name": self.name,
            "created_timestamp": self.created_timestamp.isoformat(),
            "seed": self.seed,
            "adoption_rates": json.dumps(self.adoption_rates),
            "contribution_rates": json.dumps(self.contribution_rates),
            "version": self.version,
        }

    @classmethod
    def from_row(cls, row: dict) -> "GridAnalysis":
        """Create GridAnalysis from database row."""
        import json
        return cls(
            id=row["id"],
            census_id=row["census_id"],
            name=row["name"],
            created_timestamp=_parse_datetime(row["created_timestamp"]),
            seed=row["seed"],
            adoption_rates=json.loads(row["adoption_rates"]),
            contribution_rates=json.loads(row["contribution_rates"]),
            version=row["version"],
        )


@dataclass
class ImportMetadata:
    """
    Information about how a census was imported.

    Stores column mapping and import details for reproducibility.
    """
    id: str
    census_id: str
    source_filename: str
    column_mapping: dict[str, str]
    row_count: int
    created_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        import json
        return {
            "id": self.id,
            "census_id": self.census_id,
            "source_filename": self.source_filename,
            "column_mapping": json.dumps(self.column_mapping),
            "row_count": self.row_count,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_row(cls, row: dict) -> "ImportMetadata":
        """Create ImportMetadata from database row."""
        import json
        return cls(
            id=row["id"],
            census_id=row["census_id"],
            source_filename=row["source_filename"],
            column_mapping=json.loads(row["column_mapping"]),
            row_count=row["row_count"],
            created_at=_parse_datetime(row["created_at"]),
        )


# ============================================================================
# CSV Import Wizard Models (Feature 003-csv-import-wizard)
# ============================================================================

# Type aliases for wizard
WizardStep = Literal["upload", "map", "validate", "preview", "confirm", "completed"]
Severity = Literal["error", "warning", "info"]
DuplicateResolutionAction = Literal["replace", "skip"]


@dataclass
class ImportSession:
    """
    Represents an in-progress import wizard session.

    Tracks wizard state, uploaded file reference, column mapping,
    validation results, and user progress through wizard steps.
    """
    id: str
    created_at: datetime
    expires_at: datetime
    current_step: WizardStep = "upload"
    user_id: str | None = None
    workspace_id: str | None = None
    updated_at: datetime | None = None
    file_reference: str | None = None
    original_filename: str | None = None
    file_size_bytes: int | None = None
    row_count: int | None = None
    headers: list[str] | None = None
    column_mapping: dict[str, str] | None = None
    date_format: str | None = None  # T004: User-selected date format
    validation_results: dict | None = None
    duplicate_resolution: dict[str, DuplicateResolutionAction] | None = None
    import_result_id: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        import json
        return {
            "id": self.id,
            "user_id": self.user_id,
            "workspace_id": self.workspace_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat(),
            "current_step": self.current_step,
            "file_reference": self.file_reference,
            "original_filename": self.original_filename,
            "file_size_bytes": self.file_size_bytes,
            "row_count": self.row_count,
            "headers": json.dumps(self.headers) if self.headers else None,
            "column_mapping": json.dumps(self.column_mapping) if self.column_mapping else None,
            "date_format": self.date_format,
            "validation_results": json.dumps(self.validation_results) if self.validation_results else None,
            "duplicate_resolution": json.dumps(self.duplicate_resolution) if self.duplicate_resolution else None,
            "import_result_id": self.import_result_id,
        }

    @classmethod
    def from_row(cls, row: dict) -> "ImportSession":
        """Create ImportSession from database row."""
        import json
        return cls(
            id=row["id"],
            user_id=row.get("user_id"),
            workspace_id=row.get("workspace_id"),
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row.get("updated_at")),
            expires_at=_parse_datetime(row["expires_at"]),
            current_step=row["current_step"],
            file_reference=row.get("file_reference"),
            original_filename=row.get("original_filename"),
            file_size_bytes=row.get("file_size_bytes"),
            row_count=row.get("row_count"),
            headers=json.loads(row["headers"]) if row.get("headers") else None,
            column_mapping=json.loads(row["column_mapping"]) if row.get("column_mapping") else None,
            date_format=row.get("date_format"),
            validation_results=json.loads(row["validation_results"]) if row.get("validation_results") else None,
            duplicate_resolution=json.loads(row["duplicate_resolution"]) if row.get("duplicate_resolution") else None,
            import_result_id=row.get("import_result_id"),
        )


@dataclass
class MappingProfile:
    """
    Saved column mapping configuration for reuse.

    Stores a named configuration linking CSV column names to
    census field identifiers for future uploads from the same source.
    T005: Extended with workspace_id, date_format, is_default fields.
    """
    id: str
    name: str
    column_mapping: dict[str, str]
    created_at: datetime
    user_id: str | None = None
    workspace_id: str | None = None  # T005: Associate profile with workspace
    description: str | None = None
    date_format: str | None = None  # T005: Preferred date format for this profile
    updated_at: datetime | None = None
    expected_headers: list[str] | None = None
    is_default: bool = False  # T005: Auto-apply on new imports

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        import json
        return {
            "id": self.id,
            "user_id": self.user_id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "description": self.description,
            "date_format": self.date_format,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "column_mapping": json.dumps(self.column_mapping),
            "expected_headers": json.dumps(self.expected_headers) if self.expected_headers else None,
            "is_default": 1 if self.is_default else 0,
        }

    @classmethod
    def from_row(cls, row: dict) -> "MappingProfile":
        """Create MappingProfile from database row."""
        import json
        return cls(
            id=row["id"],
            user_id=row.get("user_id"),
            workspace_id=row.get("workspace_id"),
            name=row["name"],
            description=row.get("description"),
            date_format=row.get("date_format"),
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row.get("updated_at")),
            column_mapping=json.loads(row["column_mapping"]),
            expected_headers=json.loads(row["expected_headers"]) if row.get("expected_headers") else None,
            is_default=bool(row.get("is_default", 0)),
        )


@dataclass
class ValidationIssue:
    """
    Individual data quality problem found during validation.

    Contains severity level, row reference, field reference,
    issue code, and user-friendly message.
    """
    id: str
    session_id: str
    row_number: int
    field_name: str
    severity: Severity
    issue_code: str
    message: str
    source_column: str | None = None
    suggestion: str | None = None
    raw_value: str | None = None
    related_row: int | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "row_number": self.row_number,
            "field_name": self.field_name,
            "source_column": self.source_column,
            "severity": self.severity,
            "issue_code": self.issue_code,
            "message": self.message,
            "suggestion": self.suggestion,
            "raw_value": self.raw_value,
            "related_row": self.related_row,
        }

    @classmethod
    def from_row(cls, row: dict) -> "ValidationIssue":
        """Create ValidationIssue from database row."""
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            row_number=row["row_number"],
            field_name=row["field_name"],
            source_column=row.get("source_column"),
            severity=row["severity"],
            issue_code=row["issue_code"],
            message=row["message"],
            suggestion=row.get("suggestion"),
            raw_value=row.get("raw_value"),
            related_row=row.get("related_row"),
        )


@dataclass
class ImportLog:
    """
    Completed import operation results and audit trail.

    Contains success count, rejection count, warning count,
    timestamp, and reference to detailed log.
    """
    id: str
    original_filename: str
    total_rows: int
    column_mapping_used: dict[str, str]
    created_at: datetime
    session_id: str | None = None
    census_id: str | None = None
    completed_at: datetime | None = None
    imported_count: int = 0
    rejected_count: int = 0
    warning_count: int = 0
    replaced_count: int = 0
    skipped_count: int = 0
    detailed_results: list[dict] | None = None
    deleted_at: datetime | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        import json
        return {
            "id": self.id,
            "session_id": self.session_id,
            "census_id": self.census_id,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "original_filename": self.original_filename,
            "total_rows": self.total_rows,
            "imported_count": self.imported_count,
            "rejected_count": self.rejected_count,
            "warning_count": self.warning_count,
            "replaced_count": self.replaced_count,
            "skipped_count": self.skipped_count,
            "column_mapping_used": json.dumps(self.column_mapping_used),
            "detailed_results": json.dumps(self.detailed_results) if self.detailed_results else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

    @classmethod
    def from_row(cls, row: dict) -> "ImportLog":
        """Create ImportLog from database row."""
        import json
        return cls(
            id=row["id"],
            session_id=row.get("session_id"),
            census_id=row.get("census_id"),
            created_at=_parse_datetime(row["created_at"]),
            completed_at=_parse_datetime(row.get("completed_at")),
            original_filename=row["original_filename"],
            total_rows=row["total_rows"],
            imported_count=row.get("imported_count", 0),
            rejected_count=row.get("rejected_count", 0),
            warning_count=row.get("warning_count", 0),
            replaced_count=row.get("replaced_count", 0),
            skipped_count=row.get("skipped_count", 0),
            column_mapping_used=json.loads(row["column_mapping_used"]),
            detailed_results=json.loads(row["detailed_results"]) if row.get("detailed_results") else None,
            deleted_at=_parse_datetime(row.get("deleted_at")),
        )
