# Quickstart: Census Management

**Feature**: 002-census-management
**Date**: 2026-01-12

## Prerequisites

- Python 3.11+
- Existing mega_backdoor_acp project setup
- pytest for running tests

## Quick Test

Run existing tests to verify the system is working:

```bash
cd /workspaces/mega_backdoor_acp
pytest tests/ -v
```

## Feature Overview

This feature adds Census Management as a first-class capability:

1. **Create Census**: Import CSV with column mapping and HCE mode selection
2. **List Censuses**: View all censuses with filtering by plan year/client
3. **View Census**: See full details including import metadata and participants
4. **Edit Metadata**: Update census name and client name (participant data immutable)
5. **Delete Census**: Remove with warning if analyses exist

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/census` | Upload new census |
| GET | `/api/v1/census` | List censuses |
| GET | `/api/v1/census/{id}` | Get census details |
| PATCH | `/api/v1/census/{id}` | Update metadata |
| DELETE | `/api/v1/census/{id}` | Delete census |
| GET | `/api/v1/census/{id}/participants` | List participants |
| GET | `/api/v1/census/{id}/metadata` | Get import metadata |
| POST | `/api/v1/census/column-mapping/detect` | Detect column mapping |
| GET | `/api/v1/hce-thresholds` | Get HCE thresholds |

## Example Usage

### 1. Upload a Census with Explicit HCE Mode

```bash
curl -X POST http://localhost:8000/api/v1/census \
  -F "file=@census.csv" \
  -F "name=Q4 2025 Census" \
  -F "client_name=Acme Corp" \
  -F "plan_year=2025" \
  -F "hce_mode=explicit"
```

### 2. Upload with Compensation Threshold Mode

```bash
curl -X POST http://localhost:8000/api/v1/census \
  -F "file=@census.csv" \
  -F "name=Q4 2025 Census" \
  -F "plan_year=2025" \
  -F "hce_mode=compensation_threshold"
```

### 3. List Censuses by Plan Year

```bash
curl "http://localhost:8000/api/v1/census?plan_year=2025"
```

### 4. Update Census Name

```bash
curl -X PATCH http://localhost:8000/api/v1/census/{census_id} \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Census Name"}'
```

### 5. Get Import Metadata (Column Mapping)

```bash
curl http://localhost:8000/api/v1/census/{census_id}/metadata
```

## CSV File Format

### Required Columns (or mapped equivalents)

| Field | Description | Example |
|-------|-------------|---------|
| Employee ID | Unique employee identifier | EMP001 |
| Annual Compensation | Yearly salary in dollars | 150000 |
| Current Deferral Rate | Deferral percentage (0-100) | 6.0 |

### Conditional Columns

| Field | Required When | Description |
|-------|---------------|-------------|
| HCE Status | `hce_mode=explicit` | TRUE/FALSE or 1/0 |

### Optional Columns

| Field | Description |
|-------|-------------|
| Current Match Rate | Match percentage |
| Current After-Tax Rate | After-tax percentage |

### Sample CSV

```csv
Employee ID,Full Name,SSN,Annual Compensation,Current Deferral Rate,Current Match Rate,Current After-Tax Rate,HCE Status
EMP001,John Doe,123-45-6789,175000,6.0,3.0,2.0,TRUE
EMP002,Jane Smith,987-65-4321,85000,4.0,2.0,0.0,FALSE
```

Note: PII columns (Full Name, SSN) are automatically stripped during import.

## HCE Determination Modes

### Explicit Mode (`hce_mode=explicit`)

Uses the HCE Status column from the CSV file directly. The column must contain:
- TRUE/FALSE, True/False, true/false
- 1/0
- Yes/No

### Compensation Threshold Mode (`hce_mode=compensation_threshold`)

Calculates HCE status based on the plan year's IRS threshold:

| Plan Year | Threshold |
|-----------|-----------|
| 2024 | $155,000 |
| 2025 | $160,000 |
| 2026 | $165,000 |

Participants with compensation >= threshold are classified as HCE.

## Key Files to Modify

| File | Changes |
|------|---------|
| `src/storage/models.py` | Add client_name, hce_mode, avg_* fields to Census |
| `src/storage/database.py` | Add import_metadata table, alter census table |
| `src/storage/repository.py` | Add update(), ImportMetadataRepository |
| `src/api/routes/census.py` | Add PATCH endpoint, enhance POST |
| `src/api/schemas.py` | Add new request/response schemas |
| `src/core/census_parser.py` | Add column mapping, HCE mode support |
| `src/core/hce_thresholds.py` | NEW: Historical threshold lookup |
| `src/ui/pages/census_list.py` | NEW: Census list/view/edit UI |

## Testing Strategy

1. **Unit Tests**: HCE threshold lookup, column mapping detection
2. **Integration Tests**: Full import flow with both HCE modes
3. **Contract Tests**: API response schema validation
4. **Edge Cases**: Duplicate IDs, missing columns, invalid values

## Next Steps

After implementation:

1. Run `/speckit.tasks` to generate implementation tasks
2. Implement tasks in dependency order
3. Run tests after each task
4. Create PR when complete
