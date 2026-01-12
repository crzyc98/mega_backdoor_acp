# Data Model: CSV Import + Column Mapping Wizard

**Feature**: 003-csv-import-wizard
**Date**: 2026-01-12

## Entity Overview

This feature introduces 4 new entities and extends 1 existing entity:

| Entity | Type | Purpose |
|--------|------|---------|
| ImportSession | New | Tracks wizard state and progress |
| MappingProfile | New | Saved column mapping configurations |
| ValidationIssue | New | Individual validation problem details |
| ImportLog | New | Completed import results and audit trail |
| CensusRecord | Extended | Target entity with new required fields |

## New Entities

### ImportSession

Represents an in-progress import wizard session.

```
ImportSession
├── id: UUID (PK)
├── user_id: string (optional, for future multi-user)
├── created_at: datetime
├── updated_at: datetime
├── expires_at: datetime (created_at + 24 hours)
├── current_step: enum [upload, map, validate, preview, confirm, completed]
├── file_reference: string (temp file path)
├── original_filename: string
├── file_size_bytes: integer
├── row_count: integer (null until parsed)
├── headers: JSON array of strings
├── column_mapping: JSON object {target_field: source_column}
├── validation_results: JSON object (summary + issues)
├── duplicate_resolution: JSON object {ssn: 'replace'|'skip'}
└── import_result_id: UUID (FK to ImportLog, set after completion)
```

**State Transitions**:
```
upload → map (file uploaded, headers extracted)
map → validate (all required fields mapped)
validate → preview (validation complete)
preview → confirm (user reviewed results)
confirm → completed (import executed)
```

**Constraints**:
- Session expires 24 hours after creation
- Only one active session per user (if user_id provided)
- File reference must be valid path
- current_step progression is linear (no skipping)

### MappingProfile

Saved column mapping configuration for reuse.

```
MappingProfile
├── id: UUID (PK)
├── user_id: string (optional)
├── name: string (max 255, unique per user)
├── description: string (optional)
├── created_at: datetime
├── updated_at: datetime
├── column_mapping: JSON object {target_field: source_column}
└── expected_headers: JSON array of strings (for matching)
```

**Constraints**:
- Name must be unique per user_id
- Name max length: 255 characters
- column_mapping must include all 9 required fields

**Relationships**:
- One user can have many profiles
- Profile can be applied to many import sessions

### ValidationIssue

Individual data quality problem found during validation.

```
ValidationIssue
├── id: UUID (PK)
├── session_id: UUID (FK to ImportSession)
├── row_number: integer (1-indexed from CSV)
├── field_name: string (target field identifier)
├── source_column: string (original CSV column name)
├── severity: enum [error, warning, info]
├── issue_code: string (machine-readable code)
├── message: string (user-friendly description)
├── suggestion: string (optional resolution hint)
├── raw_value: string (the problematic value)
└── related_row: integer (optional, for duplicate references)
```

**Issue Codes**:
| Code | Severity | Description |
|------|----------|-------------|
| MISSING_REQUIRED | error | Required field is empty |
| INVALID_SSN | error | SSN not 9 digits |
| INVALID_DATE | error | Date format unrecognized |
| INVALID_AMOUNT | error | Not a valid dollar amount |
| NEGATIVE_AMOUNT | error | Dollar amount is negative |
| DUPLICATE_IN_FILE | error | SSN appears multiple times in file |
| DUPLICATE_EXISTING | warning | SSN exists in database |
| DATE_FORMAT_CONVERTED | info | Date auto-converted from different format |
| OPTIONAL_MISSING | info | Optional field not mapped |

**Constraints**:
- session_id is required
- row_number must be positive
- severity must be one of: error, warning, info

### ImportLog

Completed import operation results and audit trail.

```
ImportLog
├── id: UUID (PK)
├── session_id: UUID (FK to ImportSession)
├── census_id: UUID (FK to Census, if created)
├── created_at: datetime
├── completed_at: datetime
├── original_filename: string
├── total_rows: integer
├── imported_count: integer
├── rejected_count: integer
├── warning_count: integer
├── replaced_count: integer (existing records updated)
├── skipped_count: integer (duplicates skipped)
├── column_mapping_used: JSON object
├── detailed_results: JSON array (per-row outcomes)
└── deleted_at: datetime (null, for soft delete)
```

**Constraints**:
- Retained indefinitely until deleted_at is set
- detailed_results includes row-by-row import status
- total_rows = imported_count + rejected_count

**Relationships**:
- One-to-one with ImportSession
- One-to-one with Census (the created census record)

## Extended Entity

### CensusRecord (Census + Participant)

The existing Census and Participant entities are extended with new fields.

**New Required Fields for Participant**:
```
Participant (extended)
├── ... existing fields ...
├── ssn_hash: string (hashed SSN for duplicate detection)
├── dob: date
├── hire_date: date
├── employee_pre_tax_cents: integer
├── employee_after_tax_cents: integer
├── employee_roth_cents: integer
├── employer_match_cents: integer
└── employer_non_elective_cents: integer
```

**Note**: SSN is hashed before storage (privacy). The hash is used for duplicate detection. Original SSN is never stored.

## Database Schema Extensions

### New Tables

```sql
-- Import wizard session state
CREATE TABLE IF NOT EXISTS import_session (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL,
    current_step TEXT NOT NULL DEFAULT 'upload'
        CHECK (current_step IN ('upload', 'map', 'validate', 'preview', 'confirm', 'completed')),
    file_reference TEXT,
    original_filename TEXT,
    file_size_bytes INTEGER,
    row_count INTEGER,
    headers TEXT,  -- JSON array
    column_mapping TEXT,  -- JSON object
    validation_results TEXT,  -- JSON object
    duplicate_resolution TEXT,  -- JSON object
    import_result_id TEXT REFERENCES import_log(id)
);

-- Saved column mapping profiles
CREATE TABLE IF NOT EXISTS mapping_profile (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    column_mapping TEXT NOT NULL,  -- JSON object
    expected_headers TEXT,  -- JSON array
    UNIQUE (user_id, name)
);

-- Validation issues (denormalized for query performance)
CREATE TABLE IF NOT EXISTS validation_issue (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES import_session(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL CHECK (row_number > 0),
    field_name TEXT NOT NULL,
    source_column TEXT,
    severity TEXT NOT NULL CHECK (severity IN ('error', 'warning', 'info')),
    issue_code TEXT NOT NULL,
    message TEXT NOT NULL,
    suggestion TEXT,
    raw_value TEXT,
    related_row INTEGER
);

-- Import logs with indefinite retention
CREATE TABLE IF NOT EXISTS import_log (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES import_session(id),
    census_id TEXT REFERENCES census(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    original_filename TEXT NOT NULL,
    total_rows INTEGER NOT NULL,
    imported_count INTEGER NOT NULL DEFAULT 0,
    rejected_count INTEGER NOT NULL DEFAULT 0,
    warning_count INTEGER NOT NULL DEFAULT 0,
    replaced_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,
    column_mapping_used TEXT NOT NULL,  -- JSON object
    detailed_results TEXT,  -- JSON array
    deleted_at TEXT  -- soft delete
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_import_session_expires ON import_session(expires_at);
CREATE INDEX IF NOT EXISTS idx_import_session_user ON import_session(user_id);
CREATE INDEX IF NOT EXISTS idx_mapping_profile_user ON mapping_profile(user_id);
CREATE INDEX IF NOT EXISTS idx_validation_issue_session ON validation_issue(session_id);
CREATE INDEX IF NOT EXISTS idx_validation_issue_severity ON validation_issue(session_id, severity);
CREATE INDEX IF NOT EXISTS idx_import_log_census ON import_log(census_id);
CREATE INDEX IF NOT EXISTS idx_import_log_created ON import_log(created_at DESC);
```

### Participant Table Extension

```sql
-- Add new columns to existing participant table
ALTER TABLE participant ADD COLUMN ssn_hash TEXT;
ALTER TABLE participant ADD COLUMN dob TEXT;
ALTER TABLE participant ADD COLUMN hire_date TEXT;
ALTER TABLE participant ADD COLUMN employee_pre_tax_cents INTEGER DEFAULT 0;
ALTER TABLE participant ADD COLUMN employee_after_tax_cents INTEGER DEFAULT 0;
ALTER TABLE participant ADD COLUMN employee_roth_cents INTEGER DEFAULT 0;
ALTER TABLE participant ADD COLUMN employer_match_cents INTEGER DEFAULT 0;
ALTER TABLE participant ADD COLUMN employer_non_elective_cents INTEGER DEFAULT 0;

-- Index for duplicate detection
CREATE INDEX IF NOT EXISTS idx_participant_ssn_hash ON participant(ssn_hash);
```

## Validation Rules

### Field-Level Validation

| Field | Type | Validation Rules | On Invalid |
|-------|------|------------------|------------|
| SSN | string | Exactly 9 digits, no dashes | Error |
| DOB | date | Valid date, not future, reasonable range (1900-today) | Error |
| Hire Date | date | Valid date, not future | Error |
| Compensation | decimal | Non-negative, max 10M | Error |
| Employee Pre Tax | decimal | Non-negative, max 100k | Error |
| Employee After Tax | decimal | Non-negative, max 100k | Error |
| Employee Roth | decimal | Non-negative, max 100k | Error |
| Employer Match | decimal | Non-negative, max 100k | Error |
| Employer Non Elective | decimal | Non-negative, max 100k | Error |

### Row-Level Validation

| Rule | Condition | Severity |
|------|-----------|----------|
| All required fields present | Any of 9 fields null/empty | Error |
| SSN unique in file | SSN appears more than once | Error |
| SSN not in database | SSN hash matches existing participant | Warning |

### File-Level Validation

| Rule | Condition | Severity |
|------|-----------|----------|
| File not empty | Zero data rows | Error |
| File size limit | > 50MB | Error |
| Encoding supported | Not UTF-8 or Latin-1 | Error |
| Headers present | No header row detected | Error |

## Data Flow

```
CSV Upload
    │
    ▼
Parse Headers → Store in session.headers
    │
    ▼
Auto-Map Columns → Suggest session.column_mapping
    │
    ▼
User Adjusts Mapping → Update session.column_mapping
    │
    ▼
Validate All Rows → Create ValidationIssue records
    │                 Update session.validation_results
    ▼
User Reviews → May update session.duplicate_resolution
    │
    ▼
Execute Import → Create Participant records
    │             Create Census record
    │             Create ImportLog record
    ▼
Session Completed → session.current_step = 'completed'
```
