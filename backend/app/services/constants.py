"""
IRS Constants and Limit Functions for ACP Sensitivity Analyzer.

This module provides regulatory constants and functions for ACP (Actual Contribution
Percentage) testing per IRC Section 401(m).
"""

from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

# System version for audit trail
SYSTEM_VERSION = "1.0.0"

# ACP Test Constants (IRC Section 401(m))
ACP_MULTIPLIER = Decimal("1.25")  # Factor applied to NHCE ACP
ACP_ADDER = Decimal("2.0")  # Percentage points added to NHCE ACP

# T001: RISK threshold - margin below which a passing result is classified as RISK
# 0.50 percentage points represents a fragile buffer that could be eroded by
# late-year adjustments, compensation corrections, or HCE reclassification
RISK_THRESHOLD = Decimal("0.50")

# T053: Error message constants for edge cases
ERROR_NO_HCES = "ACP test not applicable: no HCE participants in census"
ERROR_NO_NHCES = "ACP test cannot be calculated: no NHCE participants (NHCE ACP undefined)"
ERROR_EMPTY_CENSUS = "ACP test cannot be calculated: census is empty"

# Default configuration
DEFAULT_PLAN_YEAR = 2025
DEFAULT_RANDOM_SEED = 42

# Database configuration
DATABASE_PATH = Path("data/acp_analyzer.db")

# Rate limiting
RATE_LIMIT = "60/minute"


def _load_plan_constants() -> dict[str, Any]:
    """Load plan constants from YAML configuration file."""
    yaml_path = Path(__file__).parent / "plan_constants.yaml"
    if yaml_path.exists():
        with open(yaml_path) as f:
            return yaml.safe_load(f)
    return {}


# Load constants at module level
_PLAN_CONSTANTS = _load_plan_constants()


def get_annual_limits(plan_year: int) -> dict[str, int]:
    """
    Get IRS annual limits for a specific plan year.

    Args:
        plan_year: The plan year (e.g., 2024, 2025, 2026)

    Returns:
        Dictionary with limit names and values:
        - compensation_limit_401a17: Annual compensation limit
        - hce_threshold: HCE definition threshold
        - elective_deferral_limit_402g: Elective deferral limit
        - annual_additions_limit_415c: Annual additions limit
        - catch_up_limit_414v: Catch-up contribution limit

    Raises:
        ValueError: If plan year is not available in configuration
    """
    annual_limits = _PLAN_CONSTANTS.get("annual_limits", {})
    if plan_year not in annual_limits:
        available_years = sorted(annual_limits.keys())
        raise ValueError(
            f"Plan year {plan_year} not configured. "
            f"Available years: {available_years}"
        )
    return annual_limits[plan_year]


def get_415c_limit(plan_year: int) -> int:
    """
    Get the IRC Section 415(c) annual additions limit for a plan year.

    This limit caps total employer + employee contributions.

    Args:
        plan_year: The plan year

    Returns:
        The 415(c) limit in dollars
    """
    limits = get_annual_limits(plan_year)
    return limits["annual_additions_limit_415c"]


def get_compensation_limit(plan_year: int) -> int:
    """
    Get the IRC Section 401(a)(17) compensation limit for a plan year.

    This limit caps the compensation used for contribution calculations.

    Args:
        plan_year: The plan year

    Returns:
        The compensation limit in dollars
    """
    limits = get_annual_limits(plan_year)
    return limits["compensation_limit_401a17"]


def get_hce_threshold(plan_year: int) -> int:
    """
    Get the HCE (Highly Compensated Employee) threshold for a plan year.

    Employees earning above this threshold are classified as HCEs.

    Args:
        plan_year: The plan year

    Returns:
        The HCE threshold in dollars
    """
    limits = get_annual_limits(plan_year)
    return limits["hce_threshold"]


def get_elective_deferral_limit(plan_year: int) -> int:
    """
    Get the IRC Section 402(g) elective deferral limit for a plan year.

    This limits pre-tax and Roth 401(k) contributions.

    Args:
        plan_year: The plan year

    Returns:
        The elective deferral limit in dollars
    """
    limits = get_annual_limits(plan_year)
    return limits["elective_deferral_limit_402g"]


def calculate_acp_threshold(nhce_acp: Decimal) -> tuple[Decimal, str]:
    """
    Calculate the ACP test threshold based on NHCE ACP.

    The IRS dual test uses the MORE favorable of:
    1. NHCE ACP × 1.25
    2. NHCE ACP + 2.0 percentage points

    Args:
        nhce_acp: The NHCE group ACP percentage

    Returns:
        Tuple of (threshold, limiting_test) where:
        - threshold: The maximum allowed HCE ACP
        - limiting_test: "1.25x" or "+2.0" indicating which test determines the threshold
    """
    limit_125x = nhce_acp * ACP_MULTIPLIER
    limit_plus2 = nhce_acp + ACP_ADDER

    if limit_125x >= limit_plus2:
        return limit_125x, "1.25x"
    else:
        return limit_plus2, "+2.0"


def get_scenario_defaults() -> dict[str, list[float]]:
    """
    Get default scenario configuration for grid analysis.

    Returns:
        Dictionary with 'adoption_rates' and 'contribution_rates' lists
    """
    return _PLAN_CONSTANTS.get("scenario_defaults", {
        "adoption_rates": [0.0, 0.25, 0.50, 0.75, 1.0],
        "contribution_rates": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
    })


def get_validation_rules() -> dict[str, int]:
    """
    Get data validation rules for census data.

    Returns:
        Dictionary with 'min_compensation' and 'max_compensation'
    """
    return _PLAN_CONSTANTS.get("data_validation", {
        "min_compensation": 10000,
        "max_compensation": 500000
    })
