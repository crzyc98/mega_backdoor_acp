"""
ACP Eligibility and Permissive Disaggregation Logic.

Determines whether a participant is ACP-includable based on age, service,
entry dates, and plan year boundaries.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal


ACPExclusionReason = Literal["TERMINATED_BEFORE_ENTRY", "NOT_ELIGIBLE_DURING_YEAR"]


class ACPInclusionError(ValueError):
    """Raised when required data for ACP eligibility is missing or invalid."""


@dataclass(frozen=True)
class ACPInclusionResult:
    """Computed ACP eligibility fields for a participant."""

    eligibility_date: date
    entry_date: date
    acp_includable: bool
    acp_exclusion_reason: ACPExclusionReason | None


_DATE_FORMATS = (
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%m-%d-%Y",
    "%m-%d-%y",
    "%Y/%m/%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
)


def _parse_date_value(value: object, field_name: str) -> date:
    """Parse a date value into a date, raising ACPInclusionError on failure."""
    if value is None:
        raise ACPInclusionError(f"Missing {field_name}")

    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime().date()

    value_str = str(value).strip()
    if not value_str:
        raise ACPInclusionError(f"Missing {field_name}")

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value_str, fmt).date()
        except ValueError:
            continue

    raise ACPInclusionError(f"Invalid {field_name} format: {value_str}")


def _add_years(value: date, years: int) -> date:
    """Add years to a date, handling leap years deterministically."""
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(month=2, day=28, year=value.year + years)


def _next_entry_date(eligibility_date: date) -> date:
    """Return the first Jan 1 or Jul 1 on or after eligibility_date."""
    jan_1 = date(eligibility_date.year, 1, 1)
    jul_1 = date(eligibility_date.year, 7, 1)
    if eligibility_date <= jan_1:
        return jan_1
    if eligibility_date <= jul_1:
        return jul_1
    return date(eligibility_date.year + 1, 1, 1)


def plan_year_bounds(plan_year: int) -> tuple[date, date]:
    """Return plan year start and end dates for a calendar-year plan."""
    return date(plan_year, 1, 1), date(plan_year, 12, 31)


def determine_acp_inclusion(
    *,
    dob: object,
    hire_date: object,
    termination_date: object | None,
    plan_year_start: date,
    plan_year_end: date,
) -> ACPInclusionResult:
    """
    Determine ACP inclusion using IRC 401(m) permissive disaggregation logic.
    """
    dob_date = _parse_date_value(dob, "DOB")
    hire_date_value = _parse_date_value(hire_date, "hire date")
    term_date = None
    if termination_date is not None and str(termination_date).strip():
        term_date = _parse_date_value(termination_date, "termination date")

    age21_date = _add_years(dob_date, 21)
    yos1_date = _add_years(hire_date_value, 1)
    eligibility_date = max(age21_date, yos1_date)

    entry_date = _next_entry_date(eligibility_date)

    participation_start = entry_date
    participation_end = term_date if term_date else plan_year_end

    acp_includable = (
        participation_start <= plan_year_end
        and (term_date is None or term_date >= participation_start)
    )

    exclusion_reason: ACPExclusionReason | None = None
    if not acp_includable:
        if term_date is not None and term_date < participation_start:
            exclusion_reason = "TERMINATED_BEFORE_ENTRY"
        elif participation_start > plan_year_end:
            exclusion_reason = "NOT_ELIGIBLE_DURING_YEAR"

    return ACPInclusionResult(
        eligibility_date=eligibility_date,
        entry_date=entry_date,
        acp_includable=acp_includable,
        acp_exclusion_reason=exclusion_reason,
    )
