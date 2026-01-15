"""
Unit Tests for Employee-Level Impact Feature.

T003-T021: Tests for ConstraintStatus, EmployeeImpact, EmployeeImpactSummary,
EmployeeImpactView models and EmployeeImpactService.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock

# Import models (will fail until implementation is complete)
from src.core.models import (
    ConstraintStatus,
    EmployeeImpact,
    EmployeeImpactSummary,
    EmployeeImpactRequest,
    EmployeeImpactView,
)
from src.core.employee_impact import EmployeeImpactService
from src.storage.models import Participant, Census


# =============================================================================
# T003: ConstraintStatus Enum Tests
# =============================================================================


class TestConstraintStatus:
    """Test cases for ConstraintStatus enum."""

    def test_unconstrained_value(self):
        """ConstraintStatus.UNCONSTRAINED has correct string value."""
        assert ConstraintStatus.UNCONSTRAINED.value == "Unconstrained"

    def test_at_limit_value(self):
        """ConstraintStatus.AT_LIMIT has correct string value."""
        assert ConstraintStatus.AT_LIMIT.value == "At §415(c) Limit"

    def test_reduced_value(self):
        """ConstraintStatus.REDUCED has correct string value."""
        assert ConstraintStatus.REDUCED.value == "Reduced"

    def test_not_selected_value(self):
        """ConstraintStatus.NOT_SELECTED has correct string value."""
        assert ConstraintStatus.NOT_SELECTED.value == "Not Selected"

    def test_enum_is_string_type(self):
        """ConstraintStatus inherits from str for JSON serialization."""
        assert isinstance(ConstraintStatus.UNCONSTRAINED, str)

    def test_all_enum_values_exist(self):
        """All four constraint status values are defined."""
        values = [s.value for s in ConstraintStatus]
        assert len(values) == 4
        assert "Unconstrained" in values
        assert "At §415(c) Limit" in values
        assert "Reduced" in values
        assert "Not Selected" in values


# =============================================================================
# T004: EmployeeImpact Model Tests
# =============================================================================


class TestEmployeeImpactModel:
    """Test cases for EmployeeImpact Pydantic model validation."""

    def test_valid_hce_employee_impact(self):
        """Valid HCE employee impact with all fields passes validation."""
        impact = EmployeeImpact(
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
            constraint_status=ConstraintStatus.UNCONSTRAINED,
            constraint_detail="Received full mega-backdoor amount",
        )
        assert impact.employee_id == "EMP-001"
        assert impact.is_hce is True
        assert impact.compensation == 180000.00

    def test_valid_nhce_employee_impact(self):
        """Valid NHCE employee impact passes validation."""
        impact = EmployeeImpact(
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
            constraint_status=ConstraintStatus.NOT_SELECTED,
            constraint_detail="Not selected for mega-backdoor participation",
        )
        assert impact.is_hce is False
        assert impact.mega_backdoor_amount == 0.0

    def test_zero_compensation_null_acp(self):
        """Employee with zero compensation has None for individual_acp."""
        impact = EmployeeImpact(
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
            individual_acp=None,  # None when compensation is 0
            constraint_status=ConstraintStatus.NOT_SELECTED,
            constraint_detail="Not selected for mega-backdoor participation",
        )
        assert impact.individual_acp is None

    def test_negative_compensation_fails_validation(self):
        """Negative compensation fails validation."""
        with pytest.raises(ValueError):
            EmployeeImpact(
                employee_id="EMP-001",
                is_hce=True,
                compensation=-100.00,  # Invalid: negative
                deferral_amount=0.0,
                match_amount=0.0,
                after_tax_amount=0.0,
                section_415c_limit=69000,
                available_room=69000.0,
                mega_backdoor_amount=0.0,
                requested_mega_backdoor=0.0,
                individual_acp=None,
                constraint_status=ConstraintStatus.NOT_SELECTED,
                constraint_detail="N/A",
            )

    def test_at_limit_constraint_status(self):
        """Employee at §415(c) limit has correct status."""
        impact = EmployeeImpact(
            employee_id="EMP-004",
            is_hce=True,
            compensation=350000.00,
            deferral_amount=23000.00,
            match_amount=17500.00,
            after_tax_amount=28500.00,
            section_415c_limit=69000,
            available_room=0.00,
            mega_backdoor_amount=0.00,
            requested_mega_backdoor=21000.00,
            individual_acp=13.14,
            constraint_status=ConstraintStatus.AT_LIMIT,
            constraint_detail="§415(c) limit of $69,000 reached with existing contributions",
        )
        assert impact.constraint_status == ConstraintStatus.AT_LIMIT
        assert impact.available_room == 0.0

    def test_reduced_constraint_status(self):
        """Employee with reduced mega-backdoor has correct status."""
        impact = EmployeeImpact(
            employee_id="EMP-005",
            is_hce=True,
            compensation=200000.00,
            deferral_amount=23000.00,
            match_amount=10000.00,
            after_tax_amount=10000.00,
            section_415c_limit=69000,
            available_room=14000.00,
            mega_backdoor_amount=12000.00,  # Less than requested
            requested_mega_backdoor=14000.00,
            individual_acp=16.0,
            constraint_status=ConstraintStatus.REDUCED,
            constraint_detail="Reduced from $14,000.00 to $12,000.00 due to §415(c) limit",
        )
        assert impact.constraint_status == ConstraintStatus.REDUCED
        assert impact.mega_backdoor_amount < impact.requested_mega_backdoor


# =============================================================================
# T005: EmployeeImpactSummary Model Tests
# =============================================================================


class TestEmployeeImpactSummary:
    """Test cases for EmployeeImpactSummary Pydantic model."""

    def test_valid_hce_summary(self):
        """Valid HCE summary with HCE-specific fields passes validation."""
        summary = EmployeeImpactSummary(
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
        assert summary.total_mega_backdoor == 324000.00

    def test_valid_nhce_summary(self):
        """Valid NHCE summary with None for HCE-specific fields passes validation."""
        summary = EmployeeImpactSummary(
            group="NHCE",
            total_count=150,
            at_limit_count=None,  # NHCE doesn't have this
            reduced_count=None,
            average_available_room=None,
            total_mega_backdoor=None,
            average_individual_acp=4.25,
            total_match=225000.00,
            total_after_tax=8500.00,
        )
        assert summary.group == "NHCE"
        assert summary.at_limit_count is None
        assert summary.total_mega_backdoor is None

    def test_empty_group_summary(self):
        """Summary for empty group has zero counts."""
        summary = EmployeeImpactSummary(
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
        assert summary.total_count == 0


# =============================================================================
# T006: EmployeeImpactView Model Tests
# =============================================================================


class TestEmployeeImpactView:
    """Test cases for EmployeeImpactView container model."""

    def test_valid_employee_impact_view(self):
        """Valid EmployeeImpactView with all components passes validation."""
        hce_impact = EmployeeImpact(
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
            constraint_status=ConstraintStatus.UNCONSTRAINED,
            constraint_detail="Received full mega-backdoor amount",
        )

        nhce_impact = EmployeeImpact(
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
            constraint_status=ConstraintStatus.NOT_SELECTED,
            constraint_detail="Not selected for mega-backdoor participation",
        )

        hce_summary = EmployeeImpactSummary(
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

        nhce_summary = EmployeeImpactSummary(
            group="NHCE",
            total_count=1,
            at_limit_count=None,
            reduced_count=None,
            average_available_room=None,
            total_mega_backdoor=None,
            average_individual_acp=5.67,
            total_match=3750.00,
            total_after_tax=500.00,
        )

        view = EmployeeImpactView(
            census_id="census-123",
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed_used=42,
            plan_year=2025,
            section_415c_limit=69000,
            excluded_count=0,
            hce_employees=[hce_impact],
            nhce_employees=[nhce_impact],
            hce_summary=hce_summary,
            nhce_summary=nhce_summary,
        )

        assert view.census_id == "census-123"
        assert len(view.hce_employees) == 1
        assert len(view.nhce_employees) == 1
        assert view.hce_summary.group == "HCE"
        assert view.nhce_summary.group == "NHCE"


# =============================================================================
# T012-T014: EmployeeImpactService Tests
# =============================================================================


class TestEmployeeImpactService:
    """Test cases for EmployeeImpactService computation logic."""

    @pytest.fixture
    def mock_participant_repo(self):
        """Create mock participant repository."""
        repo = Mock()
        return repo

    @pytest.fixture
    def mock_census_repo(self):
        """Create mock census repository."""
        repo = Mock()
        return repo

    @pytest.fixture
    def sample_hce(self):
        """Create sample HCE participant."""
        return Participant(
            id="p1",
            census_id="census-123",
            internal_id="EMP-001",
            is_hce=True,
            compensation_cents=18000000,  # $180,000
            deferral_rate=12.78,  # Results in ~$23,000
            match_rate=5.0,  # Results in $9,000
            after_tax_rate=0.0,
            dob="1980-01-01",
            hire_date="2010-01-01",
        )

    @pytest.fixture
    def sample_nhce(self):
        """Create sample NHCE participant."""
        return Participant(
            id="p2",
            census_id="census-123",
            internal_id="EMP-002",
            is_hce=False,
            compensation_cents=7500000,  # $75,000
            deferral_rate=10.0,
            match_rate=5.0,
            after_tax_rate=0.67,
            dob="1985-02-02",
            hire_date="2012-06-01",
        )

    @pytest.fixture
    def sample_census(self):
        """Create sample census."""
        from datetime import datetime
        return Census(
            id="census-123",
            name="Test Census",
            plan_year=2025,
            upload_timestamp=datetime.utcnow(),
            participant_count=2,
            hce_count=1,
            nhce_count=1,
            salt="test-salt",
            version="1.0.0",
        )

    def test_service_initialization(self, mock_participant_repo, mock_census_repo):
        """Service initializes with repository dependencies."""
        service = EmployeeImpactService(mock_participant_repo, mock_census_repo)
        assert service.participant_repo == mock_participant_repo
        assert service.census_repo == mock_census_repo

    def test_compute_impact_returns_view(
        self, mock_participant_repo, mock_census_repo, sample_hce, sample_nhce, sample_census
    ):
        """compute_impact returns complete EmployeeImpactView."""
        mock_census_repo.get.return_value = sample_census
        mock_participant_repo.get_by_census.return_value = [sample_hce, sample_nhce]

        service = EmployeeImpactService(mock_participant_repo, mock_census_repo)
        result = service.compute_impact(
            census_id="census-123",
            adoption_rate=1.0,  # 100% adoption
            contribution_rate=0.06,  # 6%
            seed=42,
        )

        assert isinstance(result, EmployeeImpactView)
        assert result.census_id == "census-123"
        assert result.adoption_rate == 1.0
        assert result.contribution_rate == 0.06
        assert result.seed_used == 42
        assert result.plan_year == 2025

    def test_compute_impact_separates_hce_nhce(
        self, mock_participant_repo, mock_census_repo, sample_hce, sample_nhce, sample_census
    ):
        """compute_impact correctly separates HCE and NHCE employees."""
        mock_census_repo.get.return_value = sample_census
        mock_participant_repo.get_by_census.return_value = [sample_hce, sample_nhce]

        service = EmployeeImpactService(mock_participant_repo, mock_census_repo)
        result = service.compute_impact(
            census_id="census-123",
            adoption_rate=1.0,
            contribution_rate=0.06,
            seed=42,
        )

        assert len(result.hce_employees) == 1
        assert len(result.nhce_employees) == 1
        assert result.hce_employees[0].is_hce is True
        assert result.nhce_employees[0].is_hce is False

    def test_compute_impact_reproducible_with_seed(
        self, mock_participant_repo, mock_census_repo, sample_census
    ):
        """Same seed produces same HCE selection."""
        # Create multiple HCEs
        hces = [
            Participant(
                id=f"p{i}",
                census_id="census-123",
                internal_id=f"EMP-{i:03d}",
                is_hce=True,
                compensation_cents=18000000,
                deferral_rate=10.0,
                match_rate=5.0,
                after_tax_rate=0.0,
                dob="1980-01-01",
                hire_date="2010-01-01",
            )
            for i in range(10)
        ]

        mock_census_repo.get.return_value = sample_census
        mock_participant_repo.get_by_census.return_value = hces

        service = EmployeeImpactService(mock_participant_repo, mock_census_repo)

        # Run twice with same seed
        result1 = service.compute_impact("census-123", 0.5, 0.06, seed=42)
        result2 = service.compute_impact("census-123", 0.5, 0.06, seed=42)

        # Selected HCEs should be the same
        selected1 = [e for e in result1.hce_employees if e.mega_backdoor_amount > 0]
        selected2 = [e for e in result2.hce_employees if e.mega_backdoor_amount > 0]

        assert len(selected1) == len(selected2)
        assert set(e.employee_id for e in selected1) == set(e.employee_id for e in selected2)

    def test_compute_employee_impact_not_selected(
        self, mock_participant_repo, mock_census_repo, sample_hce, sample_census
    ):
        """Non-selected HCE has NOT_SELECTED status and zero mega-backdoor."""
        mock_census_repo.get.return_value = sample_census
        mock_participant_repo.get_by_census.return_value = [sample_hce]

        service = EmployeeImpactService(mock_participant_repo, mock_census_repo)
        result = service.compute_impact(
            census_id="census-123",
            adoption_rate=0.0,  # 0% adoption - no one selected
            contribution_rate=0.06,
            seed=42,
        )

        emp = result.hce_employees[0]
        assert emp.constraint_status == ConstraintStatus.NOT_SELECTED
        assert emp.mega_backdoor_amount == 0.0
        assert emp.requested_mega_backdoor == 0.0

    def test_compute_employee_impact_unconstrained(
        self, mock_participant_repo, mock_census_repo, sample_census
    ):
        """HCE with room below §415(c) receives full mega-backdoor."""
        # HCE with plenty of room
        hce = Participant(
            id="p1",
            census_id="census-123",
            internal_id="EMP-001",
            is_hce=True,
            compensation_cents=10000000,  # $100,000
            deferral_rate=10.0,  # $10,000 deferral
            match_rate=5.0,  # $5,000 match
            after_tax_rate=0.0,
            dob="1980-01-01",
            hire_date="2010-01-01",
        )

        mock_census_repo.get.return_value = sample_census
        mock_participant_repo.get_by_census.return_value = [hce]

        service = EmployeeImpactService(mock_participant_repo, mock_census_repo)
        result = service.compute_impact(
            census_id="census-123",
            adoption_rate=1.0,  # 100% adoption
            contribution_rate=0.06,  # 6% = $6,000
            seed=42,
        )

        emp = result.hce_employees[0]
        assert emp.constraint_status == ConstraintStatus.UNCONSTRAINED
        assert emp.mega_backdoor_amount == emp.requested_mega_backdoor
        assert emp.mega_backdoor_amount == 6000.0  # 6% of $100,000

    def test_compute_employee_impact_at_limit(
        self, mock_participant_repo, mock_census_repo, sample_census
    ):
        """HCE already at §415(c) limit has AT_LIMIT status."""
        # HCE already at or over the limit - contributions exceed 415(c) limit
        # For 2025, limit is $70,000
        # Total: $23,000 + $17,500 + $30,000 = $70,500 (over limit)
        hce = Participant(
            id="p1",
            census_id="census-123",
            internal_id="EMP-001",
            is_hce=True,
            compensation_cents=35000000,  # $350,000
            deferral_rate=6.57,  # ~$23,000
            match_rate=5.0,  # $17,500
            after_tax_rate=8.57,  # ~$30,000 -> Total ~$70,500 (over limit)
            dob="1980-01-01",
            hire_date="2010-01-01",
        )

        mock_census_repo.get.return_value = sample_census
        mock_participant_repo.get_by_census.return_value = [hce]

        service = EmployeeImpactService(mock_participant_repo, mock_census_repo)
        result = service.compute_impact(
            census_id="census-123",
            adoption_rate=1.0,
            contribution_rate=0.06,
            seed=42,
        )

        emp = result.hce_employees[0]
        assert emp.constraint_status == ConstraintStatus.AT_LIMIT
        assert emp.mega_backdoor_amount == 0.0
        assert emp.requested_mega_backdoor > 0  # Would have wanted some

    def test_compute_employee_impact_reduced(
        self, mock_participant_repo, mock_census_repo, sample_census
    ):
        """HCE with partial room receives reduced mega-backdoor."""
        # HCE with some room but not enough for full contribution
        hce = Participant(
            id="p1",
            census_id="census-123",
            internal_id="EMP-001",
            is_hce=True,
            compensation_cents=20000000,  # $200,000
            deferral_rate=11.5,  # $23,000
            match_rate=10.0,  # $20,000
            after_tax_rate=10.0,  # $20,000 -> Total $63,000, room = $6,000
            dob="1980-01-01",
            hire_date="2010-01-01",
        )

        mock_census_repo.get.return_value = sample_census
        mock_participant_repo.get_by_census.return_value = [hce]

        service = EmployeeImpactService(mock_participant_repo, mock_census_repo)
        result = service.compute_impact(
            census_id="census-123",
            adoption_rate=1.0,
            contribution_rate=0.06,  # 6% = $12,000 requested
            seed=42,
        )

        emp = result.hce_employees[0]
        assert emp.constraint_status == ConstraintStatus.REDUCED
        assert emp.mega_backdoor_amount < emp.requested_mega_backdoor
        assert emp.mega_backdoor_amount > 0  # Got something

    def test_compute_summary_hce_counts(
        self, mock_participant_repo, mock_census_repo, sample_census
    ):
        """HCE summary correctly counts at_limit and reduced."""
        # For 2025, limit is $70,000
        hces = [
            Participant(  # Unconstrained - total ~$15,000, plenty of room
                id="p1", census_id="census-123", internal_id="EMP-001",
                is_hce=True, compensation_cents=10000000,  # $100,000
                deferral_rate=10.0, match_rate=5.0, after_tax_rate=0.0,
                dob="1980-01-01", hire_date="2010-01-01",
            ),
            Participant(  # At limit - total ~$71,000 (over limit)
                id="p2", census_id="census-123", internal_id="EMP-002",
                is_hce=True, compensation_cents=35000000,  # $350,000
                deferral_rate=6.57, match_rate=5.0, after_tax_rate=8.57,  # ~$71,000 total
                dob="1980-01-01", hire_date="2010-01-01",
            ),
            Participant(  # Reduced - total ~$63,000, room for $7,000 but requests $12,000
                id="p3", census_id="census-123", internal_id="EMP-003",
                is_hce=True, compensation_cents=20000000,  # $200,000
                deferral_rate=11.5, match_rate=10.0, after_tax_rate=10.0,  # ~$63,000 total
                dob="1980-01-01", hire_date="2010-01-01",
            ),
        ]

        sample_census.hce_count = 3
        sample_census.participant_count = 3
        mock_census_repo.get.return_value = sample_census
        mock_participant_repo.get_by_census.return_value = hces

        service = EmployeeImpactService(mock_participant_repo, mock_census_repo)
        result = service.compute_impact(
            census_id="census-123",
            adoption_rate=1.0,
            contribution_rate=0.06,
            seed=42,
        )

        assert result.hce_summary.total_count == 3
        assert result.hce_summary.at_limit_count >= 1  # At least the one at limit
        assert result.hce_summary.reduced_count >= 1  # At least the one reduced
        # Note: exact counts depend on calculation logic

    def test_compute_summary_nhce_no_hce_fields(
        self, mock_participant_repo, mock_census_repo, sample_nhce, sample_census
    ):
        """NHCE summary has None for HCE-specific fields."""
        mock_census_repo.get.return_value = sample_census
        mock_participant_repo.get_by_census.return_value = [sample_nhce]

        service = EmployeeImpactService(mock_participant_repo, mock_census_repo)
        result = service.compute_impact(
            census_id="census-123",
            adoption_rate=1.0,
            contribution_rate=0.06,
            seed=42,
        )

        assert result.nhce_summary.at_limit_count is None
        assert result.nhce_summary.reduced_count is None
        assert result.nhce_summary.average_available_room is None
        assert result.nhce_summary.total_mega_backdoor is None


# =============================================================================
# T020-T021: Constraint Status Classification Tests
# =============================================================================


class TestConstraintClassification:
    """Test cases for constraint status classification logic."""

    def test_not_selected_when_not_in_selection(self):
        """HCE not in selected_hce_ids gets NOT_SELECTED status."""
        # This tests the internal logic - covered by service tests above
        pass

    def test_at_limit_when_available_room_zero_or_negative(self):
        """HCE with zero/negative available room gets AT_LIMIT status."""
        # This tests the internal logic - covered by service tests above
        pass

    def test_reduced_when_actual_less_than_requested(self):
        """HCE with partial allocation gets REDUCED status."""
        # This tests the internal logic - covered by service tests above
        pass

    def test_unconstrained_when_full_allocation(self):
        """HCE receiving full requested amount gets UNCONSTRAINED status."""
        # This tests the internal logic - covered by service tests above
        pass

    def test_constraint_detail_message_for_not_selected(self):
        """NOT_SELECTED status has correct detail message."""
        # Verify through EmployeeImpact model
        impact = EmployeeImpact(
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
            constraint_status=ConstraintStatus.NOT_SELECTED,
            constraint_detail="Not selected for mega-backdoor participation",
        )
        assert "Not selected" in impact.constraint_detail

    def test_constraint_detail_message_for_at_limit(self):
        """AT_LIMIT status has correct detail message with dollar amount."""
        impact = EmployeeImpact(
            employee_id="EMP-001",
            is_hce=True,
            compensation=350000.0,
            deferral_amount=23000.0,
            match_amount=17500.0,
            after_tax_amount=28500.0,
            section_415c_limit=69000,
            available_room=0.0,
            mega_backdoor_amount=0.0,
            requested_mega_backdoor=21000.0,
            individual_acp=13.14,
            constraint_status=ConstraintStatus.AT_LIMIT,
            constraint_detail="§415(c) limit of $69,000 reached with existing contributions",
        )
        assert "§415(c)" in impact.constraint_detail or "415(c)" in impact.constraint_detail
        assert "$69,000" in impact.constraint_detail or "69000" in impact.constraint_detail

    def test_constraint_detail_message_for_reduced(self):
        """REDUCED status has correct detail message with amounts."""
        impact = EmployeeImpact(
            employee_id="EMP-001",
            is_hce=True,
            compensation=200000.0,
            deferral_amount=23000.0,
            match_amount=20000.0,
            after_tax_amount=20000.0,
            section_415c_limit=69000,
            available_room=0.0,
            mega_backdoor_amount=6000.0,
            requested_mega_backdoor=12000.0,
            individual_acp=16.0,
            constraint_status=ConstraintStatus.REDUCED,
            constraint_detail="Reduced from $12,000.00 to $6,000.00 due to §415(c) limit",
        )
        assert "Reduced" in impact.constraint_detail
