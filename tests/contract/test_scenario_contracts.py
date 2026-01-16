"""
Contract tests for V2 Scenario Analysis API endpoints.

T018, T031: Validates v2 API endpoints match the OpenAPI specification.
"""

import io
import tempfile
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.schemas import (
    ScenarioRequestV2,
    ScenarioResultV2,
    GridRequestV2,
    GridResultV2,
    GridSummaryV2,
)
from src.storage import database


@pytest.fixture(scope="module")
def openapi_spec() -> dict:
    """Load the OpenAPI specification."""
    spec_path = Path(__file__).parent.parent.parent / "specs/004-scenario-analysis/contracts/openapi.yaml"
    if not spec_path.exists():
        pytest.skip("OpenAPI spec not found")
    with open(spec_path) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    """Reset database for each test using a test workspace."""
    import uuid

    # Use a unique test workspace for each test
    test_workspace_id = f"test-{uuid.uuid4()}"

    # Close any existing connections
    database.close_db()

    # Initialize fresh database for test workspace
    from src.storage.database import get_workspace_db_path, create_connection, init_database

    db_path = get_workspace_db_path(test_workspace_id)
    conn = create_connection(db_path)
    init_database(conn)
    database._connections[test_workspace_id] = conn

    # Store workspace ID for tests to access
    yield test_workspace_id

    # Cleanup
    database.close_db(test_workspace_id)

    # Remove test database file
    try:
        db_path = get_workspace_db_path(test_workspace_id)
        if db_path.exists():
            db_path.unlink()
        # Remove workspace directory if empty
        db_path.parent.rmdir()
    except Exception:
        pass


@pytest.fixture
def client(reset_db):
    """Create test client with workspace header."""
    test_client = TestClient(app)
    # Set default workspace header for tests
    test_client.headers["X-Workspace-ID"] = reset_db
    return test_client


@pytest.fixture
def sample_csv_content() -> bytes:
    """Sample CSV census file with required columns."""
    return b"""Employee ID,HCE Status,Date of Birth,Hire Date,Termination Date,Annual Compensation,Current Deferral Rate,Current Match Rate,Current After-Tax Rate
E001,TRUE,1990-01-01,2010-01-01,,180000,10,4,0
E002,FALSE,1990-01-01,2010-01-01,,75000,6,3,2
E003,TRUE,1990-01-01,2010-01-01,,200000,10,4,3
E004,FALSE,1990-01-01,2010-01-01,,65000,5,2.5,1
E005,TRUE,1990-01-01,2010-01-01,,150000,8,4,2
E006,FALSE,1990-01-01,2010-01-01,,80000,7,3,0
E007,FALSE,1990-01-01,2010-01-01,,70000,5,2,1
"""


@pytest.fixture
def uploaded_census(client, sample_csv_content) -> dict:
    """Upload a census and return the response data."""
    response = client.post(
        "/api/v1/census",
        files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
        data={"name": "V2 Contract Test Census", "plan_year": "2025"},
    )
    assert response.status_code == 201
    return response.json()


class TestV2SingleScenarioContract:
    """T018: Contract tests for POST /api/v2/analysis/scenario endpoint."""

    def test_v2_scenario_returns_all_required_fields(
        self, client, uploaded_census
    ) -> None:
        """V2 scenario should return all fields per spec."""
        census_id = uploaded_census["id"]

        response = client.post(
            "/api/v1/v2/scenario",
            json={
                "census_id": census_id,
                "adoption_rate": 0.5,
                "contribution_rate": 0.06,
                "seed": 42,
            },
        )
        assert response.status_code == 200

        data = response.json()
        result = ScenarioResultV2(**data)

        # Verify all required fields are present
        assert result.status in ["PASS", "RISK", "FAIL", "ERROR"]
        assert isinstance(result.seed_used, int)
        assert isinstance(result.adoption_rate, float)
        assert isinstance(result.contribution_rate, float)

        # For non-ERROR status, these should be present
        if result.status != "ERROR":
            assert result.nhce_acp is not None
            assert result.hce_acp is not None
            assert result.max_allowed_acp is not None
            assert result.margin is not None
            assert result.limiting_bound in ["MULTIPLE", "ADDITIVE"]
            assert result.hce_contributor_count is not None
            assert result.nhce_contributor_count is not None
            assert result.total_mega_backdoor_amount is not None

    def test_v2_scenario_status_values(self, client, uploaded_census) -> None:
        """V2 scenario should return valid status values."""
        census_id = uploaded_census["id"]

        # Test with low contribution (should PASS or RISK)
        response = client.post(
            "/api/v1/v2/scenario",
            json={
                "census_id": census_id,
                "adoption_rate": 0.25,
                "contribution_rate": 0.02,
                "seed": 42,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["PASS", "RISK", "FAIL"]

    def test_v2_scenario_validates_rate_bounds(self, client, uploaded_census) -> None:
        """V2 scenario should validate adoption and contribution rates."""
        census_id = uploaded_census["id"]

        # Adoption rate > 1.0 should fail
        response = client.post(
            "/api/v1/v2/scenario",
            json={
                "census_id": census_id,
                "adoption_rate": 1.5,
                "contribution_rate": 0.06,
            },
        )
        assert response.status_code == 422

        # Contribution rate > 1.0 should fail
        response = client.post(
            "/api/v1/v2/scenario",
            json={
                "census_id": census_id,
                "adoption_rate": 0.5,
                "contribution_rate": 1.5,
            },
        )
        assert response.status_code == 422

        # Negative rates should fail
        response = client.post(
            "/api/v1/v2/scenario",
            json={
                "census_id": census_id,
                "adoption_rate": -0.1,
                "contribution_rate": 0.06,
            },
        )
        assert response.status_code == 422

    def test_v2_scenario_census_not_found(self, client) -> None:
        """V2 scenario should return 404 for non-existent census."""
        response = client.post(
            "/api/v1/v2/scenario",
            json={
                "census_id": "non-existent-id",
                "adoption_rate": 0.5,
                "contribution_rate": 0.06,
            },
        )
        assert response.status_code == 404

    def test_v2_scenario_debug_mode(self, client, uploaded_census) -> None:
        """V2 scenario with include_debug=true should return debug details."""
        census_id = uploaded_census["id"]

        response = client.post(
            "/api/v1/v2/scenario",
            json={
                "census_id": census_id,
                "adoption_rate": 0.5,
                "contribution_rate": 0.06,
                "seed": 42,
                "include_debug": True,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["debug_details"] is not None
        assert "selected_hce_ids" in data["debug_details"]
        assert "hce_contributions" in data["debug_details"]
        assert "nhce_contributions" in data["debug_details"]
        assert "intermediate_values" in data["debug_details"]


class TestV2GridScenarioContract:
    """T031: Contract tests for POST /api/v2/analysis/grid endpoint."""

    def test_v2_grid_returns_all_required_fields(
        self, client, uploaded_census
    ) -> None:
        """V2 grid should return all fields per spec."""
        census_id = uploaded_census["id"]

        response = client.post(
            "/api/v1/v2/grid",
            json={
                "census_id": census_id,
                "adoption_rates": [0.25, 0.5, 0.75],
                "contribution_rates": [0.04, 0.06, 0.08],
                "seed": 42,
            },
        )
        assert response.status_code == 200

        data = response.json()
        result = GridResultV2(**data)

        # Verify required fields
        assert isinstance(result.scenarios, list)
        assert len(result.scenarios) == 9  # 3x3 grid
        assert isinstance(result.summary, GridSummaryV2)
        assert isinstance(result.seed_used, int)

        # Verify summary fields
        assert result.summary.pass_count >= 0
        assert result.summary.risk_count >= 0
        assert result.summary.fail_count >= 0
        assert result.summary.error_count >= 0
        assert result.summary.total_count == 9
        assert (
            result.summary.pass_count
            + result.summary.risk_count
            + result.summary.fail_count
            + result.summary.error_count
        ) == 9

    def test_v2_grid_validates_array_length(self, client, uploaded_census) -> None:
        """V2 grid should validate array length constraints."""
        census_id = uploaded_census["id"]

        # Less than 2 adoption rates should fail
        response = client.post(
            "/api/v1/v2/grid",
            json={
                "census_id": census_id,
                "adoption_rates": [0.5],
                "contribution_rates": [0.04, 0.06],
            },
        )
        assert response.status_code == 422

        # Less than 2 contribution rates should fail
        response = client.post(
            "/api/v1/v2/grid",
            json={
                "census_id": census_id,
                "adoption_rates": [0.25, 0.5],
                "contribution_rates": [0.06],
            },
        )
        assert response.status_code == 422

    def test_v2_grid_determinism(self, client, uploaded_census) -> None:
        """V2 grid with same seed should produce identical results."""
        census_id = uploaded_census["id"]

        request_data = {
            "census_id": census_id,
            "adoption_rates": [0.25, 0.5, 0.75],
            "contribution_rates": [0.04, 0.06],
            "seed": 12345,
        }

        response1 = client.post("/api/v1/v2/grid", json=request_data)
        response2 = client.post("/api/v1/v2/grid", json=request_data)

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Results should be identical
        assert data1["seed_used"] == data2["seed_used"]
        assert len(data1["scenarios"]) == len(data2["scenarios"])

        for s1, s2 in zip(data1["scenarios"], data2["scenarios"]):
            assert s1["status"] == s2["status"]
            assert s1["hce_acp"] == s2["hce_acp"]
            assert s1["nhce_acp"] == s2["nhce_acp"]
            assert s1["margin"] == s2["margin"]

    def test_v2_grid_summary_metrics(self, client, uploaded_census) -> None:
        """V2 grid summary should include all required metrics."""
        census_id = uploaded_census["id"]

        response = client.post(
            "/api/v1/v2/grid",
            json={
                "census_id": census_id,
                "adoption_rates": [0.0, 0.5, 1.0],
                "contribution_rates": [0.02, 0.06, 0.10],
                "seed": 42,
            },
        )
        assert response.status_code == 200

        data = response.json()
        summary = data["summary"]

        # All summary fields should be present
        assert "pass_count" in summary
        assert "risk_count" in summary
        assert "fail_count" in summary
        assert "error_count" in summary
        assert "total_count" in summary
        assert "worst_margin" in summary
        # first_failure_point and max_safe_contribution can be null
        assert "first_failure_point" in summary
        assert "max_safe_contribution" in summary

    def test_v2_grid_census_not_found(self, client) -> None:
        """V2 grid should return 404 for non-existent census."""
        response = client.post(
            "/api/v1/v2/grid",
            json={
                "census_id": "non-existent-id",
                "adoption_rates": [0.25, 0.5],
                "contribution_rates": [0.04, 0.06],
            },
        )
        assert response.status_code == 404


class TestV2SchemaValidation:
    """Additional schema validation tests."""

    def test_scenario_request_v2_schema(self) -> None:
        """ScenarioRequestV2 should validate correctly."""
        # Valid request
        request = ScenarioRequestV2(
            census_id="test-id",
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
            include_debug=False,
        )
        assert request.census_id == "test-id"
        assert request.adoption_rate == 0.5
        assert request.contribution_rate == 0.06
        assert request.seed == 42
        assert request.include_debug is False

        # Invalid rates should raise
        with pytest.raises(ValueError):
            ScenarioRequestV2(
                census_id="test-id",
                adoption_rate=1.5,  # > 1.0
                contribution_rate=0.06,
            )

        with pytest.raises(ValueError):
            ScenarioRequestV2(
                census_id="test-id",
                adoption_rate=0.5,
                contribution_rate=-0.1,  # < 0.0
            )

    def test_grid_request_v2_schema(self) -> None:
        """GridRequestV2 should validate correctly."""
        # Valid request
        request = GridRequestV2(
            census_id="test-id",
            adoption_rates=[0.25, 0.5, 0.75],
            contribution_rates=[0.04, 0.06, 0.08],
            seed=42,
        )
        assert request.census_id == "test-id"
        assert len(request.adoption_rates) == 3
        assert len(request.contribution_rates) == 3

        # Too few items should raise
        with pytest.raises(ValueError):
            GridRequestV2(
                census_id="test-id",
                adoption_rates=[0.5],  # Only 1 item
                contribution_rates=[0.04, 0.06],
            )
