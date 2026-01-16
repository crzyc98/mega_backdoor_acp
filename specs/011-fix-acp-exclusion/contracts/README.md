# API Contract Changes: 011-fix-acp-exclusion

## Overview

This feature extends existing API contracts to support new exclusion reasons for data quality errors. All changes are **backward compatible** - new fields have defaults.

## Changed Schemas

### ExclusionInfo

**File**: [exclusion-info.yaml](./exclusion-info.yaml)

| Field | Change | Default |
|-------|--------|---------|
| missing_dob_count | Added | 0 |
| missing_hire_date_count | Added | 0 |

### ACPExclusionReason

**File**: [exclusion-info.yaml](./exclusion-info.yaml)

New enum values:
- `MISSING_DOB`
- `MISSING_HIRE_DATE`

### ExcludedParticipant

**File**: [exclusion-info.yaml](./exclusion-info.yaml)

- `eligibility_date`: Now nullable (null when data error)
- `entry_date`: Now nullable (null when data error)
- `exclusion_reason`: Extended with new values

## Affected Endpoints

No endpoint signatures change. Response bodies may contain new exclusion reasons and counts.

| Endpoint | Response Field | Notes |
|----------|----------------|-------|
| POST /census/{id}/analysis | exclusion_breakdown | New count fields |
| POST /census/{id}/grid | summary.exclusion_breakdown | New count fields |
| POST /census/{id}/impact | exclusion_breakdown | New count fields |

## Migration Notes

- Existing clients will continue to work (new fields are optional/defaulted)
- Clients should handle unknown enum values gracefully
- No database migration required (computed at runtime)
