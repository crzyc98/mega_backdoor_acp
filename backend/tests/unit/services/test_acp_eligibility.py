"""
Unit tests for ACP eligibility and permissive disaggregation logic.

Tests IRC 401(m) permissive disaggregation rules for determining
which participants are ACP-includable based on age, service,
entry dates, and plan year boundaries.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.services.acp_eligibility import (
    ACPInclusionError,
    ACPInclusionResult,
    determine_acp_inclusion,
    plan_year_bounds,
)


class TestPlanYearBounds:
    """Tests for plan_year_bounds function."""

    def test_plan_year_2024(self):
        """Plan year 2024 returns Jan 1, 2024 to Dec 31, 2024."""
        start, end = plan_year_bounds(2024)
        assert start == date(2024, 1, 1)
        assert end == date(2024, 12, 31)

    def test_plan_year_2025(self):
        """Plan year 2025 returns Jan 1, 2025 to Dec 31, 2025."""
        start, end = plan_year_bounds(2025)
        assert start == date(2025, 1, 1)
        assert end == date(2025, 12, 31)


class TestDetermineACPInclusion:
    """Tests for determine_acp_inclusion function."""

    # --- Successful inclusion cases ---

    def test_hired_early_eligible_mid_year_included(self):
        """
        Employee hired early who becomes eligible mid-year should be included.

        Employee hired 2022-12-20:
        - YOS 1 year reached: 2023-12-20
        - Age 21 (born 1990-01-10): 2011-01-10
        - Eligibility date: 2023-12-20 (max of the two)
        - Entry date: Jan 1, 2024 (first Jan 1 or Jul 1 on/after eligibility)
        - Plan year 2024: Jan 1 - Dec 31
        - Entry date (Jan 1, 2024) <= plan year end (Dec 31, 2024)
        - No termination
        - Result: INCLUDABLE
        """
        result = determine_acp_inclusion(
            dob="1990-01-10",
            hire_date="2022-12-20",
            termination_date=None,
            plan_year_start=date(2024, 1, 1),
            plan_year_end=date(2024, 12, 31),
        )
        assert result.acp_includable is True
        assert result.acp_exclusion_reason is None
        assert result.entry_date == date(2024, 1, 1)

    def test_hired_mid_year_eligible_jul_entry(self):
        """
        Employee hired mid-year who becomes eligible for Jul 1 entry.

        Employee hired 2023-06-15:
        - YOS 1 year reached: 2024-06-15
        - Age 21 (born 1990-01-10): 2011-01-10
        - Eligibility date: 2024-06-15
        - Entry date: Jul 1, 2024
        - Plan year 2024: Jan 1 - Dec 31
        - Entry date (Jul 1, 2024) <= plan year end (Dec 31, 2024)
        - No termination
        - Result: INCLUDABLE
        """
        result = determine_acp_inclusion(
            dob="1990-01-10",
            hire_date="2023-06-15",
            termination_date=None,
            plan_year_start=date(2024, 1, 1),
            plan_year_end=date(2024, 12, 31),
        )
        assert result.acp_includable is True
        assert result.acp_exclusion_reason is None
        assert result.entry_date == date(2024, 7, 1)

    def test_terminates_after_entry_included(self):
        """
        Employee who terminates AFTER their entry date should be included.

        Employee hired 2022-01-15, terminated 2024-03-01:
        - YOS 1 year reached: 2023-01-15
        - Age 21 (born 1985-02-20): 2006-02-20
        - Eligibility date: 2023-01-15
        - Entry date: Jul 1, 2023
        - Plan year 2024: Jan 1 - Dec 31
        - Entry date (Jul 1, 2023) <= plan year end (Dec 31, 2024)
        - Termination (2024-03-01) >= entry date (Jul 1, 2023)
        - Result: INCLUDABLE
        """
        result = determine_acp_inclusion(
            dob="1985-02-20",
            hire_date="2022-01-15",
            termination_date="2024-03-01",
            plan_year_start=date(2024, 1, 1),
            plan_year_end=date(2024, 12, 31),
        )
        assert result.acp_includable is True
        assert result.acp_exclusion_reason is None

    # --- Exclusion cases ---

    def test_hired_late_eligible_next_year_excluded(self):
        """
        Employee hired late in the year who won't be eligible until next year.

        Employee hired 2024-03-10:
        - YOS 1 year reached: 2025-03-10
        - Age 21 (born 1990-06-15): 2011-06-15
        - Eligibility date: 2025-03-10 (max of the two)
        - Entry date: Jul 1, 2025 (first Jan 1 or Jul 1 on/after eligibility)
        - Plan year 2024: Jan 1 - Dec 31
        - Entry date (Jul 1, 2025) > plan year end (Dec 31, 2024)
        - Result: EXCLUDABLE, reason: NOT_ELIGIBLE_DURING_YEAR
        """
        result = determine_acp_inclusion(
            dob="1990-06-15",
            hire_date="2024-03-10",
            termination_date=None,
            plan_year_start=date(2024, 1, 1),
            plan_year_end=date(2024, 12, 31),
        )
        assert result.acp_includable is False
        assert result.acp_exclusion_reason == "NOT_ELIGIBLE_DURING_YEAR"
        assert result.entry_date == date(2025, 7, 1)

    def test_under_21_excluded(self):
        """
        Employee under 21 at end of year should be excluded.

        Employee born 2006-08-01, hired 2023-09-01:
        - Age 21 reached: 2027-08-01
        - YOS 1 year reached: 2024-09-01
        - Eligibility date: 2027-08-01 (age requirement is limiting)
        - Entry date: Jan 1, 2028
        - Plan year 2024: Jan 1 - Dec 31
        - Entry date (Jan 1, 2028) > plan year end (Dec 31, 2024)
        - Result: EXCLUDABLE, reason: NOT_ELIGIBLE_DURING_YEAR
        """
        result = determine_acp_inclusion(
            dob="2006-08-01",
            hire_date="2023-09-01",
            termination_date=None,
            plan_year_start=date(2024, 1, 1),
            plan_year_end=date(2024, 12, 31),
        )
        assert result.acp_includable is False
        assert result.acp_exclusion_reason == "NOT_ELIGIBLE_DURING_YEAR"

    def test_terminates_before_entry_excluded(self):
        """
        Employee who terminates BEFORE their entry date should be excluded.

        Employee hired 2023-05-01, terminated 2023-12-15:
        - YOS 1 year reached: 2024-05-01
        - Age 21 (born 1985-02-20): 2006-02-20
        - Eligibility date: 2024-05-01
        - Entry date: Jul 1, 2024
        - Plan year 2024: Jan 1 - Dec 31
        - Termination (2023-12-15) < entry date (Jul 1, 2024)
        - Result: EXCLUDABLE, reason: TERMINATED_BEFORE_ENTRY
        """
        result = determine_acp_inclusion(
            dob="1985-02-20",
            hire_date="2023-05-01",
            termination_date="2023-12-15",
            plan_year_start=date(2024, 1, 1),
            plan_year_end=date(2024, 12, 31),
        )
        assert result.acp_includable is False
        assert result.acp_exclusion_reason == "TERMINATED_BEFORE_ENTRY"

    # --- Date format handling ---

    def test_accepts_date_objects(self):
        """Function accepts date objects for all date parameters."""
        result = determine_acp_inclusion(
            dob=date(1990, 1, 10),
            hire_date=date(2020, 1, 1),
            termination_date=None,
            plan_year_start=date(2024, 1, 1),
            plan_year_end=date(2024, 12, 31),
        )
        assert result.acp_includable is True

    def test_accepts_various_date_formats(self):
        """Function accepts various string date formats."""
        # ISO format
        result1 = determine_acp_inclusion(
            dob="1990-01-10",
            hire_date="2020-01-01",
            termination_date=None,
            plan_year_start=date(2024, 1, 1),
            plan_year_end=date(2024, 12, 31),
        )
        assert result1.acp_includable is True

        # US format MM/DD/YYYY
        result2 = determine_acp_inclusion(
            dob="01/10/1990",
            hire_date="01/01/2020",
            termination_date=None,
            plan_year_start=date(2024, 1, 1),
            plan_year_end=date(2024, 12, 31),
        )
        assert result2.acp_includable is True

    # --- Error handling ---

    def test_missing_dob_raises_error(self):
        """Missing DOB raises ACPInclusionError."""
        with pytest.raises(ACPInclusionError, match="Missing DOB"):
            determine_acp_inclusion(
                dob=None,
                hire_date="2020-01-01",
                termination_date=None,
                plan_year_start=date(2024, 1, 1),
                plan_year_end=date(2024, 12, 31),
            )

    def test_missing_hire_date_raises_error(self):
        """Missing hire date raises ACPInclusionError."""
        with pytest.raises(ACPInclusionError, match="Missing hire date"):
            determine_acp_inclusion(
                dob="1990-01-10",
                hire_date=None,
                termination_date=None,
                plan_year_start=date(2024, 1, 1),
                plan_year_end=date(2024, 12, 31),
            )

    def test_empty_dob_raises_error(self):
        """Empty string DOB raises ACPInclusionError."""
        with pytest.raises(ACPInclusionError, match="Missing DOB"):
            determine_acp_inclusion(
                dob="",
                hire_date="2020-01-01",
                termination_date=None,
                plan_year_start=date(2024, 1, 1),
                plan_year_end=date(2024, 12, 31),
            )

    def test_invalid_date_format_raises_error(self):
        """Invalid date format raises ACPInclusionError."""
        with pytest.raises(ACPInclusionError, match="Invalid DOB format"):
            determine_acp_inclusion(
                dob="not-a-date",
                hire_date="2020-01-01",
                termination_date=None,
                plan_year_start=date(2024, 1, 1),
                plan_year_end=date(2024, 12, 31),
            )


class TestACPInclusionResult:
    """Tests for ACPInclusionResult dataclass."""

    def test_includable_result(self):
        """Result with acp_includable=True has no exclusion reason."""
        result = ACPInclusionResult(
            eligibility_date=date(2023, 1, 1),
            entry_date=date(2023, 1, 1),
            acp_includable=True,
            acp_exclusion_reason=None,
        )
        assert result.acp_includable is True
        assert result.acp_exclusion_reason is None

    def test_excluded_result(self):
        """Result with acp_includable=False has an exclusion reason."""
        result = ACPInclusionResult(
            eligibility_date=date(2025, 1, 1),
            entry_date=date(2025, 1, 1),
            acp_includable=False,
            acp_exclusion_reason="NOT_ELIGIBLE_DURING_YEAR",
        )
        assert result.acp_includable is False
        assert result.acp_exclusion_reason == "NOT_ELIGIBLE_DURING_YEAR"
