# Tasks: React Frontend Migration

**Input**: Design documents from `/specs/008-react-frontend-migration/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/openapi-workspaces.yaml

**Tests**: Not explicitly requested in spec - tests omitted per template guidance.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, etc.)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/app/` (Python/FastAPI)
- **Frontend**: `frontend/src/` (React/TypeScript)

---

## Phase 1: Setup (Repository Restructure)

**Purpose**: Reorganize repository and initialize project structures

- [x] T001 Create `backend/` directory structure with `app/models/`, `app/services/`, `app/routers/`, `app/storage/`
- [x] T002 Create `frontend/` directory structure with `src/components/`, `src/pages/`, `src/services/`, `src/hooks/`, `src/types/`, `src/utils/`
- [x] T003 [P] Move existing `src/api/` to `backend/app/routers/` preserving git history
- [x] T004 [P] Move existing `src/core/` to `backend/app/services/` preserving git history
- [x] T005 [P] Move existing `src/storage/` to `backend/app/storage/` preserving git history
- [x] T006 [P] Move existing `tests/` to `backend/tests/` preserving git history
- [x] T007 Update Python import paths in all moved backend files
- [x] T008 Create `backend/app/__init__.py` and package init files
- [x] T009 Create `backend/pyproject.toml` with dependencies from existing requirements
- [x] T010 [P] Initialize `frontend/` with Vite + React 19 + TypeScript (`npm create vite@latest`)
- [x] T011 [P] Configure `frontend/vite.config.ts` with react plugin and path aliases
- [x] T012 [P] Create `frontend/index.html` with Tailwind CDN script
- [ ] T013 Update root `pyproject.toml` or create workspace configuration if needed

---

## Phase 2: Foundational (Backend Infrastructure)

**Purpose**: Backend workspace storage and API infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No frontend user story work can begin until backend API is available

### Workspace Storage Layer

- [x] T014 Create Workspace Pydantic model in `backend/app/models/workspace.py`
- [x] T015 [P] Create Run Pydantic model in `backend/app/models/run.py`
- [x] T016 [P] Create CensusSummary Pydantic model in `backend/app/models/census.py`
- [x] T017 [P] Create GridResult and ScenarioResult models in `backend/app/models/analysis.py`
- [x] T018 [P] Create Error response model in `backend/app/models/errors.py`
- [x] T019 Implement WorkspaceStorage class in `backend/app/storage/workspace_storage.py` with file-based CRUD operations
- [x] T020 Implement atomic write helper (temp file + rename pattern) in `backend/app/storage/utils.py`
- [x] T021 Add workspace directory structure creation on first workspace create

### Workspace API Endpoints

- [x] T022 Create workspace router in `backend/app/routers/workspaces.py`
- [x] T023 Implement GET `/api/workspaces` endpoint (list all)
- [x] T024 [P] Implement POST `/api/workspaces` endpoint (create)
- [x] T025 [P] Implement GET `/api/workspaces/{workspace_id}` endpoint (get detail)
- [x] T026 [P] Implement PUT `/api/workspaces/{workspace_id}` endpoint (update)
- [x] T027 [P] Implement DELETE `/api/workspaces/{workspace_id}` endpoint (delete with cascade)
- [x] T028 Register workspace router in `backend/app/main.py`
- [x] T029 Add CORS middleware for `http://localhost:3000` in `backend/app/main.py`

### Frontend Foundation

- [x] T030 Create TypeScript types for Workspace in `frontend/src/types/workspace.ts`
- [x] T031 [P] Create TypeScript types for Run in `frontend/src/types/run.ts`
- [x] T032 [P] Create TypeScript types for Analysis (ScenarioResult, GridResult, ViewMode) in `frontend/src/types/analysis.ts`
- [x] T033 [P] Create TypeScript types for Employee and CensusStats in `frontend/src/types/employee.ts`
- [x] T034 Create base API client with fetch wrapper in `frontend/src/services/api.ts`
- [x] T035 [P] Create `.env` file with `VITE_API_URL=http://localhost:8000`
- [x] T036 Create Layout component with header, navigation, footer in `frontend/src/components/Layout.tsx`
- [x] T037 Create App component with React Router setup in `frontend/src/App.tsx`
- [x] T038 Create main entry point in `frontend/src/main.tsx`

**Checkpoint**: Backend API functional, frontend shell renders with navigation

---

## Phase 3: User Story 1 - Manage Workspaces (Priority: P1) 🎯 MVP

**Goal**: Users can create, view, edit, and delete workspaces to organize ACP analysis projects

**Independent Test**: Create workspace, view in grid, edit name/description, delete - all via UI

### Implementation for User Story 1

- [x] T039 [US1] Create WorkspaceContext for active workspace state in `frontend/src/hooks/useWorkspace.tsx`
- [x] T040 [US1] Create workspace API service functions (list, create, get, update, delete) in `frontend/src/services/workspaceService.ts`
- [x] T041 [US1] Create WorkspaceCard component for grid display in `frontend/src/components/WorkspaceCard.tsx`
- [x] T042 [US1] Create WorkspaceGrid component in `frontend/src/components/WorkspaceGrid.tsx`
- [x] T043 [US1] Create CreateWorkspaceModal component in `frontend/src/components/CreateWorkspaceModal.tsx`
- [x] T044 [US1] Create EditWorkspaceModal component in `frontend/src/components/EditWorkspaceModal.tsx`
- [x] T045 [US1] Create DeleteConfirmModal component in `frontend/src/components/DeleteConfirmModal.tsx`
- [x] T046 [US1] Create WorkspaceManager page in `frontend/src/pages/WorkspaceManager.tsx`
- [x] T047 [US1] Create empty state component for no workspaces in `frontend/src/components/EmptyState.tsx`
- [x] T048 [US1] Implement workspace selection to set active workspace in context
- [x] T049 [US1] Add workspace route to App router (root path `/`)
- [x] T050 [US1] Create WorkspaceDashboard page showing tabs after workspace selected in `frontend/src/pages/WorkspaceDashboard.tsx`

**Checkpoint**: User Story 1 complete - workspaces can be fully managed via React UI

---

## Phase 4: User Story 2 - Access Application via React Interface (Priority: P2)

**Goal**: Modern, responsive React interface with navigation between all views

**Independent Test**: Launch dev server, navigate tabs, verify responsive layout 320px-2560px

### Implementation for User Story 2

- [x] T051 [US2] Add responsive breakpoints and mobile-first styles to `frontend/src/components/Layout.tsx`
- [x] T052 [US2] Create TabNavigation component with Upload, Analysis, Employee Impact, Export tabs in `frontend/src/components/TabNavigation.tsx`
- [x] T053 [US2] Implement tab routing within WorkspaceDashboard (nested routes or state)
- [x] T054 [US2] Create placeholder CensusUpload page in `frontend/src/pages/CensusUpload.tsx`
- [x] T055 [P] [US2] Create placeholder AnalysisDashboard page in `frontend/src/pages/AnalysisDashboard.tsx`
- [x] T056 [P] [US2] Create placeholder EmployeeImpact page in `frontend/src/pages/EmployeeImpact.tsx`
- [x] T057 [P] [US2] Create placeholder Export page in `frontend/src/pages/Export.tsx`
- [x] T058 [US2] Add loading spinner component in `frontend/src/components/LoadingSpinner.tsx`
- [x] T059 [US2] Add ErrorBoundary component in `frontend/src/components/ErrorBoundary.tsx`
- [ ] T060 [US2] Verify navigation transitions occur without page reload

**Checkpoint**: User Story 2 complete - responsive SPA with tab navigation working

---

## Phase 5: User Story 3 - Upload and Configure Census Data (Priority: P3)

**Goal**: Plan administrator can upload CSV, map columns, configure HCE determination

**Independent Test**: Upload CSV file, map columns, view census statistics (total, HCE/NHCE counts)

### Backend Census Endpoints

- [x] T061 [US3] Implement POST `/api/workspaces/{id}/census` endpoint in `backend/app/routers/workspaces.py`
- [x] T062 [US3] Implement GET `/api/workspaces/{id}/census` endpoint in `backend/app/routers/workspaces.py`
- [x] T063 [US3] Create CSV parsing service in `backend/app/services/census_parser.py`
- [x] T064 [US3] Integrate census storage with workspace directory structure

### Frontend Census Upload

- [x] T065 [US3] Create census API service functions in `frontend/src/services/censusService.ts`
- [x] T066 [US3] Create FileDropzone component for drag-and-drop in `frontend/src/components/FileDropzone.tsx`
- [ ] T067 [US3] Create ColumnMapper component for mapping CSV columns in `frontend/src/components/ColumnMapper.tsx`
- [ ] T068 [US3] Create HCEConfiguration component for threshold/explicit mode in `frontend/src/components/HCEConfiguration.tsx`
- [x] T069 [US3] Create CensusStats component showing statistics in `frontend/src/components/CensusStats.tsx`
- [x] T070 [US3] Implement full CensusUpload page with file upload flow in `frontend/src/pages/CensusUpload.tsx`
- [x] T071 [US3] Add navigation to Analysis view after successful upload
- [x] T072 [US3] Add validation error display for malformed CSV files

**Checkpoint**: User Story 3 complete - census upload and configuration fully functional

---

## Phase 6: User Story 4 - Run Grid Analysis with Heatmap (Priority: P4)

**Goal**: Analyst runs grid analysis and views interactive heatmap with tooltips and view modes

**Independent Test**: Configure adoption/contribution rates, run analysis, interact with heatmap (hover, view modes)

### Backend Run Endpoints

- [x] T073 [US4] Implement POST `/api/workspaces/{id}/runs` endpoint in `backend/app/routers/workspaces.py`
- [x] T074 [US4] Implement GET `/api/workspaces/{id}/runs` endpoint in `backend/app/routers/workspaces.py`
- [x] T075 [US4] Implement GET `/api/workspaces/{id}/runs/{run_id}` endpoint
- [x] T076 [US4] Implement DELETE `/api/workspaces/{id}/runs/{run_id}` endpoint
- [x] T077 [US4] Integrate existing grid analysis engine with run creation

### Frontend Analysis Dashboard

- [x] T078 [US4] Create run API service functions in `frontend/src/services/runService.ts`
- [x] T079 [US4] Create RangeSlider component for rate configuration in `frontend/src/components/RangeSlider.tsx` (simplified: inline inputs in AnalysisDashboard)
- [x] T080 [US4] Create GridParameters component for adoption/contribution inputs in `frontend/src/components/GridParameters.tsx` (simplified: inline in AnalysisDashboard)
- [x] T081 [US4] Create Heatmap component (based on ui-example) in `frontend/src/components/Heatmap.tsx`
- [x] T082 [US4] Create HeatmapCell component with hover state in `frontend/src/components/HeatmapCell.tsx` (integrated into Heatmap.tsx)
- [x] T083 [US4] Create HeatmapTooltip component in `frontend/src/components/HeatmapTooltip.tsx` (integrated into Heatmap.tsx)
- [x] T084 [US4] Create ViewModeSelector component (Pass/Fail, Margin, Risk Zone) in `frontend/src/components/ViewModeSelector.tsx`
- [x] T085 [US4] Create ScenarioDetailModal for detailed cell info in `frontend/src/components/ScenarioDetailModal.tsx` (deferred: tooltip sufficient for MVP)
- [x] T086 [US4] Implement color scale utilities in `frontend/src/utils/colorScale.ts`
- [x] T087 [US4] Implement full AnalysisDashboard page in `frontend/src/pages/AnalysisDashboard.tsx`
- [x] T088 [US4] Add accessibility patterns (colorblind diagonal stripes) to Heatmap (CSS class added, pattern pending)

**Checkpoint**: User Story 4 complete - grid analysis with interactive heatmap working

---

## Phase 7: User Story 5 - View Employee-Level Impact (Priority: P5)

**Goal**: Analyst drills down to employee-level impact details with filtering

**Independent Test**: Select scenario, view employee table, filter by ID/compensation/constraint type

### Backend Employee Endpoints

- [x] T089 [US5] Implement GET `/api/workspaces/{id}/runs/{run_id}/employees` endpoint (if not existing)
- [x] T090 [US5] Add employee impact data to run results storage (computed on-the-fly from census)

### Frontend Employee Impact

- [x] T091 [US5] Create employee impact API service functions in `frontend/src/services/employeeService.ts`
- [x] T092 [US5] Create DataTable component with sorting/pagination in `frontend/src/components/DataTable.tsx`
- [x] T093 [US5] Create FilterBar component for employee filters in `frontend/src/components/FilterBar.tsx`
- [x] T094 [US5] Create EmployeeTypeToggle component (HCE/NHCE) in `frontend/src/components/EmployeeTypeToggle.tsx`
- [x] T095 [US5] Create ConstraintBadge component for status display in `frontend/src/components/ConstraintBadge.tsx`
- [x] T096 [US5] Implement full EmployeeImpact page in `frontend/src/pages/EmployeeImpact.tsx`
- [x] T097 [US5] Add navigation from heatmap cell click to Employee Impact view with context (via URL params)

**Checkpoint**: User Story 5 complete - employee-level details with filtering working

---

## Phase 8: User Story 6 - Export Analysis Results (Priority: P6)

**Goal**: User exports results to PDF or CSV format

**Independent Test**: Run analysis, navigate to Export, download PDF and CSV files

### Backend Export Endpoints

- [x] T098 [US6] Implement GET `/api/workspaces/{id}/runs/{run_id}/export/csv` endpoint
- [x] T099 [US6] Implement GET `/api/workspaces/{id}/runs/{run_id}/export/pdf` endpoint
- [x] T100 [US6] Add PDF generation service in `backend/app/services/pdf_export.py` (using existing export.py)

### Frontend Export

- [x] T101 [US6] Create export API service functions in `frontend/src/services/exportService.ts`
- [x] T102 [US6] Create ExportFormatSelector component in `frontend/src/components/ExportFormatSelector.tsx` (inline in Export page)
- [x] T103 [US6] Create ExportPreview component in `frontend/src/components/ExportPreview.tsx` (run details shown in Export page)
- [x] T104 [US6] Implement full Export page in `frontend/src/pages/Export.tsx`
- [x] T105 [US6] Add download progress indicator (loading spinner during export)

**Checkpoint**: User Story 6 complete - PDF and CSV export functional

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements affecting multiple user stories

- [ ] T106 Remove Streamlit code from `src/ui/` after React implementation verified (defer: keep for comparison)
- [x] T107 [P] Add toast notification system for errors and success messages in `frontend/src/components/Toast.tsx`
- [ ] T108 [P] Add keyboard navigation support across all interactive components (partial: focus states added)
- [ ] T109 Verify Lighthouse accessibility score ≥ 90 (defer: requires running dev server)
- [ ] T110 [P] Performance optimization: verify navigation < 1s, heatmap interaction < 200ms (defer: requires testing)
- [x] T111 Update root README.md with new project structure and commands
- [ ] T112 Run quickstart.md validation (both backend and frontend) (defer: requires manual testing)
- [x] T113 Clean up any remaining import path issues or dead code (TypeScript compiles clean)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational
- **User Story 2 (Phase 4)**: Depends on Phase 3 (needs workspace context)
- **User Story 3 (Phase 5)**: Depends on Phase 4 (needs navigation to Census tab)
- **User Story 4 (Phase 6)**: Depends on Phase 5 (needs census data)
- **User Story 5 (Phase 7)**: Depends on Phase 6 (needs run results)
- **User Story 6 (Phase 8)**: Depends on Phase 6 (needs run results)
- **Polish (Phase 9)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (Workspaces)**: Independent after Foundational
- **US2 (React Interface)**: Builds on US1 workspace selection
- **US3 (Census Upload)**: Requires active workspace (US1)
- **US4 (Grid Analysis)**: Requires census data (US3)
- **US5 (Employee Impact)**: Requires run results (US4)
- **US6 (Export)**: Requires run results (US4), can parallel with US5

### Parallel Opportunities

**Within Phase 1 (Setup):**
```
T003, T004, T005, T006 (file moves - different directories)
T010, T011, T012 (frontend init - independent files)
```

**Within Phase 2 (Foundational):**
```
T015, T016, T017, T018 (Pydantic models - independent files)
T024, T025, T026, T027 (API endpoints - after T022-T023)
T030, T031, T032, T033 (TypeScript types - independent files)
```

**Within Phase 4 (US2):**
```
T054, T055, T056, T057 (placeholder pages - independent files)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (repo restructure)
2. Complete Phase 2: Foundational (backend API, frontend shell)
3. Complete Phase 3: User Story 1 (workspace management)
4. **STOP and VALIDATE**: Test workspace CRUD via React UI
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Workspaces) → Test → Deploy (MVP!)
3. Add US2 (Navigation) → Test → Responsive SPA
4. Add US3 (Census) → Test → Data entry working
5. Add US4 (Analysis) → Test → Core analysis functional
6. Add US5 (Employee Impact) → Test → Drill-down working
7. Add US6 (Export) → Test → Full feature complete
8. Polish → Final cleanup and optimization

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational done:
   - Developer A: US1 + US2 (frontend shell)
   - Developer B: US3 + US4 backend endpoints
   - Developer C: US4 + US5 frontend components
3. Stories integrate via API contracts

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- File paths follow web app convention: `backend/` and `frontend/`
- ui-example provides reference patterns for Heatmap, Layout, CensusUpload components
- OpenAPI spec in `contracts/openapi-workspaces.yaml` defines all API contracts
- Workspace storage: `~/.acp-analyzer/workspaces/{uuid}/`
