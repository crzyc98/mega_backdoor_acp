# Feature Specification: Employee-Level Impact Views

**Feature Branch**: `006-employee-level-impact`
**Created**: 2026-01-13
**Status**: Draft
**Input**: User description: "Add Employee-Level Impact views: for a selected scenario, the user can see employee-level details separated by HCE and NHCE, including compensation, existing contributions (by type), §415(c) limit, available room, and computed mega-backdoor amount. The experience should support sorting/filtering and make it easy to explain why the ACP result looks the way it does (e.g., how many HCEs are constrained by limits). Define acceptance criteria for transparency, interpretability, and exportability of these details."

## Clarifications

### Session 2026-01-13

- Q: How should the HCE and NHCE panels be arranged? → A: Tabbed panels (switch between HCE and NHCE views)
- Q: What format should "Export All" produce? → A: Single CSV file with "Group" column (HCE/NHCE identifier per row)
- Q: What happens if scenario was run without debug_details? → A: Fetch participant data from census and compute employee impact on demand

## Overview

This feature provides employee-level transparency into how individual participants contribute to an ACP test outcome. When viewing a scenario result, users can drill down to see each employee's compensation, existing contributions by type, regulatory limits, available headroom, and computed mega-backdoor amount. The view separates HCEs and NHCEs into distinct panels and provides sorting, filtering, and export capabilities. The goal is to make ACP results fully explainable by showing exactly which employees are constrained by limits and how individual contributions roll up to the aggregate ACP percentages.

## User Scenarios & Testing

### User Story 1 - View Employee Details for Selected Scenario (Priority: P1)

An analyst viewing a scenario result (from the heatmap or scenario runner) can drill down to see a tabular view of all employees with their individual contribution details, separated by HCE and NHCE groups.

**Why this priority**: This is the foundational capability. Without employee-level visibility, analysts cannot explain or audit ACP results to stakeholders or regulators.

**Independent Test**: Can be fully tested by selecting a scenario with known participants and verifying all participant rows appear with correct values matching census data plus computed mega-backdoor amounts.

**Acceptance Scenarios**:

1. **Given** a completed scenario result, **When** the analyst clicks "View Employee Details," **Then** the system displays a tabbed view with "HCEs" tab active by default, showing all HCE participants; a second "NHCEs" tab allows switching to view NHCE participants.

2. **Given** the employee detail view is displayed, **When** the analyst views an HCE row, **Then** the following columns are visible: Employee ID (anonymized), Compensation, Deferral Contributions, Match Contributions, After-Tax Contributions, §415(c) Limit, Available Room, Mega-Backdoor Amount, Individual ACP, and Constraint Status.

3. **Given** the employee detail view is displayed, **When** the analyst views an NHCE row, **Then** the following columns are visible: Employee ID (anonymized), Compensation, Deferral Contributions, Match Contributions, After-Tax Contributions, and Individual ACP.

4. **Given** an HCE who was selected for mega-backdoor contributions, **When** viewing that row, **Then** the Mega-Backdoor Amount shows the computed contribution value, and Constraint Status indicates whether they received the full amount or were capped.

---

### User Story 2 - Sort Employee Data (Priority: P1)

An analyst can sort employee tables by any column to quickly identify outliers, highest contributors, or employees most constrained by limits.

**Why this priority**: Sorting is essential for quickly identifying patterns and outliers in large census data without manual scanning.

**Independent Test**: Can be tested by clicking column headers and verifying rows reorder correctly in ascending/descending order.

**Acceptance Scenarios**:

1. **Given** the HCE employee detail view, **When** the analyst clicks the "Compensation" column header, **Then** rows are sorted by compensation in ascending order; clicking again reverses to descending order.

2. **Given** any employee table, **When** a column is sorted, **Then** a visual indicator (arrow icon) shows the current sort direction.

3. **Given** the HCE employee detail view, **When** the analyst sorts by "Available Room," **Then** HCEs with $0 available room (fully constrained) appear at the top in ascending sort, making it easy to identify limit-bound participants.

---

### User Story 3 - Filter Employee Data (Priority: P2)

An analyst can apply filters to focus on specific subsets of employees, such as only those at the §415(c) limit or those with mega-backdoor contributions above a threshold.

**Why this priority**: Filtering helps analysts focus analysis and quickly answer specific questions like "How many HCEs hit the limit?"

**Independent Test**: Can be tested by applying filters and verifying only matching rows remain visible with correct counts displayed.

**Acceptance Scenarios**:

1. **Given** the HCE employee detail view, **When** the analyst applies the filter "Constraint Status = At Limit," **Then** only HCEs whose mega-backdoor contribution was capped by §415(c) are displayed.

2. **Given** any filter is applied, **When** viewing the table header, **Then** a badge or count shows "Showing X of Y employees" to indicate filter is active.

3. **Given** the HCE employee detail view, **When** the analyst applies a compensation range filter (e.g., $150,000 - $250,000), **Then** only employees within that compensation range are displayed.

4. **Given** filters are active, **When** the analyst clicks "Clear Filters," **Then** all filters are removed and the full employee list is restored.

---

### User Story 4 - Understand Limit Constraints (Priority: P1)

An analyst can quickly see aggregated statistics about limit constraints, including how many HCEs are at the §415(c) limit, how many received reduced mega-backdoor amounts, and the total impact of constraints.

**Why this priority**: Understanding limit constraints is critical for explaining why ACP results differ from what might be expected at face value.

**Independent Test**: Can be tested by computing expected constraint counts from known census data and verifying displayed summary matches.

**Acceptance Scenarios**:

1. **Given** the employee detail view for HCEs, **When** viewing the summary panel, **Then** the following statistics are displayed: Total HCE Count, Count at §415(c) Limit, Count with Reduced Mega-Backdoor, Average Available Room, and Total Mega-Backdoor Amount.

2. **Given** an HCE is "at limit," **When** viewing their row, **Then** a tooltip or icon explains: "This employee's total contributions reached the §415(c) annual additions limit of $XX,XXX. Their mega-backdoor contribution was reduced from [requested] to [actual]."

3. **Given** the constraint summary, **When** the analyst hovers over "Count at Limit," **Then** a breakdown appears showing the distribution of constraint reasons (e.g., "12 at §415(c) limit, 3 below minimum headroom threshold").

---

### User Story 5 - Export Employee Details (Priority: P2)

An analyst can export the employee-level detail view to CSV for further analysis, audit documentation, or sharing with stakeholders who need offline access.

**Why this priority**: Exportability is essential for audit trails, external analysis, and stakeholder communication.

**Independent Test**: Can be tested by exporting data and verifying the CSV file contains all visible columns and correctly formatted values.

**Acceptance Scenarios**:

1. **Given** the employee detail view is displayed (with or without filters), **When** the analyst clicks "Export to CSV," **Then** a CSV file is downloaded containing all currently visible rows with column headers.

2. **Given** the exported CSV, **When** opened in a spreadsheet application, **Then** all numeric values are correctly formatted (compensation as numbers, percentages as decimals), and the file includes a header row with column names.

3. **Given** filters are active, **When** exporting, **Then** only the filtered subset of employees is included in the export, and the filename includes a suffix indicating filters were applied (e.g., "hce_details_filtered.csv").

4. **Given** the employee detail view is open, **When** the analyst clicks "Export All," **Then** a single CSV file is downloaded containing all HCE and NHCE rows with a "Group" column identifying each row as "HCE" or "NHCE".

---

### User Story 6 - Navigate from Heatmap to Employee Detail (Priority: P1)

An analyst can seamlessly navigate from a heatmap cell or scenario result directly to the employee-level detail view for that specific scenario.

**Why this priority**: Integration with existing heatmap navigation ensures a smooth user experience and workflow continuity.

**Independent Test**: Can be tested by clicking a heatmap cell, opening the detail panel, and verifying a "View Employees" action is available that loads the correct scenario's employee data.

**Acceptance Scenarios**:

1. **Given** a heatmap cell is clicked and the scenario detail panel is open, **When** the analyst clicks "View Employee Details," **Then** the employee detail view opens displaying participants for that specific scenario (adoption rate and contribution rate).

2. **Given** the employee detail view is open, **When** viewing the header, **Then** the current scenario parameters are displayed (e.g., "Scenario: 50% Adoption, 6% Contribution Rate - PASS").

3. **Given** the employee detail view is open, **When** the analyst clicks "Back to Heatmap" or presses Escape, **Then** the view closes and focus returns to the previously selected heatmap cell.

---

### Edge Cases

- What happens when a scenario has zero HCEs selected for mega-backdoor (0% adoption)? The HCE table shows all HCEs with Mega-Backdoor Amount = $0 and constraint columns show "N/A - Not Selected."
- What happens when an HCE has compensation below the §415(c) limit but existing contributions already exhaust their limit? The Available Room shows $0 and Constraint Status indicates "Pre-existing Limit Exhaustion."
- What happens when the census is very large (10,000+ participants)? The table uses pagination or virtual scrolling, showing 50-100 rows at a time with performance remaining responsive.
- What happens when an employee has zero compensation? The row is displayed with a warning indicator and Individual ACP shows "N/A" (division by zero would be avoided).
- What happens when the user exports while a sort is active? The exported data reflects the current sort order.

## Requirements

### Functional Requirements

#### Employee Detail Display

- **FR-001**: System MUST display employee details using tabbed navigation with two tabs: "HCEs" and "NHCEs", allowing users to switch between views while maintaining full-width table display.
- **FR-002**: HCE panel MUST display columns: Employee ID, Compensation, Deferral Rate (%), Match Amount, After-Tax Amount, §415(c) Limit, Available Room, Mega-Backdoor Amount, Individual ACP (%), Constraint Status.
- **FR-003**: NHCE panel MUST display columns: Employee ID, Compensation, Deferral Rate (%), Match Amount, After-Tax Amount, Individual ACP (%).
- **FR-004**: System MUST format monetary values with dollar signs and comma separators (e.g., "$123,456").
- **FR-005**: System MUST format percentage values to 2 decimal places with "%" suffix (e.g., "4.50%").
- **FR-006**: System MUST display row counts for each panel (e.g., "Showing 45 HCEs").

#### Constraint Information

- **FR-007**: System MUST calculate Available Room as: §415(c) Limit - (Deferral + Match + After-Tax + any simulated mega-backdoor).
- **FR-008**: System MUST classify Constraint Status as one of: "Unconstrained" (received full mega-backdoor), "At §415(c) Limit" (capped by annual additions limit), "Reduced" (received partial mega-backdoor), "Not Selected" (not chosen for mega-backdoor adoption).
- **FR-009**: System MUST display the §415(c) limit value for the appropriate plan year (sourced from constants).
- **FR-010**: System MUST provide tooltip explanations for each constraint status with specific dollar amounts.

#### Sorting

- **FR-011**: System MUST support sorting by any visible column in both HCE and NHCE tables.
- **FR-012**: System MUST toggle between ascending and descending sort on repeated clicks.
- **FR-013**: System MUST display a visual sort indicator (arrow) on the currently sorted column.
- **FR-014**: System MUST maintain sort state when switching between HCE and NHCE panels.

#### Filtering

- **FR-015**: System MUST provide filter controls for HCE table including: Constraint Status (dropdown), Compensation range (min/max inputs), Has Mega-Backdoor (yes/no).
- **FR-016**: System MUST provide filter controls for NHCE table including: Compensation range (min/max inputs), Individual ACP range (min/max inputs).
- **FR-017**: System MUST display active filter count and "Clear Filters" action when any filters are applied.
- **FR-018**: System MUST update the "Showing X of Y" count in real-time as filters are applied.

#### Summary Statistics

- **FR-019**: System MUST display an HCE summary panel containing: Total Count, At §415(c) Limit Count, With Reduced Contribution Count, Average Available Room, Total Mega-Backdoor Amount, Average Individual ACP.
- **FR-020**: System MUST display an NHCE summary panel containing: Total Count, Average Individual ACP, Total Match Amount, Total After-Tax Amount.
- **FR-021**: Summary statistics MUST update when filters are applied (showing filtered vs. total).

#### Export

- **FR-022**: System MUST provide "Export to CSV" button for each employee table (HCE and NHCE).
- **FR-023**: Exported CSV MUST include all currently visible columns in display order.
- **FR-024**: Exported CSV MUST respect current filter and sort state.
- **FR-025**: Exported CSV filename MUST include scenario parameters and timestamp (e.g., "hce_details_50pct_6pct_20260113.csv").
- **FR-026**: System MUST provide "Export All" option that exports a single CSV file containing both HCE and NHCE rows, with a "Group" column as the first column identifying each row as "HCE" or "NHCE".

#### Navigation Integration

- **FR-027**: System MUST add "View Employee Details" action to the existing scenario detail panel (from heatmap drill-down).
- **FR-028**: System MUST display current scenario parameters (adoption rate, contribution rate, status) in the employee detail view header.
- **FR-029**: System MUST provide navigation to return to the heatmap or scenario view.
- **FR-030**: System MUST preserve the selected scenario context when navigating between views.

#### Accessibility

- **FR-031**: Tables MUST be navigable via keyboard (arrow keys for cell navigation, Enter for actions).
- **FR-032**: Sort and filter controls MUST be keyboard accessible.
- **FR-033**: System MUST meet WCAG 2.1 AA contrast requirements for all text and interactive elements.
- **FR-034**: Screen readers MUST announce table context, row/column headers, and sorted column.

### Key Entities

- **EmployeeImpact**: Individual employee contribution breakdown for a scenario
  - employee_id: Anonymized identifier from census (internal_id)
  - is_hce: Boolean indicating HCE or NHCE classification
  - compensation: Annual compensation in dollars
  - deferral_amount: Employee deferral contributions in dollars
  - match_amount: Employer match contributions in dollars
  - after_tax_amount: After-tax contributions in dollars (existing)
  - section_415c_limit: The applicable §415(c) limit for this plan year
  - available_room: Remaining capacity before hitting §415(c) limit
  - mega_backdoor_amount: Computed mega-backdoor contribution for this scenario
  - individual_acp: This employee's ACP percentage
  - constraint_status: "Unconstrained" | "At §415(c) Limit" | "Reduced" | "Not Selected"
  - constraint_detail: Human-readable explanation of any constraint

- **EmployeeImpactSummary**: Aggregated statistics for a participant group
  - group: "HCE" | "NHCE"
  - total_count: Number of participants in group
  - at_limit_count: Number at §415(c) limit (HCE only)
  - reduced_count: Number with reduced mega-backdoor (HCE only)
  - average_available_room: Mean available room in dollars (HCE only)
  - total_mega_backdoor: Sum of mega-backdoor amounts (HCE only)
  - average_individual_acp: Mean individual ACP percentage
  - total_match: Sum of match contributions
  - total_after_tax: Sum of after-tax contributions

- **EmployeeImpactView**: Container for employee-level scenario analysis
  - scenario_result: Reference to the parent ScenarioResult
  - hce_employees: List of EmployeeImpact for HCEs
  - nhce_employees: List of EmployeeImpact for NHCEs
  - hce_summary: EmployeeImpactSummary for HCE group
  - nhce_summary: EmployeeImpactSummary for NHCE group

## Success Criteria

### Transparency

- **SC-001**: Users can identify which specific employees are at the §415(c) limit within 30 seconds of opening employee details
- **SC-002**: Users can determine the total dollar impact of §415(c) constraints within 10 seconds using summary statistics
- **SC-003**: Every ACP result can be traced back to individual employee contributions (audit trail complete)

### Interpretability

- **SC-004**: Users report understanding why a scenario passed or failed after reviewing employee details (user testing: 90% comprehension rate)
- **SC-005**: Constraint status explanations are rated as "clear" or "very clear" by 85% of users in usability testing
- **SC-006**: Users can answer "How many HCEs are constrained by limits?" within 5 seconds

### Exportability

- **SC-007**: CSV exports open correctly in Excel, Google Sheets, and common spreadsheet applications without data corruption
- **SC-008**: Exported data matches on-screen data exactly (100% fidelity)
- **SC-009**: Export operation completes within 3 seconds for censuses up to 10,000 participants

### Performance

- **SC-010**: Employee detail view loads within 2 seconds for censuses up to 10,000 participants
- **SC-011**: Sorting operation completes within 500ms for any column
- **SC-012**: Filter operations update the display within 500ms

### Accessibility

- **SC-013**: All functionality is operable using keyboard-only navigation
- **SC-014**: Screen reader users can navigate and understand table content independently
- **SC-015**: Color contrast meets WCAG 2.1 AA requirements (4.5:1 for text, 3:1 for graphics)

## Assumptions

- Employee data is available from the census loaded for the scenario (via Participant model from spec 002)
- The §415(c) limit for the plan year is available from constants configuration
- Employee IDs displayed are the anonymized internal_id values, not any PII
- The parent ScenarioResult contains the adoption_rate, contribution_rate, and seed_used to reproduce HCE selection
- Deferral contributions are calculated from deferral_rate × compensation as stored in census
- Employee impact data is computed on demand using scenario parameters and census data (not dependent on debug_details)

## Dependencies

- **Spec 004 (Scenario Analysis)**: Provides ScenarioResult with scenario parameters (adoption_rate, contribution_rate, seed_used) needed to reproduce employee-level calculations
- **Spec 005 (Heatmap Exploration)**: Provides the scenario detail panel where "View Employee Details" action is added
- **Spec 002 (Census Management)**: Provides Participant data model with compensation and contribution rates for on-demand impact calculation

## Out of Scope

- Editing or modifying employee data from this view (read-only display)
- Running new scenarios from the employee detail view
- Comparing employee impacts across multiple scenarios side-by-side
- Showing historical employee contribution data across plan years
- Real-time recalculation as employee data changes
- Batch operations on employees (e.g., bulk exclusion from mega-backdoor)
- Print-optimized layout (export to CSV then print from spreadsheet)
