# Feature Specification: Heatmap Exploration

**Feature Branch**: `005-heatmap-exploration`
**Created**: 2026-01-13
**Status**: Draft
**Input**: User description: "Create Heatmap Exploration for scenario grids: users can view Pass/Fail, Margin, and Risk Zone heatmaps over the (adoption x contribution) grid, hover for tooltips, and click a cell to see the underlying scenario detail. Define what each heatmap must display, how the axes are labeled, how missing/invalid scenarios are handled, and what summary stats are shown (min/max/avg margin, safe/risk/fail counts). Include accessibility requirements (keyboard nav + non-color cues) and acceptance criteria."

## Clarifications

### Session 2026-01-13

- Q: Should the detail panel be a slide-out or modal? → A: Slide-out panel (heatmap stays visible alongside details)

## Overview

This feature provides interactive heatmap visualizations for exploring ACP scenario analysis results. Building on the scenario analysis engine (spec 004), it enables analysts to visually comprehend pass/fail patterns, margin distributions, and risk zones across the adoption × contribution parameter space. The heatmaps support multiple view modes, accessible interactions, and drill-down to individual scenario details.

## User Scenarios & Testing

### User Story 1 - View Pass/Fail Heatmap (Priority: P1)

An analyst views a color-coded heatmap showing which adoption/contribution combinations pass, are at risk, or fail the ACP test, allowing them to immediately identify the compliance landscape.

**Why this priority**: This is the foundational visualization that provides immediate actionable insight. Understanding which scenarios pass or fail is the primary use case for grid analysis.

**Independent Test**: Can be fully tested by loading a completed grid result and verifying the heatmap renders with correct colors for each known PASS/RISK/FAIL/ERROR cell.

**Acceptance Scenarios**:

1. **Given** a completed grid analysis with 25 scenarios (5 adoption rates × 5 contribution rates), **When** the analyst opens the Pass/Fail heatmap view, **Then** the system displays a 5×5 grid where each cell is colored according to its status: green for PASS, yellow for RISK, red for FAIL, and gray for ERROR.

2. **Given** a Pass/Fail heatmap is displayed, **When** the analyst views the grid, **Then** the X-axis displays contribution rates (ascending left-to-right) and the Y-axis displays adoption rates (ascending bottom-to-top), with clear numeric labels at each axis tick.

3. **Given** a heatmap is displayed, **When** the analyst views any cell, **Then** each cell includes a non-color indicator (icon or pattern) to distinguish status for colorblind users: checkmark for PASS, warning triangle for RISK, X for FAIL, and question mark for ERROR.

---

### User Story 2 - View Margin Heatmap (Priority: P1)

An analyst views a gradient heatmap showing the margin values across the grid, enabling identification of how far each scenario is from the compliance threshold.

**Why this priority**: Margin values reveal the "safety buffer" at each point, which is critical for making conservative contribution recommendations.

**Independent Test**: Can be tested by loading a grid with known margin values and verifying the gradient coloring correctly reflects margin magnitude.

**Acceptance Scenarios**:

1. **Given** a completed grid analysis, **When** the analyst selects the Margin heatmap view, **Then** the system displays a gradient-colored grid where cell color intensity represents margin value: deeper green for larger positive margins (safer), transitioning to yellow near zero, and deeper red for larger negative margins (worse failures).

2. **Given** a Margin heatmap, **When** displayed, **Then** a legend is shown indicating the color scale with numeric values at key points (minimum margin, zero, maximum margin).

3. **Given** a Margin heatmap, **When** viewing cells, **Then** each cell displays the numeric margin value directly within the cell (e.g., "+1.25" or "-0.50") in addition to the color coding.

---

### User Story 3 - View Risk Zone Heatmap (Priority: P2)

An analyst views a heatmap that highlights the "risk zone" - scenarios that pass but are dangerously close to failure - to identify where caution is needed.

**Why this priority**: Risk zone visualization helps analysts avoid recommending contribution rates that technically pass but could fail with minor data changes.

**Independent Test**: Can be tested by loading a grid with known RISK-status scenarios and verifying they are prominently highlighted.

**Acceptance Scenarios**:

1. **Given** a completed grid analysis with several RISK-status scenarios, **When** the analyst selects the Risk Zone heatmap view, **Then** RISK cells are prominently highlighted (e.g., bright amber with pulsing border or distinct pattern), PASS cells are dimmed green, FAIL cells are dimmed red, and ERROR cells are gray.

2. **Given** a Risk Zone heatmap, **When** displayed, **Then** a summary count appears showing "X scenarios in risk zone" prominently above the heatmap.

---

### User Story 4 - Hover Tooltips (Priority: P1)

An analyst hovers over any cell to see detailed information about that scenario without leaving the heatmap view.

**Why this priority**: Tooltips enable rapid exploration without the friction of clicking through to detail views for every cell.

**Independent Test**: Can be tested by hovering over cells with known values and verifying tooltip content matches expected scenario data.

**Acceptance Scenarios**:

1. **Given** any heatmap is displayed, **When** the analyst hovers over a cell, **Then** a tooltip appears within 200ms showing: Status (with icon), Adoption Rate (%), Contribution Rate (%), Margin (percentage points), HCE ACP (%), NHCE ACP (%), Threshold (%), and Limiting Bound (MULTIPLE or ADDITIVE).

2. **Given** an ERROR cell, **When** the analyst hovers over it, **Then** the tooltip displays the error message explaining why the scenario could not be calculated.

3. **Given** a tooltip is displayed, **When** the analyst moves the mouse away from the cell, **Then** the tooltip dismisses after a brief delay (300ms) to prevent flickering during mouse movement.

---

### User Story 5 - Click to View Scenario Detail (Priority: P1)

An analyst clicks on any cell to see the complete scenario details in an expanded view, including all output fields from the scenario result.

**Why this priority**: Drill-down capability is essential for analysts who need to understand or explain specific scenarios to stakeholders.

**Independent Test**: Can be tested by clicking on a cell and verifying the detail panel displays all ScenarioResult fields correctly.

**Acceptance Scenarios**:

1. **Given** any heatmap is displayed, **When** the analyst clicks on a cell, **Then** a slide-out detail panel opens (keeping heatmap visible) displaying all ScenarioResult fields: status, nhce_acp, hce_acp, max_allowed_acp, margin, limiting_bound, hce_contributor_count, nhce_contributor_count, total_mega_backdoor_amount, and seed_used.

2. **Given** a detail panel is open, **When** the analyst views it, **Then** values are formatted for readability: percentages show 2 decimal places with "%" suffix, dollar amounts show currency formatting with commas, and status shows with icon and color.

3. **Given** a detail panel is open, **When** the analyst clicks outside the panel or presses Escape, **Then** the panel closes and focus returns to the previously selected cell in the heatmap.

4. **Given** an ERROR cell is clicked, **When** the detail panel opens, **Then** the error_message is prominently displayed with an explanation of the condition that caused the error.

---

### User Story 6 - View Summary Statistics (Priority: P2)

An analyst views aggregate statistics for the grid alongside the heatmap, providing quick insight without manual counting.

**Why this priority**: Summary statistics contextualize the heatmap and provide key metrics that stakeholders often request.

**Independent Test**: Can be tested by loading a grid with known distributions and verifying all summary statistics match expected values.

**Acceptance Scenarios**:

1. **Given** any heatmap is displayed, **When** the analyst views the summary panel, **Then** the following statistics are shown: Pass Count, Risk Count, Fail Count, Error Count, Total Scenario Count.

2. **Given** a summary panel, **When** viewed, **Then** margin statistics are displayed: Minimum Margin (with scenario coordinates), Maximum Margin (with scenario coordinates), Average Margin (across all non-ERROR scenarios).

3. **Given** a summary panel, **When** viewed, **Then** the following derived insights are shown: Max Safe Contribution Rate (at 100% adoption), First Failure Point (adoption %, contribution %).

---

### User Story 7 - Keyboard Navigation (Priority: P2)

An analyst navigates the heatmap using keyboard controls for accessibility and power-user efficiency.

**Why this priority**: Accessibility is a requirement, and keyboard navigation also improves efficiency for analysts who prefer not to use a mouse.

**Independent Test**: Can be tested by navigating the grid using only keyboard inputs and verifying all cells are reachable and interactive.

**Acceptance Scenarios**:

1. **Given** the heatmap has focus, **When** the analyst presses Tab, **Then** focus moves to the first cell (top-left) with a visible focus indicator (2px solid border, contrasting color).

2. **Given** a cell has focus, **When** the analyst presses Arrow keys (Up/Down/Left/Right), **Then** focus moves to the adjacent cell in that direction, wrapping at grid boundaries.

3. **Given** a cell has focus, **When** the analyst presses Enter or Space, **Then** the detail panel opens for that cell (equivalent to click).

4. **Given** a cell has focus, **When** the analyst hovers or waits 500ms, **Then** the tooltip appears for the focused cell (keyboard-accessible tooltips).

5. **Given** the heatmap has focus, **When** the analyst presses "?" or "H", **Then** a keyboard shortcut help overlay appears listing all available shortcuts.

---

### Edge Cases

- What happens when a grid result has all ERROR scenarios? The heatmap displays all gray cells with icons, summary shows 0 PASS/RISK/FAIL, and margin statistics show "N/A" since no valid margins exist.
- What happens when grid dimensions are very large (e.g., 50×50)? The heatmap supports zooming and panning, cell labels may be hidden until zoomed, and axis labels show every Nth tick to prevent overlap.
- What happens when a single row or column is loaded (1×N or N×1 grid)? The heatmap renders as a single row or column with appropriate axis scaling.
- What happens when margin values have extreme range (e.g., -50% to +10%)? The gradient scale adjusts dynamically with zero clearly marked, and the legend updates to show the actual range.
- What happens when the user quickly moves between cells? Tooltips debounce to prevent performance issues; only the final hovered cell's tooltip is shown.

## Requirements

### Functional Requirements

#### Heatmap Display

- **FR-001**: System MUST display heatmap grid with contribution rates on the X-axis (ascending left-to-right) and adoption rates on the Y-axis (ascending bottom-to-top).
- **FR-002**: System MUST label both axes with numeric percentage values at each grid line, formatted as "XX%" (e.g., "50%", "100%").
- **FR-003**: System MUST size cells proportionally to fit the available viewport while maintaining square aspect ratio for each cell.
- **FR-004**: System MUST support three heatmap view modes: Pass/Fail, Margin, and Risk Zone.

#### Pass/Fail Heatmap

- **FR-005**: System MUST color cells by status: green (#22C55E) for PASS, amber (#F59E0B) for RISK, red (#EF4444) for FAIL, gray (#9CA3AF) for ERROR.
- **FR-006**: System MUST display a status icon within each cell: checkmark for PASS, warning triangle for RISK, X-mark for FAIL, question mark for ERROR.
- **FR-007**: System MUST ensure icons have sufficient contrast against cell background colors for visibility.

#### Margin Heatmap

- **FR-008**: System MUST display a continuous color gradient from green (positive margins) through yellow (near zero) to red (negative margins).
- **FR-009**: System MUST display the numeric margin value within each cell, formatted as "+X.XX" or "-X.XX" percentage points.
- **FR-010**: System MUST display a color legend showing the gradient scale with labeled tick marks at minimum, zero, and maximum values.
- **FR-011**: System MUST display ERROR cells as gray with "ERR" label instead of a margin value.

#### Risk Zone Heatmap

- **FR-012**: System MUST visually emphasize RISK-status cells using high-contrast styling (e.g., bold border, pattern overlay, or animation).
- **FR-013**: System MUST display non-RISK cells with reduced visual prominence (dimmed colors or lower opacity).
- **FR-014**: System MUST display a prominent count of RISK scenarios above the heatmap (e.g., "3 scenarios in risk zone").

#### Tooltips

- **FR-015**: System MUST display tooltips on mouse hover within 200ms of cursor entering a cell.
- **FR-016**: Tooltip MUST contain: Status (with icon), Adoption Rate, Contribution Rate, Margin, HCE ACP, NHCE ACP, Max Allowed ACP (threshold), and Limiting Bound.
- **FR-017**: Tooltip for ERROR cells MUST display the error_message instead of ACP values.
- **FR-018**: System MUST dismiss tooltips 300ms after cursor leaves the cell, unless cursor enters another cell first.
- **FR-019**: System MUST position tooltips to avoid viewport overflow (flip positioning as needed).

#### Cell Detail View

- **FR-020**: System MUST open a slide-out detail panel when a cell is clicked, keeping the heatmap visible alongside the panel and displaying all ScenarioResult fields.
- **FR-021**: Detail panel MUST format values for readability: percentages to 2 decimal places with "%" suffix, currency with "$" prefix and comma separators, counts as integers.
- **FR-022**: Detail panel MUST be dismissible via Escape key, clicking outside, or close button.
- **FR-023**: System MUST return keyboard focus to the clicked cell after detail panel closes.

#### Summary Statistics

- **FR-024**: System MUST display summary statistics panel alongside (or above/below) the heatmap.
- **FR-025**: Summary MUST include status counts: Pass Count, Risk Count, Fail Count, Error Count, Total Count.
- **FR-026**: Summary MUST include margin statistics: Minimum Margin (with coordinates), Maximum Margin (with coordinates), Average Margin (excluding ERROR scenarios).
- **FR-027**: Summary MUST include insights: Max Safe Contribution Rate (at highest adoption rate tested), First Failure Point coordinates (or "None" if all pass).

#### Accessibility

- **FR-028**: System MUST support keyboard navigation: Tab to enter grid, Arrow keys to move between cells, Enter/Space to activate.
- **FR-029**: System MUST display visible focus indicator (2px solid border in contrasting color) on focused cell.
- **FR-030**: System MUST provide keyboard-accessible tooltips that appear after 500ms of focus on a cell.
- **FR-031**: System MUST provide non-color visual indicators (icons, patterns, or labels) to distinguish statuses for colorblind users.
- **FR-032**: System MUST meet WCAG 2.1 AA color contrast requirements for all text and meaningful graphics.
- **FR-033**: System MUST provide a keyboard shortcuts help overlay accessible via "?" or "H" key.

#### Missing/Invalid Scenario Handling

- **FR-034**: System MUST render ERROR scenarios as gray cells with a question mark icon.
- **FR-035**: System MUST exclude ERROR scenarios from margin statistics calculations (average, min, max).
- **FR-036**: System MUST display error_message in both tooltip and detail view for ERROR cells.
- **FR-037**: If grid has gaps (missing scenarios), system MUST render empty cells as gray with dashed border and "No data" tooltip.

### Key Entities

- **HeatmapViewMode**: Enumeration of available visualization modes
  - PASS_FAIL: Status-based categorical coloring
  - MARGIN: Continuous gradient based on margin value
  - RISK_ZONE: Emphasis on RISK-status scenarios

- **HeatmapCell**: Display representation of a single scenario in the grid
  - row_index: Position in the grid (adoption rate axis)
  - col_index: Position in the grid (contribution rate axis)
  - scenario_result: Reference to underlying ScenarioResult (from spec 004)
  - display_color: Calculated color based on current view mode
  - display_icon: Icon appropriate for status and view mode
  - display_label: Optional text label for cell (margin value in Margin view)

- **HeatmapSummary**: Aggregate statistics for the displayed grid
  - pass_count: Number of PASS scenarios
  - risk_count: Number of RISK scenarios
  - fail_count: Number of FAIL scenarios
  - error_count: Number of ERROR scenarios
  - total_count: Total scenarios in grid
  - min_margin: Smallest margin value (with coordinates)
  - max_margin: Largest margin value (with coordinates)
  - avg_margin: Average margin across non-ERROR scenarios
  - max_safe_contribution: Highest passing contribution rate at max adoption
  - first_failure_point: Coordinates of first failure (or null)

- **TooltipContent**: Data displayed in cell hover tooltip
  - status: Scenario status with icon
  - adoption_rate: Y-axis value
  - contribution_rate: X-axis value
  - margin: Distance from threshold
  - hce_acp: HCE Actual Contribution Percentage
  - nhce_acp: NHCE Actual Contribution Percentage
  - threshold: Max allowed ACP
  - limiting_bound: Which test determined threshold
  - error_message: Present only for ERROR status

## Success Criteria

### Usability

- **SC-001**: Users can identify passing vs. failing regions within 5 seconds of viewing the heatmap
- **SC-002**: Users can find the maximum safe contribution rate within 10 seconds using the summary panel or heatmap exploration
- **SC-003**: 95% of user interactions (hover, click, keyboard) receive visual feedback within 200ms

### Accessibility

- **SC-004**: All heatmap functionality is operable using keyboard-only navigation
- **SC-005**: Status information is distinguishable without relying solely on color (icons, patterns, or labels present)
- **SC-006**: Text and graphic elements meet WCAG 2.1 AA contrast ratio requirements (4.5:1 for text, 3:1 for graphics)

### Completeness

- **SC-007**: All three heatmap view modes (Pass/Fail, Margin, Risk Zone) display correctly for any valid grid result
- **SC-008**: Summary statistics match grid summary values from scenario analysis engine with 100% accuracy
- **SC-009**: Tooltips display complete scenario information for 100% of cells (including ERROR cells)

### Performance

- **SC-010**: Heatmap renders within 1 second for grids up to 25×25 (625 scenarios)
- **SC-011**: Tooltips appear within 200ms of hover initiation
- **SC-012**: View mode switching (between Pass/Fail, Margin, Risk Zone) completes within 500ms

## Assumptions

- GridResult data from the scenario analysis engine (spec 004) is available and correctly populated before heatmap display
- The heatmap component receives pre-computed GridResult and GridSummary; it does not execute scenario calculations
- Users have modern browsers supporting CSS Grid, CSS Variables, and standard accessibility APIs
- Grid dimensions are reasonable for interactive display (typically up to 20×20; larger grids may require scrolling/panning)
- Margin values are in percentage points (not percentages) as defined in spec 004

## Dependencies

- **Spec 004 (Scenario Analysis)**: Provides GridResult and GridSummary data structures that this feature visualizes
- **Spec 002 (Census Management)**: Provides census data context for scenario results (indirectly via spec 004)

## Out of Scope

- Running or re-running scenario calculations (this feature only visualizes existing results)
- Exporting heatmap as image or PDF (may be added in future feature)
- Comparing multiple grid results side-by-side
- Filtering or excluding specific scenarios from the heatmap display
- Custom color theme configuration
- 3D visualization or additional chart types
