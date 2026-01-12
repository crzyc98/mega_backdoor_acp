# Tasks: Scenario Analysis

**Input**: Design documents from `/specs/004-scenario-analysis/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included (constitution specifies Test-First approach)

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add constants and enums needed across all scenarios

- [x] T001 Add RISK_THRESHOLD constant (Decimal("0.50")) in src/core/constants.py
- [x] T002 [P] Add ScenarioStatus enum (PASS, RISK, FAIL, ERROR) in src/core/models.py
- [x] T003 [P] Add LimitingBound enum (MULTIPLE, ADDITIVE) in src/core/models.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create ScenarioRequest pydantic model in src/core/models.py (census_id, adoption_rate, contribution_rate, seed, include_debug)
- [x] T005 [P] Create ScenarioResult pydantic model in src/core/models.py with all fields per data-model.md
- [x] T006 [P] Create DebugDetails pydantic model in src/core/models.py (selected_hce_ids, hce_contributions, nhce_contributions, intermediate_values)
- [x] T007 [P] Create ParticipantContribution pydantic model in src/core/models.py
- [x] T008 [P] Create IntermediateValues pydantic model in src/core/models.py
- [x] T009 Create GridRequest pydantic model in src/core/models.py (census_id, adoption_rates, contribution_rates, seed, include_debug)
- [x] T010 [P] Create GridResult pydantic model in src/core/models.py (scenarios, summary, seed_used)
- [x] T011 [P] Create GridSummary pydantic model in src/core/models.py (pass_count, risk_count, fail_count, error_count, total_count, first_failure_point, max_safe_contribution, worst_margin)
- [x] T012 [P] Create FailurePoint pydantic model in src/core/models.py (adoption_rate, contribution_rate)
- [x] T013 Add classify_status(margin: Decimal) -> ScenarioStatus helper function in src/core/scenario_runner.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Single Scenario Execution (Priority: P1) 🎯 MVP

**Goal**: Run a single scenario and return full ACP outcome details with PASS/FAIL/RISK/ERROR status

**Independent Test**: Provide census + adoption rate + contribution rate, verify all 13 output fields match manual calculation

### Tests for User Story 1

- [x] T014 [P] [US1] Unit test for classify_status() function (PASS/RISK/FAIL boundaries) in tests/unit/test_scenario_runner.py
- [x] T015 [P] [US1] Unit test for enhanced run_single_scenario() with new ScenarioResult fields in tests/unit/test_scenario_runner.py
- [x] T016 [P] [US1] Unit test for ERROR status (zero HCEs, zero NHCEs) in tests/unit/test_scenario_runner.py
- [x] T017 [P] [US1] Unit test for determinism (same seed = identical results 100 times) in tests/unit/test_scenario_runner.py
- [x] T018 [P] [US1] Contract test for POST /api/v2/analysis/scenario endpoint in tests/contract/test_scenario_contracts.py

### Implementation for User Story 1

- [x] T019 [US1] Update apply_acp_test() to use LimitingBound.MULTIPLE/ADDITIVE instead of "1.25x"/"+2.0" in src/core/acp_calculator.py
- [x] T020 [US1] Add calculate_total_mega_backdoor() function in src/core/acp_calculator.py
- [x] T021 [US1] Update select_adopting_hces() to use round() instead of int() for adoption count in src/core/scenario_runner.py
- [x] T022 [US1] Create run_single_scenario_v2() returning new ScenarioResult with all fields in src/core/scenario_runner.py
- [x] T023 [US1] Add edge case detection (zero HCEs, zero NHCEs) returning ERROR status in run_single_scenario_v2() in src/core/scenario_runner.py
- [x] T024 [US1] Add nhce_contributor_count calculation in run_single_scenario_v2() in src/core/scenario_runner.py
- [x] T025 [US1] Add total_mega_backdoor_amount field to ScenarioResult in run_single_scenario_v2() in src/core/scenario_runner.py
- [x] T026 [US1] Create ScenarioRequest/ScenarioResult API schemas in src/api/schemas.py
- [x] T027 [US1] Add POST /api/v2/analysis/scenario endpoint in src/api/routes/analysis.py
- [x] T028 [US1] Add validation for adoption_rate and contribution_rate (0.0-1.0) in src/api/routes/analysis.py

**Checkpoint**: Single scenario execution fully functional with PASS/RISK/FAIL/ERROR classification

---

## Phase 4: User Story 2 - Grid Scenario Execution (Priority: P2)

**Goal**: Run scenarios across all combinations of adoption and contribution rates

**Independent Test**: Provide census + 3x3 grid (9 scenarios), verify all 9 results returned in structured format

### Tests for User Story 2

- [x] T029 [P] [US2] Unit test for run_grid_scenarios_v2() returning GridResult in tests/unit/test_scenario_runner.py
- [x] T030 [P] [US2] Unit test for grid determinism (same seed = identical 9 results) in tests/unit/test_scenario_runner.py
- [x] T031 [P] [US2] Contract test for POST /api/v2/analysis/grid endpoint in tests/contract/test_scenario_contracts.py

### Implementation for User Story 2

- [x] T032 [US2] Create run_grid_scenarios_v2() returning GridResult with list of ScenarioResults in src/core/scenario_runner.py
- [x] T033 [US2] Ensure same seed used for all scenarios in grid (FR-017) in run_grid_scenarios_v2() in src/core/scenario_runner.py
- [x] T034 [US2] Create GridRequest/GridResult API schemas in src/api/schemas.py
- [x] T035 [US2] Add POST /api/v2/analysis/grid endpoint in src/api/routes/analysis.py
- [x] T036 [US2] Add validation for adoption_rates and contribution_rates lists (2-20 items each) in src/api/routes/analysis.py

**Checkpoint**: Grid scenario execution functional, returning structured results for all combinations

---

## Phase 5: User Story 3 - Grid Summary Generation (Priority: P2)

**Goal**: Generate compact summary with pass/fail/risk counts, first failure point, max safe contribution, worst margin

**Independent Test**: Run grid with known distribution, verify summary metrics match expected counts

### Tests for User Story 3

- [x] T037 [P] [US3] Unit test for compute_grid_summary() pass/risk/fail/error counts in tests/unit/test_grid_summary.py
- [x] T038 [P] [US3] Unit test for find_first_failure_point() algorithm in tests/unit/test_grid_summary.py
- [x] T039 [P] [US3] Unit test for find_max_safe_contribution() algorithm in tests/unit/test_grid_summary.py
- [x] T040 [P] [US3] Unit test for worst_margin calculation in tests/unit/test_grid_summary.py
- [x] T041 [P] [US3] Unit test for all-PASS grid (first_failure_point = null) in tests/unit/test_grid_summary.py

### Implementation for User Story 3

- [x] T042 [US3] Create compute_grid_summary() function in src/core/scenario_runner.py
- [x] T043 [US3] Implement find_first_failure_point() helper in src/core/scenario_runner.py
- [x] T044 [US3] Implement find_max_safe_contribution() helper in src/core/scenario_runner.py
- [x] T045 [US3] Implement worst_margin calculation in compute_grid_summary() in src/core/scenario_runner.py
- [x] T046 [US3] Integrate GridSummary into GridResult in run_grid_scenarios_v2() in src/core/scenario_runner.py
- [x] T047 [US3] Update GridResult API response to include summary in src/api/routes/analysis.py

**Checkpoint**: Grid analysis returns complete summary with all metrics (pass/risk/fail counts, first failure, max safe, worst margin)

---

## Phase 6: User Story 4 - Edge Case Handling (Priority: P3)

**Goal**: Handle boundary conditions gracefully with clear ERROR messages

**Independent Test**: Provide edge-case census (zero HCEs, zero NHCEs, etc.), verify appropriate error messages

### Tests for User Story 4

- [x] T048 [P] [US4] Unit test for zero HCE census → ERROR status with message in tests/unit/test_scenario_runner.py
- [x] T049 [P] [US4] Unit test for zero NHCE census → ERROR status with message in tests/unit/test_scenario_runner.py
- [x] T050 [P] [US4] Unit test for 0% adoption rate → valid result with contributor_count=0 in tests/unit/test_scenario_runner.py
- [x] T051 [P] [US4] Unit test for 100% adoption rate → all HCEs selected in tests/unit/test_scenario_runner.py
- [x] T052 [P] [US4] Unit test for empty census → ERROR status in tests/unit/test_scenario_runner.py

### Implementation for User Story 4

- [x] T053 [US4] Add error message constants for edge cases in src/core/constants.py
- [x] T054 [US4] Enhance edge case detection in run_single_scenario_v2() for empty census in src/core/scenario_runner.py
- [x] T055 [US4] Ensure 0% adoption returns valid result (not ERROR) with hce_contributor_count=0 in src/core/scenario_runner.py
- [x] T056 [US4] Ensure 100% adoption selects all HCEs in src/core/scenario_runner.py

**Checkpoint**: All edge cases return appropriate responses (ERROR with message or valid result)

---

## Phase 7: Debug Mode (Priority: P3)

**Goal**: Optional detailed calculation breakdown for audit/debugging

**Independent Test**: Request with include_debug=true, verify debug_details contains all intermediate values

### Tests for Debug Mode

- [x] T057 [P] [US4] Unit test for include_debug=true returns debug_details in tests/unit/test_debug_mode.py
- [x] T058 [P] [US4] Unit test for include_debug=false/omitted omits debug_details in tests/unit/test_debug_mode.py
- [x] T059 [P] [US4] Unit test for debug_details contains correct selected_hce_ids in tests/unit/test_debug_mode.py

### Implementation for Debug Mode

- [x] T060 [US4] Add debug_details generation in run_single_scenario_v2() when include_debug=true in src/core/scenario_runner.py
- [x] T061 [US4] Collect per-HCE contribution details for debug output in src/core/scenario_runner.py
- [x] T062 [US4] Collect per-NHCE contribution details for debug output in src/core/scenario_runner.py
- [x] T063 [US4] Add intermediate_values (threshold calculations) to debug output in src/core/scenario_runner.py
- [x] T064 [US4] Wire include_debug flag through API to scenario runner in src/api/routes/analysis.py

**Checkpoint**: Debug mode provides full calculation breakdown when requested

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Performance validation, documentation, and cleanup

- [x] T065 [P] Performance benchmark for single scenario <100ms (10K participants) in tests/unit/test_scenario_runner.py
- [x] T066 [P] Performance benchmark for 100-scenario grid <5s (10K participants) in tests/unit/test_scenario_runner.py
- [x] T067 [P] Integration test for full API workflow (upload census → run scenario → verify result) in tests/integration/test_analysis_api.py
- [x] T068 [P] Integration test for grid API workflow in tests/integration/test_analysis_api.py
- [x] T069 Validate quickstart.md examples work with implemented API
- [x] T070 Register v2 routes in FastAPI app in src/api/main.py (routes already registered via analysis router)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phases 3-7)**: All depend on Foundational phase completion
  - US1 (Phase 3): No dependencies on other stories - **MVP**
  - US2 (Phase 4): Uses run_single_scenario_v2() from US1
  - US3 (Phase 5): Depends on US2 (needs grid results to summarize)
  - US4 (Phases 6-7): Can run in parallel with US2/US3 after US1
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ─────────────────────────────────────┐
    ↓                                                        │
Phase 3 (US1: Single Scenario) ← MVP STOP POINT             │
    ↓                                    ↓                   │
Phase 4 (US2: Grid Execution)    Phase 6 (US4: Edge Cases)  │
    ↓                                    ↓                   │
Phase 5 (US3: Grid Summary)      Phase 7 (Debug Mode)       │
    ↓                                    ↓                   │
    └────────────── Phase 8 (Polish) ←───┘                  │
```

### Parallel Opportunities

**Within Setup (Phase 1)**:
- T002, T003 can run in parallel

**Within Foundational (Phase 2)**:
- T005, T006, T007, T008 can run in parallel
- T010, T011, T012 can run in parallel

**Within User Story 1 (Phase 3)**:
- All tests (T014-T018) can run in parallel
- After tests: T019, T020, T021 can run in parallel

**Within User Story 2 (Phase 4)**:
- All tests (T029-T031) can run in parallel

**Within User Story 3 (Phase 5)**:
- All tests (T037-T041) can run in parallel
- T043, T044 can run in parallel

**Within User Story 4 (Phases 6-7)**:
- All tests (T048-T052, T057-T059) can run in parallel
- T061, T062, T063 can run in parallel

**Within Polish (Phase 8)**:
- T065, T066, T067, T068 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for classify_status() in tests/unit/test_scenario_runner.py"
Task: "Unit test for enhanced run_single_scenario() in tests/unit/test_scenario_runner.py"
Task: "Unit test for ERROR status in tests/unit/test_scenario_runner.py"
Task: "Unit test for determinism in tests/unit/test_scenario_runner.py"
Task: "Contract test for POST /api/v2/analysis/scenario in tests/contract/test_scenario_contracts.py"

# After tests fail as expected, launch parallel implementation:
Task: "Update apply_acp_test() to use LimitingBound enum in src/core/acp_calculator.py"
Task: "Add calculate_total_mega_backdoor() in src/core/acp_calculator.py"
Task: "Update select_adopting_hces() rounding in src/core/scenario_runner.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (3 tasks)
2. Complete Phase 2: Foundational (10 tasks)
3. Complete Phase 3: User Story 1 (15 tasks)
4. **STOP and VALIDATE**: Test single scenario independently
5. Deploy/demo if ready - basic scenario analysis working

### Incremental Delivery

1. Setup + Foundational → Foundation ready (13 tasks)
2. Add User Story 1 → Test independently → **MVP!** (15 tasks)
3. Add User Story 2 → Grid execution working (8 tasks)
4. Add User Story 3 → Full grid with summary (12 tasks)
5. Add User Story 4 + Debug → Complete feature (17 tasks)
6. Polish → Production ready (6 tasks)

### Task Count Summary

| Phase | Tasks | Cumulative |
|-------|-------|------------|
| Setup | 3 | 3 |
| Foundational | 10 | 13 |
| US1 (MVP) | 15 | 28 |
| US2 | 8 | 36 |
| US3 | 12 | 48 |
| US4 + Debug | 17 | 65 |
| Polish | 6 | 71 |

**Total: 70 tasks**

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at Phase 3 checkpoint for MVP validation
