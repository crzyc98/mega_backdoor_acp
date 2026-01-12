# Feature Specification: Scenario Analysis

**Feature Branch**: `004-scenario-analysis`
**Created**: 2026-01-12
**Status**: Draft
**Input**: User description: "Provide Scenario Analysis features: run a single scenario (one adoption rate + one contribution rate) and return the full ACP outcome details needed for interpretation (PASS/FAIL, NHCE ACP, HCE ACP, max allowed ACP, margin, which limit bound, contributor counts, and total mega-backdoor amount). Also support running a grid of scenarios and returning a structured results set plus a compact summary (pass/fail/risk counts, first failure point, max safe contribution, worst margin). Define what RISK means (e.g., near the boundary) and the acceptance criteria for correctness, determinism, and performance expectations."

## Clarifications

### Session 2026-01-12

- Q: How should the system report edge case conditions (e.g., zero HCEs, zero NHCEs)? → A: Return ScenarioResult with status="ERROR" and error_message field
- Q: Should scenario results include detailed calculation breakdowns for audit/debugging? → A: Include only when optional debug flag is set

## Overview

This feature provides the core scenario analysis engine for ACP sensitivity testing. It enables users to run individual scenarios or comprehensive grid analyses to understand how mega-backdoor Roth contributions affect ACP test outcomes. The feature introduces a "RISK" classification for scenarios that pass but are dangerously close to failure thresholds, giving analysts actionable warning signals.

## Definitions

### RISK Status Definition

A scenario is classified as **RISK** when:
- The scenario **PASSES** the ACP test, BUT
- The **margin** (distance between HCE ACP and the applicable threshold) is **less than or equal to 0.50 percentage points**

**Rationale**: A 0.50 percentage point margin represents a buffer that could easily be eroded by:
- Late-year contribution adjustments by a few participants
- Compensation corrections
- Reclassification of HCE/NHCE status after true-up
- Minor census data corrections

**Status Classification**:

| Status | Condition                                 |
|--------|-------------------------------------------|
| PASS   | HCE ACP ≤ threshold AND margin > 0.50     |
| RISK   | HCE ACP ≤ threshold AND margin ≤ 0.50     |
| FAIL   | HCE ACP > threshold                       |
| ERROR  | Scenario cannot be calculated (e.g., zero HCEs, zero NHCEs) |

## User Scenarios & Testing

### User Story 1 - Single Scenario Execution (Priority: P1)

An analyst runs a single scenario with a specific adoption rate and contribution rate to get complete ACP test outcome details, including all data points needed to interpret and explain the result.

**Why this priority**: This is the foundational capability. Every other feature (grid analysis, summaries) depends on being able to run a single scenario correctly and return comprehensive results.

**Independent Test**: Can be fully tested by providing a census, one adoption rate (e.g., 50%), one contribution rate (e.g., 6%), and verifying all output fields are returned with correct values matching manual calculation.

**Acceptance Scenarios**:

1. **Given** a valid census with HCE and NHCE participants, **When** the analyst runs a scenario with 50% adoption rate and 6% contribution rate, **Then** the system returns a complete result containing: status (PASS/FAIL/RISK), NHCE ACP (percentage), HCE ACP (percentage), max allowed ACP (threshold value), margin (percentage points), limiting bound (which test formula determined the threshold), HCE contributor count, NHCE contributor count, and total mega-backdoor dollar amount.

2. **Given** a valid census, **When** the analyst runs multiple scenarios with the same parameters and same random seed, **Then** the system returns identical results every time (determinism requirement).

3. **Given** a scenario where HCE ACP is 5.25% and the threshold is 5.50%, **When** the scenario is analyzed, **Then** the status is "RISK" because the margin (0.25 percentage points) is below the 0.50 threshold.

4. **Given** a scenario that fails the ACP test, **When** analyzed, **Then** the margin is reported as a negative value indicating how far over the threshold the HCE ACP is.

---

### User Story 2 - Grid Scenario Execution (Priority: P2)

An analyst runs a grid of scenarios across multiple adoption rates and contribution rates to explore the compliance landscape comprehensively.

**Why this priority**: Grid analysis provides strategic value by mapping the entire pass/fail terrain, but requires P1's single scenario capability as its foundation.

**Independent Test**: Can be tested by providing a census and a 3x3 grid (3 adoption rates × 3 contribution rates = 9 scenarios), verifying all 9 results are returned in a structured format.

**Acceptance Scenarios**:

1. **Given** a valid census, **When** the analyst runs a grid with adoption rates [25%, 50%, 75%] and contribution rates [4%, 6%, 8%], **Then** the system returns a structured results set containing 9 individual scenario results (one for each combination).

2. **Given** a grid analysis request, **When** executed, **Then** results are organized in a two-dimensional structure indexed by adoption rate and contribution rate for easy lookup.

3. **Given** a grid with multiple scenarios using the same random seed, **When** run multiple times, **Then** all 9 scenarios produce identical results each time.

---

### User Story 3 - Grid Summary Generation (Priority: P2)

An analyst receives a compact summary of grid results that highlights key findings without requiring manual review of every cell.

**Why this priority**: Summary statistics transform raw grid data into actionable insights, delivered alongside the grid results.

**Independent Test**: Can be tested by running a grid with known pass/fail distribution and verifying summary metrics match expected counts and values.

**Acceptance Scenarios**:

1. **Given** a completed grid analysis with 5 PASS, 3 RISK, and 2 FAIL scenarios, **When** the summary is generated, **Then** it reports: pass_count=5, risk_count=3, fail_count=2, total_count=10.

2. **Given** a grid where the first failure occurs at 75% adoption / 8% contribution, **When** the summary is generated, **Then** first_failure_point reports adoption_rate=75 and contribution_rate=8.

3. **Given** a grid where the highest contribution rate that passes at 100% adoption is 6%, **When** the summary is generated, **Then** max_safe_contribution reports 6.0 (at full adoption).

4. **Given** a grid with varying margins, **When** the summary is generated, **Then** worst_margin reports the smallest margin value across all scenarios (most negative or smallest positive).

5. **Given** a grid where all scenarios pass, **When** the summary is generated, **Then** first_failure_point is null/None indicating no failures.

---

### User Story 4 - Edge Case Handling (Priority: P3)

The system handles boundary conditions and unusual census configurations gracefully with clear, informative responses.

**Why this priority**: Robust edge case handling ensures reliability but is less critical than core happy-path functionality.

**Independent Test**: Can be tested by providing edge-case census files and parameters, verifying appropriate error messages or valid results.

**Acceptance Scenarios**:

1. **Given** a census with zero HCE participants, **When** a scenario is run, **Then** the system returns an informative result indicating ACP test is not applicable (no HCEs to test).

2. **Given** a census with zero NHCE participants, **When** a scenario is run, **Then** the system handles the division case gracefully and reports that the test cannot be completed (NHCE ACP would be undefined).

3. **Given** 0% adoption rate, **When** a scenario is run, **Then** the system returns a valid result where HCE ACP only includes their existing contributions (no mega-backdoor), and contributor_count for mega-backdoor is 0.

4. **Given** 100% adoption rate, **When** a scenario is run, **Then** all HCEs are selected as mega-backdoor contributors.

---

### Edge Cases

- What happens when adoption rate is not a round percentage of HCE count? System rounds the selected count to nearest integer (e.g., 50% of 5 HCEs = 2.5 → 3 selected).
- What happens when contribution rate exceeds legal limits? System calculates using provided rate but may flag a warning; does not block calculation.
- How does the system handle a census with exactly one participant? System calculates correctly; if that participant is an HCE, NHCE ACP may be undefined.
- What happens with floating-point precision in ACP calculations? System uses sufficient precision internally and rounds final display values to 2 decimal places.
- What happens when all scenarios in a grid PASS? Summary reports pass_count equal to total, first_failure_point as null, risk_count may be non-zero if any are near threshold.

## Requirements

### Functional Requirements

#### Single Scenario Execution
- **FR-001**: System MUST accept a scenario request containing: census data reference, adoption rate (0-100%), contribution rate (0-100% of compensation), and optional random seed.
- **FR-002**: System MUST return a complete ScenarioResult containing all fields defined in Key Entities section.
- **FR-003**: System MUST calculate HCE ACP as: average of [(existing match + existing after-tax + simulated mega-backdoor) / compensation] for all HCEs, where simulated mega-backdoor is added only for selected HCE contributors.
- **FR-004**: System MUST calculate NHCE ACP as: average of [(existing match + existing after-tax) / compensation] for all NHCEs.
- **FR-005**: System MUST apply the IRS dual-test criteria: threshold = minimum of (NHCE_ACP × 1.25) and (NHCE_ACP + 2.0, capped at NHCE_ACP × 2.0).
- **FR-006**: System MUST determine limiting_bound as "MULTIPLE" when the 1.25× test is more restrictive, or "ADDITIVE" when the +2.0 test is more restrictive.
- **FR-007**: System MUST calculate margin as: (threshold - HCE_ACP), which is positive for passing scenarios and negative for failing scenarios.
- **FR-008**: System MUST classify status as PASS (margin > 0.50), RISK (0 < margin ≤ 0.50), FAIL (margin ≤ 0), or ERROR (calculation not possible due to edge case).
- **FR-009**: System MUST count and return hce_contributor_count (HCEs receiving simulated mega-backdoor contributions) and nhce_contributor_count (NHCEs with any match or after-tax contributions).
- **FR-010**: System MUST calculate and return total_mega_backdoor_amount as the sum of all simulated mega-backdoor contributions across selected HCEs.

#### HCE Selection for Partial Adoption
- **FR-011**: System MUST select HCEs for partial adoption using deterministic random selection seeded by the provided random seed.
- **FR-012**: System MUST provide a default random seed value when none is specified, ensuring reproducibility within a session.
- **FR-013**: System MUST return the actual seed used in the scenario result for audit purposes.

#### Grid Scenario Execution
- **FR-014**: System MUST accept a grid request containing: census data reference, list of adoption rates, list of contribution rates, and optional random seed.
- **FR-015**: System MUST execute all combinations of adoption rates × contribution rates (Cartesian product).
- **FR-016**: System MUST return results as a structured GridResult containing individual ScenarioResults indexed by (adoption_rate, contribution_rate).
- **FR-017**: System MUST use the same random seed for all scenarios within a single grid execution to ensure consistent HCE selection patterns across comparable scenarios.

#### Grid Summary
- **FR-018**: System MUST generate a GridSummary containing: pass_count, risk_count, fail_count, total_count.
- **FR-019**: System MUST identify first_failure_point as the scenario with lowest contribution rate that fails at the highest adoption rate where failure first occurs, or null if no failures.
- **FR-020**: System MUST identify max_safe_contribution as the highest contribution rate that passes at 100% adoption (or at the highest tested adoption rate if 100% not in grid).
- **FR-021**: System MUST calculate worst_margin as the minimum margin value across all scenarios in the grid.

#### Debug Mode
- **FR-022**: System MUST accept an optional include_debug flag in scenario and grid requests.
- **FR-023**: When include_debug=true, system MUST include debug_details in ScenarioResult containing: selected HCE IDs, per-participant contribution breakdowns, and intermediate calculation values.
- **FR-024**: When include_debug=false or omitted, system MUST omit debug_details from the response to minimize payload size.

#### Determinism and Reproducibility
- **FR-025**: System MUST produce identical results when given identical inputs (census, parameters, seed).
- **FR-026**: System MUST not rely on any external state, current time, or random sources that are not seeded by the input parameters.

### Key Entities

- **ScenarioRequest**: Input parameters for running a single scenario
  - census_id: Reference to the census data
  - adoption_rate: Percentage of HCEs who participate (0.0 to 1.0)
  - contribution_rate: Mega-backdoor contribution as percentage of compensation (0.0 to 1.0)
  - seed: Optional random seed for HCE selection
  - include_debug: Optional boolean flag to request detailed calculation breakdown (default: false)

- **ScenarioResult**: Complete output of a single scenario analysis
  - status: "PASS" | "RISK" | "FAIL" | "ERROR"
  - nhce_acp: NHCE Actual Contribution Percentage (decimal, e.g., 0.0450 for 4.50%); null if ERROR
  - hce_acp: HCE Actual Contribution Percentage (decimal); null if ERROR
  - max_allowed_acp: The threshold value that HCE ACP must not exceed (decimal); null if ERROR
  - margin: Distance from threshold (positive = passing, negative = failing); null if ERROR
  - limiting_bound: "MULTIPLE" (1.25× test) | "ADDITIVE" (+2.0 test); null if ERROR
  - hce_contributor_count: Number of HCEs receiving mega-backdoor contributions; null if ERROR
  - nhce_contributor_count: Number of NHCEs with any qualifying contributions; null if ERROR
  - total_mega_backdoor_amount: Sum of simulated mega-backdoor contributions (dollars); null if ERROR
  - seed_used: The actual random seed applied for HCE selection
  - adoption_rate: Echo of input for context
  - contribution_rate: Echo of input for context
  - error_message: Human-readable description of why calculation failed; null if not ERROR
  - debug_details: Optional detailed breakdown; present only when include_debug=true
    - selected_hce_ids: List of participant IDs selected for mega-backdoor contributions
    - hce_contributions: Per-HCE contribution details (id, compensation, existing_acp_contributions, simulated_mega_backdoor)
    - nhce_contributions: Per-NHCE contribution details (id, compensation, acp_contributions)
    - intermediate_values: Calculation intermediates (hce_sum, nhce_sum, both_thresholds)

- **GridRequest**: Input parameters for running a grid of scenarios
  - census_id: Reference to the census data
  - adoption_rates: List of adoption rate values to test
  - contribution_rates: List of contribution rate values to test
  - seed: Optional random seed (applied consistently across all scenarios)
  - include_debug: Optional boolean flag to request detailed calculation breakdown for each scenario (default: false)

- **GridResult**: Complete output of a grid analysis
  - scenarios: Two-dimensional map of ScenarioResults indexed by (adoption_rate, contribution_rate)
  - summary: GridSummary with aggregate metrics

- **GridSummary**: Compact summary statistics of a grid analysis
  - pass_count: Number of scenarios with PASS status
  - risk_count: Number of scenarios with RISK status
  - fail_count: Number of scenarios with FAIL status
  - total_count: Total number of scenarios in grid
  - first_failure_point: {adoption_rate, contribution_rate} of first failure, or null
  - max_safe_contribution: Highest contribution rate that passes at maximum tested adoption rate
  - worst_margin: Smallest margin value across all scenarios

## Success Criteria

### Correctness
- **SC-001**: 100% of scenario calculations match manual spreadsheet verification with variance < 0.001 percentage points
- **SC-002**: Status classification (PASS/RISK/FAIL) is correct for 100% of test cases based on margin calculation
- **SC-003**: Limiting bound identification is correct for 100% of scenarios (verified against manual test selection)

### Determinism
- **SC-004**: Running the same scenario 100 times with the same seed produces identical results 100% of the time
- **SC-005**: Running the same grid analysis 10 times with the same seed produces identical results 100% of the time

### Performance
- **SC-006**: Single scenario execution completes within 100 milliseconds for a census of 10,000 participants
- **SC-007**: Grid analysis of 100 scenarios (10×10) completes within 5 seconds for a census of 10,000 participants
- **SC-008**: Grid analysis scales linearly with scenario count (e.g., 400 scenarios takes approximately 4× as long as 100 scenarios)

### Usability
- **SC-009**: All output fields are present and correctly typed in every ScenarioResult
- **SC-010**: Grid summary metrics are accurate within 0 tolerance (exact counts, not approximations)

## Assumptions

- Census data is already loaded and validated by the census management feature (spec 002)
- HCE/NHCE classification is provided in census data, not calculated by this feature
- Compensation values are annual and already validated as positive numbers
- Contribution rates in census represent current deferral rates (not simulated)
- The 0.50 percentage point RISK threshold is fixed and not user-configurable (though implementation may parameterize it)
- All monetary amounts are in the same currency (no currency conversion needed)
- Performance targets assume modern hardware and are not guaranteed on constrained environments

## Out of Scope

- Census upload and validation (covered by spec 002)
- Persistent storage of scenario results (results are returned but not automatically saved)
- UI/visualization components (this spec covers the calculation engine only)
- Export functionality (covered by spec 001, User Story 3)
- QMAC/QNEC corrective contribution modeling
- ADP testing (only ACP testing is in scope)
- Parallel or distributed computation optimization
