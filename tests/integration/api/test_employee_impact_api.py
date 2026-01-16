"""
Integration Tests for Employee Impact API Endpoints.

T023: Test POST /api/v1/v2/scenario/{census_id}/employee-impact endpoint.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
import uuid as uuid_module

from src.api.main import app
from src.storage import database
from src.storage.repository import CensusRepository, ParticipantRepository
from src.storage.models import Census, Participant


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    """Reset database for each test using a test workspace."""
    # Use a unique test workspace for each test
    test_workspace_id = f"test-{uuid_module.uuid4()}"

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
def db_connection(reset_db):
    """Get the database connection for the test workspace."""
    return database._connections[reset_db]


@pytest.fixture
def test_census(db_connection):
    """Create a test census with participants."""
    census_id = str(uuid_module.uuid4())

    # Create census
    census = Census(
        id=census_id,
        name="Test Census",
        plan_year=2025,
        upload_timestamp=datetime.utcnow(),
        participant_count=5,
        hce_count=2,
        nhce_count=3,
        salt="test-salt",
        version="1.0.0",
    )

    # Save census
    repo = CensusRepository(db_connection)
    repo.save(census)

    # Create participants
    participants = [
        # HCE 1 - Unconstrained
        Participant(
            id=str(uuid_module.uuid4()),
            census_id=census_id,
            internal_id="EMP-001",
            is_hce=True,
            compensation_cents=10000000,  # $100,000
            deferral_rate=10.0,  # $10,000 deferral
            match_rate=5.0,  # $5,000 match
            after_tax_rate=0.0,
            dob="1980-01-01",
            hire_date="2010-01-01",
        ),
        # HCE 2 - Near limit
        Participant(
            id=str(uuid_module.uuid4()),
            census_id=census_id,
            internal_id="EMP-002",
            is_hce=True,
            compensation_cents=20000000,  # $200,000
            deferral_rate=11.5,  # $23,000
            match_rate=10.0,  # $20,000
            after_tax_rate=10.0,  # $20,000 -> Total $63,000
            dob="1980-01-01",
            hire_date="2010-01-01",
        ),
        # NHCE 1
        Participant(
            id=str(uuid_module.uuid4()),
            census_id=census_id,
            internal_id="EMP-003",
            is_hce=False,
            compensation_cents=5000000,  # $50,000
            deferral_rate=8.0,
            match_rate=4.0,
            after_tax_rate=0.0,
            dob="1985-02-02",
            hire_date="2012-06-01",
        ),
        # NHCE 2
        Participant(
            id=str(uuid_module.uuid4()),
            census_id=census_id,
            internal_id="EMP-004",
            is_hce=False,
            compensation_cents=6000000,  # $60,000
            deferral_rate=6.0,
            match_rate=3.0,
            after_tax_rate=1.0,
            dob="1985-02-02",
            hire_date="2012-06-01",
        ),
        # NHCE 3
        Participant(
            id=str(uuid_module.uuid4()),
            census_id=census_id,
            internal_id="EMP-005",
            is_hce=False,
            compensation_cents=7500000,  # $75,000
            deferral_rate=10.0,
            match_rate=5.0,
            after_tax_rate=0.5,
            dob="1985-02-02",
            hire_date="2012-06-01",
        ),
    ]

    # Save participants
    part_repo = ParticipantRepository(db_connection)
    part_repo.bulk_insert(participants)

    return census


class TestGetEmployeeImpactEndpoint:
    """Integration tests for POST /api/v1/v2/scenario/{census_id}/employee-impact."""

    def test_get_employee_impact_success(self, client, test_census):
        """Successful request returns 200 with EmployeeImpactView."""
        response = client.post(
            f"/api/v1/v2/scenario/{test_census.id}/employee-impact",
            json={
                "adoption_rate": 1.0,
                "contribution_rate": 0.06,
                "seed": 42,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "census_id" in data
        assert data["census_id"] == test_census.id
        assert "adoption_rate" in data
        assert data["adoption_rate"] == 1.0
        assert "contribution_rate" in data
        assert data["contribution_rate"] == 0.06
        assert "seed_used" in data
        assert data["seed_used"] == 42
        assert "plan_year" in data
        assert "section_415c_limit" in data
        assert "hce_employees" in data
        assert "nhce_employees" in data
        assert "hce_summary" in data
        assert "nhce_summary" in data

    def test_get_employee_impact_census_not_found(self, client):
        """Request for non-existent census returns 404."""
        response = client.post(
            "/api/v1/v2/scenario/non-existent-census-id/employee-impact",
            json={
                "adoption_rate": 0.5,
                "contribution_rate": 0.06,
                "seed": 42,
            },
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_employee_impact_invalid_adoption_rate(self, client, test_census):
        """Request with invalid adoption_rate returns 400."""
        response = client.post(
            f"/api/v1/v2/scenario/{test_census.id}/employee-impact",
            json={
                "adoption_rate": 1.5,  # Invalid: > 1.0
                "contribution_rate": 0.06,
                "seed": 42,
            },
        )

        assert response.status_code == 422  # Validation error

    def test_get_employee_impact_invalid_contribution_rate(self, client, test_census):
        """Request with invalid contribution_rate returns 400."""
        response = client.post(
            f"/api/v1/v2/scenario/{test_census.id}/employee-impact",
            json={
                "adoption_rate": 0.5,
                "contribution_rate": -0.01,  # Invalid: < 0
                "seed": 42,
            },
        )

        assert response.status_code == 422  # Validation error

    def test_get_employee_impact_invalid_seed(self, client, test_census):
        """Request with invalid seed returns 400."""
        response = client.post(
            f"/api/v1/v2/scenario/{test_census.id}/employee-impact",
            json={
                "adoption_rate": 0.5,
                "contribution_rate": 0.06,
                "seed": 0,  # Invalid: < 1
            },
        )

        assert response.status_code == 422  # Validation error

    def test_get_employee_impact_hce_count_matches(self, client, test_census):
        """Response HCE count matches census HCE count."""
        response = client.post(
            f"/api/v1/v2/scenario/{test_census.id}/employee-impact",
            json={
                "adoption_rate": 1.0,
                "contribution_rate": 0.06,
                "seed": 42,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["hce_employees"]) == test_census.hce_count
        assert data["hce_summary"]["total_count"] == test_census.hce_count

    def test_get_employee_impact_nhce_count_matches(self, client, test_census):
        """Response NHCE count matches census NHCE count."""
        response = client.post(
            f"/api/v1/v2/scenario/{test_census.id}/employee-impact",
            json={
                "adoption_rate": 1.0,
                "contribution_rate": 0.06,
                "seed": 42,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["nhce_employees"]) == test_census.nhce_count
        assert data["nhce_summary"]["total_count"] == test_census.nhce_count

    def test_get_employee_impact_seed_reproducibility(self, client, test_census):
        """Same seed produces same results."""
        # First request
        response1 = client.post(
            f"/api/v1/v2/scenario/{test_census.id}/employee-impact",
            json={
                "adoption_rate": 0.5,
                "contribution_rate": 0.06,
                "seed": 42,
            },
        )

        # Second request with same seed
        response2 = client.post(
            f"/api/v1/v2/scenario/{test_census.id}/employee-impact",
            json={
                "adoption_rate": 0.5,
                "contribution_rate": 0.06,
                "seed": 42,
            },
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Selected HCEs should be identical
        hce_ids1 = [e["employee_id"] for e in data1["hce_employees"] if e["mega_backdoor_amount"] > 0]
        hce_ids2 = [e["employee_id"] for e in data2["hce_employees"] if e["mega_backdoor_amount"] > 0]

        assert set(hce_ids1) == set(hce_ids2)

    def test_get_employee_impact_zero_adoption(self, client, test_census):
        """Zero adoption rate results in no mega-backdoor allocations."""
        response = client.post(
            f"/api/v1/v2/scenario/{test_census.id}/employee-impact",
            json={
                "adoption_rate": 0.0,
                "contribution_rate": 0.06,
                "seed": 42,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # All HCEs should have NOT_SELECTED status and zero mega-backdoor
        for hce in data["hce_employees"]:
            assert hce["constraint_status"] == "Not Selected"
            assert hce["mega_backdoor_amount"] == 0.0

    def test_get_employee_impact_full_adoption(self, client, test_census):
        """Full adoption rate includes all HCEs in mega-backdoor."""
        response = client.post(
            f"/api/v1/v2/scenario/{test_census.id}/employee-impact",
            json={
                "adoption_rate": 1.0,
                "contribution_rate": 0.06,
                "seed": 42,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # No HCEs should have NOT_SELECTED status
        for hce in data["hce_employees"]:
            assert hce["constraint_status"] != "Not Selected"

    def test_get_employee_impact_summary_totals(self, client, test_census):
        """Summary totals match sum of individual amounts."""
        response = client.post(
            f"/api/v1/v2/scenario/{test_census.id}/employee-impact",
            json={
                "adoption_rate": 1.0,
                "contribution_rate": 0.06,
                "seed": 42,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify HCE summary totals
        hce_match_total = sum(e["match_amount"] for e in data["hce_employees"])
        hce_after_tax_total = sum(e["after_tax_amount"] for e in data["hce_employees"])
        hce_mega_backdoor_total = sum(e["mega_backdoor_amount"] for e in data["hce_employees"])

        assert abs(data["hce_summary"]["total_match"] - hce_match_total) < 0.01
        assert abs(data["hce_summary"]["total_after_tax"] - hce_after_tax_total) < 0.01
        assert abs(data["hce_summary"]["total_mega_backdoor"] - hce_mega_backdoor_total) < 0.01

    def test_get_employee_impact_constraint_counts(self, client, test_census):
        """Summary constraint counts match individual statuses."""
        response = client.post(
            f"/api/v1/v2/scenario/{test_census.id}/employee-impact",
            json={
                "adoption_rate": 1.0,
                "contribution_rate": 0.06,
                "seed": 42,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Count statuses from individual employees
        at_limit_count = sum(1 for e in data["hce_employees"] if e["constraint_status"] == "At §415(c) Limit")
        reduced_count = sum(1 for e in data["hce_employees"] if e["constraint_status"] == "Reduced")

        # Verify summary matches
        assert data["hce_summary"]["at_limit_count"] == at_limit_count
        assert data["hce_summary"]["reduced_count"] == reduced_count


class TestEmployeeImpactExportEndpoint:
    """Integration tests for POST /api/v1/v2/scenario/{census_id}/employee-impact/export."""

    def test_export_hce_only(self, client, test_census):
        """Export with export_group='hce' returns only HCE data."""
        response = client.post(
            f"/api/v1/v2/scenario/{test_census.id}/employee-impact/export",
            json={
                "adoption_rate": 1.0,
                "contribution_rate": 0.06,
                "seed": 42,
                "export_group": "hce",
            },
        )

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

        # CSV should contain HCE count + 1 header row
        csv_lines = response.text.strip().split("\n")
        assert len(csv_lines) == test_census.hce_count + 1

    def test_export_nhce_only(self, client, test_census):
        """Export with export_group='nhce' returns only NHCE data."""
        response = client.post(
            f"/api/v1/v2/scenario/{test_census.id}/employee-impact/export",
            json={
                "adoption_rate": 1.0,
                "contribution_rate": 0.06,
                "seed": 42,
                "export_group": "nhce",
            },
        )

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

        # CSV should contain NHCE count + 1 header row
        csv_lines = response.text.strip().split("\n")
        assert len(csv_lines) == test_census.nhce_count + 1

    def test_export_all_with_group_column(self, client, test_census):
        """Export with export_group='all' includes Group column."""
        response = client.post(
            f"/api/v1/v2/scenario/{test_census.id}/employee-impact/export",
            json={
                "adoption_rate": 1.0,
                "contribution_rate": 0.06,
                "seed": 42,
                "export_group": "all",
                "include_group_column": True,
            },
        )

        assert response.status_code == 200

        # First line should contain "Group" column
        header_line = response.text.split("\n")[0]
        assert "Group" in header_line

    def test_export_all_without_group_column(self, client, test_census):
        """Export with include_group_column=False excludes Group column."""
        response = client.post(
            f"/api/v1/v2/scenario/{test_census.id}/employee-impact/export",
            json={
                "adoption_rate": 1.0,
                "contribution_rate": 0.06,
                "seed": 42,
                "export_group": "all",
                "include_group_column": False,
            },
        )

        assert response.status_code == 200

        # First line should NOT contain "Group" column
        header_line = response.text.split("\n")[0]
        assert "Group" not in header_line

    def test_export_census_not_found(self, client):
        """Export for non-existent census returns 404."""
        response = client.post(
            "/api/v1/v2/scenario/non-existent-census-id/employee-impact/export",
            json={
                "adoption_rate": 0.5,
                "contribution_rate": 0.06,
                "seed": 42,
            },
        )

        assert response.status_code == 404
