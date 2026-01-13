# Tasks: Enhanced Census CSV Upload Wizard

**Input**: Design documents from `/specs/009-csv-upload-wizard/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in spec - test tasks omitted. Add tests as needed.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/app/` for source, `backend/tests/` for tests
- **Frontend**: `frontend/src/` for source, `frontend/tests/` for tests

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: TypeScript types and API client foundation

- [x] T001 Create TypeScript interfaces for import wizard in frontend/src/types/importWizard.ts
- [x] T002 Create import wizard API service client in frontend/src/services/importWizardService.ts
- [x] T003 [P] Create WizardProgress component for step indicator in frontend/src/components/ImportWizard/WizardProgress.tsx

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend model extensions and core wizard container that MUST be complete before user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Extend ImportSession model with date_format field in backend/app/storage/models.py
- [x] T005 [P] Extend MappingProfile model with workspace_id, date_format, is_default fields in backend/app/storage/models.py
- [x] T006 Create ImportWizard container component with step state management in frontend/src/components/ImportWizard/index.tsx
- [x] T007 Integrate ImportWizard into CensusUpload page in frontend/src/pages/CensusUpload.tsx

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Upload and Map Census CSV (Priority: P1) 🎯 MVP

**Goal**: Upload CSV file and map columns with auto-detection and confidence scores

**Independent Test**: Upload a CSV file, verify column suggestions appear with confidence scores, adjust mappings, confirm preview updates

### Backend Implementation for US1

- [x] T008 [P] [US1] Add confidence score calculation to suggest_mapping() in backend/app/services/field_mappings.py
- [x] T009 [P] [US1] Implement POST /api/workspaces/{workspace_id}/import/sessions endpoint in backend/app/routers/routes/import_wizard.py
- [x] T010 [P] [US1] Implement GET /api/import/sessions/{session_id} endpoint in backend/app/routers/routes/import_wizard.py
- [x] T011 [P] [US1] Implement GET /api/import/sessions/{session_id}/preview endpoint in backend/app/routers/routes/import_wizard.py
- [x] T012 [P] [US1] Implement GET /api/import/sessions/{session_id}/mapping/suggest endpoint in backend/app/routers/routes/import_wizard.py
- [x] T013 [US1] Implement PUT /api/import/sessions/{session_id}/mapping endpoint in backend/app/routers/routes/import_wizard.py

### Frontend Implementation for US1

- [x] T014 [P] [US1] Create StepUpload component with file dropzone in frontend/src/components/ImportWizard/StepUpload.tsx
- [x] T015 [P] [US1] Create ColumnMapper component with confidence indicators in frontend/src/components/ColumnMapper.tsx
- [x] T016 [US1] Create StepMapping component integrating ColumnMapper in frontend/src/components/ImportWizard/StepMapping.tsx
- [x] T017 [US1] Add file upload API calls to importWizardService in frontend/src/services/importWizardService.ts
- [x] T018 [US1] Add mapping API calls to importWizardService in frontend/src/services/importWizardService.ts
- [x] T019 [US1] Wire StepUpload and StepMapping into ImportWizard flow in frontend/src/components/ImportWizard/index.tsx

**Checkpoint**: User Story 1 complete - CSV upload and column mapping works independently

---

## Phase 4: User Story 2 - Date Format Selection with Live Preview (Priority: P2)

**Goal**: Select date format from list of options and see live preview of parsed dates

**Independent Test**: Upload CSV with date columns, change date format selection, verify preview shows correctly parsed dates or errors

### Backend Implementation for US2

- [x] T020 [P] [US2] Create date_parser service with format detection in backend/app/services/date_parser.py
- [x] T021 [P] [US2] Implement GET /api/import/sessions/{session_id}/date-format/detect endpoint in backend/app/routers/routes/import_wizard.py
- [x] T022 [P] [US2] Implement GET /api/import/sessions/{session_id}/date-format/preview endpoint in backend/app/routers/routes/import_wizard.py
- [x] T023 [US2] Implement PUT /api/import/sessions/{session_id}/date-format endpoint in backend/app/routers/routes/import_wizard.py

### Frontend Implementation for US2

- [x] T024 [P] [US2] Create DateFormatPicker component with format options and preview in frontend/src/components/DateFormatPicker.tsx
- [x] T025 [US2] Create StepDateFormat wizard step component in frontend/src/components/ImportWizard/StepDateFormat.tsx
- [x] T026 [US2] Add date format API calls to importWizardService in frontend/src/services/importWizardService.ts
- [x] T027 [US2] Wire StepDateFormat into ImportWizard flow in frontend/src/components/ImportWizard/index.tsx

**Checkpoint**: User Story 2 complete - Date format selection works independently

---

## Phase 5: User Story 3 - Validation Feedback with Row Status (Priority: P2)

**Goal**: Display color-coded validation status (green/yellow/red) for each row with error messages

**Independent Test**: Upload CSV with invalid data, verify rows show appropriate colors and error messages, see validation summary

### Backend Implementation for US3

- [x] T028 [P] [US3] Implement POST /api/import/sessions/{session_id}/validate endpoint in backend/app/routers/routes/import_wizard.py
- [x] T029 [P] [US3] Implement GET /api/import/sessions/{session_id}/validation-issues endpoint with filtering in backend/app/routers/routes/import_wizard.py
- [x] T030 [P] [US3] Implement GET /api/import/sessions/{session_id}/preview-rows endpoint with status filtering in backend/app/routers/routes/import_wizard.py
- [x] T031 [US3] Implement POST /api/import/sessions/{session_id}/execute endpoint with error blocking in backend/app/routers/routes/import_wizard.py

### Frontend Implementation for US3

- [x] T032 [P] [US3] Create ValidationPreview component with color-coded rows in frontend/src/components/ValidationPreview.tsx
- [x] T033 [US3] Create StepValidation wizard step component in frontend/src/components/ImportWizard/StepValidation.tsx
- [x] T034 [US3] Create StepConfirm wizard step component with import execution in frontend/src/components/ImportWizard/StepConfirm.tsx
- [x] T035 [US3] Add validation API calls to importWizardService in frontend/src/services/importWizardService.ts
- [x] T036 [US3] Wire StepValidation and StepConfirm into ImportWizard flow in frontend/src/components/ImportWizard/index.tsx

**Checkpoint**: User Story 3 complete - Full import flow with validation works independently

---

## Phase 6: User Story 4 - Saved Mapping Profiles per Workspace (Priority: P3)

**Goal**: Save and reuse column mappings per workspace for repeat imports

**Independent Test**: Complete import with mappings, start new import, verify saved profile can be applied

### Backend Implementation for US4

- [x] T037 [P] [US4] Implement GET /api/workspaces/{workspace_id}/import/mapping-profiles endpoint in backend/app/routers/routes/import_wizard.py
- [x] T038 [P] [US4] Implement POST /api/workspaces/{workspace_id}/import/mapping-profiles endpoint in backend/app/routers/routes/import_wizard.py
- [x] T039 [P] [US4] Implement PUT /api/workspaces/{workspace_id}/import/mapping-profiles/{profile_id} endpoint in backend/app/routers/routes/import_wizard.py
- [x] T040 [P] [US4] Implement DELETE /api/workspaces/{workspace_id}/import/mapping-profiles/{profile_id} endpoint in backend/app/routers/routes/import_wizard.py
- [x] T041 [US4] Implement POST /api/import/sessions/{session_id}/apply-profile endpoint in backend/app/routers/routes/import_wizard.py

### Frontend Implementation for US4

- [x] T042 [P] [US4] Create MappingProfileSelector component for profile management in frontend/src/components/MappingProfileSelector.tsx
- [x] T043 [US4] Integrate MappingProfileSelector into StepMapping in frontend/src/components/ImportWizard/StepMapping.tsx
- [x] T044 [US4] Add profile management API calls to importWizardService in frontend/src/services/importWizardService.ts
- [x] T045 [US4] Add save profile option to StepConfirm component in frontend/src/components/ImportWizard/StepConfirm.tsx

**Checkpoint**: User Story 4 complete - All user stories functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, error handling, and final polish

- [x] T046 [P] Add empty file and headers-only error handling to StepUpload in frontend/src/components/ImportWizard/StepUpload.tsx
- [x] T047 [P] Add delimiter/encoding display to file preview in frontend/src/components/ImportWizard/StepUpload.tsx
- [x] T048 [P] Add session expiration handling with user notification in frontend/src/components/ImportWizard/index.tsx
- [x] T049 [P] Add jump-to-error navigation in ValidationPreview in frontend/src/components/ImportWizard/StepValidation.tsx
- [ ] T050 Run manual test using census_example.csv to validate full flow

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (P1): Must complete first - MVP
  - US2 (P2): Can start after Foundational, uses existing session from US1
  - US3 (P2): Can start after Foundational, extends validation from US1
  - US4 (P3): Can start after Foundational, adds to mapping step from US1
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories - Complete first for MVP
- **User Story 2 (P2)**: No dependencies - Adds date step between mapping and validation
- **User Story 3 (P2)**: No dependencies - Adds validation step after date format
- **User Story 4 (P3)**: No dependencies - Enhances mapping step with profiles

### Within Each User Story

- Backend endpoints before frontend components that call them
- Models/services before API endpoints
- Components before integration into wizard flow
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**: T001, T002, T003 can run in parallel

**Phase 2 (Foundational)**: T004, T005 can run in parallel

**User Story 1**:
- Backend: T008, T009, T010, T011, T012 can run in parallel
- Frontend: T014, T015 can run in parallel

**User Story 2**:
- Backend: T020, T021, T022 can run in parallel
- Frontend: T024 standalone

**User Story 3**:
- Backend: T028, T029, T030 can run in parallel
- Frontend: T032 standalone

**User Story 4**:
- Backend: T037, T038, T039, T040 can run in parallel
- Frontend: T042 standalone

---

## Parallel Example: User Story 1 Backend

```bash
# Launch all backend endpoints in parallel:
Task: "Add confidence score to suggest_mapping() in backend/app/services/field_mappings.py"
Task: "Implement POST /workspaces/{workspace_id}/import/sessions in backend/app/routers/routes/import_wizard.py"
Task: "Implement GET /import/sessions/{session_id} in backend/app/routers/routes/import_wizard.py"
Task: "Implement GET /import/sessions/{session_id}/preview in backend/app/routers/routes/import_wizard.py"
Task: "Implement GET /import/sessions/{session_id}/mapping/suggest in backend/app/routers/routes/import_wizard.py"

# Then sequentially:
Task: "Implement PUT /import/sessions/{session_id}/mapping in backend/app/routers/routes/import_wizard.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T007)
3. Complete Phase 3: User Story 1 (T008-T019)
4. **STOP and VALIDATE**: Test upload and mapping flow with census_example.csv
5. Deploy/demo if ready - users can upload and map CSVs

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy (MVP!)
3. Add User Story 2 → Test date format selection → Deploy
4. Add User Story 3 → Test validation preview → Deploy
5. Add User Story 4 → Test saved profiles → Deploy
6. Each story adds value without breaking previous stories

### Effort Estimate

- **Phase 1-2 (Foundation)**: 7 tasks
- **User Story 1 (P1 MVP)**: 12 tasks
- **User Story 2 (P2)**: 8 tasks
- **User Story 3 (P2)**: 9 tasks
- **User Story 4 (P3)**: 9 tasks
- **Polish**: 5 tasks

**Total**: 50 tasks

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Backend has existing import_wizard.py with session/validation logic - extend don't rewrite
- Frontend uses React 19 with TypeScript
- Each user story independently testable using census_example.csv
- Commit after each task or logical group
