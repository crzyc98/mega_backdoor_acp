# Tasks: Heatmap Exploration

**Input**: Design documents from `/specs/005-heatmap-exploration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create shared models, constants, and prepare component structure

- [x] T001 [P] Create heatmap constants module with colors and icons in src/ui/components/heatmap_constants.py
- [x] T002 [P] Create heatmap models module with HeatmapViewMode, HeatmapState, HeatmapFocusState in src/ui/components/heatmap_models.py
- [x] T003 [P] Create TooltipData and HeatmapCellDisplay models in src/ui/components/heatmap_models.py
- [x] T004 [P] Create HeatmapSummaryDisplay and MarginCoordinate models in src/ui/components/heatmap_models.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Refactor existing heatmap.py to support view mode switching and shared rendering infrastructure

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Backup and refactor existing render_heatmap() to support view mode parameter in src/ui/components/heatmap.py
- [x] T006 Add view mode selector (radio buttons) to heatmap component in src/ui/components/heatmap.py
- [x] T007 Create helper function to build data matrices from GridResult in src/ui/components/heatmap.py
- [x] T008 Initialize HeatmapState in session_state in src/ui/components/heatmap.py
- [x] T009 Update analysis.py to pass GridResult to enhanced heatmap in src/ui/pages/analysis.py

**Checkpoint**: Foundation ready - view mode selector appears but only Pass/Fail mode works

---

## Phase 3: User Story 1 - View Pass/Fail Heatmap (Priority: P1) 🎯 MVP

**Goal**: Display color-coded heatmap with PASS/RISK/FAIL/ERROR status colors and accessibility icons

**Independent Test**: Load a grid result and verify cells show correct colors (green/yellow/red/gray) with status icons (✓/⚠/✗/?)

### Implementation for User Story 1

- [x] T010 [US1] Implement _render_pass_fail_heatmap() function with status-based coloring in src/ui/components/heatmap.py
- [x] T011 [US1] Add status icons (✓, ⚠, ✗, ?) as text annotations to cells in src/ui/components/heatmap.py
- [x] T012 [US1] Configure axis labels with percentage formatting (X: contribution, Y: adoption) in src/ui/components/heatmap.py
- [x] T013 [US1] Ensure icon contrast against background colors meets WCAG requirements in src/ui/components/heatmap.py
- [x] T014 [US1] Handle ERROR scenarios with gray cells and question mark icon in src/ui/components/heatmap.py

**Checkpoint**: Pass/Fail heatmap fully functional with accessibility icons - MVP complete

---

## Phase 4: User Story 2 - View Margin Heatmap (Priority: P1)

**Goal**: Display gradient heatmap showing margin values with color scale legend

**Independent Test**: Load a grid and verify gradient coloring reflects margin magnitude (green positive, red negative) with numeric labels

### Implementation for User Story 2

- [x] T015 [US2] Implement _render_margin_heatmap() function with RdYlGn gradient in src/ui/components/heatmap.py
- [x] T016 [US2] Add numeric margin labels to each cell formatted as "+X.XX" or "-X.XX" in src/ui/components/heatmap.py
- [x] T017 [US2] Configure color scale legend with min/zero/max tick marks in src/ui/components/heatmap.py
- [x] T018 [US2] Handle ERROR cells with gray background and "ERR" label in src/ui/components/heatmap.py
- [x] T019 [US2] Set dynamic zmin/zmax based on actual margin range with zero at midpoint in src/ui/components/heatmap.py

**Checkpoint**: Margin heatmap shows gradient with numeric values and legend

---

## Phase 5: User Story 4 - Hover Tooltips (Priority: P1)

**Goal**: Display detailed scenario information on cell hover within 200ms

**Independent Test**: Hover over cells and verify tooltip shows all required fields (status, rates, margin, ACPs, threshold, limiting bound)

### Implementation for User Story 4

- [x] T020 [P] [US4] Create heatmap_tooltip.py with TooltipData.to_hover_html() implementation in src/ui/components/heatmap_tooltip.py
- [x] T021 [US4] Build hover text matrix from scenario results for Plotly hovertemplate in src/ui/components/heatmap.py
- [x] T022 [US4] Configure tooltip positioning to avoid viewport overflow in src/ui/components/heatmap.py
- [x] T023 [US4] Handle ERROR cells with error_message in tooltip instead of ACP values in src/ui/components/heatmap_tooltip.py
- [x] T024 [US4] Set tooltip timing (200ms appear, 300ms dismiss delay) via Plotly config in src/ui/components/heatmap.py

**Checkpoint**: Tooltips appear on hover with complete scenario details

---

## Phase 6: User Story 5 - Click to View Scenario Detail (Priority: P1)

**Goal**: Open slide-out detail panel showing all ScenarioResult fields when cell is clicked

**Independent Test**: Click a cell and verify sidebar panel opens with formatted values; press Escape to close

### Implementation for User Story 5

- [x] T025 [P] [US5] Create heatmap_detail.py with render_detail_panel() function in src/ui/components/heatmap_detail.py
- [x] T026 [US5] Implement value formatting (percentages 2dp, currency with commas, status with icon) in src/ui/components/heatmap_detail.py
- [x] T027 [US5] Add click event handling to set selected_cell in session_state in src/ui/components/heatmap.py
- [x] T028 [US5] Render detail panel in st.sidebar when cell selected in src/ui/components/heatmap.py
- [x] T029 [US5] Implement close button and Escape key handling to dismiss panel in src/ui/components/heatmap_detail.py
- [x] T030 [US5] Handle ERROR cells with prominent error_message display in src/ui/components/heatmap_detail.py

**Checkpoint**: Click opens sidebar panel; Escape/close button dismisses it

---

## Phase 7: User Story 3 - View Risk Zone Heatmap (Priority: P2)

**Goal**: Highlight RISK-status cells with emphasis styling; dim non-RISK cells

**Independent Test**: Select Risk Zone view and verify RISK cells are prominently highlighted while others are dimmed

### Implementation for User Story 3

- [x] T031 [US3] Implement _render_risk_zone_heatmap() function in src/ui/components/heatmap.py
- [x] T032 [US3] Apply dimmed opacity (0.5) to non-RISK cells in Risk Zone mode in src/ui/components/heatmap.py
- [x] T033 [US3] Add CSS for pulsing border animation on RISK cells via st.markdown in src/ui/components/heatmap.py
- [x] T034 [US3] Display "X scenarios in risk zone" count above heatmap in src/ui/components/heatmap.py

**Checkpoint**: Risk Zone view highlights RISK cells with emphasis styling

---

## Phase 8: User Story 6 - View Summary Statistics (Priority: P2)

**Goal**: Display aggregate statistics panel with status counts, margin stats, and derived insights

**Independent Test**: Load a grid and verify summary shows correct counts and margin statistics matching GridSummary

### Implementation for User Story 6

- [x] T035 [P] [US6] Create heatmap_summary.py with render_summary_panel() function in src/ui/components/heatmap_summary.py
- [x] T036 [US6] Implement status counts row (Pass/Risk/Fail/Error/Total) using st.metric in src/ui/components/heatmap_summary.py
- [x] T037 [US6] Calculate min/max/avg margin with coordinates from scenarios list in src/ui/components/heatmap_summary.py
- [x] T038 [US6] Add expandable margin details section with coordinates in src/ui/components/heatmap_summary.py
- [x] T039 [US6] Display max safe contribution and first failure point insights in src/ui/components/heatmap_summary.py
- [x] T040 [US6] Integrate summary panel above heatmap in render_heatmap() in src/ui/components/heatmap.py

**Checkpoint**: Summary panel shows all required statistics above heatmap

---

## Phase 9: User Story 7 - Keyboard Navigation (Priority: P2)

**Goal**: Enable keyboard navigation with visible focus indicator and accessible tooltips

**Independent Test**: Tab into heatmap, use arrow keys to navigate, Enter/Space to open details, verify focus ring visible

### Implementation for User Story 7

- [x] T041 [P] [US7] Add focus state CSS (2px blue border) via st.markdown in src/ui/components/heatmap.py
- [x] T042 [US7] Implement keyboard event handler via st.components.html() in src/ui/components/heatmap.py
- [x] T043 [US7] Add arrow key navigation logic updating HeatmapFocusState in src/ui/components/heatmap.py
- [x] T044 [US7] Implement Enter/Space key to open detail panel for focused cell in src/ui/components/heatmap.py
- [x] T045 [US7] Add keyboard-accessible tooltips (500ms focus delay) in src/ui/components/heatmap.py
- [x] T046 [US7] Create keyboard shortcuts help overlay ("?" or "H" key) in src/ui/components/heatmap.py
- [x] T047 [US7] Ensure focus returns to cell after detail panel closes in src/ui/components/heatmap.py

**Checkpoint**: Full keyboard navigation works with visible focus and accessible tooltips

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, performance, and documentation

- [x] T048 [P] Handle all-ERROR grid scenario (show "N/A" for margin stats) in src/ui/components/heatmap_summary.py
- [x] T049 [P] Handle missing scenarios (gaps in grid) with dashed border and "No data" tooltip in src/ui/components/heatmap.py
- [x] T050 [P] Add large grid handling (50×50) with axis tick decimation in src/ui/components/heatmap.py
- [x] T051 [P] Implement tooltip debouncing for rapid mouse movement in src/ui/components/heatmap.py
- [x] T052 Verify WCAG 2.1 AA color contrast for all text/icons in src/ui/components/heatmap_constants.py
- [ ] T053 Performance test: verify <1s render for 25×25 grid
- [ ] T054 Run quickstart.md validation and update if needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-9)**: All depend on Foundational phase completion
  - P1 stories (US1, US2, US4, US5) should complete before P2 stories
  - Within P1: US1 (Pass/Fail) is MVP; US2/US4/US5 can proceed in parallel after
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

| Story | Priority | Depends On | Can Parallel With |
|-------|----------|------------|-------------------|
| US1 Pass/Fail | P1 | Foundation | - |
| US2 Margin | P1 | US1 (for refactored render) | US4, US5 |
| US4 Tooltips | P1 | US1 | US2, US5 |
| US5 Detail Panel | P1 | US1 | US2, US4 |
| US3 Risk Zone | P2 | US1 | US6, US7 |
| US6 Summary | P2 | US1 | US3, US7 |
| US7 Keyboard | P2 | US5 (for detail panel) | US3, US6 |

### Within Each User Story

- Models/constants before implementation
- Core rendering before integration
- Basic functionality before edge cases

### Parallel Opportunities

**Setup Phase (all parallel)**:
```
T001: heatmap_constants.py
T002: heatmap_models.py (enums, state)
T003: heatmap_models.py (cell display, tooltip)
T004: heatmap_models.py (summary display)
```

**After US1 Complete (P1 stories parallel)**:
```
T015-T019: US2 Margin heatmap
T020-T024: US4 Tooltips
T025-T030: US5 Detail panel
```

**After P1 Complete (P2 stories parallel)**:
```
T031-T034: US3 Risk Zone
T035-T040: US6 Summary
T041-T047: US7 Keyboard (after US5)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T009)
3. Complete Phase 3: User Story 1 - Pass/Fail Heatmap (T010-T014)
4. **STOP and VALIDATE**: Test Pass/Fail heatmap with icons independently
5. Deploy/demo if ready - this is the MVP!

### Incremental Delivery (Recommended)

1. **MVP**: Setup + Foundation + US1 → Deployable Pass/Fail heatmap
2. **Enhanced Views**: Add US2 (Margin) + US4 (Tooltips) → Richer exploration
3. **Drill-down**: Add US5 (Detail Panel) → Complete interaction model
4. **P2 Features**: Add US3/US6/US7 → Full feature set
5. **Polish**: Edge cases, performance, accessibility audit

### Task Counts by User Story

| Story | Tasks | Files Modified |
|-------|-------|----------------|
| Setup | 4 | 2 new files |
| Foundational | 5 | 2 files |
| US1 Pass/Fail | 5 | 1 file |
| US2 Margin | 5 | 1 file |
| US3 Risk Zone | 4 | 1 file |
| US4 Tooltips | 5 | 2 files |
| US5 Detail | 6 | 2 files |
| US6 Summary | 6 | 2 files |
| US7 Keyboard | 7 | 1 file |
| Polish | 7 | 3 files |
| **Total** | **54** | |

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently testable after completion
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Existing heatmap.py is being enhanced, not replaced - preserve backward compatibility
