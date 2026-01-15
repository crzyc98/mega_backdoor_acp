"""
Unit tests for ACP eligibility and permissive disaggregation logic.
"""

from datetime import date

from src.core.acp_eligibility import determine_acp_inclusion, plan_year_bounds


def test_hired_late_eligible_next_year_excluded():
    """Hired late -> eligibility after plan year -> excluded."""
    plan_year_start, plan_year_end = plan_year_bounds(2024)
    result = determine_acp_inclusion(
        dob=date(1990, 1, 1),
        hire_date=date(2024, 12, 15),
        termination_date=None,
        plan_year_start=plan_year_start,
        plan_year_end=plan_year_end,
    )

    assert result.entry_date == date(2026, 1, 1)
    assert result.acp_includable is False
    assert result.acp_exclusion_reason == "NOT_ELIGIBLE_DURING_YEAR"


def test_hired_early_eligible_mid_year_included():
    """Hired early -> eligibility mid-year -> included."""
    plan_year_start, plan_year_end = plan_year_bounds(2024)
    result = determine_acp_inclusion(
        dob=date(1990, 1, 1),
        hire_date=date(2023, 7, 1),
        termination_date=None,
        plan_year_start=plan_year_start,
        plan_year_end=plan_year_end,
    )

    assert result.entry_date == date(2024, 7, 1)
    assert result.acp_includable is True
    assert result.acp_exclusion_reason is None


def test_terminates_before_entry_excluded():
    """Termination before entry -> excluded with termination reason."""
    plan_year_start, plan_year_end = plan_year_bounds(2024)
    result = determine_acp_inclusion(
        dob=date(1990, 1, 1),
        hire_date=date(2023, 1, 1),
        termination_date=date(2023, 12, 15),
        plan_year_start=plan_year_start,
        plan_year_end=plan_year_end,
    )

    assert result.entry_date == date(2024, 1, 1)
    assert result.acp_includable is False
    assert result.acp_exclusion_reason == "TERMINATED_BEFORE_ENTRY"


def test_terminates_after_entry_included():
    """Termination after entry -> included."""
    plan_year_start, plan_year_end = plan_year_bounds(2024)
    result = determine_acp_inclusion(
        dob=date(1990, 1, 1),
        hire_date=date(2023, 1, 1),
        termination_date=date(2024, 2, 1),
        plan_year_start=plan_year_start,
        plan_year_end=plan_year_end,
    )

    assert result.entry_date == date(2024, 1, 1)
    assert result.acp_includable is True
    assert result.acp_exclusion_reason is None
