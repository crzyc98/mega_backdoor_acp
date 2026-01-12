"""
Integration Tests for V2 Analysis API.

T067-T068: Full API workflow tests for scenario and grid analysis.
"""

import io
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.storage import database


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    """Reset database for each test."""
    database.close_db()
    temp_dir = tempfile.mkdtemp()
    test_db_path = Path(temp_dir) / "test_integration.db"
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
    """Sample CSV census file with HCEs and NHCEs."""
    return b"""Employee ID,HCE Status,Annual Compensation,Current Deferral Rate,Current Match Rate,Current After-Tax Rate
E001,TRUE,180000,10,4,2
E002,FALSE,75000,6,3,0
E003,TRUE,200000,10,4,3
E004,FALSE,65000,5,2.5,1
E005,TRUE,150000,8,4,2
E006,FALSE,80000,7,3,0
E007,FALSE,70000,5,2,1
E008,FALSE,60000,4,2,0
E009,TRUE,220000,12,5,4
E010,FALSE,55000,3,1.5,0
"""


class TestSingleScenarioWorkflow:
    """T067: Integration test for full single scenario API workflow."""

    def test_full_workflow_upload_census_run_scenario(
        self, client, sample_csv_content
    ) -> None:
        """Upload census → run v2 scenario → verify result."""
        # Step 1: Upload census
        upload_response = client.post(
            "/api/v1/census",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            data={"name": "Integration Test Census", "plan_year": "2025"},
        )
        assert upload_response.status_code == 201
        census_id = upload_response.json()["id"]
        census_data = upload_response.json()

        # Verify census has expected counts
        assert census_data["participant_count"] == 10
        assert census_data["hce_count"] == 4
        assert census_data["nhce_count"] == 6

        # Step 2: Run v2 scenario
        scenario_response = client.post(
            "/api/v1/v2/scenario",
            json={
                "census_id": census_id,
                "adoption_rate": 0.5,
                "contribution_rate": 0.06,
                "seed": 42,
            },
        )
        assert scenario_response.status_code == 200
        result = scenario_response.json()

        # Step 3: Verify result
        assert result["status"] in ["PASS", "RISK", "FAIL"]
        assert result["nhce_acp"] is not None
        assert result["hce_acp"] is not None
        assert result["max_allowed_acp"] is not None
        assert result["margin"] is not None
        assert result["limiting_bound"] in ["MULTIPLE", "ADDITIVE"]
        assert result["hce_contributor_count"] == 2  # 50% of 4 HCEs
        assert result["nhce_contributor_count"] >= 0
        assert result["seed_used"] == 42
        assert result["adoption_rate"] == 0.5
        assert result["contribution_rate"] == 0.06

    def test_scenario_with_debug_mode(self, client, sample_csv_content) -> None:
        """Run scenario with debug mode and verify debug details."""
        # Upload census
        upload_response = client.post(
            "/api/v1/census",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            data={"name": "Debug Test Census", "plan_year": "2025"},
        )
        census_id = upload_response.json()["id"]

        # Run scenario with debug
        scenario_response = client.post(
            "/api/v1/v2/scenario",
            json={
                "census_id": census_id,
                "adoption_rate": 0.75,
                "contribution_rate": 0.04,
                "seed": 123,
                "include_debug": True,
            },
        )
        assert scenario_response.status_code == 200
        result = scenario_response.json()

        # Verify debug details
        assert result["debug_details"] is not None
        dd = result["debug_details"]

        assert "selected_hce_ids" in dd
        assert len(dd["selected_hce_ids"]) == 3  # 75% of 4 HCEs

        assert "hce_contributions" in dd
        assert len(dd["hce_contributions"]) == 4  # All HCEs

        assert "nhce_contributions" in dd
        assert len(dd["nhce_contributions"]) == 6  # All NHCEs

        assert "intermediate_values" in dd
        iv = dd["intermediate_values"]
        assert iv["hce_count"] == 4
        assert iv["nhce_count"] == 6

    def test_scenario_determinism(self, client, sample_csv_content) -> None:
        """Same seed should produce identical results."""
        # Upload census
        upload_response = client.post(
            "/api/v1/census",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            data={"name": "Determinism Test Census", "plan_year": "2025"},
        )
        census_id = upload_response.json()["id"]

        # Run same scenario twice
        request_data = {
            "census_id": census_id,
            "adoption_rate": 0.5,
            "contribution_rate": 0.06,
            "seed": 12345,
        }

        response1 = client.post("/api/v1/v2/scenario", json=request_data)
        response2 = client.post("/api/v1/v2/scenario", json=request_data)

        assert response1.status_code == 200
        assert response2.status_code == 200

        result1 = response1.json()
        result2 = response2.json()

        assert result1["status"] == result2["status"]
        assert result1["hce_acp"] == result2["hce_acp"]
        assert result1["nhce_acp"] == result2["nhce_acp"]
        assert result1["margin"] == result2["margin"]


class TestGridScenarioWorkflow:
    """T068: Integration test for full grid API workflow."""

    def test_full_workflow_upload_census_run_grid(
        self, client, sample_csv_content
    ) -> None:
        """Upload census → run v2 grid → verify results."""
        # Step 1: Upload census
        upload_response = client.post(
            "/api/v1/census",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            data={"name": "Grid Test Census", "plan_year": "2025"},
        )
        assert upload_response.status_code == 201
        census_id = upload_response.json()["id"]

        # Step 2: Run v2 grid
        grid_response = client.post(
            "/api/v1/v2/grid",
            json={
                "census_id": census_id,
                "adoption_rates": [0.25, 0.5, 0.75, 1.0],
                "contribution_rates": [0.02, 0.04, 0.06, 0.08],
                "seed": 42,
            },
        )
        assert grid_response.status_code == 200
        result = grid_response.json()

        # Step 3: Verify results
        assert len(result["scenarios"]) == 16  # 4x4 grid
        assert result["seed_used"] == 42

        # Verify summary
        summary = result["summary"]
        assert summary["total_count"] == 16
        assert summary["pass_count"] >= 0
        assert summary["risk_count"] >= 0
        assert summary["fail_count"] >= 0
        assert summary["error_count"] >= 0
        assert (
            summary["pass_count"]
            + summary["risk_count"]
            + summary["fail_count"]
            + summary["error_count"]
        ) == 16

        # worst_margin should be present
        assert "worst_margin" in summary
        # first_failure_point and max_safe_contribution can be null
        assert "first_failure_point" in summary
        assert "max_safe_contribution" in summary

    def test_grid_covers_all_combinations(self, client, sample_csv_content) -> None:
        """Grid should include all adoption x contribution combinations."""
        # Upload census
        upload_response = client.post(
            "/api/v1/census",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            data={"name": "Combo Test Census", "plan_year": "2025"},
        )
        census_id = upload_response.json()["id"]

        adoption_rates = [0.2, 0.4, 0.6]
        contribution_rates = [0.03, 0.06]

        grid_response = client.post(
            "/api/v1/v2/grid",
            json={
                "census_id": census_id,
                "adoption_rates": adoption_rates,
                "contribution_rates": contribution_rates,
                "seed": 42,
            },
        )
        assert grid_response.status_code == 200
        result = grid_response.json()

        # Extract all combinations
        combos = [
            (s["adoption_rate"], s["contribution_rate"])
            for s in result["scenarios"]
        ]
        expected = [
            (a, c) for a in adoption_rates for c in contribution_rates
        ]

        assert sorted(combos) == sorted(expected)

    def test_grid_determinism(self, client, sample_csv_content) -> None:
        """Same seed should produce identical grid results."""
        # Upload census
        upload_response = client.post(
            "/api/v1/census",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            data={"name": "Grid Determinism Census", "plan_year": "2025"},
        )
        census_id = upload_response.json()["id"]

        request_data = {
            "census_id": census_id,
            "adoption_rates": [0.25, 0.5, 0.75],
            "contribution_rates": [0.04, 0.06],
            "seed": 99999,
        }

        response1 = client.post("/api/v1/v2/grid", json=request_data)
        response2 = client.post("/api/v1/v2/grid", json=request_data)

        assert response1.status_code == 200
        assert response2.status_code == 200

        result1 = response1.json()
        result2 = response2.json()

        assert len(result1["scenarios"]) == len(result2["scenarios"])

        for s1, s2 in zip(result1["scenarios"], result2["scenarios"]):
            assert s1["status"] == s2["status"]
            assert s1["hce_acp"] == s2["hce_acp"]
            assert s1["margin"] == s2["margin"]

    def test_grid_summary_accuracy(self, client, sample_csv_content) -> None:
        """Grid summary should accurately reflect scenario statuses."""
        # Upload census
        upload_response = client.post(
            "/api/v1/census",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            data={"name": "Summary Test Census", "plan_year": "2025"},
        )
        census_id = upload_response.json()["id"]

        grid_response = client.post(
            "/api/v1/v2/grid",
            json={
                "census_id": census_id,
                "adoption_rates": [0.0, 0.5, 1.0],
                "contribution_rates": [0.02, 0.06, 0.10],
                "seed": 42,
            },
        )
        assert grid_response.status_code == 200
        result = grid_response.json()

        # Manually count statuses
        statuses = [s["status"] for s in result["scenarios"]]
        expected_pass = statuses.count("PASS")
        expected_risk = statuses.count("RISK")
        expected_fail = statuses.count("FAIL")
        expected_error = statuses.count("ERROR")

        summary = result["summary"]
        assert summary["pass_count"] == expected_pass
        assert summary["risk_count"] == expected_risk
        assert summary["fail_count"] == expected_fail
        assert summary["error_count"] == expected_error


class TestEdgeCaseWorkflows:
    """Edge case workflows for the API."""

    def test_census_not_found_single_scenario(self, client) -> None:
        """Non-existent census should return 404."""
        response = client.post(
            "/api/v1/v2/scenario",
            json={
                "census_id": "non-existent-census-id",
                "adoption_rate": 0.5,
                "contribution_rate": 0.06,
            },
        )
        assert response.status_code == 404

    def test_census_not_found_grid(self, client) -> None:
        """Non-existent census should return 404 for grid."""
        response = client.post(
            "/api/v1/v2/grid",
            json={
                "census_id": "non-existent-census-id",
                "adoption_rates": [0.25, 0.5],
                "contribution_rates": [0.04, 0.06],
            },
        )
        assert response.status_code == 404

    def test_invalid_adoption_rate(self, client, sample_csv_content) -> None:
        """Adoption rate > 1.0 should be rejected."""
        upload_response = client.post(
            "/api/v1/census",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            data={"name": "Validation Test Census", "plan_year": "2025"},
        )
        census_id = upload_response.json()["id"]

        response = client.post(
            "/api/v1/v2/scenario",
            json={
                "census_id": census_id,
                "adoption_rate": 1.5,  # Invalid
                "contribution_rate": 0.06,
            },
        )
        assert response.status_code == 422

    def test_invalid_contribution_rate(self, client, sample_csv_content) -> None:
        """Contribution rate > 1.0 should be rejected."""
        upload_response = client.post(
            "/api/v1/census",
            files={"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            data={"name": "Validation Test Census 2", "plan_year": "2025"},
        )
        census_id = upload_response.json()["id"]

        response = client.post(
            "/api/v1/v2/scenario",
            json={
                "census_id": census_id,
                "adoption_rate": 0.5,
                "contribution_rate": 1.5,  # Invalid
            },
        )
        assert response.status_code == 422
