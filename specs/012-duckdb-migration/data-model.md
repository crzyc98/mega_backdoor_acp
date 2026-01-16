# Data Model: DuckDB Migration

**Feature**: 012-duckdb-migration
**Date**: 2026-01-16

## Overview

This document defines the DuckDB schema for the ACP Sensitivity Analyzer. The schema maintains functional parity with the existing SQLite schema while adapting to DuckDB's native types and conventions.

## Entity Relationship Diagram

```
┌─────────────────┐
│     census      │
├─────────────────┤
│ id (PK)         │◄──────────────────────────────────────┐
│ name            │                                        │
│ client_name     │                                        │
│ plan_year       │                                        │
│ hce_mode        │                                        │
│ upload_timestamp│                                        │
│ participant_cnt │                                        │
│ hce_count       │                                        │
│ nhce_count      │                                        │
│ avg_comp_cents  │                                        │
│ avg_deferral    │                                        │
│ salt            │                                        │
│ version         │                                        │
└─────────────────┘                                        │
        │                                                  │
        │ 1:N                                              │
        ▼                                                  │
┌─────────────────┐     ┌─────────────────┐               │
│   participant   │     │  grid_analysis  │               │
├─────────────────┤     ├─────────────────┤               │
│ id (PK)         │     │ id (PK)         │◄──────┐       │
│ census_id (FK)──┼────►│ census_id (FK)──┼───────┼───────┤
│ internal_id     │     │ name            │       │       │
│ is_hce          │     │ created_ts      │       │       │
│ comp_cents      │     │ seed            │       │       │
│ deferral_rate   │     │ adoption_rates  │       │       │
│ match_rate      │     │ contrib_rates   │       │       │
│ after_tax_rate  │     │ version         │       │       │
│ dob             │     └─────────────────┘       │       │
│ hire_date       │              │                │       │
│ termination_dt  │              │ 1:N            │       │
│ ssn_hash        │              ▼                │       │
│ employee_*_cents│     ┌─────────────────┐       │       │
│ employer_*_cents│     │ analysis_result │       │       │
└─────────────────┘     ├─────────────────┤       │       │
                        │ id (PK)         │       │       │
                        │ census_id (FK)──┼───────┼───────┤
                        │ grid_id (FK)────┼───────┘       │
                        │ adoption_rate   │               │
                        │ contrib_rate    │               │
                        │ seed            │               │
                        │ nhce_acp        │               │
                        │ hce_acp         │               │
                        │ threshold       │               │
                        │ margin          │               │
                        │ result          │               │
                        │ limiting_test   │               │
                        │ run_timestamp   │               │
                        │ version         │               │
                        └─────────────────┘               │
                                                          │
┌─────────────────┐     ┌─────────────────┐               │
│ import_metadata │     │   import_log    │               │
├─────────────────┤     ├─────────────────┤               │
│ id (PK)         │     │ id (PK)         │◄──────┐       │
│ census_id (FK)──┼─────┼─────────────────┼───────┼───────┤
│ source_filename │     │ session_id (FK) │       │       │
│ column_mapping  │     │ census_id (FK)──┼───────┼───────┘
│ row_count       │     │ created_at      │       │
│ created_at      │     │ completed_at    │       │
└─────────────────┘     │ orig_filename   │       │
                        │ total_rows      │       │
                        │ imported_count  │       │
                        │ rejected_count  │       │
                        │ warning_count   │       │
                        │ replaced_count  │       │
                        │ skipped_count   │       │
                        │ col_mapping_used│       │
                        │ detailed_results│       │
                        │ deleted_at      │       │
                        └─────────────────┘       │
                                 ▲                │
                                 │ FK             │
┌─────────────────┐     ┌───────┴─────────┐      │
│ mapping_profile │     │ import_session  │      │
├─────────────────┤     ├─────────────────┤      │
│ id (PK)         │     │ id (PK)         │◄─────┤
│ user_id         │     │ user_id         │      │
│ name            │     │ created_at      │      │
│ description     │     │ updated_at      │      │
│ created_at      │     │ expires_at      │      │
│ updated_at      │     │ current_step    │      │
│ column_mapping  │     │ file_reference  │      │
│ expected_headers│     │ orig_filename   │      │
└─────────────────┘     │ file_size_bytes │      │
                        │ row_count       │      │
                        │ headers         │      │
                        │ column_mapping  │      │
                        │ validation_res  │      │
                        │ duplicate_res   │      │
                        │ import_result_id│      │
                        └─────────────────┘      │
                                 │               │
                                 │ 1:N           │
                                 ▼               │
                        ┌─────────────────┐      │
                        │validation_issue │      │
                        ├─────────────────┤      │
                        │ id (PK)         │      │
                        │ session_id (FK)─┼──────┘
                        │ row_number      │
                        │ field_name      │
                        │ source_column   │
                        │ severity        │
                        │ issue_code      │
                        │ message         │
                        │ suggestion      │
                        │ raw_value       │
                        │ related_row     │
                        └─────────────────┘
```

## Schema Definitions (DuckDB SQL)

### Schema Version Table (New)

```sql
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT current_timestamp,
    description TEXT NOT NULL
);

-- Initial version
INSERT INTO schema_version (version, description)
VALUES (1, 'Initial DuckDB schema');
```

### Census Table

```sql
CREATE TABLE IF NOT EXISTS census (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    client_name VARCHAR,
    plan_year INTEGER NOT NULL CHECK (plan_year BETWEEN 2020 AND 2100),
    hce_mode VARCHAR NOT NULL DEFAULT 'explicit'
        CHECK (hce_mode IN ('explicit', 'compensation_threshold')),
    upload_timestamp TIMESTAMP NOT NULL DEFAULT current_timestamp,
    participant_count INTEGER NOT NULL CHECK (participant_count >= 0),
    hce_count INTEGER NOT NULL CHECK (hce_count >= 0),
    nhce_count INTEGER NOT NULL CHECK (nhce_count >= 0),
    avg_compensation_cents BIGINT,
    avg_deferral_rate DOUBLE,
    salt VARCHAR NOT NULL,
    version VARCHAR NOT NULL,
    CHECK (hce_count + nhce_count = participant_count)
);

CREATE INDEX IF NOT EXISTS idx_census_plan_year ON census(plan_year);
CREATE INDEX IF NOT EXISTS idx_census_upload ON census(upload_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_census_client ON census(client_name);
```

### Participant Table

```sql
CREATE TABLE IF NOT EXISTS participant (
    id VARCHAR PRIMARY KEY,
    census_id VARCHAR NOT NULL REFERENCES census(id) ON DELETE CASCADE,
    internal_id VARCHAR NOT NULL,
    is_hce BOOLEAN NOT NULL,
    compensation_cents BIGINT NOT NULL CHECK (compensation_cents > 0),
    deferral_rate DOUBLE NOT NULL CHECK (deferral_rate BETWEEN 0 AND 100),
    match_rate DOUBLE NOT NULL CHECK (match_rate >= 0),
    after_tax_rate DOUBLE NOT NULL CHECK (after_tax_rate >= 0),
    ssn_hash VARCHAR,
    dob DATE,
    hire_date DATE,
    termination_date DATE,
    employee_pre_tax_cents BIGINT DEFAULT 0,
    employee_after_tax_cents BIGINT DEFAULT 0,
    employee_roth_cents BIGINT DEFAULT 0,
    employer_match_cents BIGINT DEFAULT 0,
    employer_non_elective_cents BIGINT DEFAULT 0,
    UNIQUE (census_id, internal_id)
);

CREATE INDEX IF NOT EXISTS idx_participant_census ON participant(census_id);
CREATE INDEX IF NOT EXISTS idx_participant_hce ON participant(census_id, is_hce);
CREATE INDEX IF NOT EXISTS idx_participant_ssn_hash ON participant(ssn_hash);
```

### Grid Analysis Table

```sql
CREATE TABLE IF NOT EXISTS grid_analysis (
    id VARCHAR PRIMARY KEY,
    census_id VARCHAR NOT NULL REFERENCES census(id) ON DELETE CASCADE,
    name VARCHAR,
    created_timestamp TIMESTAMP NOT NULL DEFAULT current_timestamp,
    seed INTEGER NOT NULL,
    adoption_rates VARCHAR NOT NULL,  -- JSON array stored as text
    contribution_rates VARCHAR NOT NULL,  -- JSON array stored as text
    version VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_grid_census ON grid_analysis(census_id);
```

### Analysis Result Table

```sql
CREATE TABLE IF NOT EXISTS analysis_result (
    id VARCHAR PRIMARY KEY,
    census_id VARCHAR NOT NULL REFERENCES census(id) ON DELETE CASCADE,
    grid_analysis_id VARCHAR REFERENCES grid_analysis(id) ON DELETE CASCADE,
    adoption_rate DOUBLE NOT NULL CHECK (adoption_rate BETWEEN 0 AND 100),
    contribution_rate DOUBLE NOT NULL CHECK (contribution_rate BETWEEN 0 AND 15),
    seed INTEGER NOT NULL,
    nhce_acp DOUBLE NOT NULL,
    hce_acp DOUBLE NOT NULL,
    threshold DOUBLE NOT NULL,
    margin DOUBLE NOT NULL,
    result VARCHAR NOT NULL CHECK (result IN ('PASS', 'FAIL')),
    limiting_test VARCHAR NOT NULL CHECK (limiting_test IN ('1.25x', '+2.0')),
    run_timestamp TIMESTAMP NOT NULL DEFAULT current_timestamp,
    version VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_result_census ON analysis_result(census_id);
CREATE INDEX IF NOT EXISTS idx_result_grid ON analysis_result(grid_analysis_id);
CREATE INDEX IF NOT EXISTS idx_result_timestamp ON analysis_result(run_timestamp DESC);
```

### Import Metadata Table

```sql
CREATE TABLE IF NOT EXISTS import_metadata (
    id VARCHAR PRIMARY KEY,
    census_id VARCHAR NOT NULL UNIQUE REFERENCES census(id) ON DELETE CASCADE,
    source_filename VARCHAR NOT NULL,
    column_mapping VARCHAR NOT NULL,  -- JSON object stored as text
    row_count INTEGER NOT NULL CHECK (row_count >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);

CREATE INDEX IF NOT EXISTS idx_import_metadata_census ON import_metadata(census_id);
```

### Import Log Table

```sql
CREATE TABLE IF NOT EXISTS import_log (
    id VARCHAR PRIMARY KEY,
    session_id VARCHAR,
    census_id VARCHAR REFERENCES census(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    completed_at TIMESTAMP,
    original_filename VARCHAR NOT NULL,
    total_rows INTEGER NOT NULL,
    imported_count INTEGER NOT NULL DEFAULT 0,
    rejected_count INTEGER NOT NULL DEFAULT 0,
    warning_count INTEGER NOT NULL DEFAULT 0,
    replaced_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,
    column_mapping_used VARCHAR NOT NULL,  -- JSON object
    detailed_results VARCHAR,  -- JSON array
    deleted_at TIMESTAMP  -- soft delete
);

CREATE INDEX IF NOT EXISTS idx_import_log_census ON import_log(census_id);
CREATE INDEX IF NOT EXISTS idx_import_log_created ON import_log(created_at DESC);
```

### Import Session Table

```sql
CREATE TABLE IF NOT EXISTS import_session (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    expires_at TIMESTAMP NOT NULL,
    current_step VARCHAR NOT NULL DEFAULT 'upload'
        CHECK (current_step IN ('upload', 'map', 'validate', 'preview', 'confirm', 'completed')),
    file_reference VARCHAR,
    original_filename VARCHAR,
    file_size_bytes BIGINT,
    row_count INTEGER,
    headers VARCHAR,  -- JSON array
    column_mapping VARCHAR,  -- JSON object
    validation_results VARCHAR,  -- JSON object
    duplicate_resolution VARCHAR,  -- JSON object
    import_result_id VARCHAR REFERENCES import_log(id)
);

CREATE INDEX IF NOT EXISTS idx_import_session_expires ON import_session(expires_at);
CREATE INDEX IF NOT EXISTS idx_import_session_user ON import_session(user_id);
```

### Mapping Profile Table

```sql
CREATE TABLE IF NOT EXISTS mapping_profile (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR,
    name VARCHAR NOT NULL,
    description VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    column_mapping VARCHAR NOT NULL,  -- JSON object
    expected_headers VARCHAR,  -- JSON array
    UNIQUE (user_id, name)
);

CREATE INDEX IF NOT EXISTS idx_mapping_profile_user ON mapping_profile(user_id);
```

### Validation Issue Table

```sql
CREATE TABLE IF NOT EXISTS validation_issue (
    id VARCHAR PRIMARY KEY,
    session_id VARCHAR NOT NULL REFERENCES import_session(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL CHECK (row_number > 0),
    field_name VARCHAR NOT NULL,
    source_column VARCHAR,
    severity VARCHAR NOT NULL CHECK (severity IN ('error', 'warning', 'info')),
    issue_code VARCHAR NOT NULL,
    message VARCHAR NOT NULL,
    suggestion VARCHAR,
    raw_value VARCHAR,
    related_row INTEGER
);

CREATE INDEX IF NOT EXISTS idx_validation_issue_session ON validation_issue(session_id);
CREATE INDEX IF NOT EXISTS idx_validation_issue_severity ON validation_issue(session_id, severity);
```

## Type Mapping: SQLite → DuckDB

| SQLite Type | DuckDB Type | Notes |
|-------------|-------------|-------|
| TEXT | VARCHAR | Standard string type |
| INTEGER | INTEGER / BIGINT | Use BIGINT for cents values |
| REAL | DOUBLE | 64-bit floating point |
| INTEGER (0/1) | BOOLEAN | Native boolean type |
| TEXT (datetime) | TIMESTAMP | Native timestamp type |
| TEXT (date) | DATE | Native date type |
| TEXT (JSON) | VARCHAR | JSON stored as text |

## Validation Rules

All validation rules from the existing schema are preserved:
- `plan_year` must be between 2020 and 2100
- `participant_count`, `hce_count`, `nhce_count` must be >= 0
- `hce_count + nhce_count` must equal `participant_count`
- `compensation_cents` must be > 0
- `deferral_rate` must be between 0 and 100
- `adoption_rate` must be between 0 and 100
- `contribution_rate` must be between 0 and 15
- `hce_mode` must be 'explicit' or 'compensation_threshold'
- `result` must be 'PASS' or 'FAIL'
- `limiting_test` must be '1.25x' or '+2.0'
- `current_step` must be one of the wizard steps
- `severity` must be 'error', 'warning', or 'info'

## State Transitions

### Import Session States

```
upload → map → validate → preview → confirm → completed
```

Each transition updates `current_step` and `updated_at`.
