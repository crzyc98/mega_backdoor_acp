"""
Integration tests for export API endpoints.

Tests CSV and PDF export via API with proper audit metadata.
"""

import io
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.routers.main import app
from app.storage import database


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    """Reset database for each test."""
    # Close existing connection
    database.close_db()

    # Create temp database
    temp_dir = tempfile.mkdtemp()
    test_db_path = Path(temp_dir) / "test_export.db"

    # Initialize fresh database
    database.init_database(str(test_db_path))
    database._connection = database.create_connection(str(test_db_path))

    yield

    # Cleanup
    database.close_db()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_csv_content() -> bytes:
    """Sample CSV census file with required columns."""
    return b"""Employee ID,HCE Status,Annual Compensation,Current Deferral Rate,Current Match Rate,Current After-Tax Rate
E001,TRUE,180000,10,4,0
E002,FALSE,75000,6,3,2
E003,TRUE,200000,10,4,3
E004,FALSE,65000,5,2.5,1
E005,TRUE,150000,8,4,2
"""


@pytest.fixture
def uploaded_census(client, sample_csv_content) -> dict:
    """Upload a census and return the response data."""
    response = client.post(
        "/api/v1/census",
        files={"file": ("test_census.csv", io.BytesIO(sample_csv_content), "text/csv")},
        data={"name": "Export Test Census", "plan_year": "2025"},
    )
    assert response.status_code == 201
    data = response.json()
    # Map to expected keys for convenience
    return {"census_id": data["id"], "name": data["name"]}


@pytest.fixture
def census_with_results(client, uploaded_census) -> dict:
    """Census with analysis results."""
    census_id = uploaded_census["census_id"]

    # Run single scenario analysis
    response = client.post(
        f"/api/v1/census/{census_id}/analysis",
        json={
            "adoption_rate": 50.0,
            "contribution_rate": 6.0,
            "seed": 42,
        },
    )
    assert response.status_code == 200

    return {"census_id": census_id, "census_name": uploaded_census["name"]}


@pytest.fixture
def census_with_grid_results(client, uploaded_census) -> dict:
    """Census with grid analysis results."""
    census_id = uploaded_census["census_id"]

    # Run grid analysis
    response = client.post(
        f"/api/v1/census/{census_id}/grid",
        json={
            "adoption_rates": [25.0, 50.0, 75.0],
            "contribution_rates": [4.0, 6.0, 8.0],
            "seed": 42,
        },
    )
    assert response.status_code == 200

    return {
        "census_id": census_id,
        "census_name": uploaded_census["name"],
        "grid_id": response.json()["id"],  # Response uses "id" not "grid_id"
    }


class TestCSVExportAPI:
    """Tests for CSV export API endpoint."""

    def test_export_csv_success(self, client, census_with_results) -> None:
        """T072: Export CSV returns valid CSV content."""
        census_id = census_with_results["census_id"]

        response = client.get(f"/api/v1/export/{census_id}/csv")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert ".csv" in response.headers["content-disposition"]

        # Verify CSV content
        content = response.text
        assert "# ACP Sensitivity Analysis Export" in content
        assert f"# Census ID: {census_id}" in content
        assert "adoption_rate" in content

    def test_export_csv_includes_audit_metadata(
        self, client, census_with_results
    ) -> None:
        """CSV export includes full audit metadata."""
        census_id = census_with_results["census_id"]

        response = client.get(f"/api/v1/export/{census_id}/csv")
        content = response.text

        # Check audit metadata
        assert "# Census Name:" in content
        assert "# Plan Year:" in content
        assert "# Participants:" in content
        assert "# Generated:" in content
        assert "# System Version:" in content

    def test_export_csv_grid_results(self, client, census_with_grid_results) -> None:
        """CSV export with grid_id includes seed."""
        census_id = census_with_grid_results["census_id"]
        grid_id = census_with_grid_results["grid_id"]

        response = client.get(f"/api/v1/export/{census_id}/csv?grid_id={grid_id}")

        assert response.status_code == 200
        content = response.text
        assert "# Seed: 42" in content

    def test_export_csv_census_not_found(self, client) -> None:
        """CSV export returns 404 for non-existent census."""
        response = client.get("/api/v1/export/nonexistent-id/csv")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_export_csv_no_results(self, client, uploaded_census) -> None:
        """CSV export returns 404 when no analysis results exist."""
        census_id = uploaded_census["census_id"]

        response = client.get(f"/api/v1/export/{census_id}/csv")

        assert response.status_code == 404
        assert "No analysis results" in response.json()["detail"]


class TestPDFExportAPI:
    """Tests for PDF export API endpoint."""

    def test_export_pdf_success(self, client, census_with_results) -> None:
        """T073: Export PDF returns valid PDF content."""
        census_id = census_with_results["census_id"]

        response = client.get(f"/api/v1/export/{census_id}/pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert ".pdf" in response.headers["content-disposition"]

        # Verify PDF magic bytes
        assert response.content[:4] == b"%PDF"

    def test_export_pdf_grid_results(self, client, census_with_grid_results) -> None:
        """PDF export works with grid analysis results."""
        census_id = census_with_grid_results["census_id"]
        grid_id = census_with_grid_results["grid_id"]

        response = client.get(f"/api/v1/export/{census_id}/pdf?grid_id={grid_id}")

        assert response.status_code == 200
        assert response.content[:4] == b"%PDF"

    def test_export_pdf_census_not_found(self, client) -> None:
        """PDF export returns 404 for non-existent census."""
        response = client.get("/api/v1/export/nonexistent-id/pdf")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_export_pdf_no_results(self, client, uploaded_census) -> None:
        """PDF export returns 404 when no analysis results exist."""
        census_id = uploaded_census["census_id"]

        response = client.get(f"/api/v1/export/{census_id}/pdf")

        assert response.status_code == 404
        assert "No analysis results" in response.json()["detail"]


class TestExportFilenames:
    """Tests for export filename generation."""

    def test_csv_filename_format(self, client, census_with_results) -> None:
        """CSV filename includes date."""
        census_id = census_with_results["census_id"]

        response = client.get(f"/api/v1/export/{census_id}/csv")

        disposition = response.headers["content-disposition"]
        # Should be like: attachment; filename="acp_results_2025-01-15.csv"
        assert "acp_results_" in disposition
        assert ".csv" in disposition

    def test_pdf_filename_format(self, client, census_with_results) -> None:
        """PDF filename includes date."""
        census_id = census_with_results["census_id"]

        response = client.get(f"/api/v1/export/{census_id}/pdf")

        disposition = response.headers["content-disposition"]
        # Should be like: attachment; filename="acp_report_2025-01-15.pdf"
        assert "acp_report_" in disposition
        assert ".pdf" in disposition
