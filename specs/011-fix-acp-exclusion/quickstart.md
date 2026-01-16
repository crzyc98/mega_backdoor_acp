# Quickstart: Implementing ACP Exclusion Bug Fix

**Feature**: 011-fix-acp-exclusion
**Date**: 2026-01-15

## Prerequisites

- Python 3.11+
- pytest installed
- Repository cloned and on `011-fix-acp-exclusion` branch

## Implementation Order

### Step 1: Extend ACPExclusionReason Type (acp_eligibility.py)

```python
# src/core/acp_eligibility.py line 13
ACPExclusionReason = Literal[
    "TERMINATED_BEFORE_ENTRY",
    "NOT_ELIGIBLE_DURING_YEAR",
    "MISSING_DOB",
    "MISSING_HIRE_DATE",
]
```

### Step 2: Update ACPInclusionResult Dataclass (acp_eligibility.py)

```python
# src/core/acp_eligibility.py lines 20-27
@dataclass(frozen=True)
class ACPInclusionResult:
    eligibility_date: date | None  # None if data error
    entry_date: date | None        # None if data error
    acp_includable: bool
    acp_exclusion_reason: ACPExclusionReason | None
```

### Step 3: Modify determine_acp_inclusion() (acp_eligibility.py)

Replace exception-raising with error result returns:

```python
def determine_acp_inclusion(...) -> ACPInclusionResult:
    # Handle missing DOB
    try:
        dob_date = _parse_date_value(dob, "DOB")
    except ACPInclusionError:
        return ACPInclusionResult(
            eligibility_date=None,
            entry_date=None,
            acp_includable=False,
            acp_exclusion_reason="MISSING_DOB",
        )

    # Handle missing hire_date
    try:
        hire_date_value = _parse_date_value(hire_date, "hire date")
    except ACPInclusionError:
        return ACPInclusionResult(
            eligibility_date=None,
            entry_date=None,
            acp_includable=False,
            acp_exclusion_reason="MISSING_HIRE_DATE",
        )

    # ... rest of existing logic unchanged
```

### Step 4: Extend ExclusionInfo Model (models.py)

```python
# src/core/models.py class ExclusionInfo
class ExclusionInfo(BaseModel):
    total_excluded: int = Field(..., ge=0)
    terminated_before_entry_count: int = Field(..., ge=0)
    not_eligible_during_year_count: int = Field(..., ge=0)
    missing_dob_count: int = Field(0, ge=0)          # NEW
    missing_hire_date_count: int = Field(0, ge=0)    # NEW
```

### Step 5: Extend ACPExclusionReason Enum (models.py)

```python
# src/core/models.py class ACPExclusionReason
class ACPExclusionReason(str, Enum):
    TERMINATED_BEFORE_ENTRY = "TERMINATED_BEFORE_ENTRY"
    NOT_ELIGIBLE_DURING_YEAR = "NOT_ELIGIBLE_DURING_YEAR"
    MISSING_DOB = "MISSING_DOB"                      # NEW
    MISSING_HIRE_DATE = "MISSING_HIRE_DATE"          # NEW
```

### Step 6: Update ExcludedParticipant Literal (models.py)

```python
# src/core/models.py class ExcludedParticipant
exclusion_reason: Literal[
    "TERMINATED_BEFORE_ENTRY",
    "NOT_ELIGIBLE_DURING_YEAR",
    "MISSING_DOB",
    "MISSING_HIRE_DATE",
]
```

### Step 7: Update Scenario Runner Exclusion Tracking (scenario_runner.py)

Add counters for new exclusion reasons in the exclusion tracking loop:

```python
# Around line 229-253 in scenario_runner.py
missing_dob_count = 0
missing_hire_date_count = 0

for p in participants:
    if "acp_includable" in p and not p["acp_includable"]:
        reason = p.get("acp_exclusion_reason")
        if reason == "TERMINATED_BEFORE_ENTRY":
            terminated_before_entry_count += 1
        elif reason == "NOT_ELIGIBLE_DURING_YEAR":
            not_eligible_during_year_count += 1
        elif reason == "MISSING_DOB":              # NEW
            missing_dob_count += 1
        elif reason == "MISSING_HIRE_DATE":       # NEW
            missing_hire_date_count += 1
    else:
        includable_participants.append(p)
```

### Step 8: Update Repository Error Handling (repository.py)

Remove the exception re-raise since `determine_acp_inclusion` no longer raises:

```python
# src/storage/repository.py lines 287-298
for participant in participants:
    inclusion = determine_acp_inclusion(...)  # No longer raises
    # No try/except needed - errors are returned as results
```

### Step 9: Add Comprehensive Tests (test_acp_eligibility.py)

```python
# tests/unit/test_acp_eligibility.py - Add these tests

def test_missing_dob_excluded():
    """Missing DOB -> excluded with MISSING_DOB reason."""
    result = determine_acp_inclusion(
        dob=None,
        hire_date=date(2023, 1, 1),
        termination_date=None,
        plan_year_start=date(2024, 1, 1),
        plan_year_end=date(2024, 12, 31),
    )
    assert result.acp_includable is False
    assert result.acp_exclusion_reason == "MISSING_DOB"
    assert result.eligibility_date is None
    assert result.entry_date is None


def test_missing_hire_date_excluded():
    """Missing hire_date -> excluded with MISSING_HIRE_DATE reason."""
    result = determine_acp_inclusion(
        dob=date(1990, 1, 1),
        hire_date=None,
        termination_date=None,
        plan_year_start=date(2024, 1, 1),
        plan_year_end=date(2024, 12, 31),
    )
    assert result.acp_includable is False
    assert result.acp_exclusion_reason == "MISSING_HIRE_DATE"


def test_eligibility_exactly_on_jan_1():
    """Eligibility on Jan 1 -> entry same day."""
    result = determine_acp_inclusion(
        dob=date(2003, 1, 1),  # Turns 21 on Jan 1, 2024
        hire_date=date(2022, 1, 1),  # 1 year by Jan 1, 2023
        termination_date=None,
        plan_year_start=date(2024, 1, 1),
        plan_year_end=date(2024, 12, 31),
    )
    assert result.entry_date == date(2024, 1, 1)
    assert result.acp_includable is True


def test_eligibility_exactly_on_jul_1():
    """Eligibility on Jul 1 -> entry same day."""
    result = determine_acp_inclusion(
        dob=date(2003, 7, 1),  # Turns 21 on Jul 1, 2024
        hire_date=date(2022, 1, 1),
        termination_date=None,
        plan_year_start=date(2024, 1, 1),
        plan_year_end=date(2024, 12, 31),
    )
    assert result.entry_date == date(2024, 7, 1)
    assert result.acp_includable is True


def test_eligibility_on_dec_31_excluded():
    """Eligibility on Dec 31 -> entry Jan 1 next year -> excluded."""
    result = determine_acp_inclusion(
        dob=date(2003, 12, 31),  # Turns 21 on Dec 31, 2024
        hire_date=date(2022, 1, 1),
        termination_date=None,
        plan_year_start=date(2024, 1, 1),
        plan_year_end=date(2024, 12, 31),
    )
    assert result.entry_date == date(2025, 1, 1)
    assert result.acp_includable is False
    assert result.acp_exclusion_reason == "NOT_ELIGIBLE_DURING_YEAR"


def test_feb_29_birthday_age21():
    """Feb 29 birthday -> age 21 uses Feb 28 in non-leap year."""
    result = determine_acp_inclusion(
        dob=date(2004, 2, 29),  # Leap year birthday
        hire_date=date(2022, 1, 1),
        termination_date=None,
        plan_year_start=date(2025, 1, 1),  # 2025 is not a leap year
        plan_year_end=date(2025, 12, 31),
    )
    # Age 21 on Feb 28, 2025 (not Feb 29)
    assert result.eligibility_date == date(2025, 2, 28)


def test_plan_year_end_is_dec_31():
    """Assert plan_year_bounds returns correct end date."""
    start, end = plan_year_bounds(2024)
    assert start == date(2024, 1, 1)
    assert end == date(2024, 12, 31)  # NOT 2023-12-31
```

## Verification

Run tests to verify implementation:

```bash
cd /workspaces/mega_backdoor_acp
pytest tests/unit/test_acp_eligibility.py -v
```

Run full test suite for regression check:

```bash
pytest tests/ -v
```

## Files Changed Summary

| File | Change |
|------|--------|
| `src/core/acp_eligibility.py` | Extend type, update dataclass, modify function |
| `src/core/models.py` | Extend ExclusionInfo, enum, literal |
| `src/core/scenario_runner.py` | Add counters for new reasons |
| `src/core/employee_impact.py` | Add counters for new reasons |
| `src/storage/repository.py` | Remove exception handling |
| `tests/unit/test_acp_eligibility.py` | Add 7+ new tests |
