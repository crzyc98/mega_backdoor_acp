# Tasks: UI Style Update

**Input**: Design documents from `/specs/007-ui-style-update/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Tests are NOT explicitly requested in the spec. Visual verification is manual per the plan. Minimal unit tests included for theme constants validation only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths follow existing structure from plan.md

---

## Phase 1: Setup (Theme Module Infrastructure)

**Purpose**: Create the centralized theme module that all styling depends on

- [x] T001 Create theme module directory structure at src/ui/theme/
- [x] T002 [P] Create color palette constants in src/ui/theme/colors.py
- [x] T003 [P] Create typography constants in src/ui/theme/typography.py
- [x] T004 [P] Create spacing and border-radius constants in src/ui/theme/spacing.py
- [x] T005 [P] Create shadow constants in src/ui/theme/shadows.py
- [x] T006 [P] Create status configuration (PASS/RISK/FAIL/ERROR mapping) in src/ui/theme/status.py
- [x] T007 Create CSS generation utilities in src/ui/theme/css.py
- [x] T008 Create Streamlit CSS injection helper in src/ui/theme/inject.py
- [x] T009 Create theme module exports in src/ui/theme/__init__.py

---

## Phase 2: Foundational (Reusable Styled Components)

**Purpose**: Create base components that user stories depend on

**Note**: These components are shared across multiple user stories and MUST be complete before story-specific styling

- [x] T010 [P] Create styled card wrapper component in src/ui/components/card.py
- [x] T011 [P] Create status badge component (PASS/RISK/FAIL/ERROR) in src/ui/components/status_badge.py
- [x] T012 [P] Create styled metric card component in src/ui/components/metric_card.py
- [x] T013 [P] Create styled empty state component in src/ui/components/empty_state.py
- [x] T014 Update components/__init__.py to export new components in src/ui/components/__init__.py

**Checkpoint**: Foundation ready - theme module and base components complete

---

## Phase 3: User Story 1 - Professional First Impression (Priority: P1) MVP

**Goal**: Application displays professional appearance with header branding, card-based layouts, and bold typography

**Independent Test**: Launch app, verify header shows branding/version badge, all content in styled cards, headings use bold typography

### Implementation for User Story 1

- [x] T015 [US1] Inject theme CSS at app startup in src/ui/app.py
- [x] T016 [US1] Add header branding (logo icon, app name, BETA badge) in src/ui/app.py
- [x] T017 [US1] Apply global typography CSS (font-family, weights) via theme injection in src/ui/theme/css.py
- [x] T018 [US1] Apply global card styling CSS (border-radius, shadows, borders) via theme injection in src/ui/theme/css.py
- [x] T019 [US1] Update upload page to use card layouts in src/ui/pages/upload.py
- [x] T020 [P] [US1] Update import wizard page to use card layouts in src/ui/pages/import_wizard.py
- [x] T021 [P] [US1] Update analysis page to use card layouts in src/ui/pages/analysis.py
- [x] T022 [P] [US1] Update export page to use card layouts in src/ui/pages/export.py

**Checkpoint**: User Story 1 complete - app has professional visual appearance with styled layouts

---

## Phase 4: User Story 2 - Clear Workflow Navigation (Priority: P1)

**Goal**: Navigation shows numbered steps with active state indication, empty states guide users

**Independent Test**: Navigate through pages, verify numbered labels (1. Upload Census, etc.), active tab highlighted, empty states show guidance

### Implementation for User Story 2

- [x] T023 [US2] Update navigation labels to numbered format (1. Upload Census, 2. Run Analysis, etc.) in src/ui/app.py
- [x] T024 [US2] Add CSS for navigation active state styling in src/ui/theme/css.py
- [x] T025 [US2] Implement empty state on analysis page when no census selected in src/ui/pages/analysis.py
- [x] T026 [P] [US2] Implement empty state on export page when no results available in src/ui/pages/export.py
- [x] T027 [US2] Add sidebar styling (selected census display, step indicators) in src/ui/app.py

**Checkpoint**: User Story 2 complete - clear workflow navigation with empty state guidance

---

## Phase 5: User Story 3 - Status-at-a-Glance Analysis Results (Priority: P1)

**Goal**: Analysis results display status prominently with color coding and styled metric cards

**Independent Test**: Run single scenario analysis, verify PASS/FAIL shows large colored badge with icon, metrics in styled cards, margin color indicates status

### Implementation for User Story 3

- [x] T028 [US3] Replace basic st.success/st.error with status_badge component in src/ui/pages/analysis.py
- [x] T029 [US3] Replace st.metric calls with styled metric_card component in src/ui/pages/analysis.py
- [x] T030 [US3] Add color-coded margin display (emerald positive, rose negative) in src/ui/pages/analysis.py
- [x] T031 [US3] Style single scenario result display with large status indicator in src/ui/pages/analysis.py

**Checkpoint**: User Story 3 complete - analysis results show status at a glance with color coding

---

## Phase 6: User Story 4 - Professional Heatmap Visualization (Priority: P2)

**Goal**: Heatmap displays with improved styling while maintaining functionality

**Independent Test**: Run grid analysis, verify heatmap in rounded container, status colors match theme, tooltip styled

### Implementation for User Story 4

- [x] T032 [US4] Update heatmap color constants to use theme colors in src/ui/components/heatmap_constants.py
- [x] T033 [US4] Update heatmap container styling (rounded, padded) in src/ui/components/heatmap.py
- [x] T034 [US4] Style view mode toggle bar in src/ui/components/heatmap.py
- [x] T035 [US4] Update tooltip styling to dark panel with organized layout in src/ui/components/heatmap.py
- [x] T036 [US4] Update Plotly chart template to use theme font family in src/ui/components/heatmap.py
- [x] T037 [P] [US4] Update heatmap summary panel styling in src/ui/components/heatmap_summary.py
- [x] T038 [P] [US4] Update heatmap detail panel styling in src/ui/components/heatmap_detail.py

**Checkpoint**: User Story 4 complete - heatmap has professional styling with theme integration

---

## Phase 7: User Story 5 - Enhanced Data Tables (Priority: P2)

**Goal**: Employee impact tables have professional styling with uppercase headers and constraint indicators

**Independent Test**: View employee impact data, verify headers uppercase with letter-spacing, rows have hover states, constraint icons colored

### Implementation for User Story 5

- [x] T039 [US5] Update table header styling (uppercase, tracking, background) in src/ui/components/employee_impact.py
- [x] T040 [US5] Update constraint status icons to use theme colors in src/ui/components/employee_impact.py
- [x] T041 [US5] Add table row hover state styling via CSS in src/ui/theme/css.py
- [x] T042 [US5] Update value formatting and cell padding in src/ui/components/employee_impact.py
- [x] T043 [P] [US5] Update results_table component styling in src/ui/components/results_table.py

**Checkpoint**: User Story 5 complete - tables have professional appearance with clear status indicators

---

## Phase 8: User Story 6 - Styled Export Interface (Priority: P3)

**Goal**: Export options display as visually distinct cards with accent borders

**Independent Test**: View export page, verify PDF and CSV options in separate styled cards with colored top borders, buttons styled

### Implementation for User Story 6

- [x] T044 [US6] Refactor export page to use card components for PDF/CSV options in src/ui/pages/export.py
- [x] T045 [US6] Add accent border styling (indigo for PDF, emerald for CSV) in src/ui/pages/export.py
- [x] T046 [US6] Add icons to export option cards in src/ui/pages/export.py
- [x] T047 [US6] Style export buttons with proper padding and hover effects in src/ui/pages/export.py

**Checkpoint**: User Story 6 complete - export interface has card-based visual distinction

---

## Phase 9: User Story 7 - Form Styling Improvements (Priority: P3)

**Goal**: Form controls have modern styling with accent colors

**Independent Test**: Interact with sliders/buttons throughout app, verify indigo accent on sliders, buttons have shadows and hover transitions

### Implementation for User Story 7

- [x] T048 [US7] Add slider accent color CSS (indigo active portion) in src/ui/theme/css.py
- [x] T049 [US7] Add button styling CSS (padding, border-radius, shadow, hover) in src/ui/theme/css.py
- [x] T050 [US7] Add input field styling CSS (border-radius, focus states) in src/ui/theme/css.py
- [x] T051 [US7] Add selectbox/dropdown styling CSS in src/ui/theme/css.py
- [x] T052 [US7] Add file uploader styling in src/ui/theme/css.py

**Checkpoint**: User Story 7 complete - all form controls have modern, consistent styling

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup, validation, and documentation

- [x] T053 Run existing test suite to verify no functional regressions
- [x] T054 [P] Add unit tests for theme color constants in tests/unit/ui/theme/test_colors.py
- [x] T055 [P] Add unit tests for CSS generation in tests/unit/ui/theme/test_css.py
- [x] T056 Create tests directory structure at tests/unit/ui/theme/
- [x] T057 Manual visual verification checklist per quickstart.md
- [x] T058 Update any hardcoded colors in existing components to use theme constants
- [x] T059 [P] Verify responsive behavior on narrow viewports
- [x] T060 [P] Document any Streamlit styling limitations encountered

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion - BLOCKS all user stories
- **User Stories (Phase 3-9)**: All depend on Foundational phase completion
  - P1 stories (US1, US2, US3) can proceed in parallel after Phase 2
  - P2 stories (US4, US5) can proceed after Phase 2
  - P3 stories (US6, US7) can proceed after Phase 2
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories - establishes base visual styling
- **User Story 2 (P1)**: Uses empty_state component from Phase 2; independent of US1
- **User Story 3 (P1)**: Uses status_badge and metric_card from Phase 2; independent of US1/US2
- **User Story 4 (P2)**: Uses theme colors; independent of P1 stories but enhances them
- **User Story 5 (P2)**: Uses theme colors; independent of other stories
- **User Story 6 (P3)**: Uses card component from Phase 2; independent of other stories
- **User Story 7 (P3)**: Pure CSS additions; independent of other stories

### Within Each User Story

- Tasks marked [P] can run in parallel (different files)
- Non-parallel tasks should run sequentially
- Story complete when all tasks done

### Parallel Opportunities

**Phase 1 (Setup)**: T002-T006 can run in parallel (different files)
**Phase 2 (Foundational)**: T010-T013 can run in parallel (different files)
**Phase 3 (US1)**: T019-T022 can run in parallel after T015-T018
**Phase 4 (US2)**: T026 can run parallel to T025
**Phase 6 (US4)**: T037-T038 can run in parallel
**Phase 7 (US5)**: T043 can run parallel to T039-T042
**Phase 10 (Polish)**: T054-T055, T059-T060 can run in parallel

---

## Parallel Example: Phase 1 Setup

```bash
# Launch all theme constant files together:
Task: "Create color palette constants in src/ui/theme/colors.py"
Task: "Create typography constants in src/ui/theme/typography.py"
Task: "Create spacing and border-radius constants in src/ui/theme/spacing.py"
Task: "Create shadow constants in src/ui/theme/shadows.py"
Task: "Create status configuration in src/ui/theme/status.py"
```

## Parallel Example: User Story 1

```bash
# After T018, launch all page updates together:
Task: "Update upload page to use card layouts in src/ui/pages/upload.py"
Task: "Update import wizard page to use card layouts in src/ui/pages/import_wizard.py"
Task: "Update analysis page to use card layouts in src/ui/pages/analysis.py"
Task: "Update export page to use card layouts in src/ui/pages/export.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Complete Phase 1: Setup (theme module)
2. Complete Phase 2: Foundational (base components)
3. Complete Phase 3: User Story 1 (professional appearance)
4. Complete Phase 4: User Story 2 (clear navigation)
5. Complete Phase 5: User Story 3 (status at a glance)
6. **STOP and VALIDATE**: Test US1-3 independently
7. Deploy/demo if ready - this is a functional MVP

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready
2. Add User Story 1 -> Test -> Deploy (basic styling visible)
3. Add User Story 2 -> Test -> Deploy (navigation improved)
4. Add User Story 3 -> Test -> Deploy (analysis results styled)
5. Add User Story 4 -> Test -> Deploy (heatmap polished)
6. Add User Story 5 -> Test -> Deploy (tables improved)
7. Add User Story 6 -> Test -> Deploy (export styled)
8. Add User Story 7 -> Test -> Deploy (forms polished)
9. Polish phase -> Final validation

### Suggested MVP Scope

- Phase 1: Setup (T001-T009)
- Phase 2: Foundational (T010-T014)
- Phase 3: User Story 1 (T015-T022)

**Total MVP Tasks**: 22 tasks

This delivers professional appearance as a demonstrable increment before tackling navigation, results styling, etc.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story can be independently completed and visually verified
- Visual verification is manual per spec (no automated visual tests)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All styling uses CSS injection - no JavaScript required
