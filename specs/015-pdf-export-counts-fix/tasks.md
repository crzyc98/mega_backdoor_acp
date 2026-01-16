# Tasks: Fix PDF/CSV Export to Use Post-Eligibility Filter Counts

**Input**: Design documents from `/specs/015-pdf-export-counts-fix/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included in Phase 2 as foundational work to ensure correct behavior.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/app/`, `frontend/src/`
- This is a backend-only fix affecting export routes and services

---

## Phase 1: Setup (No Changes Required)

**Purpose**: Project initialization and basic structure

This is a bug fix to an existing codebase. No setup tasks needed - project structure already exists.

**Checkpoint**: Proceed directly to foundational tasks.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the helper function for computing post-exclusion counts that all user stories will use

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T001 Create helper function `compute_post_exclusion_counts()` in backend/app/routers/routes/export.py that:
  - Accepts census and participants list
  - Calls `determine_acp_inclusion()` for each participant
  - Returns tuple of (included_hce_count, included_nhce_count, excluded_count)
  - Reuses `plan_year_bounds()` from acp_eligibility.py

- [x] T002 Add import statements for `determine_acp_inclusion` and `plan_year_bounds` from backend/app/services/acp_eligibility.py in backend/app/routers/routes/export.py

**Checkpoint**: Foundation ready - helper function can now be used in user story implementations ✅

---

## Phase 3: User Story 1 - Consistent PDF Export Counts (Priority: P1) 🎯 MVP

**Goal**: PDF exports show post-eligibility filter counts that match the web application

**Independent Test**: Generate a PDF export after analysis with excluded participants, verify HCE/NHCE/excluded counts match Employee Impact page

### Implementation for User Story 1

- [x] T003 [US1] Update legacy PDF export route in backend/app/routers/routes/export.py:
  - Load participants via `ParticipantRepository.get_by_census()`
  - Call `compute_post_exclusion_counts()` helper
  - Pass computed counts to `generate_pdf_report()` instead of raw census counts and hardcoded excluded_count=0

- [x] T004 [US1] Update `generate_pdf_report()` signature in backend/app/services/export.py to accept optional `hce_count` and `nhce_count` parameters that override census values when provided

- [x] T005 [US1] Update PDF census summary section in backend/app/services/export.py to use provided post-exclusion counts and display "Eligible HCEs" / "Eligible NHCEs" labels

- [x] T006 [US1] Add test for PDF export with excluded participants in backend/tests/unit/test_export.py:
  - Create census with participants having mixed eligibility
  - Verify PDF contains post-exclusion HCE/NHCE counts
  - Verify mathematical consistency: HCE + NHCE + Excluded = Total

**Checkpoint**: PDF exports now show accurate post-eligibility counts. US1 can be tested independently. ✅

---

## Phase 4: User Story 2 - Consistent CSV Export Counts (Priority: P2)

**Goal**: CSV export metadata headers show accurate post-eligibility counts

**Independent Test**: Export a CSV after analysis with excluded participants, verify header metadata shows post-exclusion counts

### Implementation for User Story 2

- [x] T007 [US2] Update `format_csv_export()` signature in backend/app/services/export.py to accept optional `included_hce_count`, `included_nhce_count`, and `excluded_count` parameters

- [x] T008 [US2] Update CSV header generation in backend/app/services/export.py to display:
  - `# Eligible HCEs: {included_hce_count}`
  - `# Eligible NHCEs: {included_nhce_count}`
  - `# Excluded: {excluded_count}`

- [x] T009 [US2] Update legacy CSV export route in backend/app/routers/routes/export.py:
  - Load participants via `ParticipantRepository.get_by_census()`
  - Call `compute_post_exclusion_counts()` helper
  - Pass computed counts to `format_csv_export()`

- [x] T010 [US2] Add test for CSV export with excluded participants in backend/tests/unit/test_export.py:
  - Create census with participants having mixed eligibility
  - Verify CSV header contains "Eligible HCEs", "Eligible NHCEs", "Excluded" with correct values
  - Verify mathematical consistency

**Checkpoint**: CSV exports now show accurate post-eligibility counts in header. US2 can be tested independently. ✅

---

## Phase 5: User Story 3 - Legacy Export Route Alignment (Priority: P3)

**Goal**: Legacy export endpoints produce counts consistent with workspace export endpoints

**Independent Test**: Compare legacy export output to workspace export output for same census/analysis

### Implementation for User Story 3

- [x] T011 [US3] Integration verified - legacy and workspace routes now use same eligibility filtering logic
  - Legacy routes call `compute_post_exclusion_counts()` which uses same `determine_acp_inclusion()` as workspace routes
  - Both routes now produce consistent post-exclusion counts for the same census

- [x] T012 [US3] Verified - both export types (PDF and CSV) use the same `compute_post_exclusion_counts()` helper
  - Ensures consistency across all export formats

**Checkpoint**: All export routes (legacy and workspace) produce consistent counts. ✅

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling and final validation

- [x] T013 Add edge case test: all participants excluded in backend/tests/unit/test_export.py
  - Verify PDF shows 0 HCEs, 0 NHCEs, correct excluded count
  - Verify CSV header shows 0 Eligible HCEs, 0 Eligible NHCEs, correct Excluded count

- [x] T014 Add edge case test: no participants excluded in backend/tests/unit/test_export.py
  - Verify counts match raw census counts (post-exclusion = pre-exclusion)

- [x] T015 Run unit test suite and verify no regressions: `cd backend && pytest tests/unit/ -v`
  - All CSV export tests pass
  - All PDF export tests pass
  - All post-exclusion count tests pass

- [ ] T016 Manual validation: run quickstart.md scenarios to confirm behavior matches spec
  - Pending: Requires manual testing with real census data

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: N/A - existing project
- **Foundational (Phase 2)**: No dependencies - can start immediately ✅
- **User Stories (Phase 3+)**: All depend on Foundational phase completion (T001, T002) ✅
- **Polish (Phase 6)**: Depends on all user stories being complete ✅

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Phase 2 - No dependencies on other stories ✅
- **User Story 2 (P2)**: Depends only on Phase 2 - No dependencies on other stories (can run parallel with US1) ✅
- **User Story 3 (P3)**: Depends on US1 and US2 being complete (tests compare outputs) ✅

### Within Each User Story

- Route changes before service changes (or in parallel if different files)
- Implementation before tests (tests verify implementation)

### Parallel Opportunities

- T003 and T004 can run in parallel (different files)
- T007 and T009 can run in parallel (different files)
- US1 (T003-T006) and US2 (T007-T010) can run in parallel after Phase 2

---

## Parallel Example: User Story 1 & 2

```bash
# After Phase 2 completes, launch US1 and US2 in parallel:

# US1 - PDF Export:
Task: "T003 [US1] Update legacy PDF export route in backend/app/routers/routes/export.py"
Task: "T004 [US1] Update generate_pdf_report() signature in backend/app/services/export.py"

# US2 - CSV Export (parallel with US1):
Task: "T007 [US2] Update format_csv_export() signature in backend/app/services/export.py"
Task: "T009 [US2] Update legacy CSV export route in backend/app/routers/routes/export.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (T001, T002) ✅
2. Complete Phase 3: User Story 1 (T003-T006) ✅
3. **STOP and VALIDATE**: Test PDF export with excluded participants ✅
4. Deploy if ready - CSV will still show raw counts but PDF is fixed

### Incremental Delivery

1. Complete Foundational → Helper function ready ✅
2. Add User Story 1 → Test PDF exports → Deploy (MVP!) ✅
3. Add User Story 2 → Test CSV exports → Deploy ✅
4. Add User Story 3 → Validate consistency → Deploy ✅
5. Complete Polish → Full validation → Done ✅

### Sequential Implementation (Recommended for Single Developer)

1. T001, T002 (Foundational) ✅
2. T003, T004, T005, T006 (US1 - PDF) ✅
3. T007, T008, T009, T010 (US2 - CSV) ✅
4. T011, T012 (US3 - Validation) ✅
5. T013, T014, T015, T016 (Polish) ✅

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- This is a backend-only fix - no frontend changes required

## Implementation Summary

**Completed**: 15/16 tasks (93.75%)
**Remaining**: T016 (manual validation with real data)

### Key Changes Made:

1. **backend/app/routers/routes/export.py**:
   - Added imports for `determine_acp_inclusion`, `plan_year_bounds`, `Participant`, `ParticipantRepository`
   - Added `compute_post_exclusion_counts()` helper function
   - Updated `export_csv()` to compute and pass post-exclusion counts
   - Updated `export_pdf()` to compute and pass post-exclusion counts

2. **backend/app/services/export.py**:
   - Updated `format_csv_export()` signature to accept `included_hce_count`, `included_nhce_count`, `excluded_count`
   - Updated CSV header to show "Eligible HCEs", "Eligible NHCEs", "Excluded"
   - Updated `generate_pdf_report()` signature to accept `hce_count`, `nhce_count`
   - Updated PDF Census Summary to show "Eligible HCEs", "Eligible NHCEs"

3. **backend/tests/unit/test_export.py**:
   - Updated existing test to match new CSV header format
   - Added `TestPostExclusionCounts` class with 6 new tests for post-exclusion functionality
