# Implementation Plan: Fix ACP Permissive Disaggregation Exclusion Bug

**Branch**: `011-fix-acp-exclusion` | **Date**: 2026-01-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-fix-acp-exclusion/spec.md`

## Summary

Fix the ACP eligibility calculation to properly handle missing data (DOB, hire_date) gracefully by adding MISSING_DOB and MISSING_HIRE_DATE exclusion reasons, allowing tests to proceed while tracking error counts. The core eligibility logic (age 21, 1 year service, semi-annual entry dates) is already correctly implemented; this fix extends the error handling and adds comprehensive test coverage for boundary cases.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.104+, pandas 2.0+, pydantic 2.0+, NumPy
**Storage**: SQLite (via sqlite3) with WAL mode
**Testing**: pytest with markers (unit, integration, contract)
**Target Platform**: Linux server (containerized)
**Project Type**: Web application (backend/frontend separation)
**Performance Goals**: Existing performance maintained (no degradation)
**Constraints**: No breaking API changes; backward compatible
**Scale/Scope**: Census files up to 10k participants

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution file contains only template placeholders (no actual principles defined). Proceeding with standard best practices:

- [x] **Testing**: Unit tests required for all eligibility scenarios
- [x] **Single Source of Truth**: Eligibility logic in one reusable function
- [x] **No Breaking Changes**: Extend existing enums and models, don't replace
- [x] **Backward Compatibility**: Existing API contracts preserved

## Project Structure

### Documentation (this feature)

```text
specs/011-fix-acp-exclusion/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── api/
│   └── routes/
│       └── analysis.py      # Endpoint error handling
├── core/
│   ├── acp_eligibility.py   # PRIMARY: Eligibility logic (modify)
│   ├── models.py            # Pydantic models (extend)
│   ├── scenario_runner.py   # Scenario execution (modify)
│   └── employee_impact.py   # Impact calculation (modify)
└── storage/
    └── repository.py        # Data access (modify error handling)

tests/
├── unit/
│   └── test_acp_eligibility.py  # PRIMARY: Add comprehensive tests
├── integration/
└── contract/
```

**Structure Decision**: Existing web application structure with backend in `/src/` and frontend in `/frontend/`. This fix modifies only backend code.

## Complexity Tracking

No constitution violations - changes are minimal and focused:
- Extend existing ACPExclusionReason enum with 2 new values
- Add graceful error handling instead of raising exceptions
- Add tests for boundary cases

---

## Phase 0: Research Findings

### Investigation Results

**Current Implementation Analysis** (`src/core/acp_eligibility.py`):

1. **Eligibility Calculation** (lines 108-112): CORRECT
   - `age21_date = _add_years(dob_date, 21)`
   - `yos1_date = _add_years(hire_date_value, 1)`
   - `eligibility_date = max(age21_date, yos1_date)` - Uses MAX correctly

2. **Entry Date Rounding** (lines 75-83): CORRECT
   - `_next_entry_date()` returns first Jan 1 or Jul 1 on/after eligibility_date

3. **Plan Year Boundaries** (lines 86-88): CORRECT
   - `plan_year_bounds(plan_year)` returns `(date(year, 1, 1), date(year, 12, 31))`

4. **Inclusion Logic** (lines 117-120): CORRECT
   - `entry_date <= plan_year_end AND (term_date is None OR term_date >= entry_date)`

5. **Termination Handling** (lines 122-127): CORRECT
   - Properly distinguishes TERMINATED_BEFORE_ENTRY vs NOT_ELIGIBLE_DURING_YEAR

**Identified Defects**:

| Issue | Location | Impact |
|-------|----------|--------|
| Missing data raises exception | `_parse_date_value()` lines 44-46, 55-56 | Blocks entire census processing |
| No MISSING_DOB/MISSING_HIRE_DATE reasons | `ACPExclusionReason` type | Cannot track data quality issues |
| No error count summary | Repository/models | No visibility into data problems |
| Missing boundary test cases | `test_acp_eligibility.py` | Incomplete validation coverage |

### Root Cause

The `_parse_date_value()` function raises `ACPInclusionError` when DOB or hire_date is missing. This exception propagates up through `repository.py:295-298` and causes the entire ACP test to fail. Per FR-015/FR-016, the system should instead:
1. Mark the participant as excluded with a data error reason
2. Allow the test to proceed
3. Display an error count summary

### Design Decision

**Decision**: Extend `ACPExclusionReason` and return error results instead of raising exceptions

**Rationale**:
- Aligns with clarification that tests should proceed with missing data
- Preserves existing API contracts (ExclusionInfo already has breakdown fields)
- Minimal code changes - only modify eligibility function and add enum values

**Alternatives Rejected**:
- Separate validation pass: Over-engineering, duplicates eligibility traversal
- Pre-filter invalid participants: Loses visibility into data quality

---

## Phase 1: Design Artifacts

See companion files:
- [data-model.md](./data-model.md) - Entity changes
- [contracts/](./contracts/) - API contract updates
- [quickstart.md](./quickstart.md) - Implementation guide
