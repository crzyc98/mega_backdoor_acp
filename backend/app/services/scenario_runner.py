"""
Scenario Runner for ACP Sensitivity Analysis.

This module handles running single and grid scenarios, including
seeded random HCE selection for reproducible results.
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

import numpy as np

logger = logging.getLogger("acp_analyzer.core.scenario")

from app.services.acp_calculator import (
    calculate_nhce_acp,
    calculate_hce_acp,
    apply_acp_test,
    calculate_total_mega_backdoor,
    calculate_individual_acp,
)
from app.services.constants import (
    RISK_THRESHOLD,
    ERROR_NO_HCES,
    ERROR_NO_NHCES,
    ERROR_EMPTY_CENSUS,
)
from app.services.models import (
    ScenarioStatus,
    LimitingBound,
    ScenarioResult as ScenarioResultV2,
    DebugDetails,
    ParticipantContribution,
    IntermediateValues,
    GridResult,
    GridSummary,
    FailurePoint,
)


# T013: Classify status based on margin value
def classify_status(margin: Decimal) -> ScenarioStatus:
    """
    Classify scenario status based on margin from threshold.

    Args:
        margin: Distance from threshold (threshold - HCE_ACP)
                Positive = passing, negative = failing

    Returns:
        ScenarioStatus:
        - FAIL if margin <= 0 (over threshold)
        - RISK if 0 < margin <= 0.50 (passing but fragile)
        - PASS if margin > 0.50 (comfortable buffer)
    """
    if margin <= 0:
        return ScenarioStatus.FAIL
    elif margin <= RISK_THRESHOLD:
        return ScenarioStatus.RISK
    else:
        return ScenarioStatus.PASS


@dataclass
class ScenarioResult:
    """Result of a single scenario analysis."""
    adoption_rate: float
    contribution_rate: float
    seed: int
    nhce_acp: float
    hce_acp: float
    threshold: float
    margin: float
    result: Literal["PASS", "FAIL"]
    limiting_test: Literal["1.25x", "+2.0"]
    adopting_hce_ids: list[str]


def select_adopting_hces(
    hce_ids: list[str],
    adoption_rate: float,
    seed: int
) -> list[str]:
    """
    Select HCEs who adopt mega-backdoor based on adoption rate.

    Uses numpy's Generator with a seed for reproducible selection.

    Args:
        hce_ids: List of HCE internal IDs
        adoption_rate: Fraction of HCEs adopting (0.0 to 1.0)
        seed: Random seed for reproducibility

    Returns:
        List of internal IDs of adopting HCEs
    """
    if not hce_ids or adoption_rate == 0:
        return []

    if adoption_rate >= 1.0:
        return list(hce_ids)

    # Use seeded random generator
    rng = np.random.default_rng(seed)

    # T021: Use round() instead of int() for adoption count
    # This provides proper rounding (e.g., 50% of 5 = 2.5 → 2, 50% of 3 = 1.5 → 2)
    n_adopters = round(len(hce_ids) * adoption_rate)

    if n_adopters == 0:
        return []

    # Select without replacement
    selected = rng.choice(hce_ids, size=n_adopters, replace=False)

    return list(selected)


def run_single_scenario(
    participants: list[dict],
    adoption_rate: float,
    contribution_rate: float,
    seed: int
) -> ScenarioResult:
    """
    Run a single ACP test scenario.

    Args:
        participants: List of participant dictionaries with:
            - internal_id: str
            - is_hce: bool
            - match_cents: int
            - after_tax_cents: int
            - compensation_cents: int
        adoption_rate: Fraction of HCEs adopting (0.0 to 1.0)
        contribution_rate: Mega-backdoor contribution rate as percentage
        seed: Random seed for HCE selection

    Returns:
        ScenarioResult with all test metrics
    """
    # Extract HCE IDs
    hce_ids = [
        p["internal_id"]
        for p in participants
        if p.get("is_hce", False)
    ]

    # Select adopting HCEs
    adopting_hce_ids = select_adopting_hces(hce_ids, adoption_rate, seed)

    # Calculate ACPs
    nhce_acp = calculate_nhce_acp(participants)
    hce_acp = calculate_hce_acp(
        participants=participants,
        adopting_hce_ids=adopting_hce_ids,
        contribution_rate=Decimal(str(contribution_rate))
    )

    # Apply ACP test
    test_result = apply_acp_test(nhce_acp=nhce_acp, hce_acp=hce_acp)

    scenario_result = ScenarioResult(
        adoption_rate=adoption_rate,
        contribution_rate=contribution_rate,
        seed=seed,
        nhce_acp=float(test_result.nhce_acp),
        hce_acp=float(test_result.hce_acp),
        threshold=float(test_result.threshold),
        margin=float(test_result.margin),
        result=test_result.result,
        limiting_test=test_result.limiting_test,
        adopting_hce_ids=adopting_hce_ids
    )

    logger.info(
        "Scenario completed: adoption=%.1f%%, contrib=%.1f%%, result=%s, margin=%.3f%%",
        adoption_rate * 100,
        contribution_rate,
        test_result.result,
        float(test_result.margin)
    )

    return scenario_result


# T022-T025, T053-T056, T060-T063: Enhanced scenario runner returning new ScenarioResult model
def run_single_scenario_v2(
    participants: list[dict],
    adoption_rate: float,
    contribution_rate: float,
    seed: int,
    include_debug: bool = False
) -> ScenarioResultV2:
    """
    Run a single ACP test scenario with comprehensive result data.

    This is the v2 implementation returning the enhanced ScenarioResult model
    with PASS/RISK/FAIL/ERROR status, debug details, and all metrics.

    Args:
        participants: List of participant dictionaries with:
            - internal_id: str
            - is_hce: bool
            - match_cents: int
            - after_tax_cents: int
            - compensation_cents: int
        adoption_rate: Fraction of HCEs adopting (0.0 to 1.0)
        contribution_rate: Mega-backdoor contribution rate as fraction (0.0 to 1.0)
        seed: Random seed for HCE selection
        include_debug: Include detailed calculation breakdown

    Returns:
        ScenarioResultV2 with all test metrics and optional debug details
    """
    # T023/T054: Edge case detection - empty census
    if not participants:
        return ScenarioResultV2(
            status=ScenarioStatus.ERROR,
            seed_used=seed,
            adoption_rate=adoption_rate,
            contribution_rate=contribution_rate,
            error_message=ERROR_EMPTY_CENSUS,
        )

    # Separate HCEs and NHCEs
    hces = [p for p in participants if p.get("is_hce", False)]
    nhces = [p for p in participants if not p.get("is_hce", False)]
    hce_ids = [p["internal_id"] for p in hces]

    # T023: Edge case detection - no HCEs
    if not hces:
        return ScenarioResultV2(
            status=ScenarioStatus.ERROR,
            seed_used=seed,
            adoption_rate=adoption_rate,
            contribution_rate=contribution_rate,
            error_message=ERROR_NO_HCES,
        )

    # T023: Edge case detection - no NHCEs
    if not nhces:
        return ScenarioResultV2(
            status=ScenarioStatus.ERROR,
            seed_used=seed,
            adoption_rate=adoption_rate,
            contribution_rate=contribution_rate,
            error_message=ERROR_NO_NHCES,
        )

    # T055/T056: Select adopting HCEs (handles 0% and 100% correctly)
    adopting_hce_ids = select_adopting_hces(hce_ids, adoption_rate, seed)

    # Convert contribution rate to percentage for calculation (0.06 -> 6.0)
    contribution_pct = Decimal(str(contribution_rate * 100))

    # Calculate ACPs
    nhce_acp = calculate_nhce_acp(participants)
    hce_acp = calculate_hce_acp(
        participants=participants,
        adopting_hce_ids=adopting_hce_ids,
        contribution_rate=contribution_pct
    )

    # Apply ACP test
    test_result = apply_acp_test(nhce_acp=nhce_acp, hce_acp=hce_acp)

    # Classify status using margin (T013)
    status = classify_status(test_result.margin)

    # T024: Calculate NHCE contributor count (NHCEs with any match or after-tax)
    nhce_contributor_count = sum(
        1 for p in nhces
        if p.get("match_cents", 0) > 0 or p.get("after_tax_cents", 0) > 0
    )

    # T025: Calculate total mega-backdoor amount
    total_mega_backdoor_cents = calculate_total_mega_backdoor(
        participants=participants,
        adopting_hce_ids=adopting_hce_ids,
        contribution_rate=contribution_pct
    )
    total_mega_backdoor_dollars = total_mega_backdoor_cents / 100.0

    # T060-T063: Build debug details if requested
    debug_details = None
    if include_debug:
        # Collect HCE contributions
        adopting_set = set(adopting_hce_ids)
        hce_contributions = []
        hce_acp_sum = Decimal("0")

        for p in hces:
            match_cents = p.get("match_cents", 0)
            after_tax_cents = p.get("after_tax_cents", 0)
            compensation_cents = p.get("compensation_cents", 0)
            internal_id = p.get("internal_id", "")

            simulated_cents = 0
            if internal_id in adopting_set:
                simulated_cents = int(Decimal(compensation_cents) * contribution_pct / 100)

            individual_acp = calculate_individual_acp(
                match_cents=match_cents,
                after_tax_cents=after_tax_cents + simulated_cents,
                compensation_cents=compensation_cents
            )
            hce_acp_sum += individual_acp

            hce_contributions.append(ParticipantContribution(
                id=internal_id,
                compensation_cents=compensation_cents,
                existing_acp_contributions_cents=match_cents + after_tax_cents,
                simulated_mega_backdoor_cents=simulated_cents,
                individual_acp=float(individual_acp)
            ))

        # Collect NHCE contributions
        nhce_contributions = []
        nhce_acp_sum = Decimal("0")

        for p in nhces:
            match_cents = p.get("match_cents", 0)
            after_tax_cents = p.get("after_tax_cents", 0)
            compensation_cents = p.get("compensation_cents", 0)

            individual_acp = calculate_individual_acp(
                match_cents=match_cents,
                after_tax_cents=after_tax_cents,
                compensation_cents=compensation_cents
            )
            nhce_acp_sum += individual_acp

            nhce_contributions.append(ParticipantContribution(
                id=p.get("internal_id", ""),
                compensation_cents=compensation_cents,
                existing_acp_contributions_cents=match_cents + after_tax_cents,
                simulated_mega_backdoor_cents=0,
                individual_acp=float(individual_acp)
            ))

        # Calculate threshold intermediates
        threshold_multiple = float(test_result.limit_125)
        threshold_additive = float(test_result.limit_2pct_capped)

        debug_details = DebugDetails(
            selected_hce_ids=adopting_hce_ids,
            hce_contributions=hce_contributions,
            nhce_contributions=nhce_contributions,
            intermediate_values=IntermediateValues(
                hce_acp_sum=float(hce_acp_sum),
                hce_count=len(hces),
                nhce_acp_sum=float(nhce_acp_sum),
                nhce_count=len(nhces),
                threshold_multiple=threshold_multiple,
                threshold_additive=threshold_additive
            )
        )

    result = ScenarioResultV2(
        status=status,
        nhce_acp=float(test_result.nhce_acp),
        hce_acp=float(test_result.hce_acp),
        limit_125=float(test_result.limit_125),
        limit_2pct_uncapped=float(test_result.limit_2pct_uncapped),
        cap_2x=float(test_result.cap_2x),
        limit_2pct_capped=float(test_result.limit_2pct_capped),
        effective_limit=float(test_result.effective_limit),
        max_allowed_acp=float(test_result.threshold),
        margin=float(test_result.margin),
        binding_rule=test_result.binding_rule,
        limiting_bound=test_result.limiting_bound,
        hce_contributor_count=len(adopting_hce_ids),
        nhce_contributor_count=nhce_contributor_count,
        total_mega_backdoor_amount=total_mega_backdoor_dollars,
        seed_used=seed,
        adoption_rate=adoption_rate,
        contribution_rate=contribution_rate,
        debug_details=debug_details,
    )

    logger.info(
        "Scenario v2 completed: adoption=%.1f%%, contrib=%.1f%%, status=%s, margin=%.3f%%",
        adoption_rate * 100,
        contribution_rate * 100,
        status.value,
        float(test_result.margin)
    )

    return result


def run_grid_scenarios(
    participants: list[dict],
    adoption_rates: list[float],
    contribution_rates: list[float],
    seed: int
) -> list[ScenarioResult]:
    """
    Run multiple scenarios across a grid of adoption and contribution rates.

    Args:
        participants: List of participant dictionaries
        adoption_rates: List of adoption rates to test (0.0 to 1.0)
        contribution_rates: List of contribution rates to test (0 to 15)
        seed: Base random seed (incremented for each scenario)

    Returns:
        List of ScenarioResults for all combinations
    """
    total_scenarios = len(adoption_rates) * len(contribution_rates)
    logger.info(
        "Starting grid analysis: %d scenarios (%d adoption x %d contribution rates)",
        total_scenarios,
        len(adoption_rates),
        len(contribution_rates)
    )

    results = []

    for i, adoption_rate in enumerate(adoption_rates):
        for j, contribution_rate in enumerate(contribution_rates):
            # Use consistent seed per grid position
            scenario_seed = seed + i * len(contribution_rates) + j

            result = run_single_scenario(
                participants=participants,
                adoption_rate=adoption_rate,
                contribution_rate=contribution_rate,
                seed=scenario_seed
            )
            results.append(result)

    pass_count = sum(1 for r in results if r.result == "PASS")
    logger.info(
        "Grid analysis complete: %d/%d passed (%.1f%%)",
        pass_count,
        total_scenarios,
        pass_count / total_scenarios * 100 if total_scenarios else 0
    )

    return results


# T032-T033: V2 grid scenario runner returning GridResult model
def run_grid_scenarios_v2(
    participants: list[dict],
    adoption_rates: list[float],
    contribution_rates: list[float],
    seed: int,
    include_debug: bool = False
) -> GridResult:
    """
    Run multiple scenarios across a grid of adoption and contribution rates.

    Returns a GridResult with all scenarios and a summary.

    Args:
        participants: List of participant dictionaries
        adoption_rates: List of adoption rates to test (0.0 to 1.0)
        contribution_rates: List of contribution rates to test (0.0 to 1.0)
        seed: Base random seed (same seed used for ALL scenarios per FR-017)
        include_debug: Include debug details in each scenario result

    Returns:
        GridResult with scenarios list and summary
    """
    total_scenarios = len(adoption_rates) * len(contribution_rates)
    logger.info(
        "Starting grid analysis v2: %d scenarios (%d adoption x %d contribution rates)",
        total_scenarios,
        len(adoption_rates),
        len(contribution_rates)
    )

    scenarios = []

    # FR-017: Same seed used for all scenarios in grid
    for adoption_rate in adoption_rates:
        for contribution_rate in contribution_rates:
            result = run_single_scenario_v2(
                participants=participants,
                adoption_rate=adoption_rate,
                contribution_rate=contribution_rate,
                seed=seed,  # Same seed for all scenarios
                include_debug=include_debug
            )
            scenarios.append(result)

    # Compute summary
    summary = compute_grid_summary(scenarios, adoption_rates, contribution_rates)

    logger.info(
        "Grid analysis v2 complete: %d PASS, %d RISK, %d FAIL, %d ERROR",
        summary.pass_count,
        summary.risk_count,
        summary.fail_count,
        summary.error_count
    )

    return GridResult(
        scenarios=scenarios,
        summary=summary,
        seed_used=seed
    )


# T042-T045: Compute grid summary statistics
def compute_grid_summary(
    scenarios: list[ScenarioResultV2],
    adoption_rates: list[float],
    contribution_rates: list[float]
) -> GridSummary:
    """
    Compute summary statistics for a grid of scenario results.

    Args:
        scenarios: List of ScenarioResult objects from grid run
        adoption_rates: Ordered list of adoption rates used
        contribution_rates: Ordered list of contribution rates used

    Returns:
        GridSummary with counts, first failure point, max safe contribution, and worst margin
    """
    # Count statuses
    pass_count = sum(1 for s in scenarios if s.status == ScenarioStatus.PASS)
    risk_count = sum(1 for s in scenarios if s.status == ScenarioStatus.RISK)
    fail_count = sum(1 for s in scenarios if s.status == ScenarioStatus.FAIL)
    error_count = sum(1 for s in scenarios if s.status == ScenarioStatus.ERROR)
    total_count = len(scenarios)

    # Find first failure point (scanning grid in order)
    first_failure_point = find_first_failure_point(scenarios, adoption_rates, contribution_rates)

    # Find max safe contribution rate
    max_safe_contribution = find_max_safe_contribution(scenarios, adoption_rates, contribution_rates)

    # Find worst margin (smallest margin value)
    worst_margin = find_worst_margin(scenarios)

    return GridSummary(
        pass_count=pass_count,
        risk_count=risk_count,
        fail_count=fail_count,
        error_count=error_count,
        total_count=total_count,
        first_failure_point=first_failure_point,
        max_safe_contribution=max_safe_contribution,
        worst_margin=worst_margin
    )


# T043: Find first failure point in grid
def find_first_failure_point(
    scenarios: list[ScenarioResultV2],
    adoption_rates: list[float],
    contribution_rates: list[float]
) -> FailurePoint | None:
    """
    Find the first failure point in the grid.

    Scans the grid in order (by adoption rate, then contribution rate)
    and returns the coordinates of the first FAIL status.

    Args:
        scenarios: List of ScenarioResult objects
        adoption_rates: Ordered list of adoption rates
        contribution_rates: Ordered list of contribution rates

    Returns:
        FailurePoint with coordinates of first failure, or None if no failures
    """
    # Build lookup for quick access
    scenario_map = {
        (s.adoption_rate, s.contribution_rate): s
        for s in scenarios
    }

    # Scan in order
    for adoption_rate in adoption_rates:
        for contribution_rate in contribution_rates:
            scenario = scenario_map.get((adoption_rate, contribution_rate))
            if scenario and scenario.status == ScenarioStatus.FAIL:
                return FailurePoint(
                    adoption_rate=adoption_rate,
                    contribution_rate=contribution_rate
                )

    return None


# T044: Find max safe contribution rate
def find_max_safe_contribution(
    scenarios: list[ScenarioResultV2],
    adoption_rates: list[float],
    contribution_rates: list[float]
) -> float | None:
    """
    Find the highest contribution rate that passes at maximum adoption.

    This identifies the highest contribution rate where the test still
    passes at the highest adoption rate in the grid.

    Args:
        scenarios: List of ScenarioResult objects
        adoption_rates: Ordered list of adoption rates
        contribution_rates: Ordered list of contribution rates

    Returns:
        Maximum safe contribution rate, or None if none pass at max adoption
    """
    if not adoption_rates or not contribution_rates:
        return None

    max_adoption = max(adoption_rates)

    # Build lookup for quick access
    scenario_map = {
        (s.adoption_rate, s.contribution_rate): s
        for s in scenarios
    }

    # Find highest passing contribution at max adoption
    # Sort contribution rates in descending order
    sorted_contributions = sorted(contribution_rates, reverse=True)

    for contribution_rate in sorted_contributions:
        scenario = scenario_map.get((max_adoption, contribution_rate))
        if scenario and scenario.status in [ScenarioStatus.PASS, ScenarioStatus.RISK]:
            return contribution_rate

    return None


# T045: Find worst margin across all scenarios
def find_worst_margin(scenarios: list[ScenarioResultV2]) -> float:
    """
    Find the worst (smallest) margin across all scenarios.

    Args:
        scenarios: List of ScenarioResult objects

    Returns:
        Smallest margin value (can be negative for failing scenarios)
    """
    margins = [
        s.margin for s in scenarios
        if s.margin is not None and s.status != ScenarioStatus.ERROR
    ]

    if not margins:
        return 0.0

    return min(margins)
