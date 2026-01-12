# Tasks: Census Management

**Input**: Design documents from `/specs/002-census-management/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Tests**: Not explicitly requested in spec - tests are optional in this implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database schema changes and new modules needed for all user stories

- [X] T001 Add HCE thresholds module with historical IRS data in src/core/hce_thresholds.py
- [X] T002 [P] Add new columns to census table schema (client_name, hce_mode, avg_compensation_cents, avg_deferral_rate) in src/storage/database.py
- [X] T003 [P] Add import_metadata table schema in src/storage/database.py
- [X] T004 Extend Census dataclass with new fields (client_name, hce_mode, avg_compensation_cents, avg_deferral_rate) in src/storage/models.py
- [X] T005 [P] Create ImportMetadata dataclass model in src/storage/models.py
- [X] T006 Add new API schemas (CensusUpdateRequest, ImportMetadata, ColumnMappingDetection, HCEThresholds) in src/api/schemas.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core repository methods and parser enhancements needed before user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Create ImportMetadataRepository class with save/get methods in src/storage/repository.py
- [X] T008 Add update() method to CensusRepository for metadata edits in src/storage/repository.py
- [X] T009 Add has_analyses() method to CensusRepository to check for associated analyses in src/storage/repository.py
- [X] T010 Add column mapping detection function (detect_column_mapping) to src/core/census_parser.py
- [X] T011 Add HCE determination by compensation threshold to process_census() in src/core/census_parser.py
- [X] T012 Add summary statistics calculation (avg_compensation, avg_deferral_rate) to census processing in src/core/census_parser.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Import and Create a Census (Priority: P1) 🎯 MVP

**Goal**: Allow users to upload CSV census files with column mapping, HCE mode selection, and receive summary statistics immediately

**Independent Test**: Upload a valid census file, provide name/client/plan_year/hce_mode, verify census created with correct counts and summary stats

### Implementation for User Story 1

- [X] T013 [US1] Add POST /census/column-mapping/detect endpoint for column detection in src/api/routes/census.py
- [X] T014 [US1] Extend POST /census endpoint to accept name, client_name, hce_mode, column_mapping parameters in src/api/routes/census.py
- [X] T015 [US1] Update upload_census() to use column mapping and HCE mode from request in src/api/routes/census.py
- [X] T016 [US1] Update upload_census() to store ImportMetadata after successful import in src/api/routes/census.py
- [X] T017 [US1] Update Census response schema to include client_name, hce_mode, avg_compensation, avg_deferral_rate in src/api/schemas.py
- [X] T018 [US1] Update create_census_from_dataframe() to calculate and store summary statistics in src/storage/repository.py
- [X] T019 [US1] Add validation error response with row numbers and field details in src/api/routes/census.py

**Checkpoint**: Census import with column mapping and HCE modes is fully functional

---

## Phase 4: User Story 2 - List and View Censuses (Priority: P1)

**Goal**: Allow users to list all censuses with filtering, view census details with metadata, and view individual participants

**Independent Test**: Create multiple censuses, verify list shows all with correct info, select one and verify full details including import metadata

### Implementation for User Story 2

- [X] T020 [US2] Extend GET /census list endpoint to support client_name filter in src/api/routes/census.py
- [X] T021 [US2] Update CensusSummary schema to include client_name and hce_mode in src/api/schemas.py
- [X] T022 [US2] Create GET /census/{census_id} detail endpoint returning CensusDetail with metadata in src/api/routes/census.py
- [X] T023 [US2] Create GET /census/{census_id}/metadata endpoint in src/api/routes/census.py
- [X] T024 [US2] Create GET /census/{census_id}/participants endpoint with pagination and HCE filter in src/api/routes/census.py
- [X] T025 [US2] Add ParticipantListResponse schema with pagination in src/api/schemas.py
- [X] T026 [US2] Add list_participants() method with pagination and filtering to ParticipantRepository in src/storage/repository.py

**Checkpoint**: Census listing and detail viewing is fully functional

---

## Phase 5: User Story 3 - Delete a Census (Priority: P2)

**Goal**: Allow users to delete censuses with confirmation and warning when associated analyses exist

**Independent Test**: Create a census, delete it, verify it no longer appears; create census with analysis, verify warning on delete

### Implementation for User Story 3

- [X] T027 [US3] Update DELETE /census/{census_id} endpoint to check for analyses and return X-Warning header in src/api/routes/census.py
- [X] T028 [US3] Add has_analyses field to CensusDetail response schema in src/api/schemas.py

**Checkpoint**: Census deletion with analysis warning is fully functional

---

## Phase 6: User Story 4 - Configure HCE Determination Method (Priority: P2)

**Goal**: Support both explicit HCE flag mode and compensation-threshold mode using plan year thresholds

**Independent Test**: Import census with compensation-threshold mode, verify HCE classification matches threshold for plan year

### Implementation for User Story 4

- [X] T029 [US4] Create GET /hce-thresholds endpoint to return historical threshold data in src/api/routes/census.py
- [X] T030 [US4] Add get_threshold_for_year() function with fallback behavior in src/core/hce_thresholds.py
- [X] T031 [US4] Integrate threshold lookup into census_parser when hce_mode='compensation_threshold' in src/core/census_parser.py

**Checkpoint**: Both HCE determination modes work correctly

---

## Phase 7: User Story 5 - Edit Census Metadata (Priority: P2)

**Goal**: Allow users to edit census name and client_name after import (participant data remains immutable)

**Independent Test**: Create census, update name via PATCH, verify change persisted; attempt to change plan_year, verify rejected

### Implementation for User Story 5

- [X] T032 [US5] Create PATCH /census/{census_id} endpoint for metadata updates in src/api/routes/census.py
- [X] T033 [US5] Validate that only name and client_name can be modified (reject immutable fields) in src/api/routes/census.py

**Checkpoint**: Census metadata editing is fully functional

---

## Phase 8: User Story 6 - Rerun Analysis with Stored Census (Priority: P3)

**Goal**: Enable selection of stored censuses for new analyses with preview of summary statistics

**Independent Test**: Import census, run analysis, start new analysis selecting same census, verify identical data used

### Implementation for User Story 6

- [X] T034 [US6] Verify existing analysis endpoints accept census_id parameter correctly (integration check)
- [X] T035 [US6] Ensure census summary stats are returned when selecting census for analysis

**Checkpoint**: Census reuse for analysis is fully functional

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements across all user stories

- [X] T036 [P] Add input validation for all new endpoints (max lengths, enum values) in src/api/routes/census.py
- [X] T037 [P] Add logging for census management operations in src/api/routes/census.py
- [X] T038 [P] Update existing UI census upload page to use new parameters in src/ui/pages/upload.py
- [ ] T039 Create census list/detail page in Streamlit UI in src/ui/pages/census_list.py
- [ ] T040 Run quickstart.md validation - test all documented API examples

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1 and US2 are both P1 priority - can proceed in parallel
  - US3, US4, US5 are P2 priority - can proceed after P1 or in parallel if staffed
  - US6 is P3 priority - depends on basic census CRUD being functional
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - Benefits from US1 for test data but independently testable
- **User Story 3 (P2)**: Can start after Foundational - Independent
- **User Story 4 (P2)**: Partially implemented in US1; Phase 6 completes standalone HCE config
- **User Story 5 (P2)**: Can start after Foundational - Independent
- **User Story 6 (P3)**: Integration story - best implemented after US1/US2

### Within Each User Story

- Models/schemas before endpoints
- Repository methods before API routes
- Core parser logic before API integration
- Story complete before moving to next priority

### Parallel Opportunities

- T002 and T003 can run in parallel (different schema changes)
- T004 and T005 can run in parallel (different models)
- T013-T019 (US1) can partially parallelize: T013 and T017 are independent
- T020-T026 (US2) can partially parallelize: schema changes before endpoints
- T036, T037, T038 can run in parallel (different files)

---

## Parallel Example: Setup Phase

```bash
# Launch parallel Setup tasks:
Task: "Add new columns to census table schema in src/storage/database.py"
Task: "Add import_metadata table schema in src/storage/database.py"

# After schema, launch parallel model tasks:
Task: "Extend Census dataclass with new fields in src/storage/models.py"
Task: "Create ImportMetadata dataclass model in src/storage/models.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T012)
3. Complete Phase 3: User Story 1 (T013-T019)
4. Complete Phase 4: User Story 2 (T020-T026)
5. **STOP and VALIDATE**: Test census import, list, and view independently
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Import) → Test → Deploy (can upload censuses!)
3. Add US2 (List/View) → Test → Deploy (can browse censuses!)
4. Add US3 (Delete) → Test → Deploy (full CRUD!)
5. Add US4 (HCE Config) → Test → Deploy (both HCE modes!)
6. Add US5 (Edit Metadata) → Test → Deploy (editable names!)
7. Add US6 (Rerun Analysis) → Test → Deploy (analysis integration!)
8. Polish phase → Final release

### Parallel Team Strategy

With multiple developers after Foundational complete:

- Developer A: User Story 1 (Import)
- Developer B: User Story 2 (List/View)
- Developer C: User Story 3 + 4 (Delete + HCE)

---

## Notes

- Existing Census model and API already exist - this extends them
- Participant model unchanged - no schema migration needed for participants
- SQLite ALTER TABLE for new columns requires careful handling of existing data
- Import metadata stored as JSON for flexibility
- HCE thresholds are code constants, not database - easy to update annually
