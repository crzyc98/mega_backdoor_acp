# Data Model: Normalize Rate Inputs & HCE/NHCE Validation

**Date**: 2026-01-16
**Feature**: 014-normalize-rate-inputs

## Entities

### Rate Value

A decimal fraction representing a percentage (0.0 to 1.0).

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| value | float | ge=0.0, le=1.0 | Decimal representation of percentage |

**Usage**: `adoption_rate`, `contribution_rate` in scenario analysis requests.

**Validation Rules**:
- Must be >= 0.0 and <= 1.0
- API rejects values outside range with structured error
- Example: 0.06 represents 6%, 0.75 represents 75%

### HCE Compensation Threshold

IRS-defined annual compensation limit that determines HCE status.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| plan_year | int | 2024-2028 | Plan year for threshold lookup |
| threshold_amount | int | > 0 | Compensation threshold in dollars |

**Threshold Values (per specification)**:
| Plan Year | Threshold |
|-----------|-----------|
| 2024 | $155,000 |
| 2025 | $160,000 |
| 2026 | $160,000 |
| 2027 | $160,000 |
| 2028 | $160,000 |

### Participant HCE Status

Derived boolean indicating Highly Compensated Employee status.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| is_hce | bool | - | True if HCE, False if NHCE |

**Derivation Rule**:
```
is_hce = (compensation >= threshold_for_plan_year)
```

### Census Validation Result

Result of validating a parsed census for HCE distribution.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| is_valid | bool | - | True if census has both HCEs and NHCEs |
| hce_count | int | >= 0 | Number of HCE participants |
| nhce_count | int | >= 0 | Number of NHCE participants |
| threshold_used | int | > 0 | HCE threshold applied |
| plan_year | int | 2024-2028 | Plan year used for calculation |
| error | CensusValidationError | null if valid | Error details if invalid |

**Validation Rule**:
```
is_valid = (hce_count >= 1) AND (nhce_count >= 1)
```

### Census HCE Distribution Error

Structured error returned when census lacks HCE or NHCE participants.

| Attribute | Type | Description |
|-----------|------|-------------|
| error_code | string | "INVALID_HCE_DISTRIBUTION" |
| message | string | Human-readable error message |
| hce_count | int | Number of HCEs found |
| nhce_count | int | Number of NHCEs found |
| threshold_used | int | HCE threshold applied |
| plan_year | int | Plan year for threshold |
| suggestion | string | Remediation guidance |

## Relationships

```
Census ─────1:N────► Participant
   │                    │
   │                    │ (compensation >= threshold) → is_hce
   │                    ▼
   │              HCE Status (bool)
   │
   │──── plan_year ───► HCE Threshold Lookup
                              │
                              ▼
                    threshold_amount ($)
```

## State Transitions

### Census Parsing Flow

```
[CSV Upload]
     │
     ▼
[Parse Rows] ──► Extract compensation
     │
     ▼
[Calculate HCE Status]
     │ For each participant:
     │   is_hce = compensation >= threshold_for_year(plan_year)
     │
     ▼
[Validate Distribution]
     │
     ├─── hce_count >= 1 AND nhce_count >= 1 ───► [Valid Census]
     │
     └─── Otherwise ───► [Return HCE Distribution Error]
```

### Rate Validation Flow

```
[API Request with rate value]
     │
     ▼
[Pydantic Validation]
     │
     ├─── 0.0 <= value <= 1.0 ───► [Accept Request]
     │
     └─── Otherwise ───► [Return Validation Error]
            │
            ▼
        {
          "detail": [{
            "loc": ["body", "adoption_rate"],
            "msg": "ensure this value is less than or equal to 1.0",
            "type": "value_error.number.not_le"
          }]
        }
```

## Schema Changes Summary

### Removed Schemas (V1)
- `SingleScenarioRequest` - percentage-based rate inputs (0-100)
- `GridScenarioRequest` - percentage-based rate inputs (0-100)

### Modified Schemas (V2)
- `ScenarioRequestV2` - Updated description to emphasize decimal format
- `GridRequestV2` - Updated description to emphasize decimal format

### New Schemas
- `CensusHCEDistributionError` - Structured error for invalid HCE distribution
