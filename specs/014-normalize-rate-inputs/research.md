# Research: Normalize Rate Inputs & HCE/NHCE Validation

**Date**: 2026-01-16
**Feature**: 014-normalize-rate-inputs

## Research Tasks

### 1. Current Rate Input Patterns

**Finding**: The codebase has TWO rate input formats currently:

| Schema | Rate Fields | Range | Description Format |
|--------|-------------|-------|-------------------|
| `SingleScenarioRequest` (V1) | adoption_rate, contribution_rate | 0-100, 0-15 | "Percentage of HCEs adopting mega-backdoor (0-100)" |
| `ScenarioRequestV2` (V2) | adoption_rate, contribution_rate | 0.0-1.0 | "Fraction of HCEs participating in mega-backdoor (0.0 to 1.0)" |
| `GridScenarioRequest` (V1) | adoption_rates, contribution_rates | 0-100, 0-15 | "List of adoption rates to test (0-100)" |
| `GridRequestV2` (V2) | adoption_rates, contribution_rates | 0.0-1.0 | "List of adoption rates to test (each 0.0 to 1.0)" |
| `EmployeeImpactRequest` | adoption_rate, contribution_rate | 0.0-1.0 | Already decimal |

**Decision**: Standardize ALL rate fields to decimal format (0.0-1.0)
**Rationale**: V2 format is correct; V1 format creates confusion and requires internal conversion
**Alternatives Rejected**:
- Keeping V1 with conversion layer (adds maintenance burden)
- Auto-detecting format (ambiguous for values like 0.5)

### 2. V1 API Endpoint Usage

**Finding**: V1 endpoints in `backend/app/routers/routes/analysis.py`:
- `POST /api/v1/census/{census_id}/analyze/single` - uses `SingleScenarioRequest`
- `POST /api/v1/census/{census_id}/analyze/grid` - uses `GridScenarioRequest`

V2 endpoints:
- `POST /api/v2/scenario` - uses `ScenarioRequestV2`
- `POST /api/v2/grid` - uses `GridRequestV2`

**Decision**: Remove V1 endpoints entirely (breaking change per clarification)
**Rationale**: Clean break reduces maintenance; frontend is internal and can be updated simultaneously
**Alternatives Rejected**: Deprecation warnings (delays cleanup, extends confusion)

### 3. HCE Threshold Implementation

**Finding**: Existing implementation in `backend/app/services/hce_thresholds.py`:
```python
HCE_THRESHOLDS: dict[int, int] = {
    2020: 130_000,
    2021: 130_000,
    2022: 135_000,
    2023: 150_000,
    2024: 155_000,
    2025: 160_000,
    2026: 165_000,  # Projected - INCORRECT per spec
}
```

**Decision**: Update thresholds per user specification:
- 2024: $155,000 (unchanged)
- 2025: $160,000 (unchanged)
- 2026: $160,000 (change from $165,000)
- 2027: $160,000 (add)
- 2028: $160,000 (add)

**Rationale**: User provided specific threshold values
**Alternatives Rejected**: Using IRS projections (user has specific requirements)

### 4. Census HCE Mode

**Finding**: Current implementation supports two modes:
1. `explicit` - HCE status from CSV column
2. `compensation_threshold` - HCE calculated from compensation

Per clarification, HCE should ALWAYS be calculated from compensation.

**Decision**: Remove `explicit` mode; always use `compensation_threshold` logic
**Rationale**: User clarified HCE determination is always by compensation threshold
**Alternatives Rejected**: Keeping both modes (complicates logic, user doesn't want explicit mode)

### 5. Census Validation for HCE Distribution

**Finding**: No current validation for 0 HCE or 0 NHCE scenarios. The census parser allows any distribution.

**Decision**: Add validation after HCE calculation that requires:
- At least 1 HCE (compensation >= threshold)
- At least 1 NHCE (compensation < threshold)

Return structured error if validation fails:
```python
{
    "error": "INVALID_HCE_DISTRIBUTION",
    "message": "Census must contain both HCE and NHCE participants",
    "hce_count": 0,
    "nhce_count": 25,
    "threshold_used": 160000,
    "plan_year": 2025,
    "suggestion": "Census contains no HCE participants. Verify compensation data is correct or check that some employees earn above the HCE threshold of $160,000 for plan year 2025."
}
```

**Rationale**: ACP testing requires both groups; early validation prevents invalid analyses
**Alternatives Rejected**: Warning instead of error (invalid data would produce meaningless results)

### 6. Frontend Rate Conversion

**Finding**: Frontend forms currently submit rates directly to API. Need to:
1. Display rates as percentages to users (e.g., "75%")
2. Convert to decimal on submission (e.g., 0.75)

**Decision**: Frontend handles conversion at form submission boundary
**Rationale**: Users naturally think in percentages; API contract is decimal-only
**Alternatives Rejected**: API accepting both formats (introduces ambiguity)

## Implementation Impact Summary

### Files to Modify

**Backend (Remove/Modify):**
1. `backend/app/routers/schemas.py` - Remove V1 schemas, update descriptions
2. `backend/app/routers/routes/analysis.py` - Remove V1 endpoints
3. `backend/app/services/hce_thresholds.py` - Update threshold values
4. `backend/app/services/census_parser.py` - Remove explicit HCE mode, add distribution validation

**Backend (Add):**
1. New validation error schema for HCE distribution failures

**Frontend (Modify):**
1. API client services - ensure decimal submission
2. Form components - percentage display with decimal conversion

**Tests (Add/Modify):**
1. Contract tests for new rate validation
2. Unit tests for updated HCE thresholds
3. Integration tests for census HCE distribution validation

## Dependencies

- No new external dependencies required
- All changes use existing Pydantic, FastAPI, pandas patterns
