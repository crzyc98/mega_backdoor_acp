# Data Model: Fix PDF/CSV Export Counts

**Feature**: 015-pdf-export-counts-fix
**Date**: 2026-01-16

## Overview

This feature does not introduce new data models. It modifies how existing data is processed and displayed in exports.

## Existing Entities (No Changes)

### Census

Imported employee census data. **No schema changes.**

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Primary key |
| plan_year | int | Plan year for analysis |
| participant_count | int | Raw total participants at import |
| hce_count | int | Raw HCE count at import |
| nhce_count | int | Raw NHCE count at import |

### Participant

Individual employee in a census. **No schema changes.**

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Primary key |
| census_id | string (UUID) | Foreign key to Census |
| dob | date | Date of birth (for eligibility) |
| hire_date | date | Hire date (for eligibility) |
| termination_date | date | Termination date (optional) |
| is_hce | boolean | Highly compensated employee flag |

### Run Results (Workspace Context)

Stored analysis results. **No schema changes** - already contains post-exclusion counts.

| Field | Type | Description |
|-------|------|-------------|
| summary.excluded_count | int | Total excluded participants |
| summary.included_hce_count | int | Post-exclusion HCE count |
| summary.included_nhce_count | int | Post-exclusion NHCE count |
| summary.exclusion_breakdown | object | Breakdown by exclusion reason |

## Computed Values (Not Persisted)

For legacy export routes, these values are computed on-the-fly:

### ExportCounts (conceptual, not a stored entity)

| Field | Type | Computation |
|-------|------|-------------|
| included_hce_count | int | Count of participants where `is_hce=True` AND `acp_includable=True` |
| included_nhce_count | int | Count of participants where `is_hce=False` AND `acp_includable=True` |
| excluded_count | int | Count of participants where `acp_includable=False` |
| total_count | int | `included_hce_count + included_nhce_count + excluded_count` |

**Invariant**: `total_count == census.participant_count`

## State Transitions

Not applicable - this feature fixes data display, not state management.

## Validation Rules

1. **Mathematical Consistency**: `included_hce_count + included_nhce_count + excluded_count = participant_count`
2. **Non-negative Counts**: All count fields >= 0
3. **Eligibility Determinism**: Same participant data + plan year → same eligibility result
