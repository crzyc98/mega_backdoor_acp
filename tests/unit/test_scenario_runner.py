"""
Unit Tests for Scenario Runner Module.

Tests seeded random HCE selection for reproducible analysis.
"""

import pytest
import numpy as np

from src.core.scenario_runner import (
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
