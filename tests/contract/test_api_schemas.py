"""
Contract tests validating API schemas match OpenAPI specification.

T078: Validates that API responses match the openapi.yaml contract.
"""

import io
import tempfile
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.schemas import (
    AnalysisResult,
    Census,
    CensusListResponse,
    CensusSummary,
    GridAnalysisResult,
    GridSummary,
    HealthResponse,
)
from src.storage import database


@pytest.fixture(scope="module")
def openapi_spec() -> dict:
    """Load the OpenAPI specification."""
    spec_path = Path(__file__).parent.parent.parent / "specs/001-acp-sensitivity-analyzer/contracts/openapi.yaml"
    with open(spec_path) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    """Reset database for each test."""
    database.close_db()
    temp_dir = tempfile.mkdtemp()
    test_db_path = Path(temp_dir) / "test_contract.db"
    database.init_database(str(test_db_path))
    database._connection = database.create_connection(str(test_db_path))
    yield
    database.close_db()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_csv_content() -> bytes:
    """Sample CSV census file with required columns."""
    return b"""Employee ID,HCE Status,Date of Birth,Hire Date,Termination Date,Annual Compensation,Current Deferral Rate,Current Match Rate,Current After-Tax Rate
E001,TRUE,1990-01-01,2010-01-01,,180000,10,4,0
E002,FALSE,1990-01-01,2010-01-01,,75000,6,3,2
E003,TRUE,1990-01-01,2010-01-01,,200000,10,4,3
E004,FALSE,1990-01-01,2010-01-01,,65000,5,2.5,1
E005,TRUE,1990-01-01,2010-01-01,,150000,8,4,2
"""


class TestCensusSchemaContract:
    """Contract tests for Census schemas."""

    def test_census_response_matches_schema(
        self, client, sample_csv_content, openapi_spec
    ) -> None:
        """Verify Census response matches OpenAPI spec."""
        response = client.post(
            "/api/v1/census",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            data={"name": "Test Census", "plan_year": "2025"},
        )
        assert response.status_code == 201

        data = response.json()
        census = Census(**data)  # Validates against schema

        # Verify required fields from OpenAPI spec
        spec_schema = openapi_spec["components"]["schemas"]["Census"]
        required_fields = spec_schema.get("required", [])

        for field in required_fields:
            assert hasattr(census, field), f"Missing required field: {field}"
            assert getattr(census, field) is not None, f"Required field {field} is None"

    def test_census_list_response_matches_schema(
        self, client, sample_csv_content, openapi_spec
    ) -> None:
        """Verify CensusListResponse matches OpenAPI spec."""
        # First upload a census
        client.post(
            "/api/v1/census",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            data={"name": "Test Census", "plan_year": "2025"},
        )

        # Then list censuses
        response = client.get("/api/v1/census")
        assert response.status_code == 200

        data = response.json()
        census_list = CensusListResponse(**data)

        assert census_list.items is not None
        assert isinstance(census_list.total, int)
        assert isinstance(census_list.limit, int)
        assert isinstance(census_list.offset, int)

    def test_census_summary_matches_schema(
        self, client, sample_csv_content, openapi_spec
    ) -> None:
        """Verify CensusSummary matches OpenAPI spec."""
        # Upload a census
        client.post(
            "/api/v1/census",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            data={"name": "Test Census", "plan_year": "2025"},
        )

        response = client.get("/api/v1/census")
        data = response.json()

        for item in data["items"]:
            summary = CensusSummary(**item)

            # Check required fields
            spec_schema = openapi_spec["components"]["schemas"]["CensusSummary"]
            required_fields = spec_schema.get("required", [])

            for field in required_fields:
                assert hasattr(summary, field), f"Missing required field: {field}"


class TestAnalysisSchemaContract:
    """Contract tests for Analysis schemas."""

    @pytest.fixture
    def uploaded_census(self, client, sample_csv_content) -> dict:
        """Upload a census and return the response data."""
        response = client.post(
            "/api/v1/census",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            data={"name": "Contract Test Census", "plan_year": "2025"},
        )
        assert response.status_code == 201
        return response.json()

    def test_analysis_result_matches_schema(
        self, client, uploaded_census, openapi_spec
    ) -> None:
        """Verify AnalysisResult matches OpenAPI spec."""
        census_id = uploaded_census["id"]

        response = client.post(
            f"/api/v1/census/{census_id}/analysis",
            json={"adoption_rate": 50.0, "contribution_rate": 6.0, "seed": 42},
        )
        assert response.status_code == 200

        data = response.json()
        result = AnalysisResult(**data)

        # Check required fields
        spec_schema = openapi_spec["components"]["schemas"]["AnalysisResult"]
        required_fields = spec_schema.get("required", [])

        for field in required_fields:
            assert hasattr(result, field), f"Missing required field: {field}"

        # Verify enum values match spec
        assert result.result in ["PASS", "FAIL"]
        assert result.limiting_test in ["1.25x", "+2.0"]

    def test_grid_analysis_result_matches_schema(
        self, client, uploaded_census, openapi_spec
    ) -> None:
        """Verify GridAnalysisResult matches OpenAPI spec."""
        census_id = uploaded_census["id"]

        response = client.post(
            f"/api/v1/census/{census_id}/grid",
            json={
                "adoption_rates": [25.0, 50.0, 75.0],
                "contribution_rates": [4.0, 6.0, 8.0],
                "seed": 42,
            },
        )
        assert response.status_code == 200

        data = response.json()
        result = GridAnalysisResult(**data)

        # Check required fields
        spec_schema = openapi_spec["components"]["schemas"]["GridAnalysisResult"]
        required_fields = spec_schema.get("required", [])

        for field in required_fields:
            assert hasattr(result, field), f"Missing required field: {field}"

        # Verify nested summary
        assert isinstance(result.summary, GridSummary)
        assert result.summary.total_scenarios == 9  # 3x3 grid

        # Verify nested results
        assert len(result.results) == 9
        for item in result.results:
            assert isinstance(item, AnalysisResult)


class TestHealthSchemaContract:
    """Contract tests for Health endpoint."""

    def test_health_response_matches_schema(self, client, openapi_spec) -> None:
        """Verify HealthResponse matches OpenAPI spec."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        health = HealthResponse(**data)

        assert health.status == "healthy"
        assert health.version is not None


class TestRequestValidation:
    """Contract tests for request validation."""

    @pytest.fixture
    def uploaded_census(self, client, sample_csv_content) -> dict:
        """Upload a census and return the response data."""
        response = client.post(
            "/api/v1/census",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            data={"name": "Validation Test Census", "plan_year": "2025"},
        )
        assert response.status_code == 201
        return response.json()

    def test_single_scenario_validates_adoption_rate_range(
        self, client, uploaded_census
    ) -> None:
        """Adoption rate must be 0-100 per spec."""
        census_id = uploaded_census["id"]

        # Over 100 should fail
        response = client.post(
            f"/api/v1/census/{census_id}/analysis",
            json={"adoption_rate": 150.0, "contribution_rate": 6.0},
        )
        assert response.status_code == 422

        # Under 0 should fail
        response = client.post(
            f"/api/v1/census/{census_id}/analysis",
            json={"adoption_rate": -10.0, "contribution_rate": 6.0},
        )
        assert response.status_code == 422

    def test_single_scenario_validates_contribution_rate_range(
        self, client, uploaded_census
    ) -> None:
        """Contribution rate must be 0-15 per spec."""
        census_id = uploaded_census["id"]

        # Over 15 should fail
        response = client.post(
            f"/api/v1/census/{census_id}/analysis",
            json={"adoption_rate": 50.0, "contribution_rate": 20.0},
        )
        assert response.status_code == 422

    def test_grid_scenario_validates_array_length(
        self, client, uploaded_census
    ) -> None:
        """Grid must have 2-20 items per dimension per spec."""
        census_id = uploaded_census["id"]

        # Less than 2 items should fail
        response = client.post(
            f"/api/v1/census/{census_id}/grid",
            json={
                "adoption_rates": [50.0],  # Only 1
                "contribution_rates": [4.0, 6.0],
            },
        )
        assert response.status_code == 422

    def test_census_validates_plan_year_range(self, client, sample_csv_content) -> None:
        """Plan year must be 2020-2100 per spec."""
        # Under 2020 should fail
        response = client.post(
            "/api/v1/census",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            data={"name": "Test", "plan_year": "2019"},
        )
        assert response.status_code == 422

        # Over 2100 should fail
        response = client.post(
            "/api/v1/census",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            data={"name": "Test", "plan_year": "2101"},
        )
        assert response.status_code == 422
