# Feature Specification: ACP Sensitivity Analyzer

**Feature Branch**: `001-acp-sensitivity-analyzer`
**Created**: 2026-01-12
**Status**: Draft
**Input**: User description: "Build an ACP Sensitivity Analyzer web product that helps retirement-plan analysts quickly understand how after-tax (mega backdoor) employee contributions affect ACP test outcomes. Users should be able to upload a participant census, run a single scenario or a grid of scenarios (adoption rate x contribution rate) for a selected plan year, and see PASS/FAIL plus the limiting test result and margin. Prioritize auditability, reproducibility, and domain correctness for HCE/NHCE treatment. The product should support both interactive UI usage and programmatic API usage."

## Clarifications

### Session 2026-01-12

- Q: How should HCEs be selected for partial adoption scenarios? → A: Random selection with user-configurable seed (default seed provided for reproducibility)
- Q: How should the system handle census files exceeding 100K participants? → A: No artificial cap; allow unlimited size (accept performance risk for very large files)
- Q: How long should session/census data be retained, and how should PII be handled? → A: Data persists indefinitely; SSN and other PII (names, birthdates, addresses) must be masked/stripped on import, retaining only non-identifying data needed for ACP calculations

## Overview

The ACP Sensitivity Analyzer is a web-based tool that enables retirement-plan analysts to model how after-tax ("mega backdoor Roth") contributions impact ACP (Actual Contribution Percentage) nondiscrimination test outcomes. The tool transforms uncertainty about test compliance into actionable, quantified risk thresholds.

## User Personas

### Primary Persona: Plan Compliance Analyst
- **Role**: Retirement plan compliance specialist at a TPA (Third Party Administrator) or consulting firm
- **Goal**: Quickly assess whether proposed mega-backdoor Roth programs will pass ACP testing
- **Pain Point**: Manual spreadsheet calculations are time-consuming, error-prone, and difficult to audit
- **Technical Comfort**: Proficient with spreadsheets, comfortable with web applications, not a developer

### Secondary Persona: Plan Sponsor Benefits Manager
- **Role**: HR/Benefits professional at a company considering mega-backdoor Roth
- **Goal**: Understand compliance risks before implementing after-tax contribution features
- **Pain Point**: Needs clear pass/fail guidance without deep regulatory expertise
- **Technical Comfort**: Basic web application user

### Tertiary Persona: Integration Developer
- **Role**: Developer building automated compliance workflows
- **Goal**: Programmatically run ACP sensitivity analysis as part of larger systems
- **Pain Point**: Needs reliable, documented programmatic access to ACP calculations
- **Technical Comfort**: Software developer comfortable with APIs

## User Scenarios & Testing

### User Story 1 - Single Scenario Analysis (Priority: P1)

A compliance analyst uploads a participant census and runs a single ACP test scenario to determine if a specific mega-backdoor configuration would pass compliance testing.

**Why this priority**: This is the core value proposition - validating a specific plan configuration. Without this, the product has no utility.

**Independent Test**: Can be fully tested by uploading a census file, configuring one scenario, and verifying the PASS/FAIL result with margin calculation. Delivers immediate compliance insight.

**Acceptance Scenarios**:

1. **Given** a valid census file with HCE/NHCE data, **When** the analyst uploads the file and selects plan year 2025 with 50% HCE adoption at 6% contribution rate, **Then** the system displays PASS or FAIL status, the limiting test formula used, and the margin (distance from threshold).

2. **Given** a census file missing required columns, **When** the analyst attempts upload, **Then** the system displays specific validation errors identifying which required fields are missing.

3. **Given** a valid census with completed scenario parameters, **When** the analyst clicks "Run Analysis", **Then** results appear within 10 seconds for censuses up to 10,000 participants.

---

### User Story 2 - Grid Scenario Analysis (Priority: P2)

A compliance analyst runs a grid of scenarios across multiple adoption rates and contribution rates to visualize the "safe zone" for mega-backdoor implementation.

**Why this priority**: Grid analysis provides strategic planning value beyond single-point validation, but requires P1 functionality as foundation.

**Independent Test**: Can be tested by uploading a census, configuring adoption rate range (0%-100%) and contribution rate range (2%-12%), running grid analysis, and verifying heatmap visualization with clear pass/fail boundaries.

**Acceptance Scenarios**:

1. **Given** a valid census, **When** the analyst configures a 5x6 grid (5 adoption rates x 6 contribution rates), **Then** the system displays a heatmap showing PASS (green) and FAIL (red) zones with margin values for each cell.

2. **Given** grid results are displayed, **When** the analyst hovers over any cell, **Then** the system shows detailed breakdown including HCE ACP, NHCE ACP, test threshold, and margin.

3. **Given** a large census (10,000+ participants) with a 10x10 grid, **When** the analyst runs analysis, **Then** results complete within 60 seconds.

---

### User Story 3 - Results Export and Audit Trail (Priority: P3)

A compliance analyst exports analysis results with full audit trail for documentation, review by plan sponsors, or regulatory filing support.

**Why this priority**: Auditability is critical for compliance work but depends on having results to export from P1/P2.

**Independent Test**: Can be tested by running any analysis, exporting results, and verifying export contains all inputs, calculation details, and timestamps for audit purposes.

**Acceptance Scenarios**:

1. **Given** completed analysis results (single or grid), **When** the analyst clicks "Export", **Then** the system generates a downloadable file containing: input census summary, scenario parameters, all results with formulas applied, and timestamp.

2. **Given** exported results, **When** reviewed by an auditor, **Then** the export contains sufficient detail to manually reproduce any calculation.

3. **Given** any analysis run, **When** the analyst views results, **Then** each result row displays the exact formula/test used (e.g., "HCE ACP <= NHCE ACP x 1.25" or "HCE ACP <= NHCE ACP + 2.0").

---

### User Story 4 - Programmatic API Access (Priority: P4)

An integration developer uses the API to programmatically run ACP sensitivity analysis as part of automated compliance workflows.

**Why this priority**: API access extends value to technical users and integration scenarios, but core analysis must work first.

**Independent Test**: Can be tested by sending a census payload and scenario parameters via API, receiving structured results, and verifying results match UI output for same inputs.

**Acceptance Scenarios**:

1. **Given** valid credentials and census data, **When** a developer submits a single scenario via API, **Then** the API returns structured results including pass/fail status, limiting test, margin, and calculation details within 15 seconds.

2. **Given** a grid scenario request via API, **When** submitted with valid parameters, **Then** the API returns complete grid results in structured format suitable for further processing.

3. **Given** invalid or malformed request data, **When** submitted to the API, **Then** the API returns clear error messages identifying the validation failures.

---

### Edge Cases

- What happens when a census has zero HCEs? System displays informational message that ACP test is not applicable.
- What happens when all NHCEs have 0% contribution rate? System calculates correctly (NHCE ACP = 0) and shows likely FAIL unless HCE contribution is also 0%.
- How does the system handle a census with exactly one HCE? System performs calculation normally; single-participant scenarios are valid.
- What happens when contribution rate exceeds IRC 415(c) limits? System warns but does not block (user may be modeling theoretical scenarios).
- How does the system handle mid-year hire dates? System uses plan-year compensation and applies statutory HCE determination rules based on prior year.
- What happens if census contains duplicate employee IDs? System rejects upload with specific error message.

## Requirements

### Functional Requirements

#### Census Upload and Validation
- **FR-001**: System MUST accept census uploads in CSV format with the following required columns: Employee ID, HCE Status (boolean), Annual Compensation, Current Deferral Rate, Current Match Rate, Current After-Tax Rate
- **FR-002**: System MUST validate census data on upload and display specific errors for: missing required columns, invalid data types, duplicate employee IDs, negative values where not permitted
- **FR-003**: System MUST support census files of any size without artificial limits; performance targets (SC-001, SC-002) apply to files up to 10,000 participants, with graceful degradation for larger files
- **FR-004**: System MUST persist uploaded census data indefinitely, allowing users to return and re-analyze previously uploaded data
- **FR-004a**: System MUST mask or strip PII fields on import, including: SSN (if used as Employee ID), names, birthdates, addresses, and any other personally identifiable information; only non-identifying data required for ACP calculations shall be retained
- **FR-004b**: System MUST generate a unique, non-reversible internal identifier for each participant to replace any PII-based identifiers

#### Scenario Configuration
- **FR-005**: System MUST allow users to select a plan year for the analysis
- **FR-006**: System MUST allow single scenario configuration with: HCE adoption rate (0-100%), HCE contribution rate (0-15% of compensation)
- **FR-007**: System MUST allow grid scenario configuration with: range of adoption rates (minimum 2 values, maximum 20 values), range of contribution rates (minimum 2 values, maximum 20 values)
- **FR-008**: System MUST provide default scenario presets (e.g., "Standard Grid: 0/25/50/75/100% adoption x 2/4/6/8/10/12% contribution")

#### ACP Test Calculation
- **FR-009**: System MUST calculate NHCE ACP as the average of (match contributions + after-tax contributions) / compensation for all non-HCE participants
- **FR-010**: System MUST calculate HCE ACP as the average of (match contributions + after-tax contributions + simulated mega-backdoor contributions) / compensation for selected HCE participants
- **FR-011**: System MUST apply IRS dual test criteria: PASS if HCE ACP <= lesser of (NHCE ACP x 1.25) OR (NHCE ACP + 2.0 percentage points, capped at 2x NHCE ACP)
- **FR-012**: System MUST identify and display which test branch (1.25x or +2.0) is the limiting factor for each scenario
- **FR-013**: System MUST calculate margin as the distance between actual HCE ACP and the threshold that would cause failure

#### Results Display
- **FR-014**: System MUST display single scenario results showing: PASS/FAIL status, HCE ACP, NHCE ACP, threshold value, limiting test formula, margin
- **FR-015**: System MUST display grid results as a heatmap visualization with: PASS shown in green gradient, FAIL shown in red gradient, color intensity indicating margin size
- **FR-016**: System MUST allow drill-down from any grid cell to see detailed single-scenario results
- **FR-017**: System MUST display all percentage values to 2 decimal places

#### Reproducibility and Audit
- **FR-018**: System MUST use random HCE selection for partial adoption scenarios, seeded by a user-configurable value to ensure reproducibility; system provides a default seed if user does not specify one
- **FR-019**: System MUST log and display the seed value used for any scenario involving partial adoption; same seed + census + parameters MUST produce identical HCE selection
- **FR-020**: System MUST timestamp all analysis runs
- **FR-021**: System MUST include version identifier in all results for traceability

#### Export
- **FR-022**: System MUST export results to CSV format including all input parameters, individual participant data used, and calculated results
- **FR-023**: System MUST export results to PDF format suitable for inclusion in compliance documentation

#### API Access
- **FR-024**: System MUST provide a programmatic API endpoint for submitting census data and scenario parameters
- **FR-025**: System MUST return API results in structured JSON format
- **FR-026**: System MUST enforce rate limiting on API access to prevent abuse
- **FR-027**: API responses MUST include the same calculation details as UI results (HCE ACP, NHCE ACP, threshold, limiting test, margin)

### Key Entities

- **Census**: A collection of participant records for a single plan, representing the population for ACP testing. Contains plan year context and upload metadata.

- **Participant**: An individual plan participant with attributes including: unique identifier, HCE/NHCE classification, annual compensation, current contribution rates (deferral, match, after-tax).

- **Scenario**: A configuration for ACP simulation including: HCE adoption rate (what percentage of HCEs participate in mega-backdoor), HCE contribution rate (what percentage of compensation HCEs contribute as after-tax).

- **Analysis Result**: The outcome of running one scenario against a census, including: pass/fail status, HCE ACP, NHCE ACP, test threshold, limiting test formula, margin, list of participating HCEs, timestamp, reproducibility metadata.

- **Grid Analysis**: A collection of analysis results across multiple scenarios, organized by adoption rate and contribution rate dimensions.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Analysts can upload a census and receive single-scenario results within 10 seconds for files up to 10,000 participants
- **SC-002**: Grid analysis (up to 100 scenarios) completes within 60 seconds for censuses up to 10,000 participants
- **SC-003**: 100% of calculations match manual spreadsheet verification (variance < 0.01 percentage points due to rounding)
- **SC-004**: Analysts can complete a full analysis workflow (upload, configure, run, export) in under 5 minutes
- **SC-005**: Exported audit trails contain sufficient detail for an independent reviewer to reproduce any result within 0.01 percentage points
- **SC-006**: API consumers receive structured results that match UI results for identical inputs
- **SC-007**: Zero unhandled errors for valid census files that meet documented format requirements
- **SC-008**: System supports concurrent analysis sessions from at least 10 users without degradation

## Assumptions

- Census files will be provided in UTF-8 encoded CSV format
- HCE/NHCE status is pre-determined by the user (system does not calculate HCE status from compensation)
- Current-year testing method is used (not prior-year NHCE ACP)
- Match contributions are already calculated and provided in census (system does not apply match formulas)
- Plan contribution limits (IRC 415) are validated by the user; system warns but does not enforce
- Users have modern web browsers (Chrome, Firefox, Safari, Edge - latest 2 major versions)
- Census data is stored with PII stripped; users are responsible for maintaining their own mapping of internal IDs to original employee records if needed
- Single plan analysis per session; cross-plan comparisons are out of scope

## Out of Scope

- User authentication and multi-tenancy (single-user sessions for MVP)
- QMAC/QNEC corrective contribution modeling
- ADP (Actual Deferral Percentage) testing
- Cross-plan analysis or plan comparison features
- Mobile-optimized interface
- Real-time collaboration features
- Email or notification features
- Integration with external payroll or recordkeeping systems
