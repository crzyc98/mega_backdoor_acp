"""
Unit Tests for Scenario Runner Module.

Tests seeded random HCE selection for reproducible analysis.
"""

import pytest
import numpy as np

from backend.app.services.scenario_runner import (
    select_adopting_hces,
    run_single_scenario,
    run_grid_scenarios,
    ScenarioResult,
)


class TestSeededRandomSelection:
    """T020: Unit tests for seeded random HCE selection."""

    def test_select_adopting_hces_reproducible(self):
        """Same seed should produce same selection."""
        hce_ids = ["hce1", "hce2", "hce3", "hce4", "hce5"]
        adoption_rate = 0.6  # 60%
        seed = 42

        selection1 = select_adopting_hces(hce_ids, adoption_rate, seed)
        selection2 = select_adopting_hces(hce_ids, adoption_rate, seed)

        assert selection1 == selection2

    def test_select_adopting_hces_different_seeds(self):
        """Different seeds should produce different selections (usually)."""
        hce_ids = ["hce1", "hce2", "hce3", "hce4", "hce5", "hce6", "hce7", "hce8", "hce9", "hce10"]
        adoption_rate = 0.5
        seed1 = 42
        seed2 = 123

        selection1 = select_adopting_hces(hce_ids, adoption_rate, seed1)
        selection2 = select_adopting_hces(hce_ids, adoption_rate, seed2)

        # With 10 HCEs and 50% rate, very unlikely to get same selection
        assert selection1 != selection2

    def test_select_adopting_hces_zero_rate(self):
        """Zero adoption rate should return empty list."""
        hce_ids = ["hce1", "hce2", "hce3"]
        selection = select_adopting_hces(hce_ids, 0.0, seed=42)

        assert selection == []

    def test_select_adopting_hces_full_rate(self):
        """100% adoption rate should return all HCEs."""
        hce_ids = ["hce1", "hce2", "hce3"]
        selection = select_adopting_hces(hce_ids, 1.0, seed=42)

        assert set(selection) == set(hce_ids)

    def test_select_adopting_hces_count(self):
        """Selection count should match adoption rate."""
        hce_ids = [f"hce{i}" for i in range(100)]
        adoption_rate = 0.25  # 25%
        selection = select_adopting_hces(hce_ids, adoption_rate, seed=42)

        assert len(selection) == 25

    def test_select_adopting_hces_no_duplicates(self):
        """Selection should not contain duplicates."""
        hce_ids = [f"hce{i}" for i in range(50)]
        adoption_rate = 0.8
        selection = select_adopting_hces(hce_ids, adoption_rate, seed=42)

        assert len(selection) == len(set(selection))

    def test_select_adopting_hces_empty_input(self):
        """Empty HCE list should return empty selection."""
        selection = select_adopting_hces([], 0.5, seed=42)

        assert selection == []

    def test_select_adopting_hces_single_hce(self):
        """Single HCE with 100% rate should be selected."""
        selection = select_adopting_hces(["hce1"], 1.0, seed=42)

        assert selection == ["hce1"]

    def test_select_adopting_hces_rounding(self):
        """Selection count should round properly."""
        hce_ids = [f"hce{i}" for i in range(10)]
        # 10 HCEs * 0.35 = 3.5, should round to 3 or 4
        selection = select_adopting_hces(hce_ids, 0.35, seed=42)

        assert len(selection) in [3, 4]

    def test_select_adopting_hces_returns_list(self):
        """Selection should return a list (not numpy array)."""
        hce_ids = ["hce1", "hce2", "hce3"]
        selection = select_adopting_hces(hce_ids, 0.5, seed=42)

        assert isinstance(selection, list)


class TestSingleScenarioRunner:
    """Tests for running a single scenario analysis."""

    def test_run_single_scenario_basic(self):
        """Should run a complete scenario and return result."""
        participants = [
            # NHCEs
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "nhce2", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            # HCE
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
        ]

        result = run_single_scenario(
            participants=participants,
            adoption_rate=0.5,
            contribution_rate=6.0,
            seed=42
        )

        assert isinstance(result, ScenarioResult)
        assert result.nhce_acp > 0
        assert result.result in ["PASS", "FAIL"]
        assert result.limiting_test in ["1.25x", "+2.0"]
        assert result.seed == 42

    def test_run_single_scenario_reproducible(self):
        """Same inputs should produce same results."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "nhce2", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
        ]

        result1 = run_single_scenario(participants, 0.5, 6.0, seed=42)
        result2 = run_single_scenario(participants, 0.5, 6.0, seed=42)

        assert result1.nhce_acp == result2.nhce_acp
        assert result1.hce_acp == result2.hce_acp
        assert result1.result == result2.result
        assert result1.threshold == result2.threshold

    def test_run_single_scenario_returns_adopting_ids(self):
        """Result should include list of adopting HCE IDs."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
        ]

        result = run_single_scenario(
            participants=participants,
            adoption_rate=0.5,  # 50% of 2 HCEs = 1 adopter
            contribution_rate=6.0,
            seed=42
        )

        assert hasattr(result, 'adopting_hce_ids')
        assert len(result.adopting_hce_ids) == 1

    def test_run_single_scenario_no_hces(self):
        """Scenario with no HCEs should return zero HCE ACP."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "nhce2", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
        ]

        result = run_single_scenario(
            participants=participants,
            adoption_rate=0.5,
            contribution_rate=6.0,
            seed=42
        )

        # With no HCEs, test is not applicable - HCE ACP = 0
        assert result.hce_acp == 0
        assert result.result == "PASS"  # 0 <= any threshold

    def test_run_single_scenario_no_nhces(self):
        """Scenario with no NHCEs should have zero NHCE ACP."""
        participants = [
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
        ]

        result = run_single_scenario(
            participants=participants,
            adoption_rate=1.0,
            contribution_rate=6.0,
            seed=42
        )

        # NHCE ACP = 0, threshold = 2.0% (+2.0 wins)
        assert result.nhce_acp == 0
        assert result.threshold == 2.0


class TestGridScenarioRunner:
    """T050-T051: Unit tests for grid scenario runner."""

    def test_grid_scenario_runs_all_combinations(self):
        """Grid runner should execute all adoption x contribution combinations."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
        ]

        adoption_rates = [0.0, 0.5, 1.0]
        contribution_rates = [4.0, 8.0]

        results = run_grid_scenarios(
            participants=participants,
            adoption_rates=adoption_rates,
            contribution_rates=contribution_rates,
            seed=42
        )

        # Should have 3 x 2 = 6 results
        assert len(results) == 6

        # Verify all combinations are covered
        combos = [(r.adoption_rate, r.contribution_rate) for r in results]
        expected = [
            (0.0, 4.0), (0.0, 8.0),
            (0.5, 4.0), (0.5, 8.0),
            (1.0, 4.0), (1.0, 8.0),
        ]
        assert sorted(combos) == sorted(expected)

    def test_grid_scenario_aggregation(self):
        """Grid results should allow aggregation (pass/fail counts)."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 200000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},  # 4% ACP
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},  # 3% base
        ]

        results = run_grid_scenarios(
            participants=participants,
            adoption_rates=[0.0, 1.0],
            contribution_rates=[2.0, 6.0, 10.0],
            seed=42
        )

        # Count pass/fail
        pass_count = sum(1 for r in results if r.result == "PASS")
        fail_count = len(results) - pass_count

        assert pass_count + fail_count == 6
        # At 0% adoption, all should pass (using base rates)
        zero_adoption_results = [r for r in results if r.adoption_rate == 0.0]
        assert all(r.result == "PASS" for r in zero_adoption_results)

    def test_grid_scenario_seed_consistency(self):
        """Each grid cell should use consistent seeding."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
        ]

        results1 = run_grid_scenarios(participants, [0.5], [6.0], seed=42)
        results2 = run_grid_scenarios(participants, [0.5], [6.0], seed=42)

        assert results1[0].hce_acp == results2[0].hce_acp
        assert results1[0].adopting_hce_ids == results2[0].adopting_hce_ids


class TestScenarioResultProperties:
    """Tests for ScenarioResult data structure."""

    def test_scenario_result_has_required_fields(self):
        """ScenarioResult should have all required fields."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
        ]

        result = run_single_scenario(participants, 0.5, 6.0, seed=42)

        # Required fields per data-model.md
        assert hasattr(result, 'adoption_rate')
        assert hasattr(result, 'contribution_rate')
        assert hasattr(result, 'seed')
        assert hasattr(result, 'nhce_acp')
        assert hasattr(result, 'hce_acp')
        assert hasattr(result, 'threshold')
        assert hasattr(result, 'margin')
        assert hasattr(result, 'result')
        assert hasattr(result, 'limiting_test')

    def test_scenario_result_types(self):
        """ScenarioResult fields should have correct types."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
        ]

        result = run_single_scenario(participants, 0.5, 6.0, seed=42)

        assert isinstance(result.adoption_rate, (int, float))
        assert isinstance(result.contribution_rate, (int, float))
        assert isinstance(result.seed, int)
        assert isinstance(result.nhce_acp, (int, float))
        assert isinstance(result.hce_acp, (int, float))
        assert isinstance(result.threshold, (int, float))
        assert isinstance(result.margin, (int, float))
        assert isinstance(result.result, str)
        assert isinstance(result.limiting_test, str)


# ============================================================================
# Phase 3 (T014-T017): V2 Single Scenario Tests
# ============================================================================

from decimal import Decimal
from backend.app.services.scenario_runner import classify_status, run_single_scenario_v2
from backend.app.services.models import ScenarioStatus, LimitingBound, ScenarioResult as ScenarioResultV2


class TestClassifyStatus:
    """T014: Unit tests for classify_status() function."""

    def test_classify_fail_negative_margin(self):
        """Negative margin should return FAIL."""
        assert classify_status(Decimal("-0.5")) == ScenarioStatus.FAIL
        assert classify_status(Decimal("-1.0")) == ScenarioStatus.FAIL
        assert classify_status(Decimal("-10.0")) == ScenarioStatus.FAIL

    def test_classify_fail_zero_margin(self):
        """Zero margin should return FAIL (at threshold exactly)."""
        assert classify_status(Decimal("0")) == ScenarioStatus.FAIL
        assert classify_status(Decimal("0.0")) == ScenarioStatus.FAIL

    def test_classify_risk_small_positive_margin(self):
        """Margin > 0 but <= 0.50 should return RISK."""
        assert classify_status(Decimal("0.01")) == ScenarioStatus.RISK
        assert classify_status(Decimal("0.25")) == ScenarioStatus.RISK
        assert classify_status(Decimal("0.49")) == ScenarioStatus.RISK
        assert classify_status(Decimal("0.50")) == ScenarioStatus.RISK

    def test_classify_pass_large_margin(self):
        """Margin > 0.50 should return PASS."""
        assert classify_status(Decimal("0.51")) == ScenarioStatus.PASS
        assert classify_status(Decimal("1.0")) == ScenarioStatus.PASS
        assert classify_status(Decimal("5.0")) == ScenarioStatus.PASS

    def test_classify_boundary_exact(self):
        """Boundary value 0.50 should return RISK."""
        assert classify_status(Decimal("0.50")) == ScenarioStatus.RISK

    def test_classify_boundary_just_over(self):
        """Just over 0.50 should return PASS."""
        assert classify_status(Decimal("0.500001")) == ScenarioStatus.PASS


class TestSingleScenarioV2:
    """T015: Unit tests for enhanced run_single_scenario_v2()."""

    @pytest.fixture
    def standard_participants(self):
        """Standard test participants with HCEs and NHCEs."""
        return [
            # NHCEs with 3% ACP (150000/5000000 = 3%)
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "nhce2", "match_cents": 100000, "after_tax_cents": 50000, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "nhce3", "match_cents": 120000, "after_tax_cents": 30000, "compensation_cents": 5000000, "is_hce": False},
            # HCEs
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 100000, "compensation_cents": 20000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 15000000, "is_hce": True},
        ]

    def test_v2_returns_pydantic_model(self, standard_participants):
        """run_single_scenario_v2 should return ScenarioResultV2 model."""
        result = run_single_scenario_v2(
            participants=standard_participants,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
        )
        assert isinstance(result, ScenarioResultV2)

    def test_v2_returns_all_fields(self, standard_participants):
        """V2 result should have all required fields."""
        result = run_single_scenario_v2(
            participants=standard_participants,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
        )

        # Check all expected fields are present
        assert result.status in [ScenarioStatus.PASS, ScenarioStatus.RISK, ScenarioStatus.FAIL]
        assert result.nhce_acp is not None
        assert result.hce_acp is not None
        assert result.max_allowed_acp is not None
        assert result.margin is not None
        assert result.limiting_bound in [LimitingBound.MULTIPLE, LimitingBound.ADDITIVE]
        assert result.hce_contributor_count is not None
        assert result.nhce_contributor_count is not None
        assert result.total_mega_backdoor_amount is not None
        assert result.seed_used == 42
        assert result.adoption_rate == 0.5
        assert result.contribution_rate == 0.06

    def test_v2_status_classification(self, standard_participants):
        """V2 should correctly classify status based on margin."""
        # Low contribution should pass
        result_low = run_single_scenario_v2(
            participants=standard_participants,
            adoption_rate=0.5,
            contribution_rate=0.02,  # 2%
            seed=42,
        )
        # Should be PASS or RISK (not FAIL for low contribution)
        assert result_low.status in [ScenarioStatus.PASS, ScenarioStatus.RISK]

    def test_v2_limiting_bound_enum(self, standard_participants):
        """V2 should use LimitingBound enum."""
        result = run_single_scenario_v2(
            participants=standard_participants,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
        )
        assert result.limiting_bound in [LimitingBound.MULTIPLE, LimitingBound.ADDITIVE]


class TestSingleScenarioV2Error:
    """T016: Unit tests for ERROR status cases."""

    def test_error_zero_hces(self):
        """Census with zero HCEs should return ERROR."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "nhce2", "match_cents": 100000, "after_tax_cents": 50000, "compensation_cents": 5000000, "is_hce": False},
        ]

        result = run_single_scenario_v2(
            participants=participants,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
        )

        assert result.status == ScenarioStatus.ERROR
        assert result.error_message is not None
        assert "HCE" in result.error_message

    def test_error_zero_nhces(self):
        """Census with zero NHCEs should return ERROR."""
        participants = [
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 15000000, "is_hce": True},
        ]

        result = run_single_scenario_v2(
            participants=participants,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
        )

        assert result.status == ScenarioStatus.ERROR
        assert result.error_message is not None
        assert "NHCE" in result.error_message

    def test_error_empty_census(self):
        """Empty census should return ERROR."""
        result = run_single_scenario_v2(
            participants=[],
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
        )

        assert result.status == ScenarioStatus.ERROR
        assert result.error_message is not None
        assert "empty" in result.error_message.lower()

    def test_error_has_null_metrics(self):
        """ERROR status should have null metrics."""
        participants = [
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
        ]

        result = run_single_scenario_v2(
            participants=participants,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
        )

        assert result.status == ScenarioStatus.ERROR
        assert result.nhce_acp is None
        assert result.hce_acp is None
        assert result.max_allowed_acp is None


class TestSingleScenarioV2EdgeCases:
    """T050-T051: Edge case tests for adoption rate boundaries."""

    def test_zero_adoption_rate_valid_result(self):
        """T050: 0% adoption rate should return valid result with contributor_count=0."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "nhce2", "match_cents": 100000, "after_tax_cents": 50000, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 15000000, "is_hce": True},
        ]

        result = run_single_scenario_v2(
            participants=participants,
            adoption_rate=0.0,  # 0% adoption
            contribution_rate=0.06,
            seed=42,
        )

        # Should return valid result (not ERROR)
        assert result.status != ScenarioStatus.ERROR
        assert result.hce_contributor_count == 0
        assert result.total_mega_backdoor_amount == 0.0
        # All other metrics should be populated
        assert result.nhce_acp is not None
        assert result.hce_acp is not None
        assert result.margin is not None

    def test_full_adoption_rate_all_hces(self):
        """T051: 100% adoption rate should select all HCEs."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 15000000, "is_hce": True},
            {"internal_id": "hce3", "match_cents": 200000, "after_tax_cents": 0, "compensation_cents": 12000000, "is_hce": True},
        ]

        result = run_single_scenario_v2(
            participants=participants,
            adoption_rate=1.0,  # 100% adoption
            contribution_rate=0.06,
            seed=42,
        )

        # Should select all 3 HCEs
        assert result.hce_contributor_count == 3
        # Total mega-backdoor should be sum of all 3 HCE contributions
        # 10000000 * 0.06 + 15000000 * 0.06 + 12000000 * 0.06 = 2220000 cents = $22200
        expected_cents = 10000000 * 0.06 + 15000000 * 0.06 + 12000000 * 0.06
        expected_dollars = expected_cents / 100
        assert abs(result.total_mega_backdoor_amount - expected_dollars) < 1  # Allow small rounding

    def test_fractional_adoption_rate_rounding(self):
        """Fractional adoption rate should round correctly."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 15000000, "is_hce": True},
            {"internal_id": "hce3", "match_cents": 200000, "after_tax_cents": 0, "compensation_cents": 12000000, "is_hce": True},
        ]

        result = run_single_scenario_v2(
            participants=participants,
            adoption_rate=0.5,  # 50% of 3 = 1.5, rounds to 2
            contribution_rate=0.06,
            seed=42,
        )

        assert result.hce_contributor_count == 2


class TestSingleScenarioV2Determinism:
    """T017: Unit tests for determinism."""

    def test_same_seed_identical_results(self):
        """Same seed should produce identical results."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "nhce2", "match_cents": 100000, "after_tax_cents": 50000, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 15000000, "is_hce": True},
            {"internal_id": "hce3", "match_cents": 200000, "after_tax_cents": 50000, "compensation_cents": 12000000, "is_hce": True},
        ]

        result1 = run_single_scenario_v2(participants, 0.5, 0.06, seed=42)
        result2 = run_single_scenario_v2(participants, 0.5, 0.06, seed=42)

        assert result1.status == result2.status
        assert result1.nhce_acp == result2.nhce_acp
        assert result1.hce_acp == result2.hce_acp
        assert result1.margin == result2.margin
        assert result1.hce_contributor_count == result2.hce_contributor_count

    def test_determinism_100_iterations(self):
        """Same seed should produce identical results 100 times."""
        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 15000000, "is_hce": True},
            {"internal_id": "hce3", "match_cents": 200000, "after_tax_cents": 0, "compensation_cents": 12000000, "is_hce": True},
        ]

        baseline = run_single_scenario_v2(participants, 0.5, 0.06, seed=12345)

        for _ in range(100):
            result = run_single_scenario_v2(participants, 0.5, 0.06, seed=12345)
            assert result.status == baseline.status
            assert result.hce_acp == baseline.hce_acp
            assert result.margin == baseline.margin


# ============================================================================
# Phase 4 (T029-T030): V2 Grid Scenario Tests
# ============================================================================

class TestGridScenariosV2:
    """T029: Unit tests for run_grid_scenarios_v2()."""

    @pytest.fixture
    def standard_participants(self):
        """Standard test participants with HCEs and NHCEs."""
        return [
            # NHCEs
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "nhce2", "match_cents": 100000, "after_tax_cents": 50000, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "nhce3", "match_cents": 120000, "after_tax_cents": 30000, "compensation_cents": 5000000, "is_hce": False},
            # HCEs
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 100000, "compensation_cents": 20000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 15000000, "is_hce": True},
        ]

    def test_grid_v2_returns_grid_result(self, standard_participants):
        """run_grid_scenarios_v2 should return GridResult model."""
        from backend.app.services.scenario_runner import run_grid_scenarios_v2
        from backend.app.services.models import GridResult

        result = run_grid_scenarios_v2(
            participants=standard_participants,
            adoption_rates=[0.25, 0.5, 0.75],
            contribution_rates=[0.04, 0.06, 0.08],
            seed=42,
        )

        assert isinstance(result, GridResult)
        assert isinstance(result.scenarios, list)
        assert result.summary is not None
        assert result.seed_used == 42

    def test_grid_v2_correct_scenario_count(self, standard_participants):
        """Grid should return correct number of scenarios."""
        from backend.app.services.scenario_runner import run_grid_scenarios_v2

        result = run_grid_scenarios_v2(
            participants=standard_participants,
            adoption_rates=[0.0, 0.5, 1.0],
            contribution_rates=[0.02, 0.04, 0.06, 0.08],
            seed=42,
        )

        # 3 adoption rates x 4 contribution rates = 12 scenarios
        assert len(result.scenarios) == 12
        assert result.summary.total_count == 12

    def test_grid_v2_all_combinations(self, standard_participants):
        """Grid should include all adoption x contribution combinations."""
        from backend.app.services.scenario_runner import run_grid_scenarios_v2

        adoption_rates = [0.25, 0.5, 0.75]
        contribution_rates = [0.04, 0.06]

        result = run_grid_scenarios_v2(
            participants=standard_participants,
            adoption_rates=adoption_rates,
            contribution_rates=contribution_rates,
            seed=42,
        )

        # Check all combinations are present
        combos = [(s.adoption_rate, s.contribution_rate) for s in result.scenarios]
        expected = [
            (a, c) for a in adoption_rates for c in contribution_rates
        ]

        assert sorted(combos) == sorted(expected)

    def test_grid_v2_summary_counts(self, standard_participants):
        """Grid summary should have correct status counts."""
        from backend.app.services.scenario_runner import run_grid_scenarios_v2

        result = run_grid_scenarios_v2(
            participants=standard_participants,
            adoption_rates=[0.0, 0.5, 1.0],
            contribution_rates=[0.02, 0.06],
            seed=42,
        )

        total = (
            result.summary.pass_count
            + result.summary.risk_count
            + result.summary.fail_count
            + result.summary.error_count
        )
        assert total == result.summary.total_count
        assert total == len(result.scenarios)


class TestGridDeterminismV2:
    """T030: Unit tests for grid determinism."""

    def test_grid_v2_same_seed_identical_results(self):
        """Same seed should produce identical grid results."""
        from backend.app.services.scenario_runner import run_grid_scenarios_v2

        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 15000000, "is_hce": True},
        ]

        result1 = run_grid_scenarios_v2(
            participants=participants,
            adoption_rates=[0.25, 0.5, 0.75],
            contribution_rates=[0.04, 0.06, 0.08],
            seed=12345,
        )

        result2 = run_grid_scenarios_v2(
            participants=participants,
            adoption_rates=[0.25, 0.5, 0.75],
            contribution_rates=[0.04, 0.06, 0.08],
            seed=12345,
        )

        assert len(result1.scenarios) == len(result2.scenarios)

        for s1, s2 in zip(result1.scenarios, result2.scenarios):
            assert s1.status == s2.status
            assert s1.hce_acp == s2.hce_acp
            assert s1.margin == s2.margin
            assert s1.adoption_rate == s2.adoption_rate
            assert s1.contribution_rate == s2.contribution_rate

    def test_grid_v2_seed_used_consistent(self):
        """All scenarios in grid should use the same base seed."""
        from backend.app.services.scenario_runner import run_grid_scenarios_v2

        participants = [
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
        ]

        result = run_grid_scenarios_v2(
            participants=participants,
            adoption_rates=[0.25, 0.5],
            contribution_rates=[0.04, 0.06],
            seed=42,
        )

        # Per FR-017: same seed used for all scenarios in grid
        assert result.seed_used == 42


# ============================================================================
# Phase 8 (T065-T066): Performance Benchmarks
# ============================================================================

class TestPerformanceBenchmarks:
    """T065-T066: Performance benchmarks for scenario analysis."""

    @pytest.fixture
    def large_census(self):
        """Generate a census with 10K participants (3K HCEs, 7K NHCEs)."""
        participants = []

        # 3000 HCEs
        for i in range(3000):
            participants.append({
                "internal_id": f"hce{i}",
                "match_cents": 300000 + (i % 100) * 1000,
                "after_tax_cents": 50000 + (i % 50) * 1000,
                "compensation_cents": 15000000 + (i % 200) * 10000,
                "is_hce": True,
            })

        # 7000 NHCEs
        for i in range(7000):
            participants.append({
                "internal_id": f"nhce{i}",
                "match_cents": 100000 + (i % 50) * 1000,
                "after_tax_cents": 20000 + (i % 30) * 1000,
                "compensation_cents": 6000000 + (i % 100) * 10000,
                "is_hce": False,
            })

        return participants

    def test_single_scenario_performance(self, large_census):
        """T065: Single scenario should complete in <100ms for 10K participants."""
        import time

        start = time.perf_counter()
        result = run_single_scenario_v2(
            participants=large_census,
            adoption_rate=0.5,
            contribution_rate=0.06,
            seed=42,
        )
        elapsed = time.perf_counter() - start

        assert result.status != ScenarioStatus.ERROR
        assert elapsed < 0.100, f"Single scenario took {elapsed:.3f}s, expected <0.100s"

    def test_grid_100_scenarios_performance(self, large_census):
        """T066: 100-scenario grid should complete in <5s for 10K participants."""
        import time
        from backend.app.services.scenario_runner import run_grid_scenarios_v2

        # 10 adoption rates x 10 contribution rates = 100 scenarios
        adoption_rates = [i * 0.1 for i in range(1, 11)]  # 0.1 to 1.0
        contribution_rates = [i * 0.01 for i in range(1, 11)]  # 0.01 to 0.10

        start = time.perf_counter()
        result = run_grid_scenarios_v2(
            participants=large_census,
            adoption_rates=adoption_rates,
            contribution_rates=contribution_rates,
            seed=42,
        )
        elapsed = time.perf_counter() - start

        assert len(result.scenarios) == 100
        assert elapsed < 5.0, f"100-scenario grid took {elapsed:.3f}s, expected <5.0s"
