"""
ACP (Actual Contribution Percentage) Calculator.

This module implements the IRS ACP test calculations per IRC Section 401(m),
including the dual test (1.25x and +2.0 percentage points).
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

from src.core.constants import ACP_MULTIPLIER, ACP_ADDER, get_415c_limit
from src.core.models import LimitingBound


@dataclass
class ACPResult:
    """Result of an ACP test calculation."""
    nhce_acp: Decimal
    hce_acp: Decimal
    threshold: Decimal
    margin: Decimal
    result: Literal["PASS", "FAIL"]
    limiting_test: Literal["1.25x", "+2.0"]  # Legacy field
    limiting_bound: LimitingBound  # T019: New field with enum


def calculate_individual_acp(
    match_cents: int,
    after_tax_cents: int,
    compensation_cents: int
) -> Decimal:
    """
    Calculate individual ACP percentage.

    ACP = (match + after_tax) / compensation * 100

    Args:
        match_cents: Employer match contribution in cents
        after_tax_cents: After-tax contribution in cents
        compensation_cents: Annual compensation in cents

    Returns:
        Individual ACP as a Decimal percentage
    """
    if compensation_cents == 0:
        return Decimal("0")

    total_contribution = Decimal(match_cents + after_tax_cents)
    compensation = Decimal(compensation_cents)

    acp = (total_contribution / compensation * 100).quantize(
        Decimal("0.000001"), rounding=ROUND_HALF_UP
    )

    return acp


def calculate_group_acp(individual_acps: list[Decimal]) -> Decimal:
    """
    Calculate group ACP as the average of individual ACPs.

    Args:
        individual_acps: List of individual ACP percentages

    Returns:
        Group average ACP as a Decimal
    """
    if not individual_acps:
        return Decimal("0")

    total = sum(individual_acps)
    count = Decimal(len(individual_acps))

    return (total / count).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def calculate_nhce_acp(participants: list[dict]) -> Decimal:
    """
    Calculate NHCE group ACP from participant data.

    Args:
        participants: List of participant dictionaries with:
            - match_cents: int
            - after_tax_cents: int
            - compensation_cents: int
            - is_hce: bool

    Returns:
        NHCE group ACP as a Decimal percentage
    """
    nhce_acps = []
    for p in participants:
        if not p.get("is_hce", False):
            acp = calculate_individual_acp(
                match_cents=p.get("match_cents", 0),
                after_tax_cents=p.get("after_tax_cents", 0),
                compensation_cents=p.get("compensation_cents", 0)
            )
            nhce_acps.append(acp)

    return calculate_group_acp(nhce_acps)


def calculate_hce_acp(
    participants: list[dict],
    adopting_hce_ids: list[str],
    contribution_rate: Decimal
) -> Decimal:
    """
    Calculate HCE group ACP with simulated mega-backdoor contributions.

    For HCEs in the adopting_hce_ids list, adds simulated after-tax
    contributions at the specified contribution_rate.

    Args:
        participants: List of participant dictionaries
        adopting_hce_ids: List of internal IDs of HCEs adopting mega-backdoor
        contribution_rate: Mega-backdoor contribution rate as percentage (0-15)

    Returns:
        HCE group ACP as a Decimal percentage
    """
    hce_acps = []
    adopting_set = set(adopting_hce_ids)

    for p in participants:
        if p.get("is_hce", False):
            match_cents = p.get("match_cents", 0)
            after_tax_cents = p.get("after_tax_cents", 0)
            compensation_cents = p.get("compensation_cents", 0)

            # Add simulated contribution if this HCE is adopting
            internal_id = p.get("internal_id", "")
            if internal_id in adopting_set:
                # Simulated contribution = compensation * contribution_rate / 100
                simulated_cents = int(
                    Decimal(compensation_cents) * contribution_rate / 100
                )
                after_tax_cents += simulated_cents

            acp = calculate_individual_acp(
                match_cents=match_cents,
                after_tax_cents=after_tax_cents,
                compensation_cents=compensation_cents
            )
            hce_acps.append(acp)

    return calculate_group_acp(hce_acps)


def calculate_margin(threshold: Decimal, hce_acp: Decimal) -> Decimal:
    """
    Calculate margin (distance from threshold).

    Positive margin = PASS with room to spare
    Negative margin = FAIL by this amount
    Zero margin = Exactly at threshold (PASS)

    Args:
        threshold: Maximum allowed HCE ACP
        hce_acp: Actual HCE ACP

    Returns:
        Margin as Decimal (threshold - hce_acp)
    """
    return (threshold - hce_acp).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def apply_acp_test(nhce_acp: Decimal, hce_acp: Decimal) -> ACPResult:
    """
    Apply the IRS ACP dual test.

    The test uses the MORE favorable of:
    1. NHCE ACP × 1.25
    2. NHCE ACP + 2.0 percentage points

    The test passes if HCE ACP <= threshold (the higher of the two limits).

    Args:
        nhce_acp: NHCE group ACP percentage
        hce_acp: HCE group ACP percentage

    Returns:
        ACPResult with threshold, margin, result, and limiting test
    """
    # Calculate both test thresholds
    limit_125x = (nhce_acp * ACP_MULTIPLIER).quantize(
        Decimal("0.000001"), rounding=ROUND_HALF_UP
    )
    limit_plus2 = (nhce_acp + ACP_ADDER).quantize(
        Decimal("0.000001"), rounding=ROUND_HALF_UP
    )

    # Use the more favorable (higher) threshold
    # T019: Update to use LimitingBound enum alongside legacy field
    if limit_125x >= limit_plus2:
        threshold = limit_125x
        limiting_test = "1.25x"
        limiting_bound = LimitingBound.MULTIPLE
    else:
        threshold = limit_plus2
        limiting_test = "+2.0"
        limiting_bound = LimitingBound.ADDITIVE

    # Calculate margin and determine result
    margin = calculate_margin(threshold, hce_acp)
    result: Literal["PASS", "FAIL"] = "PASS" if hce_acp <= threshold else "FAIL"

    return ACPResult(
        nhce_acp=nhce_acp,
        hce_acp=hce_acp,
        threshold=threshold,
        margin=margin,
        result=result,
        limiting_test=limiting_test,
        limiting_bound=limiting_bound
    )


# T020: Calculate total mega-backdoor amount across adopting HCEs
def calculate_total_mega_backdoor(
    participants: list[dict],
    adopting_hce_ids: list[str],
    contribution_rate: Decimal
) -> int:
    """
    Calculate total simulated mega-backdoor contributions in cents.

    Args:
        participants: List of participant dictionaries
        adopting_hce_ids: List of internal IDs of HCEs adopting mega-backdoor
        contribution_rate: Mega-backdoor contribution rate as percentage (0-100)

    Returns:
        Total mega-backdoor amount in cents
    """
    adopting_set = set(adopting_hce_ids)
    total_cents = 0

    for p in participants:
        if p.get("is_hce", False) and p.get("internal_id", "") in adopting_set:
            compensation_cents = p.get("compensation_cents", 0)
            simulated_cents = int(Decimal(compensation_cents) * contribution_rate / 100)
            total_cents += simulated_cents

    return total_cents


def check_415c_limit(
    compensation_cents: int,
    deferral_cents: int,
    match_cents: int,
    after_tax_cents: int,
    simulated_after_tax_cents: int,
    plan_year: int
) -> dict:
    """
    Check if total contributions exceed IRC 415(c) annual additions limit.

    T088: Warns but doesn't block if simulated contributions exceed limit.

    Args:
        compensation_cents: Annual compensation in cents
        deferral_cents: Pre-tax/Roth 401(k) deferrals in cents
        match_cents: Employer match in cents
        after_tax_cents: Current after-tax contributions in cents
        simulated_after_tax_cents: Simulated mega-backdoor contribution in cents
        plan_year: Plan year for limit lookup

    Returns:
        Dictionary with:
            - exceeds_limit: bool
            - total_contributions: int (in cents)
            - limit: int (in cents)
            - warning_message: str or None
    """
    try:
        limit_dollars = get_415c_limit(plan_year)
    except ValueError:
        # If year not configured, use a reasonable default
        limit_dollars = 69000  # 2024 limit as fallback

    limit_cents = limit_dollars * 100

    total_contributions = (
        deferral_cents
        + match_cents
        + after_tax_cents
        + simulated_after_tax_cents
    )

    exceeds = total_contributions > limit_cents

    warning = None
    if exceeds:
        warning = (
            f"Total contributions (${total_contributions / 100:,.2f}) exceed "
            f"IRC 415(c) limit (${limit_dollars:,}). "
            "Actual contributions would need adjustment."
        )

    return {
        "exceeds_limit": exceeds,
        "total_contributions": total_contributions,
        "limit": limit_cents,
        "warning_message": warning
    }
