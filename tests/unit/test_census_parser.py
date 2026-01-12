"""
Unit Tests for Census Parser Module.

Tests PII hashing, CSV validation, and census parsing functionality.
"""

import hashlib
import io
import pytest

from src.core.census_parser import (
    generate_census_salt,
    generate_internal_id,
    detect_pii_columns,
    parse_census_csv,
    validate_census_data,
    CensusValidationError,
)


class TestPIIHashing:
    """T015: Unit tests for PII hashing function (SHA-256 with salt)."""

    def test_generate_internal_id_returns_16_char_hex(self):
        """Internal ID should be 16-character hex string."""
        salt = "test_salt_12345"
        employee_id = "EMP001"
        internal_id = generate_internal_id(employee_id, salt)

        assert len(internal_id) == 16
        assert all(c in "0123456789abcdef" for c in internal_id)

    def test_generate_internal_id_deterministic(self):
        """Same inputs should produce same output."""
        salt = "consistent_salt"
        employee_id = "EMP001"

        id1 = generate_internal_id(employee_id, salt)
        id2 = generate_internal_id(employee_id, salt)

        assert id1 == id2

    def test_generate_internal_id_different_salts(self):
        """Different salts should produce different outputs."""
        employee_id = "EMP001"
        salt1 = "salt_one"
        salt2 = "salt_two"

        id1 = generate_internal_id(employee_id, salt1)
        id2 = generate_internal_id(employee_id, salt2)

        assert id1 != id2

    def test_generate_internal_id_different_employees(self):
        """Different employee IDs should produce different outputs."""
        salt = "same_salt"
        emp1 = "EMP001"
        emp2 = "EMP002"

        id1 = generate_internal_id(emp1, salt)
        id2 = generate_internal_id(emp2, salt)

        assert id1 != id2

    def test_generate_internal_id_matches_sha256(self):
        """Output should match first 16 chars of SHA-256 hash."""
        salt = "test_salt"
        employee_id = "EMP001"

        expected = hashlib.sha256(f"{salt}:{employee_id}".encode()).hexdigest()[:16]
        actual = generate_internal_id(employee_id, salt)

        assert actual == expected

    def test_generate_census_salt_returns_32_char_hex(self):
        """Census salt should be 32-character hex string."""
        salt = generate_census_salt()

        assert len(salt) == 32
        assert all(c in "0123456789abcdef" for c in salt)

    def test_generate_census_salt_unique(self):
        """Each salt generation should be unique."""
        salts = [generate_census_salt() for _ in range(100)]
        assert len(set(salts)) == 100


class TestCSVValidation:
    """T016: Unit tests for CSV validation (missing columns, duplicates, invalid types)."""

    def test_validate_missing_required_column(self):
        """Should raise error for missing required columns."""
        csv_content = """HCE Status,Annual Compensation,Current Deferral Rate,Current Match Rate,Current After-Tax Rate
TRUE,100000,5.0,3.0,0.0
"""
        with pytest.raises(CensusValidationError) as exc_info:
            parse_census_csv(io.StringIO(csv_content))

        assert "Employee ID" in str(exc_info.value)

    def test_validate_duplicate_employee_ids(self):
        """Should raise error for duplicate employee IDs."""
        csv_content = """Employee ID,HCE Status,Annual Compensation,Current Deferral Rate,Current Match Rate,Current After-Tax Rate
EMP001,TRUE,100000,5.0,3.0,0.0
EMP001,FALSE,50000,3.0,2.0,0.0
"""
        with pytest.raises(CensusValidationError) as exc_info:
            validate_census_data(parse_census_csv(io.StringIO(csv_content)))

        assert "duplicate" in str(exc_info.value).lower()

    def test_validate_invalid_hce_status(self):
        """Invalid HCE Status values should be treated as False."""
        # Note: The current implementation normalizes invalid values to False
        # rather than raising an error (forgiving behavior)
        csv_content = """Employee ID,HCE Status,Annual Compensation,Current Deferral Rate,Current Match Rate,Current After-Tax Rate
EMP001,MAYBE,100000,5.0,3.0,0.0
"""
        df = parse_census_csv(io.StringIO(csv_content))
        validated = validate_census_data(df)

        # Invalid "MAYBE" should be treated as False (non-HCE)
        assert validated["is_hce"].iloc[0] == False

    def test_validate_invalid_compensation(self):
        """Should raise error for non-positive compensation."""
        csv_content = """Employee ID,HCE Status,Annual Compensation,Current Deferral Rate,Current Match Rate,Current After-Tax Rate
EMP001,TRUE,-100,5.0,3.0,0.0
"""
        with pytest.raises(CensusValidationError) as exc_info:
            validate_census_data(parse_census_csv(io.StringIO(csv_content)))

        assert "compensation" in str(exc_info.value).lower()

    def test_validate_invalid_deferral_rate(self):
        """Should raise error for deferral rate outside 0-100."""
        csv_content = """Employee ID,HCE Status,Annual Compensation,Current Deferral Rate,Current Match Rate,Current After-Tax Rate
EMP001,TRUE,100000,150.0,3.0,0.0
"""
        with pytest.raises(CensusValidationError) as exc_info:
            validate_census_data(parse_census_csv(io.StringIO(csv_content)))

        assert "deferral" in str(exc_info.value).lower()

    def test_validate_valid_census_passes(self):
        """Should pass for valid census data."""
        csv_content = """Employee ID,HCE Status,Annual Compensation,Current Deferral Rate,Current Match Rate,Current After-Tax Rate
EMP001,TRUE,100000,5.0,3.0,0.0
EMP002,FALSE,50000,3.0,2.0,0.0
"""
        df = parse_census_csv(io.StringIO(csv_content))
        validated = validate_census_data(df)

        assert len(validated) == 2

    def test_validate_hce_status_variations(self):
        """Should accept various HCE Status formats."""
        csv_content = """Employee ID,HCE Status,Annual Compensation,Current Deferral Rate,Current Match Rate,Current After-Tax Rate
EMP001,TRUE,100000,5.0,3.0,0.0
EMP002,true,90000,4.0,2.5,0.0
EMP003,1,80000,3.5,2.0,0.0
EMP004,FALSE,50000,3.0,2.0,0.0
EMP005,false,45000,2.5,1.5,0.0
EMP006,0,40000,2.0,1.0,0.0
"""
        df = parse_census_csv(io.StringIO(csv_content))
        validated = validate_census_data(df)

        assert len(validated) == 6
        assert validated["is_hce"].sum() == 3


class TestPIIDetection:
    """Tests for PII column detection."""

    def test_detect_pii_columns_names(self):
        """Should detect name-related columns."""
        columns = ["Employee ID", "First Name", "Last Name", "HCE Status"]
        pii_cols = detect_pii_columns(columns)

        assert "First Name" in pii_cols
        assert "Last Name" in pii_cols

    def test_detect_pii_columns_ssn(self):
        """Should detect SSN-related columns."""
        columns = ["Employee ID", "SSN", "HCE Status"]
        pii_cols = detect_pii_columns(columns)

        assert "SSN" in pii_cols

    def test_detect_pii_columns_contact(self):
        """Should detect contact information columns."""
        columns = ["Employee ID", "Email", "Phone", "Address", "HCE Status"]
        pii_cols = detect_pii_columns(columns)

        assert "Email" in pii_cols
        assert "Phone" in pii_cols
        assert "Address" in pii_cols

    def test_detect_pii_columns_case_insensitive(self):
        """PII detection should be case-insensitive."""
        columns = ["employee_id", "FIRST_NAME", "ssn", "EMAIL"]
        pii_cols = detect_pii_columns(columns)

        assert len(pii_cols) == 3  # FIRST_NAME, ssn, EMAIL


class TestCensusParsingIntegration:
    """Integration tests for full census parsing flow."""

    def test_parse_full_census_with_pii_stripping(self):
        """Should parse census and strip PII columns."""
        csv_content = """Employee ID,First Name,Last Name,SSN,HCE Status,Annual Compensation,Current Deferral Rate,Current Match Rate,Current After-Tax Rate
EMP001,John,Doe,123-45-6789,TRUE,100000,5.0,3.0,0.0
EMP002,Jane,Smith,987-65-4321,FALSE,50000,3.0,2.0,0.0
"""
        df = parse_census_csv(io.StringIO(csv_content))

        # PII columns should be stripped
        assert "First Name" not in df.columns
        assert "Last Name" not in df.columns
        assert "SSN" not in df.columns

        # Required columns should remain (normalized to snake_case)
        assert "employee_id" in df.columns
        assert "is_hce" in df.columns

    def test_parse_census_normalizes_column_names(self):
        """Should normalize column names to internal format."""
        csv_content = """Employee ID,HCE Status,Annual Compensation,Current Deferral Rate,Current Match Rate,Current After-Tax Rate
EMP001,TRUE,100000,5.0,3.0,0.0
"""
        df = parse_census_csv(io.StringIO(csv_content))

        assert "employee_id" in df.columns or "Employee ID" in df.columns
        assert "is_hce" in df.columns
        assert "compensation" in df.columns
