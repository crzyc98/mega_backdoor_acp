# Tasks: CSV Import + Column Mapping Wizard

**Input**: Design documents from `/specs/003-csv-import-wizard/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root (per existing project structure)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and database schema extensions

- [ ] T001 Extend database schema with wizard tables (import_session, mapping_profile, validation_issue, import_log) in src/storage/database.py
- [ ] T002 [P] Add Participant table extension (ssn_hash, dob, hire_date, contribution fields) in src/storage/database.py
- [ ] T003 [P] Create wizard Pydantic schemas in src/api/schemas.py (ImportSession, MappingProfile, ValidationIssue, ImportLog, etc.)
- [ ] T004 [P] Create wizard dataclass models in src/storage/models.py (ImportSession, MappingProfile, ValidationIssue, ImportLog)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement field alias definitions for 9 required census fields in src/core/field_mappings.py
- [ ] T006 [P] Implement suggest_mapping() function with fuzzy matching in src/core/field_mappings.py
- [ ] T007 [P] Implement CSV file parsing with delimiter/encoding auto-detection in src/core/import_wizard.py
- [ ] T008 [P] Create ImportSessionRepository with CRUD operations in src/storage/repository.py
- [ ] T009 [P] Create MappingProfileRepository with CRUD operations in src/storage/repository.py
- [ ] T010 [P] Create ValidationIssueRepository with bulk insert and query by severity in src/storage/repository.py
- [ ] T011 [P] Create ImportLogRepository with CRUD and soft delete in src/storage/repository.py
- [ ] T012 Implement session expiration check (24-hour TTL) in src/core/import_wizard.py
- [ ] T013 Register import wizard API router in src/api/main.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Upload CSV and Auto-Map Columns (Priority: P1) 🎯 MVP

**Goal**: Plan administrator uploads a CSV file and system auto-suggests column mappings

**Independent Test**: Upload CSV with common headers (SSN, DOB, Hire Date), verify auto-mapping suggestions are correct and file preview shows 5 rows

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement createImportSession endpoint (POST /import/sessions) in src/api/routes/import_wizard.py
- [ ] T015 [P] [US1] Implement getFilePreview endpoint (GET /import/sessions/{id}/preview) in src/api/routes/import_wizard.py
- [ ] T016 [P] [US1] Implement suggestColumnMapping endpoint (GET /import/sessions/{id}/mapping/suggest) in src/api/routes/import_wizard.py
- [ ] T017 [US1] Implement setColumnMapping endpoint (PUT /import/sessions/{id}/mapping) with validation for all 9 required fields in src/api/routes/import_wizard.py
- [ ] T018 [US1] Implement getImportSession endpoint (GET /import/sessions/{id}) in src/api/routes/import_wizard.py
- [ ] T019 [US1] Implement listImportSessions endpoint (GET /import/sessions) in src/api/routes/import_wizard.py
- [ ] T020 [US1] Implement deleteImportSession endpoint (DELETE /import/sessions/{id}) in src/api/routes/import_wizard.py
- [ ] T021 [US1] Create Upload step UI component with file uploader and preview table in src/ui/pages/import_wizard.py
- [ ] T022 [US1] Create Mapping step UI component with auto-suggest display and dropdown overrides in src/ui/pages/import_wizard.py
- [ ] T023 [US1] Implement wizard step navigation (Upload → Map) with state management in src/ui/pages/import_wizard.py
- [ ] T024 [US1] Add 50MB file size validation with clear error message in src/api/routes/import_wizard.py
- [ ] T025 [US1] Add file upload progress indicator in src/ui/pages/import_wizard.py

**Checkpoint**: User Story 1 complete - Can upload CSV, see preview, get auto-suggested mappings, manually adjust mappings

---

## Phase 4: User Story 2 - Validate Data and Review Issues (Priority: P1)

**Goal**: Plan administrator reviews validation results organized by severity before committing import

**Independent Test**: Upload CSV with intentional errors (invalid SSN, bad dates, negative amounts), verify validation categorizes issues correctly by severity

### Implementation for User Story 2

- [ ] T026 [P] [US2] Implement validate_ssn() function (9 digits, no dashes) in src/core/import_wizard.py
- [ ] T027 [P] [US2] Implement validate_date() function (multi-format, not future) in src/core/import_wizard.py
- [ ] T028 [P] [US2] Implement validate_amount() function (non-negative dollar) in src/core/import_wizard.py
- [ ] T029 [US2] Implement validate_row() generator yielding ValidationIssue objects in src/core/import_wizard.py
- [ ] T030 [US2] Implement validate_file() function processing all rows with performance target (10k rows <10s) in src/core/import_wizard.py
- [ ] T031 [US2] Implement runValidation endpoint (POST /import/sessions/{id}/validate) in src/api/routes/import_wizard.py
- [ ] T032 [US2] Implement getValidationIssues endpoint (GET /import/sessions/{id}/validation-issues) with severity filter and pagination in src/api/routes/import_wizard.py
- [ ] T033 [US2] Create Validation step UI showing progress and summary counts by severity in src/ui/pages/import_wizard.py
- [ ] T034 [US2] Create expandable issue details component showing row number, field, message, suggestion in src/ui/pages/import_wizard.py
- [ ] T035 [US2] Implement wizard step navigation (Map → Validate) with validation gate in src/ui/pages/import_wizard.py
- [ ] T036 [US2] Add user-friendly validation messages for all issue codes (INVALID_SSN, INVALID_DATE, etc.) in src/core/import_wizard.py

**Checkpoint**: User Story 2 complete - Can validate mapped data and see categorized issues with actionable messages

---

## Phase 5: User Story 3 - Detect and Handle Duplicates (Priority: P1)

**Goal**: Plan administrator is alerted to duplicate records and can decide how to handle them

**Independent Test**: Upload CSV with duplicate SSNs (both in-file and matching database records), verify duplicates detected and resolution options displayed

### Implementation for User Story 3

- [ ] T037 [P] [US3] Implement SSN hashing function for privacy-safe duplicate detection in src/core/import_wizard.py
- [ ] T038 [US3] Implement detect_in_file_duplicates() using pandas groupby on SSN in src/core/import_wizard.py
- [ ] T039 [US3] Implement detect_existing_duplicates() with batch SQL lookup in src/core/import_wizard.py
- [ ] T040 [US3] Extend validate_file() to include duplicate detection (in-file=Error, existing=Warning) in src/core/import_wizard.py
- [ ] T041 [US3] Implement setDuplicateResolution endpoint (PUT /import/sessions/{id}/duplicate-resolution) in src/api/routes/import_wizard.py
- [ ] T042 [US3] Create duplicate resolution UI showing which rows are duplicates of which records in src/ui/pages/import_wizard.py
- [ ] T043 [US3] Add replace/skip toggle for each existing record duplicate in src/ui/pages/import_wizard.py
- [ ] T044 [US3] Add "apply to all" option for bulk duplicate resolution in src/ui/pages/import_wizard.py

**Checkpoint**: User Story 3 complete - Can detect both in-file and existing duplicates with resolution options

---

## Phase 6: User Story 4 - Save and Reuse Mapping Profiles (Priority: P2)

**Goal**: Plan administrator saves column mapping as named profile and reuses for future uploads

**Independent Test**: Save mapping profile after import, upload new file, apply saved profile, verify mappings restored correctly

### Implementation for User Story 4

- [ ] T045 [P] [US4] Implement createMappingProfile endpoint (POST /import/mapping-profiles) in src/api/routes/import_wizard.py
- [ ] T046 [P] [US4] Implement listMappingProfiles endpoint (GET /import/mapping-profiles) in src/api/routes/import_wizard.py
- [ ] T047 [P] [US4] Implement getMappingProfile endpoint (GET /import/mapping-profiles/{id}) in src/api/routes/import_wizard.py
- [ ] T048 [P] [US4] Implement updateMappingProfile endpoint (PUT /import/mapping-profiles/{id}) in src/api/routes/import_wizard.py
- [ ] T049 [P] [US4] Implement deleteMappingProfile endpoint (DELETE /import/mapping-profiles/{id}) in src/api/routes/import_wizard.py
- [ ] T050 [US4] Implement applyMappingProfile endpoint (POST /import/mapping-profiles/{id}/apply) with header matching logic in src/api/routes/import_wizard.py
- [ ] T051 [US4] Add "Save as Profile" button and name input dialog in Mapping step UI in src/ui/pages/import_wizard.py
- [ ] T052 [US4] Add saved profiles dropdown in Upload step UI in src/ui/pages/import_wizard.py
- [ ] T053 [US4] Show visual indicator for applied vs unmatched columns when profile applied in src/ui/pages/import_wizard.py

**Checkpoint**: User Story 4 complete - Can save, list, apply, and manage mapping profiles

---

## Phase 7: User Story 5 - Confirm and Execute Import (Priority: P2)

**Goal**: Plan administrator reviews pre-commit summary, confirms import, and receives completion report

**Independent Test**: Complete wizard to confirmation step, verify summary counts match expectations, execute import, verify completion report and downloadable log

### Implementation for User Story 5

- [ ] T054 [P] [US5] Implement getImportPreview endpoint (GET /import/sessions/{id}/preview-import) with categorized counts in src/api/routes/import_wizard.py
- [ ] T055 [P] [US5] Implement getPreviewRows endpoint (GET /import/sessions/{id}/preview-import/rows) with category filter in src/api/routes/import_wizard.py
- [ ] T056 [US5] Implement executeImport endpoint (POST /import/sessions/{id}/execute) with census/participant creation in src/api/routes/import_wizard.py
- [ ] T057 [US5] Implement duplicate replace logic (full record replacement except SSN) in src/core/import_wizard.py
- [ ] T058 [US5] Create ImportLog record with detailed per-row outcomes in src/core/import_wizard.py
- [ ] T059 [P] [US5] Implement listImportLogs endpoint (GET /import/logs) in src/api/routes/import_wizard.py
- [ ] T060 [P] [US5] Implement getImportLog endpoint (GET /import/logs/{id}) in src/api/routes/import_wizard.py
- [ ] T061 [P] [US5] Implement deleteImportLog endpoint (DELETE /import/logs/{id}) with soft delete in src/api/routes/import_wizard.py
- [ ] T062 [US5] Implement downloadImportLog endpoint (GET /import/logs/{id}/download) with CSV/JSON format in src/api/routes/import_wizard.py
- [ ] T063 [US5] Create Preview step UI showing import/reject/warning row counts with drill-down in src/ui/pages/import_wizard.py
- [ ] T064 [US5] Create Confirm step UI with census name/plan year inputs and execute button in src/ui/pages/import_wizard.py
- [ ] T065 [US5] Create completion report UI showing success/failure counts with download link in src/ui/pages/import_wizard.py
- [ ] T066 [US5] Implement wizard step navigation (Validate → Preview → Confirm → Complete) in src/ui/pages/import_wizard.py
- [ ] T067 [US5] Add import execution progress indicator in src/ui/pages/import_wizard.py

**Checkpoint**: User Story 5 complete - Full wizard flow operational with import execution and completion reports

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T068 Add comprehensive error handling for all API endpoints in src/api/routes/import_wizard.py
- [ ] T069 [P] Add structured logging for import operations in src/core/import_wizard.py
- [ ] T070 [P] Implement session cleanup job for expired sessions in src/core/import_wizard.py
- [ ] T071 Add wizard navigation breadcrumb/stepper UI component in src/ui/pages/import_wizard.py
- [ ] T072 Performance optimization: ensure 10k row validation completes in <10s in src/core/import_wizard.py
- [ ] T073 Add edge case handling: empty file, headers only, encoding errors in src/core/import_wizard.py
- [ ] T074 [P] Add import wizard link to main navigation in src/ui/app.py
- [ ] T075 Run quickstart.md validation scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1, US2, US3 are all P1 priority - implement in order
  - US4, US5 are P2 priority - implement after P1 stories
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Phase 2 - Uses session/mapping from US1 but independently testable
- **User Story 3 (P1)**: Can start after Phase 2 - Extends validation from US2 but independently testable
- **User Story 4 (P2)**: Can start after Phase 2 - Profile management is independent
- **User Story 5 (P2)**: Requires US1-US3 for full flow but preview/execute logic is independent

### Within Each User Story

- Models/repositories before services
- Services before endpoints
- Endpoints before UI
- Core implementation before integration

### Parallel Opportunities

- T002, T003, T004 (Setup) can run in parallel
- T005-T011 (Foundational) most can run in parallel
- T014, T015, T016 (US1 endpoints) can run in parallel
- T026, T027, T028 (US2 validators) can run in parallel
- T045-T049 (US4 profile endpoints) can run in parallel
- T054, T055, T059, T060, T061 (US5 endpoints) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch parallelizable US1 endpoints together:
Task: "Implement createImportSession endpoint in src/api/routes/import_wizard.py"
Task: "Implement getFilePreview endpoint in src/api/routes/import_wizard.py"
Task: "Implement suggestColumnMapping endpoint in src/api/routes/import_wizard.py"

# Then sequentially:
Task: "Implement setColumnMapping endpoint (depends on suggest logic)"
Task: "Create Upload step UI (depends on API endpoints)"
Task: "Create Mapping step UI (depends on API endpoints)"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Upload + Auto-Map)
4. Complete Phase 4: User Story 2 (Validation)
5. Complete Phase 5: User Story 3 (Duplicates)
6. **STOP and VALIDATE**: Test full P1 flow independently
7. Deploy/demo if ready - basic import wizard is functional

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Can upload and map columns
3. Add User Story 2 → Test independently → Can validate data
4. Add User Story 3 → Test independently → Can handle duplicates
5. Add User Story 4 → Test independently → Can save/load profiles
6. Add User Story 5 → Test independently → Can execute imports
7. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Performance target: 10k rows validated in <10 seconds
- Session persistence: 24 hours
- File size limit: 50MB
- Required fields: 9 census fields (SSN, DOB, Hire Date, Compensation, 5 contribution fields)
