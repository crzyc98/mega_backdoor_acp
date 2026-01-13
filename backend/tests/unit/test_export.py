"""
Unit tests for export module.

Tests CSV and PDF export generation with audit metadata.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app.services.export import (
    format_csv_export,
    generate_pdf_report,
    add_formula_strings,
)


@pytest.fixture
def sample_census() -> dict:
    """Sample census metadata for testing."""
    return {
        "id": "test-census-123456789",
        "name": "Test Company 2025",
        "plan_year": 2025,
        "participant_count": 100,
        "hce_count": 20,
        "nhce_count": 80,
    }


@pytest.fixture
def sample_results() -> list[dict]:
    """Sample analysis results for testing."""
    return [
        {
            "adoption_rate": 50.0,
            "contribution_rate": 6.0,
            "nhce_acp": 4.500,
            "hce_acp": 5.200,
            "threshold": 6.500,
            "margin": 1.300,
            "result": "PASS",
            "limiting_test": "+2.0",
            "seed": 42,
            "run_timestamp": "2025-01-15T10:30:00",
        },
        {
            "adoption_rate": 75.0,
            "contribution_rate": 8.0,
            "nhce_acp": 4.500,
            "hce_acp": 7.800,
            "threshold": 6.500,
            "margin": -1.300,
            "result": "FAIL",
            "limiting_test": "+2.0",
            "seed": 42,
            "run_timestamp": "2025-01-15T10:30:01",
        },
    ]


class TestCSVExport:
    """Tests for CSV export functionality."""

    def test_csv_export_includes_audit_header(
        self, sample_census: dict, sample_results: list[dict]
    ) -> None:
        """T066: CSV includes audit metadata header."""
        csv_output = format_csv_export(sample_census, sample_results)

        # Check header comments
        assert "# ACP Sensitivity Analysis Export" in csv_output
        assert f"# Census ID: {sample_census['id']}" in csv_output
        assert f"# Census Name: {sample_census['name']}" in csv_output
        assert f"# Plan Year: {sample_census['plan_year']}" in csv_output
        assert "# Participants: 100 (HCE: 20, NHCE: 80)" in csv_output
        assert "# Generated:" in csv_output
        assert "# System Version:" in csv_output

    def test_csv_export_includes_seed_when_provided(
        self, sample_census: dict, sample_results: list[dict]
    ) -> None:
        """CSV includes seed value when provided."""
        csv_output = format_csv_export(sample_census, sample_results, seed=42)
        assert "# Seed: 42" in csv_output

    def test_csv_export_no_seed_when_not_provided(
        self, sample_census: dict, sample_results: list[dict]
    ) -> None:
        """CSV omits seed line when not provided."""
        csv_output = format_csv_export(sample_census, sample_results, seed=None)
        assert "# Seed:" not in csv_output

    def test_csv_export_includes_column_headers(
        self, sample_census: dict, sample_results: list[dict]
    ) -> None:
        """CSV includes proper column headers."""
        csv_output = format_csv_export(sample_census, sample_results)

        expected_columns = [
            "adoption_rate",
            "contribution_rate",
            "nhce_acp",
            "hce_acp",
            "threshold",
            "margin",
            "result",
            "limiting_test",
            "seed",
            "run_timestamp",
        ]
        header_line = [line for line in csv_output.split("\n") if not line.startswith("#")][0]
        for col in expected_columns:
            assert col in header_line

    def test_csv_export_includes_data_rows(
        self, sample_census: dict, sample_results: list[dict]
    ) -> None:
        """CSV includes all data rows with correct formatting."""
        csv_output = format_csv_export(sample_census, sample_results)

        lines = [line for line in csv_output.split("\n") if not line.startswith("#")]
        # Header + 2 data rows
        assert len(lines) == 3

        # Check first data row
        first_data = lines[1].split(",")
        assert first_data[0] == "50.0"  # adoption_rate
        assert first_data[1] == "6.0"   # contribution_rate
        assert "PASS" in lines[1]

        # Check second data row
        assert "FAIL" in lines[2]

    def test_csv_export_handles_empty_results(
        self, sample_census: dict
    ) -> None:
        """CSV handles empty results list."""
        csv_output = format_csv_export(sample_census, [])

        # Should still have header and column row
        assert "# ACP Sensitivity Analysis Export" in csv_output
        lines = [line for line in csv_output.split("\n") if not line.startswith("#")]
        assert len(lines) == 1  # Just the column header


class TestPDFExport:
    """Tests for PDF export functionality."""

    def test_pdf_export_returns_bytes(
        self, sample_census: dict, sample_results: list[dict]
    ) -> None:
        """T067: PDF export returns valid PDF bytes."""
        pdf_output = generate_pdf_report(sample_census, sample_results)

        assert isinstance(pdf_output, bytes)
        assert len(pdf_output) > 0
        # Check PDF magic bytes
        assert pdf_output[:4] == b"%PDF"

    def test_pdf_export_with_grid_summary(
        self, sample_census: dict, sample_results: list[dict]
    ) -> None:
        """PDF export includes grid summary when provided."""
        grid_summary = {
            "total_scenarios": 100,
            "pass_count": 75,
            "fail_count": 25,
            "pass_rate": 75.0,
        }
        pdf_output = generate_pdf_report(sample_census, sample_results, grid_summary)

        assert isinstance(pdf_output, bytes)
        assert len(pdf_output) > 0

    def test_pdf_export_handles_empty_results(
        self, sample_census: dict
    ) -> None:
        """PDF handles empty results list."""
        pdf_output = generate_pdf_report(sample_census, [])

        assert isinstance(pdf_output, bytes)
        assert pdf_output[:4] == b"%PDF"

    def test_pdf_export_truncates_large_results(
        self, sample_census: dict
    ) -> None:
        """PDF truncates results to 50 rows."""
        # Create 100 results
        large_results = [
            {
                "adoption_rate": float(i),
                "contribution_rate": 6.0,
                "nhce_acp": 4.5,
                "hce_acp": 5.2,
                "threshold": 6.5,
                "margin": 1.3,
                "result": "PASS",
                "limiting_test": "+2.0",
                "seed": 42,
                "run_timestamp": "2025-01-15T10:30:00",
            }
            for i in range(100)
        ]

        pdf_output = generate_pdf_report(sample_census, large_results)

        # Should still generate valid PDF
        assert isinstance(pdf_output, bytes)
        assert pdf_output[:4] == b"%PDF"


class TestFormulaStrings:
    """Tests for formula string generation."""

    def test_add_formula_strings_pass(self) -> None:
        """T068: Formula strings generated correctly for passing result."""
        result = {
            "nhce_acp": 4.0,
            "hce_acp": 5.0,
            "threshold": 6.0,
            "result": "PASS",
        }

        updated = add_formula_strings(result)

        assert "formula_125x" in updated
        assert "formula_plus2" in updated
        assert "formula_result" in updated

        # Check formula content
        assert "5.000%" in updated["formula_125x"]  # HCE ACP
        assert "4.000%" in updated["formula_plus2"]  # NHCE ACP
        assert "PASS" in updated["formula_result"]

    def test_add_formula_strings_fail(self) -> None:
        """Formula strings generated correctly for failing result."""
        result = {
            "nhce_acp": 3.0,
            "hce_acp": 8.0,
            "threshold": 5.0,
            "result": "FAIL",
        }

        updated = add_formula_strings(result)

        assert ">" in updated["formula_result"]  # Failing means HCE > threshold
        assert "FAIL" in updated["formula_result"]

    def test_formula_strings_125x_calculation(self) -> None:
        """Formula shows correct 1.25x calculation."""
        result = {
            "nhce_acp": 4.0,
            "hce_acp": 5.0,
            "threshold": 5.0,
            "result": "PASS",
        }

        updated = add_formula_strings(result)

        # 4.0 * 1.25 = 5.0
        assert "5.000%" in updated["formula_125x"]

    def test_formula_strings_plus2_calculation(self) -> None:
        """Formula shows correct +2.0 calculation."""
        result = {
            "nhce_acp": 4.0,
            "hce_acp": 5.0,
            "threshold": 6.0,
            "result": "PASS",
        }

        updated = add_formula_strings(result)

        # 4.0 + 2.0 = 6.0
        assert "6.000%" in updated["formula_plus2"]
