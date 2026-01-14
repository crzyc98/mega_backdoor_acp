"""
HCE Compensation Thresholds.

Historical IRS HCE compensation thresholds by plan year for ACP testing.
These thresholds determine who qualifies as a Highly Compensated Employee (HCE)
when using compensation-threshold mode.
"""

from __future__ import annotations

from typing import Literal

# Historical IRS HCE compensation thresholds by year
# Source: IRS Notice published annually
HCE_THRESHOLDS: dict[int, int] = {
    2020: 130_000,
    2021: 130_000,
    2022: 135_000,
    2023: 150_000,
    2024: 155_000,
    2025: 160_000,
    2026: 165_000,  # Projected
}

# Earliest and latest years with known thresholds
MIN_THRESHOLD_YEAR = min(HCE_THRESHOLDS.keys())
MAX_THRESHOLD_YEAR = max(HCE_THRESHOLDS.keys())


def get_threshold_for_year(year: int) -> int:
    """
    Get the HCE compensation threshold for a specific plan year.

    Args:
        year: The plan year (e.g., 2024, 2025)

    Returns:
        The HCE compensation threshold in dollars for that year.
        If the year is before known data, returns the earliest known threshold.
        If the year is after known data, returns the latest known threshold.
    """
    if year in HCE_THRESHOLDS:
        return HCE_THRESHOLDS[year]

    # Fallback: use closest known year
    if year < MIN_THRESHOLD_YEAR:
        return HCE_THRESHOLDS[MIN_THRESHOLD_YEAR]
    else:
        return HCE_THRESHOLDS[MAX_THRESHOLD_YEAR]


def get_all_thresholds() -> dict[int, int]:
    """
    Get all known HCE compensation thresholds.

    Returns:
        Dictionary mapping year to threshold amount in dollars.
    """
    return HCE_THRESHOLDS.copy()


def is_hce_by_compensation(compensation: float, year: int) -> bool:
    """
    Determine if an employee is HCE based on compensation and plan year.

    Args:
        compensation: Annual compensation in dollars
        year: Plan year for threshold lookup

    Returns:
        True if compensation >= threshold for the year, False otherwise.
    """
    threshold = get_threshold_for_year(year)
    return compensation >= threshold


# Type alias for HCE determination mode
HCEMode = Literal["explicit", "compensation_threshold"]
