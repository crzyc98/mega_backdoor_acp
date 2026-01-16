# Research: ACP Permissive Disaggregation Exclusion Bug

**Feature**: 011-fix-acp-exclusion
**Date**: 2026-01-15

## Investigation Summary

### Current Implementation Review

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| Eligibility calculation | `src/core/acp_eligibility.py` | CORRECT | Uses max(age21, yos1), entry dates correct |
| Entry date rounding | `_next_entry_date()` | CORRECT | First Jan 1/Jul 1 on or after eligibility |
| Plan year bounds | `plan_year_bounds()` | CORRECT | Returns (Jan 1, Dec 31) for calendar year |
| Inclusion logic | `determine_acp_inclusion()` | CORRECT | entry_date <= PY_END AND employed at entry |
| Missing data handling | `_parse_date_value()` | **DEFECT** | Raises exception instead of returning error result |
| Error count tracking | N/A | **MISSING** | No support for MISSING_DOB/MISSING_HIRE_DATE counts |

### Defect Analysis

**Primary Issue**: Missing data raises `ACPInclusionError` exception

**Location**: `src/core/acp_eligibility.py` lines 44-46, 55-56

```python
def _parse_date_value(value: object, field_name: str) -> date:
    if value is None:
        raise ACPInclusionError(f"Missing {field_name}")  # PROBLEM
    # ...
    if not value_str:
        raise ACPInclusionError(f"Missing {field_name}")  # PROBLEM
```

**Impact**: When `repository.py:get_as_calculation_dicts()` calls `determine_acp_inclusion()` for a participant with missing DOB or hire_date, the exception propagates and fails the entire census processing.

**Expected Behavior** (per FR-015, FR-016):
- System should allow ACP test to proceed
- Mark participant as excluded with data error reason
- Display error count summary after execution

### Design Decisions

#### Decision 1: Extend ACPExclusionReason Type

**Decision**: Add `MISSING_DOB` and `MISSING_HIRE_DATE` to the exclusion reason type

**Rationale**:
- Consistent with existing exclusion reason pattern
- Enables tracking and reporting through existing ExclusionInfo model
- No API changes required - just new enum values

**Alternatives Rejected**:
- Separate error tracking system: Over-engineering for simple data validation
- Pre-validation pass: Duplicates work and loses context

#### Decision 2: Return Error Result Instead of Raising Exception

**Decision**: Modify `determine_acp_inclusion()` to catch parse errors and return an error result

**Rationale**:
- Matches clarification that tests should proceed with missing data
- Allows per-participant error tracking
- No exception propagation to handle upstream

**Implementation Approach**:
```python
# New optional fields in ACPInclusionResult for error cases
@dataclass(frozen=True)
class ACPInclusionResult:
    eligibility_date: date | None  # None if data error
    entry_date: date | None        # None if data error
    acp_includable: bool           # Always False for errors
    acp_exclusion_reason: ACPExclusionReason | None
```

#### Decision 3: Extend ExclusionInfo Model

**Decision**: Add `missing_dob_count` and `missing_hire_date_count` fields to ExclusionInfo

**Rationale**:
- Provides visibility into data quality issues
- Consistent with existing exclusion tracking pattern
- Frontend can display counts in summary panel

### Test Coverage Gaps

Current tests cover:
- Late hire excluded (NOT_ELIGIBLE_DURING_YEAR)
- Early hire included
- Terminated before entry excluded
- Terminated after entry included

Missing tests:
- Missing DOB → excluded with MISSING_DOB
- Missing hire_date → excluded with MISSING_HIRE_DATE
- Eligibility exactly on Jan 1 → entry same day
- Eligibility exactly on Jul 1 → entry same day
- Eligibility on Dec 31 → entry Jan 1 next year (excluded)
- Feb 29 birthday → age 21 calculation
- Plan year 2024 → PY_END = 2024-12-31 assertion

### Files to Modify

| File | Changes |
|------|---------|
| `src/core/acp_eligibility.py` | Add MISSING_DOB/MISSING_HIRE_DATE reasons; return error result |
| `src/core/models.py` | Extend ExclusionInfo with error counts |
| `src/storage/repository.py` | Remove exception handling (no longer needed) |
| `src/core/scenario_runner.py` | Track new exclusion reasons in counts |
| `src/core/employee_impact.py` | Track new exclusion reasons |
| `tests/unit/test_acp_eligibility.py` | Add comprehensive boundary tests |

### Best Practices Applied

- **Single Source of Truth**: All eligibility logic in `determine_acp_inclusion()`
- **Graceful Degradation**: Missing data doesn't block entire census
- **Comprehensive Testing**: Cover all boundary cases per spec
- **Backward Compatibility**: Extend models, don't break existing contracts
