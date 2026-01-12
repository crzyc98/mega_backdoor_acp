# Data Model: Census Management

**Feature**: 002-census-management
**Date**: 2026-01-12
**Status**: Complete

## Entity Overview

This feature extends the existing Census and Participant models and adds ImportMetadata for tracking import configuration.

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     Census      │──────<│   Participant   │       │  ImportMetadata │
│  (extended)     │1    N │   (unchanged)   │       │     (new)       │
└────────┬────────┘       └─────────────────┘       └────────┬────────┘
         │                                                    │
         └────────────────────────1:1─────────────────────────┘
```

## Entities

### Census (Extended)

A named collection of participant data representing a point-in-time snapshot of a plan's population.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | TEXT | PK | UUID, auto-generated |
| name | TEXT | NOT NULL, max 255 chars | User-provided census name |
| **client_name** | TEXT | NULLABLE, max 255 chars | **NEW**: Optional client/organization name |
| plan_year | INTEGER | NOT NULL, 2020-2100 | Plan year for HCE threshold lookup |
| **hce_mode** | TEXT | NOT NULL, DEFAULT 'explicit' | **NEW**: 'explicit' or 'compensation_threshold' |
| upload_timestamp | TEXT | NOT NULL | ISO 8601 datetime |
| participant_count | INTEGER | NOT NULL, >= 0 | Total participants |
| hce_count | INTEGER | NOT NULL, >= 0 | HCE participants |
| nhce_count | INTEGER | NOT NULL, >= 0 | NHCE participants |
| **avg_compensation_cents** | INTEGER | NULLABLE | **NEW**: Average compensation in cents |
| **avg_deferral_rate** | REAL | NULLABLE | **NEW**: Average deferral rate (0-100) |
| salt | TEXT | NOT NULL | Per-census salt for ID hashing |
| version | TEXT | NOT NULL | System version at creation |

**Validation Rules**:
- `hce_count + nhce_count = participant_count`
- `hce_mode IN ('explicit', 'compensation_threshold')`
- `name` is required and non-empty
- `plan_year` is required and immutable after creation

**State Transitions**:
- Created → Active (on successful import)
- Active → Deleted (on delete with cascade)
- No soft-delete or archived state

### Participant (Unchanged)

An individual employee record within a census. No schema changes needed; existing model is sufficient.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | TEXT | PK | UUID, auto-generated |
| census_id | TEXT | FK → Census.id, ON DELETE CASCADE | Parent census |
| internal_id | TEXT | NOT NULL | Hashed employee ID |
| is_hce | INTEGER | NOT NULL, 0 or 1 | HCE status (calculated at import) |
| compensation_cents | INTEGER | NOT NULL, > 0 | Annual compensation in cents |
| deferral_rate | REAL | NOT NULL, 0-100 | Current deferral percentage |
| match_rate | REAL | NOT NULL, >= 0 | Current match percentage |
| after_tax_rate | REAL | NOT NULL, >= 0 | Current after-tax percentage |

**Validation Rules**:
- `is_hce` is calculated at import based on Census.hce_mode
- When `hce_mode = 'compensation_threshold'`: `is_hce = 1 if compensation >= threshold else 0`
- When `hce_mode = 'explicit'`: `is_hce` comes from source file HCE Status column
- Participant data is immutable after import

### ImportMetadata (New)

Information about how a census was imported, enabling consistent re-analysis.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | TEXT | PK | UUID, auto-generated |
| census_id | TEXT | FK → Census.id, ON DELETE CASCADE, UNIQUE | Parent census (1:1) |
| source_filename | TEXT | NOT NULL | Original uploaded filename |
| column_mapping | TEXT | NOT NULL | JSON object: {source_col: target_field, ...} |
| row_count | INTEGER | NOT NULL, >= 0 | Total rows processed |
| created_at | TEXT | NOT NULL | ISO 8601 import timestamp |

**Column Mapping JSON Schema**:
```json
{
  "employee_id": "Employee ID",
  "compensation": "Annual Compensation",
  "deferral_rate": "Current Deferral Rate",
  "is_hce": "HCE Status",
  "match_rate": "Current Match Rate",
  "after_tax_rate": "Current After-Tax Rate"
}
```

### HCEThreshold (Reference Data)

Historical IRS HCE compensation thresholds by year. Implemented as code constants, not database table.

| Year | Threshold ($) |
|------|--------------|
| 2020 | 130,000 |
| 2021 | 130,000 |
| 2022 | 135,000 |
| 2023 | 150,000 |
| 2024 | 155,000 |
| 2025 | 160,000 |
| 2026 | 165,000 (projected) |

## Database Schema Changes

### New Columns on `census` Table

```sql
ALTER TABLE census ADD COLUMN client_name TEXT;
ALTER TABLE census ADD COLUMN hce_mode TEXT NOT NULL DEFAULT 'explicit'
    CHECK (hce_mode IN ('explicit', 'compensation_threshold'));
ALTER TABLE census ADD COLUMN avg_compensation_cents INTEGER;
ALTER TABLE census ADD COLUMN avg_deferral_rate REAL;
```

### New Table: `import_metadata`

```sql
CREATE TABLE IF NOT EXISTS import_metadata (
    id TEXT PRIMARY KEY,
    census_id TEXT NOT NULL UNIQUE REFERENCES census(id) ON DELETE CASCADE,
    source_filename TEXT NOT NULL,
    column_mapping TEXT NOT NULL,  -- JSON
    row_count INTEGER NOT NULL CHECK (row_count >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_import_metadata_census ON import_metadata(census_id);
```

## Relationships

| From | To | Cardinality | Delete Behavior |
|------|-----|-------------|-----------------|
| Census | Participant | 1:N | CASCADE |
| Census | ImportMetadata | 1:1 | CASCADE |
| Census | AnalysisResult | 1:N | CASCADE (existing) |
| Census | GridAnalysis | 1:N | CASCADE (existing) |

## Data Flows

### Census Import Flow

```
1. User uploads CSV file
2. System detects columns, prompts for mapping if needed
3. User provides: name, client_name (optional), plan_year, hce_mode
4. System validates CSV data against mapping
5. If hce_mode = 'compensation_threshold':
   a. Look up threshold for plan_year
   b. Calculate is_hce for each participant
6. If hce_mode = 'explicit':
   a. Read is_hce from mapped HCE Status column
7. Hash employee IDs with census salt
8. Calculate summary statistics (avg_compensation, avg_deferral_rate)
9. Store Census, Participants, ImportMetadata in transaction
10. Return Census with summary stats
```

### Census Metadata Update Flow

```
1. User requests edit (PATCH /census/{id})
2. Validate only name and client_name are being modified
3. Update Census record
4. Return updated Census
```

### Census Delete Flow

```
1. User requests delete (DELETE /census/{id})
2. Check for associated analyses (AnalysisResult, GridAnalysis)
3. If analyses exist, return warning in response headers
4. Execute DELETE (cascade removes participants, metadata, analyses)
5. Return 204 No Content
```
