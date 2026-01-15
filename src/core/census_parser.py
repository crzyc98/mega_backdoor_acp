"""
Census CSV Parser with PII Stripping.

This module handles parsing of census CSV files, detecting and stripping PII columns,
and validating the census data structure. Supports column mapping and HCE determination modes.
"""

import hashlib
import secrets
from typing import Literal, TextIO

import pandas as pd

from src.core.hce_thresholds import get_threshold_for_year, HCEMode


class CensusValidationError(Exception):
    """Exception raised for census data validation errors."""
    pass


# Target fields for census data
TARGET_FIELDS = {
    "employee_id": "Employee ID",
    "is_hce": "HCE Status",
    "dob": "Date of Birth",
    "hire_date": "Hire Date",
    "termination_date": "Termination Date",
    "compensation": "Annual Compensation",
    "deferral_rate": "Current Deferral Rate",
    "match_rate": "Current Match Rate",
    "after_tax_rate": "Current After-Tax Rate",
}

# Required fields (must be present for import)
REQUIRED_FIELDS = ["employee_id", "compensation", "deferral_rate"]

# Fields required only in explicit HCE mode
EXPLICIT_HCE_REQUIRED = ["is_hce"]

# Optional fields
OPTIONAL_FIELDS = ["dob", "hire_date", "termination_date", "match_rate", "after_tax_rate"]

# Default column mapping (for backwards compatibility)
REQUIRED_COLUMNS = {
    "Employee ID": "employee_id",
    "HCE Status": "is_hce",
    "Annual Compensation": "compensation",
    "Current Deferral Rate": "deferral_rate",
    "Current Match Rate": "match_rate",
    "Current After-Tax Rate": "after_tax_rate",
}

# PII column patterns to detect and strip
PII_PATTERNS = [
    # Names
    "name", "first_name", "last_name", "full_name", "firstname", "lastname",
    "first name", "last name", "full name",
    # SSN
    "ssn", "social_security", "tax_id", "social security", "taxid",
    # Contact
    "email", "phone", "address", "city", "state", "zip", "zipcode",
    "street", "apt", "apartment",
]


def generate_census_salt() -> str:
    """
    Generate unique salt for each census upload.

    Returns:
        32-character hex string salt
    """
    return secrets.token_hex(16)


def generate_internal_id(employee_id: str, census_salt: str) -> str:
    """
    Generate non-reversible internal ID from employee identifier.

    Uses SHA-256 hash with per-census salt to create a deterministic
    but non-reversible identifier.

    Args:
        employee_id: Original employee identifier
        census_salt: Per-census salt for the hash

    Returns:
        16-character hex string internal ID
    """
    combined = f"{census_salt}:{employee_id}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def detect_pii_columns(columns: list[str]) -> list[str]:
    """
    Detect PII columns in a list of column names.

    Args:
        columns: List of column names from CSV

    Returns:
        List of column names that appear to contain PII
    """
    pii_columns = []
    for col in columns:
        col_lower = col.lower().replace("_", " ").replace("-", " ")
        for pattern in PII_PATTERNS:
            if pattern in col_lower:
                pii_columns.append(col)
                break
    return pii_columns


def detect_column_mapping(
    columns: list[str],
    hce_mode: HCEMode = "explicit",
) -> dict:
    """
    Detect column mapping from CSV headers.

    Auto-detects which source columns map to required target fields
    based on common naming patterns.

    Args:
        columns: List of column names from CSV
        hce_mode: HCE determination mode (affects required fields)

    Returns:
        Dictionary with:
        - source_columns: List of all source columns
        - suggested_mapping: Dict mapping target_field -> source_column
        - required_fields: List of required target fields
        - missing_fields: List of required fields not auto-detected
    """
    # Common column name patterns for each target field
    COLUMN_PATTERNS = {
        "employee_id": ["employee id", "emp id", "employee_id", "empid", "id", "employee"],
        "compensation": ["compensation", "salary", "annual compensation", "annual salary", "pay", "wages"],
        "deferral_rate": ["deferral rate", "deferral", "deferral_rate", "401k rate", "contribution rate"],
        "is_hce": ["hce", "hce status", "hce_status", "highly compensated", "is_hce"],
        "dob": ["dob", "date of birth", "birth date", "birthdate", "birth_date", "date_of_birth"],
        "hire_date": ["hire date", "hire_date", "hiredate", "date hired", "start date", "employment date"],
        "termination_date": ["termination date", "termination_date", "term date", "term_date", "date terminated"],
        "match_rate": ["match rate", "match", "match_rate", "employer match"],
        "after_tax_rate": ["after tax", "after_tax", "after-tax", "after tax rate", "after_tax_rate"],
    }

    suggested_mapping = {}
    columns_lower = {col.lower().replace("_", " ").replace("-", " "): col for col in columns}

    # Try to match each target field
    for target_field, patterns in COLUMN_PATTERNS.items():
        for pattern in patterns:
            # Check exact match first
            if pattern in columns_lower:
                suggested_mapping[target_field] = columns_lower[pattern]
                break
            # Check partial match
            for col_lower, col_original in columns_lower.items():
                if pattern in col_lower and target_field not in suggested_mapping:
                    suggested_mapping[target_field] = col_original
                    break
        # Also check for exact original column names
        for col in columns:
            if col in REQUIRED_COLUMNS and REQUIRED_COLUMNS[col] == target_field:
                suggested_mapping[target_field] = col
                break

    # Determine required fields based on HCE mode
    required_fields = REQUIRED_FIELDS.copy()
    if hce_mode == "explicit":
        required_fields.extend(EXPLICIT_HCE_REQUIRED)

    # Find missing fields
    missing_fields = [f for f in required_fields if f not in suggested_mapping]

    return {
        "source_columns": columns,
        "suggested_mapping": suggested_mapping,
        "required_fields": required_fields,
        "missing_fields": missing_fields,
    }


def parse_census_csv(file: TextIO) -> pd.DataFrame:
    """
    Parse census CSV file and strip PII columns.

    Args:
        file: File-like object containing CSV data

    Returns:
        DataFrame with normalized column names and PII stripped

    Raises:
        CensusValidationError: If required columns are missing
    """
    # Read CSV
    df = pd.read_csv(file)

    # Check for required columns
    missing_columns = []
    for required_col in REQUIRED_COLUMNS.keys():
        if required_col not in df.columns:
            missing_columns.append(required_col)

    if missing_columns:
        raise CensusValidationError(
            f"Missing required columns: {', '.join(missing_columns)}"
        )

    # Detect and remove PII columns
    pii_columns = detect_pii_columns(list(df.columns))
    df = df.drop(columns=pii_columns, errors="ignore")

    # Normalize column names
    column_mapping = {}
    for original, normalized in REQUIRED_COLUMNS.items():
        if original in df.columns:
            column_mapping[original] = normalized
    df = df.rename(columns=column_mapping)

    # Normalize HCE Status to boolean
    if "is_hce" in df.columns:
        df["is_hce"] = df["is_hce"].apply(_normalize_hce_status)

    return df


def _normalize_hce_status(value) -> bool:
    """
    Normalize HCE status value to boolean.

    Accepts: TRUE/FALSE, true/false, 1/0, Yes/No

    Args:
        value: Raw HCE status value

    Returns:
        Boolean HCE status
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "y")
    return False


def validate_census_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate census data and raise errors for invalid data.

    Args:
        df: DataFrame with normalized column names

    Returns:
        Validated DataFrame

    Raises:
        CensusValidationError: If validation fails
    """
    errors = []

    # Check for duplicate Employee IDs
    if "employee_id" in df.columns:
        duplicates = df[df.duplicated(subset=["employee_id"], keep=False)]
        if not duplicates.empty:
            duplicate_ids = duplicates["employee_id"].unique().tolist()
            errors.append(f"Duplicate Employee IDs found: {duplicate_ids[:5]}")

    # Validate HCE Status
    if "is_hce" in df.columns:
        # Check for any NaN values that couldn't be converted
        invalid_hce = df[df["is_hce"].isna()]
        if not invalid_hce.empty:
            errors.append("Invalid HCE Status values found (could not be converted to boolean)")

    # Validate compensation is positive
    if "compensation" in df.columns:
        invalid_comp = df[df["compensation"] <= 0]
        if not invalid_comp.empty:
            errors.append(f"Non-positive compensation values found: {len(invalid_comp)} rows")

    # Validate deferral rate is 0-100
    if "deferral_rate" in df.columns:
        invalid_deferral = df[(df["deferral_rate"] < 0) | (df["deferral_rate"] > 100)]
        if not invalid_deferral.empty:
            errors.append(f"Deferral rate outside 0-100 range: {len(invalid_deferral)} rows")

    # Validate match rate is non-negative
    if "match_rate" in df.columns:
        invalid_match = df[df["match_rate"] < 0]
        if not invalid_match.empty:
            errors.append(f"Negative match rate values found: {len(invalid_match)} rows")

    # Validate after-tax rate is non-negative
    if "after_tax_rate" in df.columns:
        invalid_after_tax = df[df["after_tax_rate"] < 0]
        if not invalid_after_tax.empty:
            errors.append(f"Negative after-tax rate values found: {len(invalid_after_tax)} rows")

    if errors:
        raise CensusValidationError("\n".join(errors))

    return df


def process_census(
    file: TextIO,
    census_salt: str | None = None,
    hce_mode: HCEMode = "explicit",
    plan_year: int | None = None,
    column_mapping: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, str, dict[str, str]]:
    """
    Complete census processing: parse, validate, and hash IDs.

    Args:
        file: File-like object containing CSV data
        census_salt: Optional salt for ID hashing (generated if not provided)
        hce_mode: HCE determination mode ('explicit' or 'compensation_threshold')
        plan_year: Plan year (required for compensation_threshold mode)
        column_mapping: Optional custom column mapping (target_field -> source_column)

    Returns:
        Tuple of (processed DataFrame with internal IDs, census salt, column mapping used)

    Raises:
        CensusValidationError: If parsing or validation fails
    """
    # Generate salt if not provided
    if census_salt is None:
        census_salt = generate_census_salt()

    # Read CSV into DataFrame
    df = pd.read_csv(file)

    # Get column mapping (auto-detect if not provided)
    if column_mapping is None:
        detection = detect_column_mapping(list(df.columns), hce_mode)
        column_mapping = detection["suggested_mapping"]
        missing_fields = detection["missing_fields"]
    else:
        # Validate provided mapping has required fields
        required_fields = REQUIRED_FIELDS.copy()
        if hce_mode == "explicit":
            required_fields.extend(EXPLICIT_HCE_REQUIRED)
        missing_fields = [f for f in required_fields if f not in column_mapping]

    if missing_fields:
        raise CensusValidationError(
            f"Missing required field mappings: {', '.join(missing_fields)}"
        )

    # Apply column mapping (rename source columns to target field names)
    reverse_mapping = {source: target for target, source in column_mapping.items()}
    df = df.rename(columns=reverse_mapping)

    # Detect and remove PII columns
    pii_columns = detect_pii_columns(list(df.columns))
    df = df.drop(columns=pii_columns, errors="ignore")

    # Fill missing optional columns with defaults
    if "match_rate" not in df.columns:
        df["match_rate"] = 0.0
    if "after_tax_rate" not in df.columns:
        df["after_tax_rate"] = 0.0

    # Handle HCE determination based on mode
    if hce_mode == "compensation_threshold":
        if plan_year is None:
            raise CensusValidationError(
                "plan_year is required when using compensation_threshold mode"
            )
        threshold = get_threshold_for_year(plan_year)
        df["is_hce"] = df["compensation"].apply(lambda x: x >= threshold if pd.notna(x) else False)
    else:
        # Explicit mode - normalize HCE status
        if "is_hce" in df.columns:
            df["is_hce"] = df["is_hce"].apply(_normalize_hce_status)
        else:
            raise CensusValidationError(
                "HCE Status column is required in explicit mode"
            )

    # Validate data
    df = validate_census_data(df)

    # Generate internal IDs
    df["internal_id"] = df["employee_id"].apply(
        lambda emp_id: generate_internal_id(str(emp_id), census_salt)
    )

    # Convert compensation to cents for integer storage
    df["compensation_cents"] = (df["compensation"] * 100).astype(int)

    return df, census_salt, column_mapping


def process_census_simple(
    file: TextIO,
    census_salt: str | None = None,
) -> tuple[pd.DataFrame, str]:
    """
    Simple census processing (backwards compatible).

    Uses explicit HCE mode with default column mapping.

    Args:
        file: File-like object containing CSV data
        census_salt: Optional salt for ID hashing (generated if not provided)

    Returns:
        Tuple of (processed DataFrame with internal IDs, census salt)

    Raises:
        CensusValidationError: If parsing or validation fails
    """
    df, salt, _ = process_census(file, census_salt, hce_mode="explicit")
    return df, salt
