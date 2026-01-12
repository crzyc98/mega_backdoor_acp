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

from src.core.acp_calculator import (
    calculate_nhce_acp,
    calculate_hce_acp,
    apply_acp_test,
)


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

    # Calculate number of adopters
    n_adopters = int(len(hce_ids) * adoption_rate)

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
