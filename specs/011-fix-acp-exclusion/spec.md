# Feature Specification: Fix ACP Permissive Disaggregation Exclusion Bug

**Feature Branch**: `011-fix-acp-exclusion`
**Created**: 2026-01-15
**Status**: Draft
**Input**: User description: "Investigate and fix ACP permissive disaggregation exclusion bug - participants who should be permissively excludable are being included in ACP testing population"

## Clarifications

### Session 2026-01-15

- Q: When participants have missing required data (DOB or hire_date), how should the system notify the user? → A: Allow test to proceed; show error count summary and include errors in participant detail/export

## Problem Statement

The ACP Sensitivity Analyzer is incorrectly including participants in the ACP test population who should be permissively excludable. This occurs because the eligibility calculation logic does not properly apply the permissive disaggregation rules based on age 21, 1 year of service, and semi-annual entry dates.

**Impact**: Including ineligible participants (typically with 0% contributions) depresses the NHCE ACP average, which distorts pass/fail outcomes and leads to incorrect test results.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Accurate ACP Test Results (Priority: P1)

As a plan administrator running ACP testing, I need the system to correctly identify which participants are includable in the ACP test population so that the test results accurately reflect compliance status.

**Why this priority**: This is the core bug fix - without correct population identification, all ACP test results are unreliable and potentially lead to incorrect compliance decisions.

**Independent Test**: Can be fully tested by running an ACP test on a census with known eligibility dates and verifying only eligible participants are included in calculations.

**Acceptance Scenarios**:

1. **Given** a 2024 plan year census with a participant hired in 2024 (already age 21) who completes 1 year of service in 2025, **When** ACP testing is run for plan year 2024, **Then** the participant is excluded from the ACP population with reason "NOT_ELIGIBLE_DURING_YEAR"
2. **Given** a participant who becomes eligible mid-2024 with entry date July 1, 2024, **When** ACP testing is run for plan year 2024, **Then** the participant is included in the ACP population regardless of contribution amount
3. **Given** a participant whose entry date is January 1, 2024 but who terminated on December 15, 2023, **When** ACP testing is run for plan year 2024, **Then** the participant is excluded with reason "TERMINATED_BEFORE_ENTRY"
4. **Given** a participant whose entry date is July 1, 2024 and who terminated on August 15, 2024, **When** ACP testing is run for plan year 2024, **Then** the participant is included in the ACP population

---

### User Story 2 - Visibility into Eligibility Calculations (Priority: P2)

As a plan administrator reviewing ACP test results, I need to see the computed eligibility fields (eligibility_date, entry_date, inclusion status, exclusion reason) for each participant so I can verify the calculations and troubleshoot discrepancies.

**Why this priority**: Transparency into calculations is essential for audit purposes and debugging, but the core fix must work first.

**Independent Test**: Can be tested by examining participant detail views or exports after running an ACP test and verifying eligibility fields are populated and visible.

**Acceptance Scenarios**:

1. **Given** an ACP test has been run, **When** I view participant details, **Then** I can see eligibility_date, entry_date, acp_includable status, and exclusion_reason for each participant
2. **Given** an ACP test has been run, **When** I export results to CSV, **Then** the export includes eligibility_date, entry_date, acp_includable, and acp_exclusion_reason columns

---

### User Story 3 - Consistent Eligibility Logic Across Features (Priority: P2)

As a system maintainer, I need the eligibility calculation logic to be implemented in a single reusable function used consistently across all features that derive ACP/eligibility populations.

**Why this priority**: Prevents future bugs from inconsistent implementations and simplifies maintenance.

**Independent Test**: Can be verified through code review showing a single source of truth for eligibility calculations used by census parsing, ACP calculation, and scenario analysis.

**Acceptance Scenarios**:

1. **Given** the codebase, **When** I search for eligibility calculations, **Then** there is exactly one authoritative function that all other code references
2. **Given** a change to eligibility rules, **When** I update the authoritative function, **Then** all features automatically reflect the change

---

### Edge Cases

- What happens when DOB is missing? System marks participant with ERROR status and excludes from calculations with explicit "MISSING_DOB" reason
- What happens when hire date is missing? System marks participant with ERROR status and excludes from calculations with explicit "MISSING_HIRE_DATE" reason
- What happens when eligibility date falls exactly on Jan 1 or Jul 1? Participant entry date equals the eligibility date (same day entry)
- What happens when eligibility date falls on Dec 31? Entry date is the following Jan 1 (next plan year, so excluded in current year)
- What happens for a participant born on Feb 29? Age 21 calculation uses Feb 28 in non-leap years for the age 21 date
- What happens when a participant has 0% contributions but is otherwise eligible? Participant is included in ACP population (0% contributions do not cause exclusion)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate age21_date as DOB + 21 years (using Feb 28 for Feb 29 birthdays in non-leap years)
- **FR-002**: System MUST calculate yos1_date as hire_date + 1 year (elapsed time approximation)
- **FR-003**: System MUST calculate eligibility_date as the maximum of age21_date and yos1_date (both conditions must be met)
- **FR-004**: System MUST calculate entry_date as the first of {Jan 1, Jul 1} on or after eligibility_date
- **FR-005**: System MUST include a participant in ACP population when entry_date <= plan_year_end AND (termination_date is null OR termination_date >= entry_date)
- **FR-006**: System MUST exclude participants with entry_date > plan_year_end with reason "NOT_ELIGIBLE_DURING_YEAR"
- **FR-007**: System MUST exclude participants with termination_date < entry_date with reason "TERMINATED_BEFORE_ENTRY"
- **FR-008**: System MUST exclude participants with missing DOB with reason "MISSING_DOB" and mark as ERROR
- **FR-009**: System MUST exclude participants with missing hire_date with reason "MISSING_HIRE_DATE" and mark as ERROR
- **FR-010**: System MUST NOT exclude participants based on contribution amount (0% contributors who are otherwise eligible must be included)
- **FR-011**: System MUST apply eligibility rules identically to HCEs and NHCEs
- **FR-012**: System MUST use plan_year_end = December 31 for calendar year plans (e.g., 2024 plan year ends 2024-12-31, not 2023-12-31)
- **FR-013**: System MUST persist computed eligibility_date, entry_date, acp_includable, and acp_exclusion_reason for each participant
- **FR-014**: System MUST expose eligibility fields in participant detail views and exports
- **FR-015**: System MUST allow ACP test execution to proceed even when participants have missing data (DOB or hire_date)
- **FR-016**: System MUST display a summary count of participants with data errors after test execution completes

### Key Entities

- **Participant**: Represents an employee in the census with DOB, hire_date, termination_date, is_hce flag, and contribution data
- **EligibilityResult**: Computed eligibility information including eligibility_date, entry_date, acp_includable (boolean), and acp_exclusion_reason (enum: INCLUDED, NOT_ELIGIBLE_DURING_YEAR, TERMINATED_BEFORE_ENTRY, MISSING_DOB, MISSING_HIRE_DATE)
- **PlanYear**: The testing period with plan_year_start (Jan 1) and plan_year_end (Dec 31) for calendar year plans

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a calendar-year 2024 ACP test run, 100% of participants with entry_date in 2025 or later are excluded from ACP population
- **SC-002**: For a calendar-year 2024 ACP test run, 100% of participants who become eligible at any point during 2024 are included regardless of contribution amount
- **SC-003**: All participants have eligibility_date, entry_date, acp_includable, and acp_exclusion_reason fields populated and visible in detail views
- **SC-004**: Unit tests pass covering all specified scenarios (new hire excluded, mid-year eligible included, terminated before entry excluded, terminated after entry included, boundary cases)
- **SC-005**: Existing test suite continues to pass with no regressions

## Assumptions

- Plan eligibility uses age 21 and 1 year of service requirements (standard safe harbor)
- Semi-annual entry dates are Jan 1 and Jul 1 (standard configuration)
- Calendar year plans are assumed (plan year = Jan 1 to Dec 31)
- Elapsed time method is used for year of service calculations (hire_date + 1 year, not hours-based)

## Out of Scope

- Configurable eligibility age (currently hardcoded to 21)
- Configurable service requirements (currently hardcoded to 1 year)
- Configurable entry dates (currently hardcoded to Jan 1 / Jul 1)
- Non-calendar plan years
- Hours-based service calculations
