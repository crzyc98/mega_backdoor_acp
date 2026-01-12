"""
Unit Tests for Debug Mode functionality.

T057-T059: Tests for include_debug flag and debug_details generation.
"""

import pytest

from src.core.scenario_runner import run_single_scenario_v2
from src.core.models import ScenarioStatus, DebugDetails, ParticipantContribution, IntermediateValues


class TestDebugModeEnabled:
    """T057: Unit tests for include_debug=true returning debug_details."""

    @pytest.fixture
    def standard_participants(self):
        """Standard test participants with HCEs and NHCEs."""
        return [
            # NHCEs
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "nhce2", "match_cents": 100000, "after_tax_cents": 50000, "compensation_cents": 5000000, "is_hce": False},
            # HCEs
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 100000, "compensation_cents": 20000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 15000000, "is_hce": True},
        ]

    def test_debug_true_returns_debug_details(self, standard_participants):
        """include_debug=true should return debug_details."""
        result = run_single_scenario_v2(
            participants=standard_participants,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
            include_debug=True,
        )

        assert result.debug_details is not None
        assert isinstance(result.debug_details, DebugDetails)

    def test_debug_details_has_all_fields(self, standard_participants):
        """debug_details should contain all required fields."""
        result = run_single_scenario_v2(
            participants=standard_participants,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
            include_debug=True,
        )

        dd = result.debug_details
        assert dd is not None

        # Check all fields are present
        assert dd.selected_hce_ids is not None
        assert isinstance(dd.selected_hce_ids, list)

        assert dd.hce_contributions is not None
        assert isinstance(dd.hce_contributions, list)

        assert dd.nhce_contributions is not None
        assert isinstance(dd.nhce_contributions, list)

        assert dd.intermediate_values is not None
        assert isinstance(dd.intermediate_values, IntermediateValues)

    def test_debug_hce_contributions_all_hces(self, standard_participants):
        """debug_details should include contributions for ALL HCEs."""
        result = run_single_scenario_v2(
            participants=standard_participants,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
            include_debug=True,
        )

        dd = result.debug_details
        assert dd is not None

        # Should have 2 HCE contributions (all HCEs, not just adopters)
        assert len(dd.hce_contributions) == 2

        # Check each HCE contribution has required fields
        for c in dd.hce_contributions:
            assert isinstance(c, ParticipantContribution)
            assert c.id is not None
            assert c.compensation_cents is not None
            assert c.existing_acp_contributions_cents is not None
            assert c.simulated_mega_backdoor_cents is not None
            assert c.individual_acp is not None

    def test_debug_nhce_contributions_all_nhces(self, standard_participants):
        """debug_details should include contributions for ALL NHCEs."""
        result = run_single_scenario_v2(
            participants=standard_participants,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
            include_debug=True,
        )

        dd = result.debug_details
        assert dd is not None

        # Should have 2 NHCE contributions (all NHCEs)
        assert len(dd.nhce_contributions) == 2

        # NHCEs should have zero simulated mega-backdoor
        for c in dd.nhce_contributions:
            assert c.simulated_mega_backdoor_cents == 0


class TestDebugModeDisabled:
    """T058: Unit tests for include_debug=false/omitted omitting debug_details."""

    @pytest.fixture
    def standard_participants(self):
        """Standard test participants with HCEs and NHCEs."""
        return [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 100000, "compensation_cents": 20000000, "is_hce": True},
        ]

    def test_debug_false_omits_debug_details(self, standard_participants):
        """include_debug=false should omit debug_details."""
        result = run_single_scenario_v2(
            participants=standard_participants,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
            include_debug=False,
        )

        assert result.debug_details is None

    def test_debug_default_omits_debug_details(self, standard_participants):
        """Omitting include_debug should default to no debug_details."""
        result = run_single_scenario_v2(
            participants=standard_participants,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
            # include_debug not specified, defaults to False
        )

        assert result.debug_details is None


class TestDebugSelectedHceIds:
    """T059: Unit tests for debug_details containing correct selected_hce_ids."""

    def test_selected_hce_ids_matches_adopters(self):
        """selected_hce_ids should match exactly who was selected."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 15000000, "is_hce": True},
            {"internal_id": "hce3", "match_cents": 200000, "after_tax_cents": 0, "compensation_cents": 12000000, "is_hce": True},
        ]

        result = run_single_scenario_v2(
            participants=participants,
            adoption_rate=1.0,  # 100% - all HCEs selected
            contribution_rate=0.06,
            seed=42,
            include_debug=True,
        )

        dd = result.debug_details
        assert dd is not None

        # All 3 HCEs should be selected
        assert len(dd.selected_hce_ids) == 3
        assert set(dd.selected_hce_ids) == {"hce1", "hce2", "hce3"}

    def test_selected_hce_ids_empty_at_zero_adoption(self):
        """At 0% adoption, selected_hce_ids should be empty."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 15000000, "is_hce": True},
        ]

        result = run_single_scenario_v2(
            participants=participants,
            adoption_rate=0.0,  # 0% - no HCEs selected
            contribution_rate=0.06,
            seed=42,
            include_debug=True,
        )

        dd = result.debug_details
        assert dd is not None

        assert len(dd.selected_hce_ids) == 0

    def test_selected_hce_ids_deterministic(self):
        """selected_hce_ids should be deterministic with same seed."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 15000000, "is_hce": True},
            {"internal_id": "hce3", "match_cents": 200000, "after_tax_cents": 0, "compensation_cents": 12000000, "is_hce": True},
        ]

        result1 = run_single_scenario_v2(
            participants=participants,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=12345,
            include_debug=True,
        )

        result2 = run_single_scenario_v2(
            participants=participants,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=12345,
            include_debug=True,
        )

        assert result1.debug_details is not None
        assert result2.debug_details is not None
        assert result1.debug_details.selected_hce_ids == result2.debug_details.selected_hce_ids


class TestDebugIntermediateValues:
    """Additional tests for intermediate_values in debug output."""

    def test_intermediate_values_correct_counts(self):
        """intermediate_values should have correct HCE and NHCE counts."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "nhce2", "match_cents": 100000, "after_tax_cents": 50000, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "nhce3", "match_cents": 120000, "after_tax_cents": 30000, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 15000000, "is_hce": True},
        ]

        result = run_single_scenario_v2(
            participants=participants,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
            include_debug=True,
        )

        iv = result.debug_details.intermediate_values
        assert iv is not None

        assert iv.hce_count == 2
        assert iv.nhce_count == 3

    def test_intermediate_values_threshold_calculations(self):
        """intermediate_values should include threshold calculations."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 200000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},  # 4% ACP
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
        ]

        result = run_single_scenario_v2(
            participants=participants,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
            include_debug=True,
        )

        iv = result.debug_details.intermediate_values
        assert iv is not None

        # NHCE ACP = 4%, so:
        # threshold_multiple = 4 * 1.25 = 5
        # threshold_additive = 4 + 2 = 6
        assert iv.threshold_multiple is not None
        assert iv.threshold_additive is not None
        assert iv.threshold_multiple > 0
        assert iv.threshold_additive > 0


class TestDebugNoDebugOnError:
    """Debug details should be None when status is ERROR."""

    def test_error_status_no_debug_details(self):
        """ERROR status should not have debug_details even if requested."""
        # Empty census triggers ERROR
        result = run_single_scenario_v2(
            participants=[],
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
            include_debug=True,  # Request debug
        )

        assert result.status == ScenarioStatus.ERROR
        # Debug details should still be None for ERROR
        assert result.debug_details is None
