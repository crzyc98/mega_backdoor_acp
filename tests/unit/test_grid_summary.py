"""
Unit Tests for Grid Summary Calculation Functions.

T037-T041: Tests for compute_grid_summary(), find_first_failure_point(),
find_max_safe_contribution(), and worst_margin calculation.
"""

import pytest
from decimal import Decimal

from backend.app.services.scenario_runner import (
    compute_grid_summary,
    find_first_failure_point,
    find_max_safe_contribution,
    find_worst_margin,
)
from backend.app.services.models import (
    ScenarioResult,
    ScenarioStatus,
    LimitingBound,
    GridSummary,
    FailurePoint,
)


def make_scenario(
    adoption_rate: float,
    contribution_rate: float,
    status: ScenarioStatus,
    margin: float = 1.0
) -> ScenarioResult:
    """Helper to create a ScenarioResult with minimal required fields."""
    return ScenarioResult(
        status=status,
        nhce_acp=3.0 if status != ScenarioStatus.ERROR else None,
        hce_acp=4.0 if status != ScenarioStatus.ERROR else None,
        max_allowed_acp=5.0 if status != ScenarioStatus.ERROR else None,
        margin=margin if status != ScenarioStatus.ERROR else None,
        limiting_bound=LimitingBound.MULTIPLE if status != ScenarioStatus.ERROR else None,
        hce_contributor_count=5 if status != ScenarioStatus.ERROR else None,
        nhce_contributor_count=10 if status != ScenarioStatus.ERROR else None,
        total_mega_backdoor_amount=50000.0 if status != ScenarioStatus.ERROR else None,
        seed_used=42,
        adoption_rate=adoption_rate,
        contribution_rate=contribution_rate,
        error_message="Error" if status == ScenarioStatus.ERROR else None,
    )


class TestComputeGridSummary:
    """T037: Unit tests for compute_grid_summary() pass/risk/fail/error counts."""

    def test_summary_counts_all_pass(self):
        """All PASS scenarios should count correctly."""
        scenarios = [
            make_scenario(0.25, 0.04, ScenarioStatus.PASS),
            make_scenario(0.25, 0.06, ScenarioStatus.PASS),
            make_scenario(0.50, 0.04, ScenarioStatus.PASS),
            make_scenario(0.50, 0.06, ScenarioStatus.PASS),
        ]
        adoption_rates = [0.25, 0.50]
        contribution_rates = [0.04, 0.06]

        summary = compute_grid_summary(scenarios, adoption_rates, contribution_rates)

        assert summary.pass_count == 4
        assert summary.risk_count == 0
        assert summary.fail_count == 0
        assert summary.error_count == 0
        assert summary.total_count == 4

    def test_summary_counts_mixed_statuses(self):
        """Mixed status scenarios should count correctly."""
        scenarios = [
            make_scenario(0.25, 0.04, ScenarioStatus.PASS),
            make_scenario(0.25, 0.06, ScenarioStatus.RISK),
            make_scenario(0.50, 0.04, ScenarioStatus.RISK),
            make_scenario(0.50, 0.06, ScenarioStatus.FAIL),
            make_scenario(0.75, 0.04, ScenarioStatus.FAIL),
            make_scenario(0.75, 0.06, ScenarioStatus.ERROR),
        ]
        adoption_rates = [0.25, 0.50, 0.75]
        contribution_rates = [0.04, 0.06]

        summary = compute_grid_summary(scenarios, adoption_rates, contribution_rates)

        assert summary.pass_count == 1
        assert summary.risk_count == 2
        assert summary.fail_count == 2
        assert summary.error_count == 1
        assert summary.total_count == 6

    def test_summary_total_equals_sum(self):
        """Total count should equal sum of all status counts."""
        scenarios = [
            make_scenario(0.25, 0.04, ScenarioStatus.PASS),
            make_scenario(0.25, 0.06, ScenarioStatus.RISK),
            make_scenario(0.50, 0.04, ScenarioStatus.FAIL),
            make_scenario(0.50, 0.06, ScenarioStatus.ERROR),
        ]
        adoption_rates = [0.25, 0.50]
        contribution_rates = [0.04, 0.06]

        summary = compute_grid_summary(scenarios, adoption_rates, contribution_rates)

        assert summary.total_count == (
            summary.pass_count + summary.risk_count + summary.fail_count + summary.error_count
        )


class TestFindFirstFailurePoint:
    """T038: Unit tests for find_first_failure_point() algorithm."""

    def test_first_failure_found(self):
        """Should find the first FAIL in grid order."""
        scenarios = [
            make_scenario(0.25, 0.04, ScenarioStatus.PASS),
            make_scenario(0.25, 0.06, ScenarioStatus.PASS),
            make_scenario(0.50, 0.04, ScenarioStatus.FAIL),  # First failure
            make_scenario(0.50, 0.06, ScenarioStatus.FAIL),
        ]
        adoption_rates = [0.25, 0.50]
        contribution_rates = [0.04, 0.06]

        failure = find_first_failure_point(scenarios, adoption_rates, contribution_rates)

        assert failure is not None
        assert failure.adoption_rate == 0.50
        assert failure.contribution_rate == 0.04

    def test_no_failure_returns_none(self):
        """Should return None if no failures."""
        scenarios = [
            make_scenario(0.25, 0.04, ScenarioStatus.PASS),
            make_scenario(0.25, 0.06, ScenarioStatus.RISK),
            make_scenario(0.50, 0.04, ScenarioStatus.PASS),
            make_scenario(0.50, 0.06, ScenarioStatus.RISK),
        ]
        adoption_rates = [0.25, 0.50]
        contribution_rates = [0.04, 0.06]

        failure = find_first_failure_point(scenarios, adoption_rates, contribution_rates)

        assert failure is None

    def test_first_failure_order_matters(self):
        """First failure should be based on grid scan order."""
        # Grid scans adoption first, then contribution
        scenarios = [
            make_scenario(0.25, 0.04, ScenarioStatus.PASS),
            make_scenario(0.25, 0.06, ScenarioStatus.FAIL),  # This is first by column
            make_scenario(0.50, 0.04, ScenarioStatus.FAIL),  # This would be first by row order
            make_scenario(0.50, 0.06, ScenarioStatus.FAIL),
        ]
        adoption_rates = [0.25, 0.50]
        contribution_rates = [0.04, 0.06]

        failure = find_first_failure_point(scenarios, adoption_rates, contribution_rates)

        # First in grid order: scan by adoption rate, then contribution rate
        assert failure is not None
        assert failure.adoption_rate == 0.25
        assert failure.contribution_rate == 0.06

    def test_error_not_counted_as_failure(self):
        """ERROR status should not be counted as first failure."""
        scenarios = [
            make_scenario(0.25, 0.04, ScenarioStatus.PASS),
            make_scenario(0.25, 0.06, ScenarioStatus.ERROR),  # Not a failure
            make_scenario(0.50, 0.04, ScenarioStatus.FAIL),   # This is the first failure
            make_scenario(0.50, 0.06, ScenarioStatus.FAIL),
        ]
        adoption_rates = [0.25, 0.50]
        contribution_rates = [0.04, 0.06]

        failure = find_first_failure_point(scenarios, adoption_rates, contribution_rates)

        assert failure is not None
        assert failure.adoption_rate == 0.50
        assert failure.contribution_rate == 0.04


class TestFindMaxSafeContribution:
    """T039: Unit tests for find_max_safe_contribution() algorithm."""

    def test_max_safe_contribution_found(self):
        """Should find highest passing contribution at max adoption."""
        scenarios = [
            # At adoption 1.0 (max), check which contributions pass
            make_scenario(1.0, 0.02, ScenarioStatus.PASS),
            make_scenario(1.0, 0.04, ScenarioStatus.PASS),
            make_scenario(1.0, 0.06, ScenarioStatus.RISK),
            make_scenario(1.0, 0.08, ScenarioStatus.FAIL),
            # Other adoption rates don't matter for this calculation
            make_scenario(0.5, 0.02, ScenarioStatus.PASS),
            make_scenario(0.5, 0.04, ScenarioStatus.PASS),
            make_scenario(0.5, 0.06, ScenarioStatus.PASS),
            make_scenario(0.5, 0.08, ScenarioStatus.PASS),
        ]
        adoption_rates = [0.5, 1.0]
        contribution_rates = [0.02, 0.04, 0.06, 0.08]

        max_safe = find_max_safe_contribution(scenarios, adoption_rates, contribution_rates)

        # 0.06 is RISK which counts as safe, 0.08 is FAIL
        assert max_safe == 0.06

    def test_no_safe_contribution_returns_none(self):
        """Should return None if no contributions pass at max adoption."""
        scenarios = [
            make_scenario(1.0, 0.02, ScenarioStatus.FAIL),
            make_scenario(1.0, 0.04, ScenarioStatus.FAIL),
            make_scenario(0.5, 0.02, ScenarioStatus.PASS),
            make_scenario(0.5, 0.04, ScenarioStatus.PASS),
        ]
        adoption_rates = [0.5, 1.0]
        contribution_rates = [0.02, 0.04]

        max_safe = find_max_safe_contribution(scenarios, adoption_rates, contribution_rates)

        assert max_safe is None

    def test_all_pass_returns_highest_contribution(self):
        """Should return highest contribution if all pass at max adoption."""
        scenarios = [
            make_scenario(1.0, 0.02, ScenarioStatus.PASS),
            make_scenario(1.0, 0.04, ScenarioStatus.PASS),
            make_scenario(1.0, 0.06, ScenarioStatus.PASS),
        ]
        adoption_rates = [1.0]
        contribution_rates = [0.02, 0.04, 0.06]

        max_safe = find_max_safe_contribution(scenarios, adoption_rates, contribution_rates)

        assert max_safe == 0.06

    def test_risk_counts_as_safe(self):
        """RISK status should count as safe for max safe contribution."""
        scenarios = [
            make_scenario(1.0, 0.02, ScenarioStatus.PASS),
            make_scenario(1.0, 0.04, ScenarioStatus.RISK),  # Should count as safe
            make_scenario(1.0, 0.06, ScenarioStatus.FAIL),
        ]
        adoption_rates = [1.0]
        contribution_rates = [0.02, 0.04, 0.06]

        max_safe = find_max_safe_contribution(scenarios, adoption_rates, contribution_rates)

        assert max_safe == 0.04


class TestFindWorstMargin:
    """T040: Unit tests for worst_margin calculation."""

    def test_worst_margin_is_minimum(self):
        """Worst margin should be the minimum value."""
        scenarios = [
            make_scenario(0.25, 0.04, ScenarioStatus.PASS, margin=2.5),
            make_scenario(0.25, 0.06, ScenarioStatus.PASS, margin=1.5),
            make_scenario(0.50, 0.04, ScenarioStatus.RISK, margin=0.3),
            make_scenario(0.50, 0.06, ScenarioStatus.FAIL, margin=-0.5),  # Worst
        ]

        worst = find_worst_margin(scenarios)

        assert worst == -0.5

    def test_worst_margin_ignores_errors(self):
        """Worst margin should ignore ERROR scenarios (null margin)."""
        scenarios = [
            make_scenario(0.25, 0.04, ScenarioStatus.PASS, margin=2.5),
            make_scenario(0.25, 0.06, ScenarioStatus.ERROR),  # No margin
            make_scenario(0.50, 0.04, ScenarioStatus.RISK, margin=0.3),
        ]

        worst = find_worst_margin(scenarios)

        assert worst == 0.3

    def test_worst_margin_all_errors_returns_zero(self):
        """If all scenarios are ERROR, return 0.0."""
        scenarios = [
            make_scenario(0.25, 0.04, ScenarioStatus.ERROR),
            make_scenario(0.25, 0.06, ScenarioStatus.ERROR),
        ]

        worst = find_worst_margin(scenarios)

        assert worst == 0.0

    def test_worst_margin_negative(self):
        """Worst margin can be negative for failing scenarios."""
        scenarios = [
            make_scenario(0.25, 0.04, ScenarioStatus.FAIL, margin=-1.0),
            make_scenario(0.25, 0.06, ScenarioStatus.FAIL, margin=-2.5),
            make_scenario(0.50, 0.04, ScenarioStatus.FAIL, margin=-0.5),
        ]

        worst = find_worst_margin(scenarios)

        assert worst == -2.5


class TestAllPassGrid:
    """T041: Unit tests for all-PASS grid (first_failure_point = null)."""

    def test_all_pass_grid_summary(self):
        """All PASS grid should have null first_failure_point."""
        scenarios = [
            make_scenario(0.25, 0.04, ScenarioStatus.PASS, margin=2.0),
            make_scenario(0.25, 0.06, ScenarioStatus.PASS, margin=1.5),
            make_scenario(0.50, 0.04, ScenarioStatus.PASS, margin=1.0),
            make_scenario(0.50, 0.06, ScenarioStatus.PASS, margin=0.8),
        ]
        adoption_rates = [0.25, 0.50]
        contribution_rates = [0.04, 0.06]

        summary = compute_grid_summary(scenarios, adoption_rates, contribution_rates)

        assert summary.first_failure_point is None
        assert summary.pass_count == 4
        assert summary.fail_count == 0

    def test_all_pass_max_safe_is_highest_contribution(self):
        """All PASS grid should have max_safe_contribution = highest contribution."""
        scenarios = [
            make_scenario(0.25, 0.04, ScenarioStatus.PASS),
            make_scenario(0.25, 0.06, ScenarioStatus.PASS),
            make_scenario(0.25, 0.08, ScenarioStatus.PASS),
            make_scenario(1.0, 0.04, ScenarioStatus.PASS),
            make_scenario(1.0, 0.06, ScenarioStatus.PASS),
            make_scenario(1.0, 0.08, ScenarioStatus.PASS),
        ]
        adoption_rates = [0.25, 1.0]
        contribution_rates = [0.04, 0.06, 0.08]

        summary = compute_grid_summary(scenarios, adoption_rates, contribution_rates)

        assert summary.max_safe_contribution == 0.08

    def test_pass_and_risk_grid_no_failure(self):
        """Grid with only PASS and RISK should have null first_failure_point."""
        scenarios = [
            make_scenario(0.25, 0.04, ScenarioStatus.PASS),
            make_scenario(0.25, 0.06, ScenarioStatus.RISK),
            make_scenario(0.50, 0.04, ScenarioStatus.RISK),
            make_scenario(0.50, 0.06, ScenarioStatus.RISK),
        ]
        adoption_rates = [0.25, 0.50]
        contribution_rates = [0.04, 0.06]

        summary = compute_grid_summary(scenarios, adoption_rates, contribution_rates)

        assert summary.first_failure_point is None
        assert summary.pass_count == 1
        assert summary.risk_count == 3
        assert summary.fail_count == 0
