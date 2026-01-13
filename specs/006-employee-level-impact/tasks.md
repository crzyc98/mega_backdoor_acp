# Tasks: Employee-Level Impact Views

**Input**: Design documents from `/specs/006-employee-level-impact/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests ARE requested per the constitution check mentioning "Test-First" approach and plan.md specifying test files.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## User Story Mapping

| Story | Title | Priority | Spec Section |
|-------|-------|----------|--------------|
| US1 | View Employee Details for Selected Scenario | P1 | User Story 1 |
| US2 | Sort Employee Data | P1 | User Story 2 |
| US3 | Filter Employee Data | P2 | User Story 3 |
| US4 | Understand Limit Constraints | P1 | User Story 4 |
| US5 | Export Employee Details | P2 | User Story 5 |
| US6 | Navigate from Heatmap to Employee Detail | P1 | User Story 6 |

---

## Phase 1: Setup

**Purpose**: Project initialization and basic structure for employee impact feature

- [X] T001 Create test directory structure: tests/unit/core/, tests/integration/api/, tests/contract/
- [X] T002 [P] Create placeholder test files for TDD approach

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and service that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundation

- [X] T003 [P] Write unit tests for ConstraintStatus enum in tests/unit/core/test_employee_impact.py
- [X] T004 [P] Write unit tests for EmployeeImpact model validation in tests/unit/core/test_employee_impact.py
- [X] T005 [P] Write unit tests for EmployeeImpactSummary model in tests/unit/core/test_employee_impact.py
- [X] T006 [P] Write unit tests for EmployeeImpactView model in tests/unit/core/test_employee_impact.py

### Implementation for Foundation

- [X] T007 Add ConstraintStatus enum to src/core/models.py (4 values: UNCONSTRAINED, AT_LIMIT, REDUCED, NOT_SELECTED)
- [X] T008 Add EmployeeImpact Pydantic model to src/core/models.py (12 fields per data-model.md)
- [X] T009 Add EmployeeImpactSummary Pydantic model to src/core/models.py (HCE/NHCE group stats)
- [X] T010 Add EmployeeImpactRequest Pydantic model to src/core/models.py (census_id, adoption_rate, contribution_rate, seed)
- [X] T011 Add EmployeeImpactView Pydantic model to src/core/models.py (container with employee lists and summaries)
- [X] T012 Write unit tests for EmployeeImpactService.compute_impact() in tests/unit/core/test_employee_impact.py
- [X] T013 Write unit tests for EmployeeImpactService._compute_employee_impact() in tests/unit/core/test_employee_impact.py
- [X] T014 Write unit tests for EmployeeImpactService._compute_summary() in tests/unit/core/test_employee_impact.py
- [X] T015 Create src/core/employee_impact.py with EmployeeImpactService class
- [X] T016 Implement EmployeeImpactService.__init__() accepting participant_repo and census_repo in src/core/employee_impact.py
- [X] T017 Implement EmployeeImpactService.compute_impact() method in src/core/employee_impact.py
- [X] T018 Implement EmployeeImpactService._compute_employee_impact() helper in src/core/employee_impact.py
- [X] T019 Implement EmployeeImpactService._compute_summary() helper in src/core/employee_impact.py
- [X] T020 Implement constraint status classification logic (NOT_SELECTED, AT_LIMIT, REDUCED, UNCONSTRAINED) in src/core/employee_impact.py
- [X] T021 Implement constraint_detail message generation in src/core/employee_impact.py

**Checkpoint**: Foundation ready - core models and service work. User story implementation can now begin.

---

## Phase 3: User Story 1 - View Employee Details (Priority: P1) 🎯 MVP

**Goal**: Display employee-level contribution details in tabbed HCE/NHCE view when user drills down from scenario

**Independent Test**: Select a scenario with known participants; verify all rows appear with correct values matching census data plus computed mega-backdoor amounts

### Tests for User Story 1

- [X] T022 [P] [US1] Write contract test for POST /v2/scenario/{census_id}/employee-impact in tests/contract/test_employee_impact_schema.py
- [X] T023 [P] [US1] Write integration test for getEmployeeImpact endpoint in tests/integration/api/test_employee_impact_api.py

### Implementation for User Story 1

- [X] T024 [P] [US1] Add EmployeeImpactRequest schema to src/api/schemas.py (adoption_rate, contribution_rate, seed fields)
- [X] T025 [P] [US1] Add EmployeeImpact response schema to src/api/schemas.py (all 12 fields from data-model)
- [X] T026 [P] [US1] Add EmployeeImpactSummary response schema to src/api/schemas.py
- [X] T027 [P] [US1] Add EmployeeImpactView response schema to src/api/schemas.py
- [X] T028 [US1] Implement POST /v2/scenario/{census_id}/employee-impact endpoint in src/api/routes/analysis.py
- [X] T029 [US1] Create src/ui/components/employee_impact.py with render_employee_impact_view() function
- [X] T030 [US1] Implement tabbed navigation (HCE/NHCE tabs) using st.tabs() in src/ui/components/employee_impact.py
- [X] T031 [US1] Implement render_employee_table() for HCE view (10 columns) in src/ui/components/employee_impact.py
- [X] T032 [US1] Implement render_employee_table() for NHCE view (6 columns) in src/ui/components/employee_impact.py
- [X] T033 [US1] Implement monetary formatting ($123,456) and percentage formatting (4.50%) in src/ui/components/employee_impact.py
- [X] T034 [US1] Add row count display ("Showing X of Y employees") in src/ui/components/employee_impact.py

**Checkpoint**: User can view employee details in tabbed view with correct data and formatting

---

## Phase 4: User Story 2 - Sort Employee Data (Priority: P1)

**Goal**: Enable sorting by any column in both HCE and NHCE tables

**Independent Test**: Click column headers and verify rows reorder correctly in ascending/descending order with visual indicator

### Implementation for User Story 2

- [X] T035 [US2] Implement column sorting using st.selectbox() and pandas sorting in src/ui/components/employee_impact.py
- [X] T036 [US2] Add sort state persistence when switching between HCE/NHCE tabs in src/ui/components/employee_impact.py

**Checkpoint**: Sorting works on all columns; sort state maintained across tab switches

---

## Phase 5: User Story 4 - Understand Limit Constraints (Priority: P1)

**Goal**: Display summary statistics showing constraint impact (count at limit, reduced count, total mega-backdoor)

**Independent Test**: Compute expected constraint counts from known census data; verify displayed summary matches

### Implementation for User Story 4

- [X] T037 [P] [US4] Create summary rendering in src/ui/components/employee_impact.py with _render_summary_panel() function
- [X] T038 [P] [US4] _render_summary_panel() handles both HCE and NHCE groups in src/ui/components/employee_impact.py
- [X] T039 [US4] Implement HCE summary panel (Total Count, At Limit Count, Reduced Count, Avg Available Room, Total Mega-Backdoor, Avg ACP) in src/ui/components/employee_impact.py
- [X] T040 [US4] Implement NHCE summary panel (Total Count, Avg ACP, Total Match, Total After-Tax) in src/ui/components/employee_impact.py
- [X] T041 [US4] Add constraint status legend and icons in table rows in src/ui/components/employee_impact.py
- [X] T042 [US4] Integrate summary panels into render_employee_impact_view() in src/ui/components/employee_impact.py

**Checkpoint**: Summary statistics visible; tooltips explain constraints with dollar amounts

---

## Phase 6: User Story 6 - Navigate from Heatmap (Priority: P1)

**Goal**: Add "View Employee Details" button to heatmap detail panel; enable seamless navigation

**Independent Test**: Click heatmap cell, open detail panel, verify "View Employee Details" action loads correct scenario's employee data

### Implementation for User Story 6

- [X] T043 [US6] Add "View Employee Impact" button to src/ui/components/heatmap_detail.py render_detail_panel() function
- [X] T044 [US6] Implement session state storage for selected scenario (st.session_state.employee_impact_scenario) in src/ui/components/heatmap_detail.py
- [ ] T045 [US6] Create employee impact view page/section in src/ui/pages/analysis.py
- [X] T046 [US6] Implement scenario header display (adoption rate, contribution rate, status) in src/ui/components/employee_impact.py (_render_scenario_context)
- [ ] T047 [US6] Add "Back to Heatmap" button with navigation logic in src/ui/components/employee_impact.py
- [ ] T048 [US6] Implement keyboard navigation (Escape to close) in src/ui/components/employee_impact.py

**Checkpoint**: Full navigation flow works: Heatmap → Detail Panel → Employee Impact View → Back to Heatmap

---

## Phase 7: User Story 3 - Filter Employee Data (Priority: P2)

**Goal**: Enable filtering by constraint status, compensation range, and other criteria

**Independent Test**: Apply filters and verify only matching rows remain visible with correct counts displayed

### Implementation for User Story 3

- [X] T049 [P] [US3] Implement HCE filters in _render_employee_table() in src/ui/components/employee_impact.py
- [X] T050 [P] [US3] Implement NHCE filters (no constraint filter needed) in src/ui/components/employee_impact.py
- [X] T051 [US3] Implement Constraint Status dropdown filter (Unconstrained, At Limit, Reduced, Not Selected) in src/ui/components/employee_impact.py
- [ ] T052 [US3] Implement Compensation range filter (min/max inputs) in src/ui/components/employee_impact.py
- [ ] T053 [US3] Implement Has Mega-Backdoor (yes/no) filter for HCE in src/ui/components/employee_impact.py
- [ ] T054 [US3] Implement Individual ACP range filter for NHCE in src/ui/components/employee_impact.py
- [X] T055 [US3] Implement filter application using pandas boolean indexing in src/ui/components/employee_impact.py
- [ ] T056 [US3] Add active filter count badge and "Clear Filters" button in src/ui/components/employee_impact.py
- [X] T057 [US3] Update "Showing X of Y" count when filters applied in src/ui/components/employee_impact.py
- [X] T058 [US3] Integrate filter controls into employee impact view in src/ui/components/employee_impact.py

**Checkpoint**: Filtering works on all criteria; count updates in real-time; clear filters restores full list

---

## Phase 8: User Story 5 - Export Employee Details (Priority: P2)

**Goal**: Enable CSV export of employee data respecting current filter/sort state

**Independent Test**: Export data and verify CSV contains all visible columns with correctly formatted values

### Tests for User Story 5

- [X] T059 [P] [US5] Write contract test for POST /v2/scenario/{census_id}/employee-impact/export in tests/contract/test_employee_impact_schema.py

### Implementation for User Story 5

- [X] T060 [P] [US5] Add EmployeeImpactExportRequest schema to src/api/schemas.py (export_group, include_group_column fields)
- [X] T061 [US5] Implement POST /v2/scenario/{census_id}/employee-impact/export endpoint in src/api/routes/analysis.py
- [X] T062 [US5] Implement export_to_csv() via render_export_button() in src/ui/components/employee_impact.py
- [X] T063 [US5] Implement CSV filename with census_id in export endpoint in src/api/routes/analysis.py
- [X] T064 [US5] Implement HCE export (all columns) in src/ui/components/employee_impact.py
- [X] T065 [US5] Implement NHCE export (all columns) in src/ui/components/employee_impact.py
- [X] T066 [US5] Implement "Export All" (combined CSV with Group column) in src/ui/components/employee_impact.py
- [X] T067 [US5] Add st.download_button() via render_export_button() in src/ui/components/employee_impact.py
- [ ] T068 [US5] Implement filtered export filename suffix (e.g., "_filtered") in src/ui/components/employee_impact.py

**Checkpoint**: CSV exports work correctly; match on-screen data exactly; filenames include context

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T069 [P] Add WCAG 2.1 AA accessibility compliance (keyboard navigation, contrast) to src/ui/components/employee_impact.py
- [ ] T070 [P] Add screen reader support (ARIA labels, table headers) to src/ui/components/employee_impact.py
- [ ] T071 Implement pagination for large censuses (>1000 rows) in src/ui/components/employee_impact.py
- [ ] T072 Add session state caching for EmployeeImpactView to avoid recomputation in src/ui/components/employee_impact.py
- [X] T073 [P] Add error handling for census not found, invalid parameters in src/api/routes/analysis.py
- [X] T074 [P] Add rate limiting to employee impact endpoints in src/api/routes/analysis.py
- [X] T075 Run all unit tests: pytest tests/unit/core/test_employee_impact.py -v (33 passed)
- [ ] T076 Run all integration tests: pytest tests/integration/api/test_employee_impact_api.py -v
- [X] T077 Run contract tests: pytest tests/contract/test_employee_impact_schema.py -v (29 passed)
- [ ] T078 Validate quickstart.md scenarios work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1 (View Details): Core functionality - MVP
  - US2 (Sort): Depends on US1 table component
  - US4 (Constraints): Depends on US1 table component
  - US6 (Navigation): Depends on US1 view component
  - US3 (Filter): Depends on US1 table component
  - US5 (Export): Depends on US1 view component
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

```
Foundational (Phase 2)
        │
        ▼
    US1 (View Details) ◄─── MVP
        │
        ├──────┬──────┬──────┐
        ▼      ▼      ▼      ▼
      US2    US4    US6    US3
     (Sort) (Constraints) (Nav) (Filter)
        │      │      │      │
        └──────┴──────┴──────┘
                    │
                    ▼
                  US5 (Export)
                    │
                    ▼
               Polish (Phase 9)
```

### Parallel Opportunities

**Within Foundational Phase:**
- T003, T004, T005, T006 (all model tests) - parallel
- T007, T008, T009, T010, T011 (all models) - sequential (same file)
- T012, T013, T014 (service tests) - parallel

**Within User Story 1:**
- T022, T023 (tests) - parallel
- T024, T025, T026, T027 (API schemas) - parallel

**Within User Story 4:**
- T037, T038 (summary components) - parallel

**Within User Story 3:**
- T049, T050 (filter components) - parallel

**Across User Stories (after US1 complete):**
- US2, US4, US6 can start in parallel
- US3 can start in parallel with US2, US4, US6
- US5 can start after any of the above

---

## Parallel Example: Foundational Phase

```bash
# Launch all model tests in parallel:
Task: "Write unit tests for ConstraintStatus enum" (T003)
Task: "Write unit tests for EmployeeImpact model" (T004)
Task: "Write unit tests for EmployeeImpactSummary model" (T005)
Task: "Write unit tests for EmployeeImpactView model" (T006)

# Then service tests in parallel:
Task: "Write unit tests for compute_impact()" (T012)
Task: "Write unit tests for _compute_employee_impact()" (T013)
Task: "Write unit tests for _compute_summary()" (T014)
```

## Parallel Example: User Story 1

```bash
# Launch all API schema tasks in parallel:
Task: "Add EmployeeImpactRequest schema" (T024)
Task: "Add EmployeeImpact response schema" (T025)
Task: "Add EmployeeImpactSummary response schema" (T026)
Task: "Add EmployeeImpactView response schema" (T027)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (View Employee Details)
4. **STOP and VALIDATE**: Test US1 independently
   - Can view employee details from a scenario
   - HCE/NHCE tabs work
   - All columns display with correct formatting
5. Deploy/demo if ready - this is the core value

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (View Details) → Test independently → **MVP!**
3. Add US2 (Sort) + US4 (Constraints) + US6 (Nav) → P1 stories complete
4. Add US3 (Filter) + US5 (Export) → P2 stories complete
5. Polish → Production ready

### Parallel Team Strategy

With 2+ developers after Foundational:
- Developer A: US1 → US2 → US3
- Developer B: After US1 complete → US4 → US6 → US5

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- MVP = Phase 1 + Phase 2 + Phase 3 (US1 only)
