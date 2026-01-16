"""
Contract Tests for Employee Impact API Schemas.

T022, T059: Validate API request/response schemas match OpenAPI specification.
"""

import pytest
from datetime import datetime
from typing import Literal

from pydantic import ValidationError

from backend.app.routers.schemas import (
    EmployeeImpactRequest,
    EmployeeImpactResponse,
    EmployeeImpactSummaryResponse,
    EmployeeImpactViewResponse,
    EmployeeImpactExportRequest,
)


# =============================================================================
# T022: POST /v2/scenario/{census_id}/employee-impact Schema Tests
# =============================================================================


class TestEmployeeImpactRequestSchema:
    """Contract tests for EmployeeImpactRequest schema."""

    def test_valid_request_all_fields(self):
        """Valid request with all required fields passes validation."""
        request = EmployeeImpactRequest(
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
        )
        assert request.adoption_rate == 0.5
        assert request.contribution_rate == 0.06
        assert request.seed == 42

    def test_adoption_rate_minimum_bound(self):
        """adoption_rate at minimum (0.0) passes validation."""
        request = EmployeeImpactRequest(
            adoption_rate=0.0,
            contribution_rate=0.06,
            seed=42,
        )
        assert request.adoption_rate == 0.0

    def test_adoption_rate_maximum_bound(self):
        """adoption_rate at maximum (1.0) passes validation."""
        request = EmployeeImpactRequest(
            adoption_rate=1.0,
            contribution_rate=0.06,
            seed=42,
        )
        assert request.adoption_rate == 1.0

    def test_adoption_rate_below_minimum_fails(self):
        """adoption_rate below 0.0 fails validation."""
        with pytest.raises(ValidationError):
            EmployeeImpactRequest(
                adoption_rate=-0.1,
                contribution_rate=0.06,
                seed=42,
            )

    def test_adoption_rate_above_maximum_fails(self):
        """adoption_rate above 1.0 fails validation."""
        with pytest.raises(ValidationError):
            EmployeeImpactRequest(
                adoption_rate=1.1,
                contribution_rate=0.06,
                seed=42,
            )

    def test_contribution_rate_minimum_bound(self):
        """contribution_rate at minimum (0.0) passes validation."""
        request = EmployeeImpactRequest(
            adoption_rate=0.5,
            contribution_rate=0.0,
            seed=42,
        )
        assert request.contribution_rate == 0.0

    def test_contribution_rate_maximum_bound(self):
        """contribution_rate at maximum (1.0) passes validation."""
        request = EmployeeImpactRequest(
            adoption_rate=0.5,
            contribution_rate=1.0,
            seed=42,
        )
        assert request.contribution_rate == 1.0

    def test_contribution_rate_below_minimum_fails(self):
        """contribution_rate below 0.0 fails validation."""
        with pytest.raises(ValidationError):
            EmployeeImpactRequest(
                adoption_rate=0.5,
                contribution_rate=-0.01,
                seed=42,
            )

    def test_contribution_rate_above_maximum_fails(self):
        """contribution_rate above 1.0 fails validation."""
        with pytest.raises(ValidationError):
            EmployeeImpactRequest(
                adoption_rate=0.5,
                contribution_rate=1.01,
                seed=42,
            )

    def test_seed_minimum_bound(self):
        """seed at minimum (1) passes validation."""
        request = EmployeeImpactRequest(
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=1,
        )
        assert request.seed == 1

    def test_seed_below_minimum_fails(self):
        """seed below 1 fails validation."""
        with pytest.raises(ValidationError):
            EmployeeImpactRequest(
                adoption_rate=0.5,
                contribution_rate=0.06,
                seed=0,
            )

    def test_missing_required_field_fails(self):
        """Missing required field fails validation."""
        with pytest.raises(ValidationError):
            EmployeeImpactRequest(
                adoption_rate=0.5,
                # missing contribution_rate and seed
            )


class TestEmployeeImpactResponseSchema:
    """Contract tests for EmployeeImpactResponse schema."""

    def test_valid_hce_response(self):
        """Valid HCE employee response passes validation."""
        response = EmployeeImpactResponse(
            employee_id="EMP-001",
            is_hce=True,
            compensation=180000.00,
            deferral_amount=23000.00,
            match_amount=9000.00,
            after_tax_amount=0.00,
            section_415c_limit=69000,
            available_room=26200.00,
            mega_backdoor_amount=10800.00,
            requested_mega_backdoor=10800.00,
            individual_acp=11.0,
            constraint_status="Unconstrained",
            constraint_detail="Received full mega-backdoor amount",
        )
        assert response.employee_id == "EMP-001"
        assert response.constraint_status == "Unconstrained"

    def test_valid_nhce_response(self):
        """Valid NHCE employee response passes validation."""
        response = EmployeeImpactResponse(
            employee_id="EMP-002",
            is_hce=False,
            compensation=75000.00,
            deferral_amount=7500.00,
            match_amount=3750.00,
            after_tax_amount=500.00,
            section_415c_limit=69000,
            available_room=57250.00,
            mega_backdoor_amount=0.00,
            requested_mega_backdoor=0.00,
            individual_acp=5.67,
            constraint_status="Not Selected",
            constraint_detail="Not selected for mega-backdoor participation",
        )
        assert response.is_hce is False

    def test_null_individual_acp_allowed(self):
        """individual_acp can be None (for zero compensation)."""
        response = EmployeeImpactResponse(
            employee_id="EMP-003",
            is_hce=True,
            compensation=0.0,
            deferral_amount=0.0,
            match_amount=0.0,
            after_tax_amount=0.0,
            section_415c_limit=69000,
            available_room=69000.0,
            mega_backdoor_amount=0.0,
            requested_mega_backdoor=0.0,
            individual_acp=None,
            constraint_status="Not Selected",
            constraint_detail="Not selected for mega-backdoor participation",
        )
        assert response.individual_acp is None

    def test_negative_available_room_allowed(self):
        """available_room can be negative (over-contributed)."""
        response = EmployeeImpactResponse(
            employee_id="EMP-004",
            is_hce=True,
            compensation=400000.00,
            deferral_amount=23000.00,
            match_amount=20000.00,
            after_tax_amount=30000.00,
            section_415c_limit=69000,
            available_room=-4000.00,  # Over the limit
            mega_backdoor_amount=0.0,
            requested_mega_backdoor=24000.0,
            individual_acp=13.25,
            constraint_status="At §415(c) Limit",
            constraint_detail="§415(c) limit exceeded",
        )
        assert response.available_room == -4000.00

    def test_all_constraint_status_values(self):
        """All valid constraint_status values are accepted."""
        valid_statuses = ["Unconstrained", "At §415(c) Limit", "Reduced", "Not Selected"]
        for status in valid_statuses:
            response = EmployeeImpactResponse(
                employee_id="EMP-001",
                is_hce=True,
                compensation=100000.0,
                deferral_amount=10000.0,
                match_amount=5000.0,
                after_tax_amount=0.0,
                section_415c_limit=69000,
                available_room=54000.0,
                mega_backdoor_amount=0.0,
                requested_mega_backdoor=0.0,
                individual_acp=5.0,
                constraint_status=status,
                constraint_detail="Test",
            )
            assert response.constraint_status == status


class TestEmployeeImpactSummaryResponseSchema:
    """Contract tests for EmployeeImpactSummaryResponse schema."""

    def test_valid_hce_summary(self):
        """Valid HCE summary with all fields passes validation."""
        summary = EmployeeImpactSummaryResponse(
            group="HCE",
            total_count=45,
            at_limit_count=12,
            reduced_count=5,
            average_available_room=18500.00,
            total_mega_backdoor=324000.00,
            average_individual_acp=8.75,
            total_match=405000.00,
            total_after_tax=12000.00,
        )
        assert summary.group == "HCE"
        assert summary.at_limit_count == 12

    def test_valid_nhce_summary(self):
        """Valid NHCE summary with nullable fields as None passes validation."""
        summary = EmployeeImpactSummaryResponse(
            group="NHCE",
            total_count=150,
            at_limit_count=None,
            reduced_count=None,
            average_available_room=None,
            total_mega_backdoor=None,
            average_individual_acp=4.25,
            total_match=225000.00,
            total_after_tax=8500.00,
        )
        assert summary.group == "NHCE"
        assert summary.at_limit_count is None

    def test_group_literal_validation(self):
        """group field only accepts 'HCE' or 'NHCE'."""
        # Valid values
        for group in ["HCE", "NHCE"]:
            summary = EmployeeImpactSummaryResponse(
                group=group,
                total_count=10,
                average_individual_acp=5.0,
                total_match=10000.0,
                total_after_tax=1000.0,
            )
            assert summary.group == group


class TestEmployeeImpactViewResponseSchema:
    """Contract tests for EmployeeImpactViewResponse schema."""

    def test_valid_complete_response(self):
        """Valid complete view response passes validation."""
        hce_employee = EmployeeImpactResponse(
            employee_id="EMP-001",
            is_hce=True,
            compensation=180000.00,
            deferral_amount=23000.00,
            match_amount=9000.00,
            after_tax_amount=0.00,
            section_415c_limit=69000,
            available_room=26200.00,
            mega_backdoor_amount=10800.00,
            requested_mega_backdoor=10800.00,
            individual_acp=11.0,
            constraint_status="Unconstrained",
            constraint_detail="Received full mega-backdoor amount",
        )

        nhce_employee = EmployeeImpactResponse(
            employee_id="EMP-002",
            is_hce=False,
            compensation=75000.00,
            deferral_amount=7500.00,
            match_amount=3750.00,
            after_tax_amount=500.00,
            section_415c_limit=69000,
            available_room=57250.00,
            mega_backdoor_amount=0.00,
            requested_mega_backdoor=0.00,
            individual_acp=5.67,
            constraint_status="Not Selected",
            constraint_detail="Not selected for mega-backdoor participation",
        )

        hce_summary = EmployeeImpactSummaryResponse(
            group="HCE",
            total_count=1,
            at_limit_count=0,
            reduced_count=0,
            average_available_room=26200.00,
            total_mega_backdoor=10800.00,
            average_individual_acp=11.0,
            total_match=9000.00,
            total_after_tax=0.00,
        )

        nhce_summary = EmployeeImpactSummaryResponse(
            group="NHCE",
            total_count=1,
            average_individual_acp=5.67,
            total_match=3750.00,
            total_after_tax=500.00,
        )

        view = EmployeeImpactViewResponse(
            census_id="census-123",
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed_used=42,
            plan_year=2025,
            section_415c_limit=69000,
            excluded_count=0,
            hce_employees=[hce_employee],
            nhce_employees=[nhce_employee],
            hce_summary=hce_summary,
            nhce_summary=nhce_summary,
        )

        assert view.census_id == "census-123"
        assert len(view.hce_employees) == 1
        assert len(view.nhce_employees) == 1

    def test_empty_employee_lists_allowed(self):
        """Empty employee lists are valid (edge case)."""
        hce_summary = EmployeeImpactSummaryResponse(
            group="HCE",
            total_count=0,
            at_limit_count=0,
            reduced_count=0,
            average_available_room=0.0,
            total_mega_backdoor=0.0,
            average_individual_acp=0.0,
            total_match=0.0,
            total_after_tax=0.0,
        )

        nhce_summary = EmployeeImpactSummaryResponse(
            group="NHCE",
            total_count=0,
            average_individual_acp=0.0,
            total_match=0.0,
            total_after_tax=0.0,
        )

        view = EmployeeImpactViewResponse(
            census_id="census-123",
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed_used=42,
            plan_year=2025,
            section_415c_limit=69000,
            excluded_count=0,
            hce_employees=[],
            nhce_employees=[],
            hce_summary=hce_summary,
            nhce_summary=nhce_summary,
        )

        assert len(view.hce_employees) == 0
        assert len(view.nhce_employees) == 0


# =============================================================================
# T059: POST /v2/scenario/{census_id}/employee-impact/export Schema Tests
# =============================================================================


class TestEmployeeImpactExportRequestSchema:
    """Contract tests for EmployeeImpactExportRequest schema."""

    def test_valid_minimal_request(self):
        """Valid request with only required fields passes validation."""
        request = EmployeeImpactExportRequest(
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
        )
        assert request.adoption_rate == 0.5
        assert request.export_group == "all"  # Default value
        assert request.include_group_column is True  # Default value

    def test_valid_full_request(self):
        """Valid request with all fields passes validation."""
        request = EmployeeImpactExportRequest(
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
            export_group="hce",
            include_group_column=False,
        )
        assert request.export_group == "hce"
        assert request.include_group_column is False

    def test_export_group_hce(self):
        """export_group='hce' is valid."""
        request = EmployeeImpactExportRequest(
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
            export_group="hce",
        )
        assert request.export_group == "hce"

    def test_export_group_nhce(self):
        """export_group='nhce' is valid."""
        request = EmployeeImpactExportRequest(
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
            export_group="nhce",
        )
        assert request.export_group == "nhce"

    def test_export_group_all(self):
        """export_group='all' is valid."""
        request = EmployeeImpactExportRequest(
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
            export_group="all",
        )
        assert request.export_group == "all"

    def test_include_group_column_true(self):
        """include_group_column=True is valid."""
        request = EmployeeImpactExportRequest(
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
            include_group_column=True,
        )
        assert request.include_group_column is True

    def test_include_group_column_false(self):
        """include_group_column=False is valid."""
        request = EmployeeImpactExportRequest(
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
            include_group_column=False,
        )
        assert request.include_group_column is False
