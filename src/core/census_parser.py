"""
Census CSV Parser with PII Stripping.

This module handles parsing of census CSV files, detecting and stripping PII columns,
and validating the census data structure.
"""

import hashlib
import secrets
from typing import TextIO

import pandas as pd


class CensusValidationError(Exception):
    """Exception raised for census data validation errors."""
    pass


# Required columns for census data
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
    # Dates
    "birth_date", "dob", "date_of_birth", "birthdate", "birth date",
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
    census_salt: str | None = None
) -> tuple[pd.DataFrame, str]:
    """
    Complete census processing: parse, validate, and hash IDs.

    Args:
        file: File-like object containing CSV data
        census_salt: Optional salt for ID hashing (generated if not provided)

    Returns:
        Tuple of (processed DataFrame with internal IDs, census salt)

    Raises:
        CensusValidationError: If parsing or validation fails
    """
    # Generate salt if not provided
    if census_salt is None:
        census_salt = generate_census_salt()

    # Parse and validate
    df = parse_census_csv(file)
    df = validate_census_data(df)

    # Generate internal IDs
    df["internal_id"] = df["employee_id"].apply(
        lambda emp_id: generate_internal_id(str(emp_id), census_salt)
    )

    # Convert compensation to cents for integer storage
    df["compensation_cents"] = (df["compensation"] * 100).astype(int)

    return df, census_salt
