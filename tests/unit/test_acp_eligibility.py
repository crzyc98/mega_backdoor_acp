"""
Unit tests for ACP eligibility and permissive disaggregation logic.
"""

from datetime import date

from backend.app.services.acp_eligibility import determine_acp_inclusion, plan_year_bounds


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


# T007: Test missing DOB excluded
def test_missing_dob_excluded():
    """Missing DOB -> excluded with MISSING_DOB reason."""
    plan_year_start, plan_year_end = plan_year_bounds(2024)
    result = determine_acp_inclusion(
        dob=None,
        hire_date=date(2023, 1, 1),
        termination_date=None,
        plan_year_start=plan_year_start,
        plan_year_end=plan_year_end,
    )

    assert result.acp_includable is False
    assert result.acp_exclusion_reason == "MISSING_DOB"
    assert result.eligibility_date is None
    assert result.entry_date is None


# T008: Test missing hire date excluded
def test_missing_hire_date_excluded():
    """Missing hire_date -> excluded with MISSING_HIRE_DATE reason."""
    plan_year_start, plan_year_end = plan_year_bounds(2024)
    result = determine_acp_inclusion(
        dob=date(1990, 1, 1),
        hire_date=None,
        termination_date=None,
        plan_year_start=plan_year_start,
        plan_year_end=plan_year_end,
    )

    assert result.acp_includable is False
    assert result.acp_exclusion_reason == "MISSING_HIRE_DATE"
    assert result.eligibility_date is None
    assert result.entry_date is None


# T009: Test eligibility exactly on Jan 1
def test_eligibility_exactly_on_jan_1():
    """Eligibility on Jan 1 -> entry same day."""
    plan_year_start, plan_year_end = plan_year_bounds(2024)
    result = determine_acp_inclusion(
        dob=date(2003, 1, 1),  # Turns 21 on Jan 1, 2024
        hire_date=date(2022, 1, 1),  # 1 year by Jan 1, 2023
        termination_date=None,
        plan_year_start=plan_year_start,
        plan_year_end=plan_year_end,
    )

    assert result.entry_date == date(2024, 1, 1)
    assert result.acp_includable is True


# T010: Test eligibility exactly on Jul 1
def test_eligibility_exactly_on_jul_1():
    """Eligibility on Jul 1 -> entry same day."""
    plan_year_start, plan_year_end = plan_year_bounds(2024)
    result = determine_acp_inclusion(
        dob=date(2003, 7, 1),  # Turns 21 on Jul 1, 2024
        hire_date=date(2022, 1, 1),  # 1 year by Jan 1, 2023
        termination_date=None,
        plan_year_start=plan_year_start,
        plan_year_end=plan_year_end,
    )

    assert result.entry_date == date(2024, 7, 1)
    assert result.acp_includable is True


# T011: Test eligibility on Dec 31 excluded
def test_eligibility_on_dec_31_excluded():
    """Eligibility on Dec 31 -> entry Jan 1 next year -> excluded."""
    plan_year_start, plan_year_end = plan_year_bounds(2024)
    result = determine_acp_inclusion(
        dob=date(2003, 12, 31),  # Turns 21 on Dec 31, 2024
        hire_date=date(2022, 1, 1),  # 1 year by Jan 1, 2023
        termination_date=None,
        plan_year_start=plan_year_start,
        plan_year_end=plan_year_end,
    )

    assert result.entry_date == date(2025, 1, 1)
    assert result.acp_includable is False
    assert result.acp_exclusion_reason == "NOT_ELIGIBLE_DURING_YEAR"


# T012: Test Feb 29 birthday age 21 calculation
def test_feb_29_birthday_age21():
    """Feb 29 birthday -> age 21 uses Feb 28 in non-leap year."""
    plan_year_start, plan_year_end = plan_year_bounds(2025)  # 2025 is not a leap year
    result = determine_acp_inclusion(
        dob=date(2004, 2, 29),  # Leap year birthday
        hire_date=date(2022, 1, 1),  # 1 year by Jan 1, 2023
        termination_date=None,
        plan_year_start=plan_year_start,
        plan_year_end=plan_year_end,
    )

    # Age 21 on Feb 28, 2025 (not Feb 29 since 2025 is not a leap year)
    assert result.eligibility_date == date(2025, 2, 28)


# T013: Test plan year end is Dec 31
def test_plan_year_end_is_dec_31():
    """Assert plan_year_bounds returns correct end date."""
    start, end = plan_year_bounds(2024)

    assert start == date(2024, 1, 1)
    assert end == date(2024, 12, 31)  # NOT 2023-12-31
