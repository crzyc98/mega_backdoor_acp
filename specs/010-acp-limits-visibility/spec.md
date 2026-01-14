# Feature Specification: ACP Limits Visibility

**Feature Branch**: `010-acp-limits-visibility`
**Created**: 2026-01-14
**Status**: Verified
**Input**: User description: "Update ACP Sensitivity Analyzer so every scenario surfaces BOTH ACP permissible limits and the HCE vs NHCE ACP rates, and the UI/export shows them clearly. Fix implementation to use capped 2% method: max(NHCE*1.25, min(NHCE+2%, 2*NHCE))."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View ACP Compliance Details in Heatmap (Priority: P1)

As a retirement plan administrator analyzing ACP sensitivity scenarios, I want to see the complete ACP compliance picture (NHCE rate, HCE rate, effective limit, margin, and which formula binds) when hovering over heatmap cells, so that I can quickly understand why a scenario passes or fails without drilling into details.

**Why this priority**: The heatmap is the primary analysis interface. Users need immediate visibility into compliance metrics to make informed decisions about contribution strategies without requiring additional clicks.

**Independent Test**: Can be fully tested by running a grid analysis, hovering over any heatmap cell, and verifying all compliance metrics are displayed in the tooltip.

**Acceptance Scenarios**:

1. **Given** a completed grid analysis with multiple scenarios, **When** I hover over a heatmap cell, **Then** I see NHCE ACP rate, HCE ACP rate, effective limit, margin, and binding rule (1.25x or 2pct/2x) in the tooltip
2. **Given** a scenario where 1.25x formula produces the effective limit, **When** I view the tooltip, **Then** binding_rule shows "1.25x"
3. **Given** a scenario where 2pct/2x formula produces the effective limit, **When** I view the tooltip, **Then** binding_rule shows "2pct/2x"
4. **Given** any scenario, **When** margin is positive, **Then** the scenario status is PASS; **When** margin is negative, **Then** status is FAIL

---

### User Story 2 - View Detailed Compliance Breakdown on Drilldown Page (Priority: P2)

As a retirement plan administrator who has identified a scenario of interest, I want to see a comprehensive compliance card showing all intermediate ACP calculations (both formula branches, the cap, and the final effective limit), so that I can explain and document the compliance determination to stakeholders.

**Why this priority**: After identifying scenarios via the heatmap, users need full transparency into how limits were calculated to support audit documentation and compliance reporting.

**Independent Test**: Can be fully tested by clicking any heatmap cell to open the drilldown page and verifying the Compliance Card displays all nine metrics.

**Acceptance Scenarios**:

1. **Given** I click on a heatmap cell for a specific scenario, **When** the EmployeeImpact drilldown page loads, **Then** I see a Compliance Card displaying: NHCE ACP, HCE ACP, limit_125, limit_2pct_uncapped, cap_2x, limit_2pct_capped, effective_limit, binding_rule, and margin
2. **Given** a scenario with NHCE ACP of 3.00%, **When** I view the Compliance Card, **Then** limit_125 shows 3.75%, limit_2pct_uncapped shows 5.00%, cap_2x shows 6.00%, limit_2pct_capped shows 5.00%, and effective_limit shows 5.00%
3. **Given** a scenario with NHCE ACP of 1.50%, **When** I view the Compliance Card, **Then** limit_125 shows 1.875%, limit_2pct_uncapped shows 3.50%, cap_2x shows 3.00%, limit_2pct_capped shows 3.00% (capped), and effective_limit shows 3.00%

---

### User Story 3 - Export Complete ACP Metrics to CSV (Priority: P2)

As a retirement plan administrator preparing compliance documentation, I want CSV exports to include all ACP compliance metrics for each scenario, so that I can perform offline analysis and integrate the data into other compliance tools or reports.

**Why this priority**: Exports are essential for audit trails and integration with external compliance systems. Users need complete data without manual transcription.

**Independent Test**: Can be fully tested by running a grid analysis, exporting to CSV, and verifying all new columns are present with correct values.

**Acceptance Scenarios**:

1. **Given** a completed grid analysis, **When** I export to CSV, **Then** the file includes columns for: nhce_acp, hce_acp, limit_125, limit_2pct_uncapped, cap_2x, limit_2pct_capped, effective_limit, binding_rule, margin
2. **Given** decimal values in the backend, **When** exported to CSV, **Then** percentage values display as basis points with 2 decimal places (e.g., 3.25 for 3.25%)
3. **Given** a scenario with ERROR status, **When** exported to CSV, **Then** rate and limit columns show empty/null values rather than zeros

---

### User Story 4 - Export Complete ACP Metrics to PDF Report (Priority: P3)

As a retirement plan administrator creating formal compliance reports, I want PDF exports to include a summary table of ACP compliance metrics for the selected scenario(s), so that I can produce professional documentation for plan sponsors and auditors.

**Why this priority**: PDF reports are used for formal documentation but are secondary to interactive analysis and CSV export for data integration.

**Independent Test**: Can be fully tested by selecting a scenario and generating a PDF report, then verifying the compliance metrics table is included.

**Acceptance Scenarios**:

1. **Given** I generate a PDF report for a selected scenario, **When** the PDF is created, **Then** it includes a table showing all nine ACP compliance metrics
2. **Given** percentage values in the metrics, **When** displayed in PDF, **Then** they show as basis points with 2 decimal places and % suffix (e.g., "3.25%")

---

### User Story 5 - Handle Edge Cases Gracefully (Priority: P1)

As a retirement plan administrator working with varied census data, I want the system to handle scenarios with no HCEs or no NHCEs gracefully, so that I can trust the results and understand why certain scenarios cannot be evaluated.

**Why this priority**: Data quality issues are common in real-world census files. The system must handle edge cases without crashing and provide clear feedback.

**Independent Test**: Can be fully tested by uploading census files with only HCEs or only NHCEs and verifying the system returns ERROR status with appropriate messages.

**Acceptance Scenarios**:

1. **Given** a scenario where census data contains no HCE employees, **When** the scenario is computed, **Then** status is ERROR and all rate/limit fields are null (not zero)
2. **Given** a scenario where census data contains no NHCE employees, **When** the scenario is computed, **Then** status is ERROR and all rate/limit fields are null
3. **Given** an ERROR scenario, **When** displayed in the heatmap, **Then** the cell indicates an error state and tooltip explains why

---

### Edge Cases

- What happens when NHCE ACP is exactly 0%? (limit_125 = 0%, limit_2pct_capped = min(2%, 0%) = 0%, effective_limit = 0%)
- What happens when no employees are eligible for ACP test? System returns ERROR status with appropriate message
- What happens when all employees have 0% contribution rates? System computes valid 0% rates and limits
- How does system handle rounding edge cases where formulas produce very close results? Internal calculations use full decimal precision; rounding applied only at display/export layer

## Requirements *(mandatory)*

### Functional Requirements

#### Backend Requirements

- **FR-001**: System MUST compute and return nhce_acp (NHCE average contribution percentage) as a decimal for each scenario
- **FR-002**: System MUST compute and return hce_acp (HCE average contribution percentage) as a decimal for each scenario
- **FR-003**: System MUST compute limit_125 as 1.25 * nhce_acp
- **FR-004**: System MUST compute limit_2pct_uncapped as nhce_acp + 0.02
- **FR-005**: System MUST compute cap_2x as 2.0 * nhce_acp
- **FR-006**: System MUST compute limit_2pct_capped as min(limit_2pct_uncapped, cap_2x)
- **FR-007**: System MUST compute effective_limit as max(limit_125, limit_2pct_capped)
- **FR-008**: System MUST set binding_rule to "1.25x" when limit_125 >= limit_2pct_capped, otherwise "2pct/2x"
- **FR-009**: System MUST compute margin as effective_limit - hce_acp
- **FR-010**: System MUST maintain backward compatibility by adding new fields without renaming or removing existing API fields
- **FR-011**: System MUST return status=ERROR and null values for all rate/limit fields when a scenario has zero HCEs or zero NHCEs
- **FR-012**: System MUST include all new fields in the Run results endpoint response
- **FR-013**: System MUST include all new fields in the employee drilldown endpoint response
- **FR-014**: System MUST use explicit Python typing for all new fields (no Any type)

#### Frontend Requirements

- **FR-015**: Heatmap tooltip MUST display: NHCE ACP, HCE ACP, effective_limit, margin, and binding_rule
- **FR-016**: Scenario drilldown page MUST display a Compliance Card showing all nine metrics: nhce_acp, hce_acp, limit_125, limit_2pct_uncapped, cap_2x, limit_2pct_capped, effective_limit, binding_rule, margin
- **FR-017**: Frontend MUST display percentage values as basis points with 2 decimal places (e.g., 3.25%)

#### Export Requirements

- **FR-018**: CSV export MUST include columns for all nine new fields
- **FR-019**: PDF export MUST include a compliance metrics table for the selected scenario
- **FR-020**: Export percentage values MUST display as basis points with 2 decimal places

#### Documentation Requirements

- **FR-021**: README MUST be updated to document the correct capped 2% formula: max(NHCE*1.25, min(NHCE+2%, 2*NHCE))
- **FR-022**: README MUST explain the binding_rule field and when each formula binds

#### Testing Requirements

- **FR-023**: Unit tests MUST validate scenarios where 1.25x formula binds
- **FR-024**: Unit tests MUST validate scenarios where 2pct/2x formula binds
- **FR-025**: Unit tests MUST validate scenarios where the 2x cap changes the result vs uncapped
- **FR-026**: Unit tests MUST validate margin sign matches PASS/FAIL status
- **FR-027**: Unit tests MUST validate ERROR status and null fields for zero HCE/NHCE scenarios

### Key Entities

- **ScenarioResult**: Extended to include nhce_acp, hce_acp, limit_125, limit_2pct_uncapped, cap_2x, limit_2pct_capped, effective_limit, binding_rule (string literal "1.25x" or "2pct/2x"), and margin. All percentage fields stored as decimals (e.g., 0.0325 for 3.25%).
- **ACPLimits**: New nested model (if needed) containing the computed limit fields for cleaner organization
- **Binding Rule**: String enumeration indicating which ACP test formula produced the effective limit

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify the binding ACP formula within 2 seconds by viewing the heatmap tooltip
- **SC-002**: Users can view all nine ACP compliance metrics on the drilldown page without scrolling the Compliance Card
- **SC-003**: 100% of scenarios in grid analysis include all new ACP metrics in API response
- **SC-004**: CSV exports include all nine new columns with correctly formatted values
- **SC-005**: PDF reports include readable compliance metrics table
- **SC-006**: Zero scenarios crash when census contains only HCEs or only NHCEs (graceful ERROR status instead)
- **SC-007**: All unit tests pass covering the four specified test cases (1.25x binds, 2pct/2x binds, 2x cap applies, margin/status alignment)
- **SC-008**: Existing API consumers continue to function without modification (backward compatibility)

## Assumptions

- Internal calculations will use full decimal precision; rounding to 2 decimal places (basis points format) occurs only at display/export boundaries
- The binding_rule field uses exact string values "1.25x" and "2pct/2x" as specified (not "1.25x rule" or other variations)
- Error scenarios (no HCEs or no NHCEs) use null values in JSON responses, empty strings in CSV, and "N/A" or similar in PDF
- The Compliance Card is a new UI component added to the existing drilldown page layout without redesigning other elements
- Performance impact of computing nine additional fields per scenario is negligible for typical grid sizes
