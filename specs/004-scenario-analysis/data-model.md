# Data Model: Scenario Analysis

**Feature**: 004-scenario-analysis
**Date**: 2026-01-12

## Overview

This document defines the data structures for the Scenario Analysis feature. All entities are transient (computed on request, not persisted) except for references to existing Census data.

---

## Enumerations

### ScenarioStatus

```
Enum: ScenarioStatus
Values:
  - PASS    # HCE ACP ≤ threshold AND margin > 0.50
  - RISK    # HCE ACP ≤ threshold AND margin ≤ 0.50
  - FAIL    # HCE ACP > threshold
  - ERROR   # Calculation not possible (edge case)
```

### LimitingBound

```
Enum: LimitingBound
Values:
  - MULTIPLE   # 1.25× test is more restrictive
  - ADDITIVE   # +2.0 test is more restrictive
```

---

## Request Entities

### ScenarioRequest

Input parameters for running a single scenario analysis.

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| census_id | string | Yes | - | Valid census UUID | Reference to loaded census data |
| adoption_rate | float | Yes | - | 0.0 to 1.0 | Fraction of HCEs participating in mega-backdoor |
| contribution_rate | float | Yes | - | 0.0 to 1.0 | Mega-backdoor contribution as fraction of compensation |
| seed | integer | No | System-generated | Positive integer | Random seed for HCE selection reproducibility |
| include_debug | boolean | No | false | - | Include detailed calculation breakdown |

**Validation Rules**:
- `adoption_rate` and `contribution_rate` must be between 0.0 and 1.0 inclusive
- `seed` if provided must be a positive integer
- `census_id` must reference an existing, valid census

---

### GridRequest

Input parameters for running a grid of scenarios.

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| census_id | string | Yes | - | Valid census UUID | Reference to loaded census data |
| adoption_rates | list[float] | Yes | - | 2-20 values, each 0.0-1.0 | Adoption rates to test |
| contribution_rates | list[float] | Yes | - | 2-20 values, each 0.0-1.0 | Contribution rates to test |
| seed | integer | No | System-generated | Positive integer | Base seed for all scenarios |
| include_debug | boolean | No | false | - | Include debug details in each result |

**Validation Rules**:
- Both rate lists must have 2-20 values
- All rate values must be between 0.0 and 1.0 inclusive
- Duplicate values in rate lists are allowed but not recommended

---

## Response Entities

### ScenarioResult

Complete output of a single scenario analysis.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| status | ScenarioStatus | No | PASS, RISK, FAIL, or ERROR |
| nhce_acp | float | Yes* | NHCE Actual Contribution Percentage (0.0-1.0 scale) |
| hce_acp | float | Yes* | HCE Actual Contribution Percentage (0.0-1.0 scale) |
| max_allowed_acp | float | Yes* | Threshold value HCE ACP must not exceed |
| margin | float | Yes* | Distance from threshold (positive=passing, negative=failing) |
| limiting_bound | LimitingBound | Yes* | Which test formula determined the threshold |
| hce_contributor_count | integer | Yes* | Number of HCEs receiving simulated mega-backdoor |
| nhce_contributor_count | integer | Yes* | Number of NHCEs with any qualifying contributions |
| total_mega_backdoor_amount | float | Yes* | Sum of simulated contributions in dollars |
| seed_used | integer | No | Actual random seed applied |
| adoption_rate | float | No | Echo of input |
| contribution_rate | float | No | Echo of input |
| error_message | string | Yes | Description of error; null if status != ERROR |
| debug_details | DebugDetails | Yes | Detailed breakdown; present only if include_debug=true |

*Nullable when status = ERROR

**Relationships**:
- Contains optional `DebugDetails` (1:0..1)

---

### DebugDetails

Detailed calculation breakdown for audit/debugging.

| Field | Type | Description |
|-------|------|-------------|
| selected_hce_ids | list[string] | IDs of HCEs selected for mega-backdoor |
| hce_contributions | list[ParticipantContribution] | Per-HCE contribution details |
| nhce_contributions | list[ParticipantContribution] | Per-NHCE contribution details |
| intermediate_values | IntermediateValues | Calculation intermediates |

---

### ParticipantContribution

Per-participant contribution breakdown.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Participant internal ID |
| compensation_cents | integer | Annual compensation in cents |
| existing_acp_contributions_cents | integer | Match + after-tax in cents |
| simulated_mega_backdoor_cents | integer | Simulated contribution in cents (0 for non-adopters) |
| individual_acp | float | This participant's ACP percentage |

---

### IntermediateValues

Calculation intermediate values for debugging.

| Field | Type | Description |
|-------|------|-------------|
| hce_acp_sum | float | Sum of individual HCE ACPs before averaging |
| hce_count | integer | Number of HCEs in calculation |
| nhce_acp_sum | float | Sum of individual NHCE ACPs before averaging |
| nhce_count | integer | Number of NHCEs in calculation |
| threshold_multiple | float | NHCE ACP × 1.25 |
| threshold_additive | float | NHCE ACP + 2.0 (capped at 2× NHCE ACP) |

---

### GridResult

Complete output of a grid analysis.

| Field | Type | Description |
|-------|------|-------------|
| scenarios | dict[tuple[float,float], ScenarioResult] | Results indexed by (adoption_rate, contribution_rate) |
| summary | GridSummary | Aggregate metrics |
| seed_used | integer | Base seed used for all scenarios |

**Note**: In API serialization, `scenarios` is represented as a list with each result containing its own adoption_rate/contribution_rate for JSON compatibility.

---

### GridSummary

Compact summary statistics.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| pass_count | integer | No | Scenarios with PASS status |
| risk_count | integer | No | Scenarios with RISK status |
| fail_count | integer | No | Scenarios with FAIL status |
| error_count | integer | No | Scenarios with ERROR status |
| total_count | integer | No | Total scenarios in grid |
| first_failure_point | FailurePoint | Yes | First failure coordinates; null if no failures |
| max_safe_contribution | float | Yes | Highest passing contribution at max adoption; null if none pass |
| worst_margin | float | No | Smallest margin value across all scenarios |

---

### FailurePoint

Coordinates of a failure in the grid.

| Field | Type | Description |
|-------|------|-------------|
| adoption_rate | float | Adoption rate where failure occurred |
| contribution_rate | float | Contribution rate where failure occurred |

---

## Entity Relationships

```
ScenarioRequest (input)
    └── references Census (external, by census_id)

GridRequest (input)
    └── references Census (external, by census_id)

ScenarioResult (output)
    └── contains DebugDetails (optional, 0..1)
            ├── contains ParticipantContribution (0..n for HCEs)
            ├── contains ParticipantContribution (0..n for NHCEs)
            └── contains IntermediateValues (1)

GridResult (output)
    ├── contains ScenarioResult (n, one per grid cell)
    └── contains GridSummary (1)
            └── contains FailurePoint (optional, 0..1)
```

---

## State Transitions

This feature has no persistent state. All entities are computed on request and returned immediately. The only state reference is to Census data managed by the Census Management feature (spec 002).

---

## Validation Rules Summary

| Rule ID | Entity | Field(s) | Validation |
|---------|--------|----------|------------|
| V001 | ScenarioRequest | adoption_rate | 0.0 ≤ value ≤ 1.0 |
| V002 | ScenarioRequest | contribution_rate | 0.0 ≤ value ≤ 1.0 |
| V003 | ScenarioRequest | census_id | Must exist and be valid |
| V004 | GridRequest | adoption_rates | 2-20 items, each 0.0-1.0 |
| V005 | GridRequest | contribution_rates | 2-20 items, each 0.0-1.0 |
| V006 | ScenarioResult | status=ERROR | All calculation fields must be null |
| V007 | ScenarioResult | status≠ERROR | All calculation fields must be non-null |
| V008 | GridSummary | counts | pass + risk + fail + error = total |
