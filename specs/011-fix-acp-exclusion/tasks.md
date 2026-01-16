# Tasks: Fix ACP Permissive Disaggregation Exclusion Bug

**Input**: Design documents from `/specs/011-fix-acp-exclusion/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Unit tests are REQUIRED per constitution check and spec (SC-004, SC-005).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `src/` at repository root
- **Tests**: `tests/` at repository root

---

## Phase 1: Setup

**Purpose**: No setup required - this is a bug fix in an existing codebase

- [x] T001 Verify branch is `011-fix-acp-exclusion` and pull latest changes

---

## Phase 2: Foundational (Type/Model Extensions)

**Purpose**: Extend types and models that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 [P] Extend ACPExclusionReason type literal with MISSING_DOB and MISSING_HIRE_DATE in src/core/acp_eligibility.py
- [x] T003 [P] Update ACPInclusionResult dataclass fields to allow None for eligibility_date and entry_date in src/core/acp_eligibility.py
- [x] T004 [P] Extend ACPExclusionReason enum with MISSING_DOB and MISSING_HIRE_DATE in src/core/models.py
- [x] T005 [P] Add missing_dob_count and missing_hire_date_count fields to ExclusionInfo model in src/core/models.py
- [x] T006 [P] Extend ExcludedParticipant exclusion_reason literal with new values in src/core/models.py

**Checkpoint**: Type definitions complete - implementation can now proceed

---

## Phase 3: User Story 1 - Accurate ACP Test Results (Priority: P1) MVP

**Goal**: Fix eligibility calculation to handle missing data gracefully and correctly exclude ineligible participants

**Independent Test**: Run ACP test on census with known eligibility dates; verify only eligible participants included

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [x] T007 [P] [US1] Add test_missing_dob_excluded() in tests/unit/test_acp_eligibility.py
- [x] T008 [P] [US1] Add test_missing_hire_date_excluded() in tests/unit/test_acp_eligibility.py
- [x] T009 [P] [US1] Add test_eligibility_exactly_on_jan_1() in tests/unit/test_acp_eligibility.py
- [x] T010 [P] [US1] Add test_eligibility_exactly_on_jul_1() in tests/unit/test_acp_eligibility.py
- [x] T011 [P] [US1] Add test_eligibility_on_dec_31_excluded() in tests/unit/test_acp_eligibility.py
- [x] T012 [P] [US1] Add test_feb_29_birthday_age21() in tests/unit/test_acp_eligibility.py
- [x] T013 [P] [US1] Add test_plan_year_end_is_dec_31() in tests/unit/test_acp_eligibility.py

### Implementation for User Story 1

- [x] T014 [US1] Modify determine_acp_inclusion() to catch ACPInclusionError for DOB and return MISSING_DOB result in src/core/acp_eligibility.py
- [x] T015 [US1] Modify determine_acp_inclusion() to catch ACPInclusionError for hire_date and return MISSING_HIRE_DATE result in src/core/acp_eligibility.py
- [x] T016 [US1] Remove try/except block around determine_acp_inclusion() call in src/storage/repository.py
- [x] T017 [US1] Run tests/unit/test_acp_eligibility.py and verify all new tests pass

**Checkpoint**: Core eligibility fix complete - participants with missing data excluded gracefully

---

## Phase 4: User Story 2 - Visibility into Eligibility Calculations (Priority: P2)

**Goal**: Track and display exclusion counts for new reasons in scenario results

**Independent Test**: Run ACP test with participants having missing data; verify exclusion counts visible in results

### Implementation for User Story 2

- [x] T018 [P] [US2] Add missing_dob_count and missing_hire_date_count counters to exclusion tracking loop in src/core/scenario_runner.py
- [x] T019 [P] [US2] Add missing_dob_count and missing_hire_date_count counters to exclusion tracking in src/core/employee_impact.py
- [x] T020 [US2] Update ExclusionInfo creation to include new count fields in src/core/scenario_runner.py
- [x] T021 [US2] Update ExclusionInfo creation to include new count fields in src/core/employee_impact.py

**Checkpoint**: Exclusion counts visible in scenario results and employee impact views

---

## Phase 5: User Story 3 - Consistent Eligibility Logic (Priority: P2)

**Goal**: Verify single source of truth for eligibility calculations

**Independent Test**: Code review confirms all eligibility calls route through determine_acp_inclusion()

### Implementation for User Story 3

- [x] T022 [US3] Verify repository.py uses determine_acp_inclusion() as single source in src/storage/repository.py
- [x] T023 [US3] Verify scenario_runner.py relies on pre-computed eligibility fields from repository in src/core/scenario_runner.py
- [x] T024 [US3] Verify employee_impact.py relies on pre-computed eligibility fields from repository in src/core/employee_impact.py

**Checkpoint**: Single authoritative eligibility function confirmed across codebase

---

## Phase 6: Polish & Verification

**Purpose**: Final validation and regression testing

- [x] T025 Run full pytest test suite to verify no regressions: `pytest tests/ -v`
- [x] T026 Verify existing 4 tests in test_acp_eligibility.py still pass
- [x] T027 Run quickstart.md verification steps
- [x] T028 Code cleanup: remove any unused imports or dead code from modified files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - Core fix
- **User Story 2 (Phase 4)**: Depends on Foundational - Can parallel with US1
- **User Story 3 (Phase 5)**: Depends on US1/US2 - Verification only
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent after Foundational - MUST complete for MVP
- **User Story 2 (P2)**: Independent after Foundational - Can start in parallel with US1
- **User Story 3 (P2)**: Depends on US1/US2 being complete (verification tasks)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Type extensions (Phase 2) before function changes
- Core function changes before consumer updates
- Unit tests before integration verification

### Parallel Opportunities

**Phase 2 (all parallel)**:
```
T002, T003, T004, T005, T006 - Different files, no dependencies
```

**Phase 3 Tests (all parallel)**:
```
T007, T008, T009, T010, T011, T012, T013 - Independent test functions
```

**Phase 4 (partial parallel)**:
```
T018, T019 - Different files (scenario_runner.py, employee_impact.py)
```

---

## Parallel Example: Phase 2

```bash
# Launch all type extension tasks together:
Task: "Extend ACPExclusionReason type literal in src/core/acp_eligibility.py"
Task: "Update ACPInclusionResult dataclass in src/core/acp_eligibility.py"
Task: "Extend ACPExclusionReason enum in src/core/models.py"
Task: "Add fields to ExclusionInfo in src/core/models.py"
Task: "Extend ExcludedParticipant literal in src/core/models.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational type extensions
3. Complete Phase 3: User Story 1 (core fix + tests)
4. **STOP and VALIDATE**: Run `pytest tests/unit/test_acp_eligibility.py -v`
5. Deploy/demo if ready - core bug is fixed

### Incremental Delivery

1. Complete Setup + Foundational → Types ready
2. Add User Story 1 → Test independently → Core fix deployed
3. Add User Story 2 → Visibility into exclusion counts
4. Add User Story 3 → Code review verification
5. Polish phase → Full regression suite passes

### Single Developer Sequence

Recommended order for one developer:
1. T001 (setup)
2. T002-T006 (foundational - can batch commit)
3. T007-T013 (write all tests - should fail)
4. T014-T016 (implement fix - tests should pass)
5. T017 (verify US1)
6. T018-T021 (visibility updates)
7. T022-T024 (verification)
8. T025-T028 (polish)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story is independently testable
- Verify tests fail before implementing
- Commit after each phase or logical group
- Total: 28 tasks across 6 phases
