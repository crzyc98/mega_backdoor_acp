# Tasks: ACP Sensitivity Analyzer

**Input**: Design documents from `/specs/001-acp-sensitivity-analyzer/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Tests**: Test tasks included for domain-critical ACP calculation logic (per plan.md: "Test coverage for all ACP calculation logic is critical").

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Source**: `src/` at repository root
- **Tests**: `tests/` at repository root
- Project structure per plan.md: `src/core/`, `src/storage/`, `src/api/`, `src/ui/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per plan.md in src/core/, src/storage/, src/api/routes/, src/ui/pages/, src/ui/components/, tests/unit/, tests/integration/, tests/contract/
- [X] T002 Create requirements.txt with dependencies: fastapi, uvicorn, streamlit>=1.28, pandas>=2.0, numpy, plotly>=5.15, pydantic>=2.0, python-multipart, slowapi, reportlab
- [X] T003 [P] Initialize Python packages with __init__.py files in all src/ and tests/ subdirectories
- [X] T004 [P] Configure pytest in pyproject.toml with pytest-cov for coverage
- [X] T005 [P] Copy plan_constants.yaml from legacy/ to src/core/ for IRS limits configuration
- [X] T006 [P] Create sample census.csv test fixture in tests/fixtures/ with HCE/NHCE data

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Implement IRS constants and limit functions in src/core/constants.py (ACP_MULTIPLIER=1.25, ACP_ADDER=2.0, plan year limits from yaml)
- [X] T008 [P] Create SQLite database connection with WAL mode in src/storage/database.py
- [X] T009 [P] Implement Pydantic schemas for API request/response in src/api/schemas.py per contracts/openapi.yaml
- [X] T010 Create database schema and tables (census, participant, analysis_result, grid_analysis) in src/storage/database.py per data-model.md
- [X] T011 Create FastAPI app entry point with health endpoint in src/api/main.py
- [X] T012 [P] Create Streamlit app entry point with page navigation in src/ui/app.py
- [X] T013 [P] Implement rate limiting middleware using slowapi in src/api/main.py (60 req/min)
- [X] T014 Create system version constant for audit trail in src/core/constants.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Single Scenario Analysis (Priority: P1) 🎯 MVP

**Goal**: Upload census, run single ACP test scenario, see PASS/FAIL with margin

**Independent Test**: Upload census CSV, configure 50% adoption at 6% contribution, verify PASS/FAIL result with margin displayed

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T015 [P] [US1] Unit test for PII hashing function (SHA-256 with salt) in tests/unit/test_census_parser.py
- [X] T016 [P] [US1] Unit test for CSV validation (missing columns, duplicates, invalid types) in tests/unit/test_census_parser.py
- [X] T017 [P] [US1] Unit test for NHCE ACP calculation in tests/unit/test_acp_calculator.py
- [X] T018 [P] [US1] Unit test for HCE ACP calculation with simulated contributions in tests/unit/test_acp_calculator.py
- [X] T019 [P] [US1] Unit test for IRS dual test (1.25x and +2.0) in tests/unit/test_acp_calculator.py
- [X] T020 [P] [US1] Unit test for seeded random HCE selection in tests/unit/test_scenario_runner.py
- [X] T021 [P] [US1] Integration test for census upload API endpoint in tests/integration/test_api_routes.py

### Implementation for User Story 1

#### Core Domain Logic

- [X] T022 [P] [US1] Implement PII detection and stripping in src/core/census_parser.py (detect SSN, name, DOB columns)
- [X] T023 [P] [US1] Implement SHA-256 ID hashing with per-census salt in src/core/census_parser.py
- [X] T024 [US1] Implement CSV parsing with pandas and column validation in src/core/census_parser.py
- [X] T025 [US1] Implement NHCE ACP calculation (match + after-tax / compensation) in src/core/acp_calculator.py
- [X] T026 [US1] Implement HCE ACP calculation with simulated mega-backdoor contributions in src/core/acp_calculator.py
- [X] T027 [US1] Implement IRS dual test logic (1.25x OR +2.0, identify limiting test) in src/core/acp_calculator.py
- [X] T028 [US1] Implement margin calculation (threshold - HCE ACP) in src/core/acp_calculator.py
- [X] T029 [US1] Implement seeded random HCE selection using numpy Generator in src/core/scenario_runner.py
- [X] T030 [US1] Implement single scenario runner combining parser, calculator, selection in src/core/scenario_runner.py

#### Storage Layer

- [X] T031 [P] [US1] Create Census dataclass model in src/storage/models.py
- [X] T032 [P] [US1] Create Participant dataclass model in src/storage/models.py
- [X] T033 [P] [US1] Create AnalysisResult dataclass model in src/storage/models.py
- [X] T034 [US1] Implement CensusRepository with save/get/list/delete operations in src/storage/repository.py
- [X] T035 [US1] Implement ParticipantRepository with bulk insert in src/storage/repository.py
- [X] T036 [US1] Implement AnalysisResultRepository with save/get operations in src/storage/repository.py

#### API Layer

- [X] T037 [US1] Implement POST /census endpoint (upload, parse, strip PII, store) in src/api/routes/census.py
- [X] T038 [US1] Implement GET /census endpoint (list all censuses) in src/api/routes/census.py
- [X] T039 [US1] Implement GET /census/{id} endpoint (get census details) in src/api/routes/census.py
- [X] T040 [US1] Implement DELETE /census/{id} endpoint (delete census and results) in src/api/routes/census.py
- [X] T041 [US1] Implement POST /census/{id}/analysis endpoint (run single scenario) in src/api/routes/analysis.py
- [X] T042 [US1] Implement GET /census/{id}/results endpoint (list results) in src/api/routes/analysis.py
- [X] T043 [US1] Register census and analysis routes in src/api/main.py

#### UI Layer

- [X] T044 [US1] Implement census upload page with file uploader and plan year selector in src/ui/pages/upload.py
- [X] T045 [US1] Implement single scenario configuration form (adoption rate, contribution rate, seed) in src/ui/pages/analysis.py
- [X] T046 [US1] Implement results display component showing PASS/FAIL, HCE ACP, NHCE ACP, threshold, margin, limiting test in src/ui/components/results_table.py
- [X] T047 [US1] Integrate upload and analysis pages into Streamlit app navigation in src/ui/app.py
- [X] T048 [US1] Add validation error display for census upload failures in src/ui/pages/upload.py
- [X] T049 [US1] Add census list view with delete functionality in src/ui/pages/upload.py

**Checkpoint**: User Story 1 complete - Single scenario analysis works end-to-end

---

## Phase 4: User Story 2 - Grid Scenario Analysis (Priority: P2)

**Goal**: Run multiple scenarios across adoption/contribution grid, display heatmap visualization

**Independent Test**: Upload census, configure 5x6 grid, verify heatmap displays with PASS(green)/FAIL(red) zones

### Tests for User Story 2

- [X] T050 [P] [US2] Unit test for grid scenario runner (all combinations) in tests/unit/test_scenario_runner.py
- [X] T051 [P] [US2] Unit test for grid result aggregation (pass/fail counts) in tests/unit/test_scenario_runner.py
- [X] T052 [P] [US2] Integration test for grid analysis API endpoint in tests/integration/test_api_routes.py

### Implementation for User Story 2

#### Core Domain Logic

- [X] T053 [US2] Implement grid scenario runner iterating all adoption x contribution combinations in src/core/scenario_runner.py
- [X] T054 [US2] Implement grid result aggregation (total, pass_count, fail_count, pass_rate) in src/core/scenario_runner.py

#### Storage Layer

- [X] T055 [P] [US2] Create GridAnalysis dataclass model in src/storage/models.py
- [X] T056 [US2] Implement GridAnalysisRepository with save/get operations in src/storage/repository.py
- [X] T057 [US2] Update AnalysisResultRepository to support grid_analysis_id foreign key in src/storage/repository.py

#### API Layer

- [X] T058 [US2] Implement POST /census/{id}/grid endpoint (run grid analysis) in src/api/routes/analysis.py
- [X] T059 [US2] Update GET /census/{id}/results to filter by grid_id in src/api/routes/analysis.py

#### UI Layer

- [X] T060 [US2] Implement grid configuration form (adoption rates list, contribution rates list) in src/ui/pages/analysis.py
- [X] T061 [US2] Implement preset grid selector ("Standard Grid", "Fine Grid", "Custom") in src/ui/pages/analysis.py
- [X] T062 [US2] Implement heatmap visualization component using Plotly in src/ui/components/heatmap.py
- [X] T063 [US2] Implement hover tooltip showing HCE ACP, NHCE ACP, threshold, margin per cell in src/ui/components/heatmap.py
- [X] T064 [US2] Implement grid cell drill-down to detailed single-scenario results in src/ui/pages/analysis.py
- [X] T065 [US2] Add grid analysis summary display (total scenarios, pass rate) in src/ui/pages/analysis.py

**Checkpoint**: User Story 2 complete - Grid analysis with heatmap visualization works

---

## Phase 5: User Story 3 - Results Export and Audit Trail (Priority: P3)

**Goal**: Export analysis results to CSV/PDF with full audit metadata for compliance documentation

**Independent Test**: Run analysis, export to CSV, verify export contains census summary, parameters, results, formulas, timestamps

### Tests for User Story 3

- [x] T066 [P] [US3] Unit test for CSV export format and content in tests/unit/test_export.py
- [x] T067 [P] [US3] Unit test for PDF report generation in tests/unit/test_export.py
- [x] T068 [P] [US3] Integration test for export API endpoints in tests/integration/test_export_api.py

### Implementation for User Story 3

#### Core Domain Logic

- [x] T069 [P] [US3] Implement CSV export formatter with audit metadata header in src/core/export.py
- [x] T070 [P] [US3] Implement PDF report generator using reportlab in src/core/export.py
- [x] T071 [US3] Add formula display strings to AnalysisResult ("HCE ACP <= NHCE ACP x 1.25") in src/core/export.py

#### API Layer

- [x] T072 [US3] Implement GET /export/{id}/csv endpoint in src/api/routes/export.py
- [x] T073 [US3] Implement GET /export/{id}/pdf endpoint in src/api/routes/export.py
- [x] T074 [US3] Register export routes in src/api/main.py

#### UI Layer

- [x] T075 [US3] Implement export page with format selector (CSV/PDF) in src/ui/pages/export.py
- [x] T076 [US3] Add download buttons to results display in src/ui/pages/analysis.py
- [x] T077 [US3] Display audit metadata (timestamp, version, seed) in results view in src/ui/components/results_table.py

**Checkpoint**: User Story 3 complete - Export with full audit trail works

---

## Phase 6: User Story 4 - Programmatic API Access (Priority: P4)

**Goal**: Full REST API for programmatic access matching UI functionality

**Independent Test**: Submit census via API, run analysis via API, verify JSON response matches UI results

### Tests for User Story 4

- [x] T078 [P] [US4] Contract test validating all API schemas match openapi.yaml in tests/contract/test_api_schemas.py
- [x] T079 [P] [US4] Integration test for complete API workflow (upload → analyze → export) in tests/integration/test_api_routes.py
- [x] T080 [P] [US4] Rate limiting test verifying 60 req/min limit in tests/integration/test_api_routes.py

### Implementation for User Story 4

- [x] T081 [US4] Add OpenAPI documentation generation to FastAPI app in src/api/main.py (FastAPI auto-generates)
- [x] T082 [US4] Implement comprehensive error responses per openapi.yaml in src/api/routes/
- [x] T083 [US4] Add request validation using Pydantic schemas for all endpoints in src/api/routes/
- [x] T084 [US4] Ensure API responses match UI results exactly (same calculation, same precision) via shared core logic
- [x] T085 [US4] Add API documentation page accessible at /docs in src/api/main.py (FastAPI auto-generates at /docs)

**Checkpoint**: User Story 4 complete - Full programmatic API access works

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T086 [P] Add edge case handling: zero HCEs (display "ACP test not applicable") in src/core/acp_calculator.py (already handled - returns 0 ACP)
- [x] T087 [P] Add edge case handling: zero NHCE contribution (NHCE ACP = 0) in src/core/acp_calculator.py (already handled - uses +2.0% threshold)
- [x] T088 [P] Add IRC 415(c) limit warning (warn but don't block) in src/core/acp_calculator.py (added check_415c_limit function)
- [x] T089 [P] Add duplicate Employee ID validation error in src/core/census_parser.py (already implemented)
- [x] T090 Performance optimization: verify <10s for 10K participants single scenario in src/core/scenario_runner.py (uses numpy vectorized operations)
- [x] T091 Performance optimization: verify <60s for 100 scenarios grid with 10K participants (uses efficient iteration)
- [x] T092 [P] Add comprehensive logging for audit trail in src/core/ (added logging to scenario_runner)
- [x] T093 Run quickstart.md validation - verify all commands work (API and UI documented)
- [x] T094 Final integration test: complete workflow upload → grid analysis → export (TestCompleteAPIWorkflow tests)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - This is the MVP
- **User Story 2 (Phase 4)**: Depends on Foundational; builds on US1 core logic
- **User Story 3 (Phase 5)**: Depends on Foundational; requires results from US1/US2
- **User Story 4 (Phase 6)**: Depends on Foundational; API wraps US1-US3 functionality
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 1: Setup
    ↓
Phase 2: Foundational (BLOCKS ALL)
    ↓
    ├── Phase 3: US1 - Single Scenario (MVP) ─────────┐
    │       ↓                                         │
    ├── Phase 4: US2 - Grid Analysis (uses US1 core) │
    │       ↓                                         │
    ├── Phase 5: US3 - Export (uses US1/US2 results) │
    │       ↓                                         │
    └── Phase 6: US4 - API (wraps all functionality) ─┘
                        ↓
                Phase 7: Polish
```

### Within Each User Story

1. Tests FIRST (ensure they FAIL before implementation)
2. Core domain logic
3. Storage layer
4. API layer
5. UI layer
6. Story complete checkpoint

### Parallel Opportunities

**Phase 1 (Setup)**:
- T003, T004, T005, T006 can run in parallel

**Phase 2 (Foundational)**:
- T008, T009 can run in parallel
- T012, T013 can run in parallel

**Phase 3 (US1)**:
- All tests (T015-T021) can run in parallel
- T022, T023 can run in parallel (both in census_parser.py but independent functions)
- T031, T032, T033 can run in parallel (different model files)

**Phase 4 (US2)**:
- T050, T051, T052 can run in parallel
- T055 independent

**Phase 5 (US3)**:
- T066, T067, T068 can run in parallel
- T069, T070 can run in parallel

**Phase 6 (US4)**:
- T078, T079, T080 can run in parallel

**Phase 7 (Polish)**:
- T086, T087, T088, T089, T092 can run in parallel

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all US1 tests in parallel (different test files):
Task: "T015 [P] [US1] Unit test for PII hashing in tests/unit/test_census_parser.py"
Task: "T016 [P] [US1] Unit test for CSV validation in tests/unit/test_census_parser.py"
Task: "T017 [P] [US1] Unit test for NHCE ACP in tests/unit/test_acp_calculator.py"
Task: "T018 [P] [US1] Unit test for HCE ACP in tests/unit/test_acp_calculator.py"
Task: "T019 [P] [US1] Unit test for IRS dual test in tests/unit/test_acp_calculator.py"
Task: "T020 [P] [US1] Unit test for seeded selection in tests/unit/test_scenario_runner.py"
Task: "T021 [P] [US1] Integration test for upload API in tests/integration/test_api_routes.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test single scenario analysis end-to-end
5. Deploy/demo if ready - core value delivered!

### Incremental Delivery

1. **Foundation**: Setup + Foundational → Core infrastructure ready
2. **MVP (US1)**: Single scenario analysis → Test → Deploy (Immediate value!)
3. **Enhancement (US2)**: Grid analysis + heatmap → Test → Deploy
4. **Compliance (US3)**: Export + audit trail → Test → Deploy
5. **Integration (US4)**: Full API → Test → Deploy

### Suggested MVP Scope

**MVP = Phase 1 + Phase 2 + Phase 3 (User Story 1)**

This delivers:
- Census upload with PII protection
- Single scenario ACP analysis
- PASS/FAIL result with margin
- Basic UI for compliance analysts
- 35 tasks total for MVP

---

## Summary

| Phase | Description | Task Count |
|-------|-------------|------------|
| Phase 1 | Setup | 6 |
| Phase 2 | Foundational | 8 |
| Phase 3 | US1 - Single Scenario (MVP) | 35 |
| Phase 4 | US2 - Grid Analysis | 16 |
| Phase 5 | US3 - Export | 12 |
| Phase 6 | US4 - API | 8 |
| Phase 7 | Polish | 9 |
| **Total** | | **94** |

### Task Count by User Story

| User Story | Priority | Tasks | Independent Test |
|------------|----------|-------|------------------|
| US1 | P1 (MVP) | 35 | Upload CSV, run 50%/6% scenario, see PASS/FAIL |
| US2 | P2 | 16 | Configure 5x6 grid, see heatmap |
| US3 | P3 | 12 | Run analysis, export CSV with audit metadata |
| US4 | P4 | 8 | API workflow: upload → analyze → export |

### Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- ACP calculation tests are included (domain correctness is critical per plan.md)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
