"""
CSV Import Wizard Core Logic.

Provides file parsing, validation, and session management for the import wizard.
"""

import csv
import hashlib
import io
import re
import uuid
from datetime import datetime, timedelta
from typing import Generator

import pandas as pd

from src.storage.models import ImportSession, ValidationIssue


# Session configuration
SESSION_TTL_HOURS = 24

# Supported date formats for auto-detection
DATE_FORMATS = [
    "%m/%d/%Y",      # MM/DD/YYYY
    "%Y-%m-%d",      # YYYY-MM-DD (ISO)
    "%m/%d/%y",      # MM/DD/YY
    "%m-%d-%Y",      # MM-DD-YYYY
    "%m-%d-%y",      # MM-DD-YY
    "%Y/%m/%d",      # YYYY/MM/DD
    "%d/%m/%Y",      # DD/MM/YYYY
    "%d-%m-%Y",      # DD-MM-YYYY
]

# Issue codes for validation
class IssueCode:
    INVALID_SSN = "INVALID_SSN"
    INVALID_DATE = "INVALID_DATE"
    FUTURE_DATE = "FUTURE_DATE"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    NEGATIVE_AMOUNT = "NEGATIVE_AMOUNT"
    MISSING_REQUIRED = "MISSING_REQUIRED"
    DUPLICATE_IN_FILE = "DUPLICATE_IN_FILE"
    DUPLICATE_EXISTING = "DUPLICATE_EXISTING"


# ============================================================================
# Session Management
# ============================================================================

def create_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid.uuid4())


def create_session(
    original_filename: str | None = None,
    file_size_bytes: int | None = None,
    user_id: str | None = None,
) -> ImportSession:
    """
    Create a new import session with default values.

    Args:
        original_filename: Name of the uploaded file
        file_size_bytes: Size of the file in bytes
        user_id: Optional user ID for multi-user environments

    Returns:
        New ImportSession with generated ID and expiration
    """
    now = datetime.utcnow()
    expires_at = now + timedelta(hours=SESSION_TTL_HOURS)

    return ImportSession(
        id=create_session_id(),
        created_at=now,
        updated_at=now,
        expires_at=expires_at,
        current_step="upload",
        user_id=user_id,
        original_filename=original_filename,
        file_size_bytes=file_size_bytes,
    )


def is_session_expired(session: ImportSession) -> bool:
    """Check if a session has expired."""
    return datetime.utcnow() > session.expires_at


# ============================================================================
# CSV Parsing
# ============================================================================

def detect_delimiter(sample: str) -> str:
    """
    Auto-detect the CSV delimiter from a sample of the file.

    Args:
        sample: First few KB of the file content

    Returns:
        Detected delimiter character
    """
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","  # Default to comma


def detect_encoding(file_bytes: bytes) -> str:
    """
    Detect file encoding from byte content.

    Args:
        file_bytes: Raw file bytes

    Returns:
        Detected encoding name
    """
    # Check for BOM markers
    if file_bytes.startswith(b'\xef\xbb\xbf'):
        return "utf-8-sig"
    if file_bytes.startswith(b'\xff\xfe'):
        return "utf-16-le"
    if file_bytes.startswith(b'\xfe\xff'):
        return "utf-16-be"

    # Try common encodings
    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            file_bytes.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue

    return "utf-8"  # Default fallback


def parse_csv_preview(
    file_content: bytes,
    max_rows: int = 5,
) -> tuple[list[str], list[list[str]], int, str, str]:
    """
    Parse CSV file and return headers and sample rows.

    Args:
        file_content: Raw file bytes
        max_rows: Maximum sample rows to return

    Returns:
        Tuple of (headers, sample_rows, total_rows, delimiter, encoding)
    """
    encoding = detect_encoding(file_content)
    content = file_content.decode(encoding)

    delimiter = detect_delimiter(content[:4096])

    # Parse with pandas
    df = pd.read_csv(
        io.StringIO(content),
        delimiter=delimiter,
        dtype=str,
        keep_default_na=False,
    )

    headers = list(df.columns)
    sample_rows = df.head(max_rows).values.tolist()
    total_rows = len(df)

    return headers, sample_rows, total_rows, delimiter, encoding


def parse_csv_file(
    file_content: bytes,
    delimiter: str | None = None,
    encoding: str | None = None,
) -> pd.DataFrame:
    """
    Parse CSV file into a DataFrame.

    Args:
        file_content: Raw file bytes
        delimiter: Optional delimiter override
        encoding: Optional encoding override

    Returns:
        DataFrame with all rows as strings
    """
    if encoding is None:
        encoding = detect_encoding(file_content)

    content = file_content.decode(encoding)

    if delimiter is None:
        delimiter = detect_delimiter(content[:4096])

    df = pd.read_csv(
        io.StringIO(content),
        delimiter=delimiter,
        dtype=str,
        keep_default_na=False,
    )

    return df


# ============================================================================
# Validation Functions
# ============================================================================

def validate_ssn(value: str) -> tuple[bool, str | None]:
    """
    Validate SSN is exactly 9 digits.

    Args:
        value: SSN value to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value or not value.strip():
        return False, "SSN is required"

    # Remove any formatting characters
    clean = re.sub(r"[^0-9]", "", str(value))

    if len(clean) != 9:
        return False, f"SSN must be 9 digits, got {len(clean)}"

    # Check for obviously invalid SSNs (all same digit)
    if len(set(clean)) == 1:
        return False, "SSN cannot be all the same digit"

    return True, None


def validate_date(value: str) -> tuple[bool, str | None, datetime | None]:
    """
    Validate and parse date from multiple formats.

    Args:
        value: Date string to validate

    Returns:
        Tuple of (is_valid, error_message, parsed_date)
    """
    if not value or not value.strip():
        return False, "Date is required", None

    value = str(value).strip()

    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
            if parsed > datetime.now():
                return False, "Date cannot be in the future", None
            return True, None, parsed
        except ValueError:
            continue

    return False, f"Unrecognized date format: {value}. Use MM/DD/YYYY, YYYY-MM-DD, or similar.", None


def validate_amount(value: str, allow_zero: bool = True) -> tuple[bool, str | None, float | None]:
    """
    Validate non-negative dollar amount.

    Args:
        value: Amount string to validate
        allow_zero: Whether zero is a valid value

    Returns:
        Tuple of (is_valid, error_message, parsed_amount)
    """
    if not value or not str(value).strip():
        if allow_zero:
            return True, None, 0.0
        return False, "Amount is required", None

    try:
        # Remove currency symbols and formatting
        clean = str(value).replace(",", "").replace("$", "").replace(" ", "").strip()
        amount = float(clean)

        if amount < 0:
            return False, "Amount cannot be negative", None

        return True, None, amount
    except ValueError:
        return False, f"Invalid amount: {value}", None


def validate_row(
    row: dict,
    mapping: dict[str, str],
    row_number: int,
) -> Generator[ValidationIssue, None, None]:
    """
    Validate a single row, yielding validation issues found.

    Args:
        row: Dictionary of column values
        mapping: Mapping of target field to source column
        row_number: 1-based row number in file

    Yields:
        ValidationIssue objects for each issue found
    """
    session_id = ""  # Will be set by caller

    # SSN validation
    ssn_col = mapping.get("ssn")
    if ssn_col:
        ssn_value = row.get(ssn_col, "")
        valid, msg = validate_ssn(ssn_value)
        if not valid:
            yield ValidationIssue(
                id=str(uuid.uuid4()),
                session_id=session_id,
                row_number=row_number,
                field_name="ssn",
                source_column=ssn_col,
                severity="error",
                issue_code=IssueCode.INVALID_SSN,
                message=msg or "Invalid SSN",
                suggestion="Enter a 9-digit SSN without dashes",
                raw_value=ssn_value,
            )

    # Date validations
    for date_field in ["dob", "hire_date"]:
        col = mapping.get(date_field)
        if col:
            date_value = row.get(col, "")
            valid, msg, _ = validate_date(date_value)
            if not valid:
                issue_code = IssueCode.FUTURE_DATE if "future" in (msg or "").lower() else IssueCode.INVALID_DATE
                yield ValidationIssue(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    row_number=row_number,
                    field_name=date_field,
                    source_column=col,
                    severity="error",
                    issue_code=issue_code,
                    message=msg or "Invalid date",
                    suggestion="Use format MM/DD/YYYY or YYYY-MM-DD",
                    raw_value=date_value,
                )

    # Compensation validation (required, must be > 0)
    comp_col = mapping.get("compensation")
    if comp_col:
        comp_value = row.get(comp_col, "")
        valid, msg, amount = validate_amount(comp_value, allow_zero=False)
        if not valid:
            yield ValidationIssue(
                id=str(uuid.uuid4()),
                session_id=session_id,
                row_number=row_number,
                field_name="compensation",
                source_column=comp_col,
                severity="error",
                issue_code=IssueCode.INVALID_AMOUNT if msg and "Invalid" in msg else IssueCode.NEGATIVE_AMOUNT,
                message=msg or "Invalid compensation",
                suggestion="Enter a positive dollar amount",
                raw_value=comp_value,
            )
        elif amount is not None and amount == 0:
            yield ValidationIssue(
                id=str(uuid.uuid4()),
                session_id=session_id,
                row_number=row_number,
                field_name="compensation",
                source_column=comp_col,
                severity="error",
                issue_code=IssueCode.INVALID_AMOUNT,
                message="Compensation cannot be zero",
                suggestion="Enter a positive compensation amount",
                raw_value=comp_value,
            )

    # Contribution validations (optional, can be 0, must be >= 0)
    contribution_fields = [
        "employee_pre_tax",
        "employee_after_tax",
        "employee_roth",
        "employer_match",
        "employer_non_elective",
    ]

    for field in contribution_fields:
        col = mapping.get(field)
        if col:
            value = row.get(col, "")
            if value and str(value).strip():  # Only validate if provided
                valid, msg, _ = validate_amount(value, allow_zero=True)
                if not valid:
                    yield ValidationIssue(
                        id=str(uuid.uuid4()),
                        session_id=session_id,
                        row_number=row_number,
                        field_name=field,
                        source_column=col,
                        severity="error",
                        issue_code=IssueCode.NEGATIVE_AMOUNT if "negative" in (msg or "").lower() else IssueCode.INVALID_AMOUNT,
                        message=msg or f"Invalid {field.replace('_', ' ')}",
                        suggestion="Enter a non-negative dollar amount",
                        raw_value=value,
                    )


def validate_file(
    df: pd.DataFrame,
    mapping: dict[str, str],
    session_id: str,
) -> tuple[list[ValidationIssue], int, int, int]:
    """
    Validate all rows in a DataFrame.

    Args:
        df: DataFrame with CSV data
        mapping: Column mapping from target field to source column
        session_id: Session ID for associating issues

    Returns:
        Tuple of (issues, error_count, warning_count, info_count)
    """
    issues = []
    error_count = 0
    warning_count = 0
    info_count = 0

    for row_num, row in enumerate(df.to_dict("records"), start=1):
        for issue in validate_row(row, mapping, row_num):
            issue.session_id = session_id
            issues.append(issue)

            if issue.severity == "error":
                error_count += 1
            elif issue.severity == "warning":
                warning_count += 1
            else:
                info_count += 1

    return issues, error_count, warning_count, info_count


# ============================================================================
# SSN Hashing for Duplicate Detection
# ============================================================================

def hash_ssn(ssn: str, salt: str = "") -> str:
    """
    Hash an SSN for privacy-safe duplicate detection.

    Uses SHA-256 with optional salt for consistent hashing.

    Args:
        ssn: The SSN to hash (will be normalized to 9 digits)
        salt: Optional salt value for additional security

    Returns:
        Hex-encoded hash string
    """
    # Normalize SSN to just digits
    clean_ssn = re.sub(r"[^0-9]", "", str(ssn))

    # Combine with salt and hash
    data = f"{salt}:{clean_ssn}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def detect_in_file_duplicates(
    df: pd.DataFrame,
    ssn_column: str,
    session_id: str,
) -> list[ValidationIssue]:
    """
    Detect duplicate SSNs within the uploaded file.

    Args:
        df: DataFrame with CSV data
        ssn_column: Name of the SSN column
        session_id: Session ID for associating issues

    Returns:
        List of ValidationIssue objects for duplicates
    """
    issues = []

    if ssn_column not in df.columns:
        return issues

    # Normalize SSNs for comparison
    df["_ssn_normalized"] = df[ssn_column].apply(
        lambda x: re.sub(r"[^0-9]", "", str(x)) if pd.notna(x) else ""
    )

    # Find duplicates
    duplicates = df[df.duplicated(subset=["_ssn_normalized"], keep=False)]

    if duplicates.empty:
        return issues

    # Group by normalized SSN
    groups = duplicates.groupby("_ssn_normalized")

    for ssn_norm, group in groups:
        if not ssn_norm:  # Skip empty SSNs
            continue

        row_numbers = (group.index + 1).tolist()  # 1-based row numbers

        # First occurrence is not marked as duplicate
        for row_num in row_numbers[1:]:
            original_value = df.loc[row_num - 1, ssn_column]
            issues.append(
                ValidationIssue(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    row_number=row_num,
                    field_name="ssn",
                    source_column=ssn_column,
                    severity="error",
                    issue_code=IssueCode.DUPLICATE_IN_FILE,
                    message=f"Duplicate SSN found in file (same as row {row_numbers[0]})",
                    suggestion="Remove duplicate rows or correct SSN values",
                    raw_value=original_value,
                    related_row=row_numbers[0],
                )
            )

    # Clean up temp column
    df.drop(columns=["_ssn_normalized"], inplace=True)

    return issues


def detect_existing_duplicates(
    df: pd.DataFrame,
    ssn_column: str,
    existing_ssn_hashes: set[str],
    salt: str,
    session_id: str,
) -> list[ValidationIssue]:
    """
    Detect SSNs that already exist in the database.

    Args:
        df: DataFrame with CSV data
        ssn_column: Name of the SSN column
        existing_ssn_hashes: Set of hashed SSNs already in database
        salt: Salt used for hashing
        session_id: Session ID for associating issues

    Returns:
        List of ValidationIssue objects for existing duplicates
    """
    issues = []

    if ssn_column not in df.columns:
        return issues

    for row_num, row in enumerate(df.to_dict("records"), start=1):
        ssn_value = row.get(ssn_column, "")
        if not ssn_value:
            continue

        ssn_hash = hash_ssn(ssn_value, salt)

        if ssn_hash in existing_ssn_hashes:
            issues.append(
                ValidationIssue(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    row_number=row_num,
                    field_name="ssn",
                    source_column=ssn_column,
                    severity="warning",
                    issue_code=IssueCode.DUPLICATE_EXISTING,
                    message="This participant already exists in the database",
                    suggestion="Choose 'Replace' to update existing record or 'Skip' to keep current",
                    raw_value=ssn_value,
                )
            )

    return issues
