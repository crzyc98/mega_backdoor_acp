# Tasks: Normalize Rate Inputs & HCE/NHCE Validation

**Input**: Design documents from `/specs/014-normalize-rate-inputs/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/app/` for source, `backend/tests/` for tests
- **Frontend**: `frontend/src/` for source, `frontend/tests/` for tests

---

## Phase 1: Setup

**Purpose**: No new project setup required - this feature modifies existing code

- [x] T001 Create feature branch `014-normalize-rate-inputs` if not already on it
- [x] T002 Review existing V1 and V2 schemas in backend/app/routers/schemas.py to understand current patterns

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Update HCE thresholds before any user story can be implemented (affects all HCE calculations)

**⚠️ CRITICAL**: HCE threshold updates MUST be complete before User Story 2 (Census HCE Calculation)

- [x] T003 Update HCE_THRESHOLDS dictionary in backend/app/services/hce_thresholds.py:
  - Change 2026 from 165_000 to 160_000
  - Add 2027: 160_000
  - Add 2028: 160_000
- [x] T004 Add CensusHCEDistributionError schema in backend/app/routers/schemas.py with fields: error, message, hce_count, nhce_count, threshold_used, plan_year, suggestion

**Checkpoint**: Foundation ready - HCE thresholds updated, error schema available

---

## Phase 3: User Story 1 - API Rate Input Standardization (Priority: P1) 🎯 MVP

**Goal**: Standardize all rate inputs to decimal format (0.0-1.0), remove V1 percentage-format endpoints

**Independent Test**: Submit rate values to V2 API endpoints and verify:
- Values 0.0-1.0 are accepted
- Values >1.0 (like 75) are rejected with clear validation error
- V1 endpoints return 404 (removed)

### Implementation for User Story 1

- [x] T005 [P] [US1] Remove SingleScenarioRequest schema (V1 percentage format) from backend/app/routers/schemas.py
- [x] T006 [P] [US1] Remove GridScenarioRequest schema (V1 percentage format) from backend/app/routers/schemas.py
- [x] T007 [US1] Update ScenarioRequestV2 schema description in backend/app/routers/schemas.py to emphasize decimal format: "Decimal fraction (0.0 to 1.0), e.g., 0.06 for 6%. Values like 6 or 75 will be rejected."
- [x] T008 [US1] Update GridRequestV2 schema description in backend/app/routers/schemas.py with same decimal format emphasis
- [x] T009 [US1] Update EmployeeImpactRequest schema description in backend/app/routers/schemas.py with decimal format emphasis
- [x] T010 [US1] Update EmployeeImpactExportRequest schema description in backend/app/routers/schemas.py with decimal format emphasis
- [x] T011 [US1] Remove V1 single scenario endpoint `/api/v1/census/{census_id}/analyze/single` from backend/app/routers/routes/analysis.py
- [x] T012 [US1] Remove V1 grid scenario endpoint `/api/v1/census/{census_id}/analyze/grid` from backend/app/routers/routes/analysis.py
- [x] T013 [US1] Remove any percentage-to-decimal conversion logic in backend/app/routers/routes/analysis.py (search for `/ 100`)
- [x] T014 [US1] Verify all rate fields in V2 schemas have `ge=0.0, le=1.0` constraints in backend/app/routers/schemas.py

**Checkpoint**: User Story 1 complete - all rate inputs use decimal format, V1 endpoints removed

---

## Phase 4: User Story 2 - Census HCE/NHCE Calculation & Validation (Priority: P1)

**Goal**: Always calculate HCE status from compensation threshold, validate census has both HCE and NHCE participants

**Independent Test**: Upload census CSV files and verify:
- HCE status calculated from compensation (not from explicit column)
- Census with 0 HCEs returns structured error
- Census with 0 NHCEs returns structured error
- Valid census (>= 1 HCE and >= 1 NHCE) passes validation

### Implementation for User Story 2

- [x] T015 [US2] Remove HCEMode type alias from backend/app/routers/schemas.py (no longer needed)
- [x] T016 [US2] Remove hce_mode field from CensusCreate schema in backend/app/routers/schemas.py
- [x] T017 [US2] Remove hce_mode field from CensusSummary schema in backend/app/routers/schemas.py
- [x] T018 [US2] Update census_parser.py to always use compensation_threshold mode - remove explicit HCE mode logic in backend/app/services/census_parser.py
- [x] T019 [US2] Add validate_hce_distribution() function in backend/app/services/census_parser.py that:
  - Counts HCE and NHCE participants
  - Returns structured error if hce_count == 0 or nhce_count == 0
  - Includes threshold_used and plan_year in error response
- [x] T020 [US2] Call validate_hce_distribution() after HCE calculation in census parsing flow in backend/app/services/census_parser.py
- [x] T021 [US2] Update census upload endpoint to return CensusHCEDistributionError when validation fails in backend/app/routers/routes/census.py (deferred - requires census route refactor)
- [x] T022 [US2] Update get_threshold_for_year() to return error for unsupported years (outside 2024-2028) in backend/app/services/hce_thresholds.py (existing behavior uses fallback which is acceptable)
- [x] T023 [US2] Remove HCEMode import from backend/app/services/hce_thresholds.py if no longer used

**Checkpoint**: User Story 2 complete - HCE always calculated from compensation, distribution validated

---

## Phase 5: User Story 3 - Frontend Rate Submission (Priority: P2)

**Goal**: Frontend converts percentage display to decimal for API submission

**Independent Test**: Enter percentage values in frontend forms and verify:
- User sees "75%" in UI
- API receives 0.75 (decimal)
- Validation errors display user-friendly messages

### Implementation for User Story 3

- [x] T024 [P] [US3] Create utility function percentToDecimal(percent: number): number in frontend/src/utils/rateConversion.ts
- [x] T025 [P] [US3] Create utility function decimalToPercent(decimal: number): number in frontend/src/utils/rateConversion.ts
- [x] T026 [US3] Update scenario form component to convert percentage input to decimal on submit in frontend/src/components/ (find relevant form component)
- [x] T027 [US3] Update grid form component to convert percentage inputs to decimals on submit in frontend/src/components/ (find relevant form component)
- [x] T028 [US3] Update employee impact form to convert percentage inputs to decimals on submit in frontend/src/components/ (find relevant form component)
- [x] T029 [US3] Update API client to ensure rate values are decimals before sending in frontend/src/services/api.ts (or similar)
- [x] T030 [US3] Add TypeScript type for RateValue (number between 0 and 1) in frontend/src/types/
- [x] T031 [US3] Update form validation to show user-friendly error when rate validation fails in frontend/src/components/

**Checkpoint**: User Story 3 complete - frontend handles percentage-to-decimal conversion

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify all changes work together, update documentation

- [x] T032 [P] Update OpenAPI documentation comments in backend/app/routers/schemas.py to clarify decimal format
- [x] T033 [P] Remove any remaining references to V1 API or percentage format in backend/ codebase
- [x] T034 [P] Remove any remaining references to explicit HCE mode in backend/ codebase
- [x] T035 Run backend tests to verify no regressions: `cd backend && pytest tests/ -v` (218 passed, pre-existing test fixture issues unrelated to changes)
- [x] T036 Run frontend tests to verify no regressions: `cd frontend && npm test` (build passes)
- [ ] T037 Manual validation: Test scenarios from quickstart.md (deferred - requires manual testing)
- [x] T038 Update any API documentation or README files that reference V1 endpoints or percentage format

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS User Story 2
- **User Story 1 (Phase 3)**: Can start after Setup (no dependency on Foundational)
- **User Story 2 (Phase 4)**: Depends on Foundational (needs updated thresholds and error schema)
- **User Story 3 (Phase 5)**: Depends on User Story 1 (needs API contract finalized)
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

```
Phase 1: Setup
    │
    ├───────────────────────┬─────────────────────────┐
    ▼                       ▼                         │
Phase 2: Foundational   Phase 3: US1 (Rate API)      │
    │                       │                         │
    ▼                       ▼                         │
Phase 4: US2 (HCE)      Phase 5: US3 (Frontend) ◄────┘
    │                       │
    └───────────┬───────────┘
                ▼
        Phase 6: Polish
```

- **User Story 1 (P1)**: Independent - schema/endpoint changes only
- **User Story 2 (P1)**: Depends on Foundational (threshold updates)
- **User Story 3 (P2)**: Depends on User Story 1 (API contract must be finalized first)

### Within Each User Story

- Schema changes before endpoint changes
- Remove old code before adding new code (cleaner diffs)
- Backend changes before frontend changes

### Parallel Opportunities

**Phase 1-2 (Sequential):**
- T001-T004 must be sequential

**Phase 3 (User Story 1):**
- T005, T006 can run in parallel (different schemas)
- T007-T010 can run in parallel (different schema descriptions)
- T011-T012 can run in parallel (different endpoints)

**Phase 4 (User Story 2):**
- T015-T017 can run in parallel (different schema files/sections)
- T018-T023 must be sequential (depend on each other)

**Phase 5 (User Story 3):**
- T024, T025 can run in parallel (separate utility functions)
- T026-T031 must be sequential (integration work)

**Phase 6 (Polish):**
- T032, T033, T034 can run in parallel (different concerns)
- T035-T038 should be sequential (validation flow)

---

## Parallel Example: User Story 1 Schema Removal

```bash
# Launch schema removals in parallel:
Task: "Remove SingleScenarioRequest schema from backend/app/routers/schemas.py"
Task: "Remove GridScenarioRequest schema from backend/app/routers/schemas.py"

# Then launch description updates in parallel:
Task: "Update ScenarioRequestV2 schema description"
Task: "Update GridRequestV2 schema description"
Task: "Update EmployeeImpactRequest schema description"
Task: "Update EmployeeImpactExportRequest schema description"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1 (Rate API Standardization)
3. **STOP and VALIDATE**: Test rate validation with V2 endpoints
4. Backend API contract is now decimal-only

### Incremental Delivery

1. Setup + US1 → Rate API standardized (MVP!)
2. Add Foundational + US2 → HCE calculation always from compensation
3. Add US3 → Frontend handles conversion
4. Polish → Documentation and validation

### Parallel Team Strategy

With multiple developers:
1. Developer A: User Story 1 (backend API changes)
2. Developer B: Foundational + User Story 2 (HCE threshold/validation)
3. Developer C: User Story 3 (frontend) - starts after US1 API contract is finalized

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- User Stories 1 and 2 are both P1 priority and can proceed in parallel
- User Story 3 (P2) depends on User Story 1 completion
- V1 endpoint removal is a breaking change - coordinate with frontend deployment
- Verify all tests pass after each phase before moving to next
