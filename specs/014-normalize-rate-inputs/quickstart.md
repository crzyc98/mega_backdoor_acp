# Quickstart: Normalize Rate Inputs & HCE/NHCE Validation

**Feature**: 014-normalize-rate-inputs
**Date**: 2026-01-16

## Overview

This feature standardizes rate inputs to decimal format (0.0-1.0) and implements compensation-based HCE determination with distribution validation.

## Key Changes

### 1. Rate Format (Breaking Change)

**Before**: V1 API accepted percentages (0-100)
```json
{
  "adoption_rate": 75,
  "contribution_rate": 6
}
```

**After**: All APIs require decimals (0.0-1.0)
```json
{
  "adoption_rate": 0.75,
  "contribution_rate": 0.06
}
```

### 2. HCE Determination

HCE status is now **always** calculated from compensation:

| Plan Year | HCE Threshold |
|-----------|---------------|
| 2024 | $155,000 |
| 2025 | $160,000 |
| 2026-2028 | $160,000 |

**Rule**: `is_hce = compensation >= threshold_for_year`

### 3. Census Validation

Census files are validated to ensure both HCE and NHCE participants exist.

**Error Response** (when validation fails):
```json
{
  "error": "INVALID_HCE_DISTRIBUTION",
  "message": "Census must contain both HCE and NHCE participants",
  "hce_count": 0,
  "nhce_count": 25,
  "threshold_used": 160000,
  "plan_year": 2025,
  "suggestion": "Census contains no HCE participants. Verify compensation data..."
}
```

## API Examples

### Single Scenario Analysis (V2)

```bash
curl -X POST "http://localhost:8000/api/v2/scenario" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-ID: <workspace-uuid>" \
  -d '{
    "census_id": "census-123",
    "adoption_rate": 0.75,
    "contribution_rate": 0.06
  }'
```

### Grid Analysis (V2)

```bash
curl -X POST "http://localhost:8000/api/v2/grid" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-ID: <workspace-uuid>" \
  -d '{
    "census_id": "census-123",
    "adoption_rates": [0.25, 0.50, 0.75, 1.0],
    "contribution_rates": [0.03, 0.06, 0.10]
  }'
```

### Get HCE Thresholds

```bash
curl "http://localhost:8000/api/v1/hce-thresholds" \
  -H "X-Workspace-ID: <workspace-uuid>"
```

Response:
```json
{
  "thresholds": {
    "2024": 155000,
    "2025": 160000,
    "2026": 160000,
    "2027": 160000,
    "2028": 160000
  }
}
```

## Frontend Integration

### Rate Input Conversion

When displaying rate fields to users:
1. Show values as percentages (e.g., "75%")
2. Convert to decimal on form submission

```typescript
// User enters "6" in percentage field
const userInput = 6;

// Convert to decimal for API
const apiValue = userInput / 100; // 0.06

// Submit to API
await api.post('/api/v2/scenario', {
  adoption_rate: adoptionRate / 100,
  contribution_rate: contributionRate / 100,
  census_id: censusId
});
```

### Handling Rate Validation Errors

```typescript
try {
  await submitScenario(data);
} catch (error) {
  if (error.response?.status === 422) {
    const detail = error.response.data.detail;
    // Show validation message to user
    // e.g., "Adoption rate must be between 0% and 100%"
  }
}
```

## Testing

### Verify Rate Validation

```bash
# Should succeed (valid decimal)
curl -X POST "http://localhost:8000/api/v2/scenario" \
  -d '{"census_id": "x", "adoption_rate": 0.5, "contribution_rate": 0.06}'

# Should fail (percentage instead of decimal)
curl -X POST "http://localhost:8000/api/v2/scenario" \
  -d '{"census_id": "x", "adoption_rate": 50, "contribution_rate": 6}'
# Returns 422 with validation error
```

### Verify HCE Distribution Validation

Upload a census where all employees earn < $160,000 for plan year 2025:
- Should return `INVALID_HCE_DISTRIBUTION` error
- Error includes count of HCEs (0) and NHCEs, plus threshold used

## Migration Notes

1. **V1 endpoints removed**: Update all API calls to use V2 endpoints
2. **Frontend changes required**: Ensure rate values are divided by 100 before submission
3. **HCE mode removed**: Census no longer accepts explicit `is_hce` column; always calculated from compensation
