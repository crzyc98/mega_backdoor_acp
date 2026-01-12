# Data Model: ACP Sensitivity Analyzer

**Feature**: 001-acp-sensitivity-analyzer
**Date**: 2026-01-12

## Entity Relationship Diagram

```
┌─────────────────────┐       ┌─────────────────────┐
│       Census        │       │     Participant     │
├─────────────────────┤       ├─────────────────────┤
│ id (PK)             │──────<│ id (PK)             │
│ name                │       │ census_id (FK)      │
│ plan_year           │       │ internal_id         │
│ upload_timestamp    │       │ is_hce              │
│ participant_count   │       │ compensation_cents  │
│ hce_count           │       │ deferral_rate       │
│ nhce_count          │       │ match_rate          │
│ salt                │       │ after_tax_rate      │
│ version             │       └─────────────────────┘
└─────────────────────┘
          │
          │
          ▼
┌─────────────────────┐       ┌─────────────────────┐
│   AnalysisResult    │       │   GridAnalysis      │
├─────────────────────┤       ├─────────────────────┤
│ id (PK)             │───────│ id (PK)             │
│ census_id (FK)      │       │ census_id (FK)      │
│ grid_analysis_id(FK)│<──────│ name                │
│ adoption_rate       │       │ created_timestamp   │
│ contribution_rate   │       │ seed                │
│ seed                │       │ adoption_rates[]    │
│ nhce_acp            │       │ contribution_rates[]│
│ hce_acp             │       │ version             │
│ threshold           │       └─────────────────────┘
│ margin              │
│ result              │
│ limiting_test       │
│ run_timestamp       │
│ version             │
└─────────────────────┘
```

---

## Entities

### Census

A collection of participant records for a single plan, representing the population for ACP testing.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-generated | Unique identifier |
| `name` | VARCHAR(255) | NOT NULL | User-provided name for the census |
| `plan_year` | INTEGER | NOT NULL, 2020-2100 | Plan year for analysis |
| `upload_timestamp` | TIMESTAMP | NOT NULL, auto | When census was uploaded |
| `participant_count` | INTEGER | NOT NULL, >= 0 | Total participants |
| `hce_count` | INTEGER | NOT NULL, >= 0 | Number of HCEs |
| `nhce_count` | INTEGER | NOT NULL, >= 0 | Number of NHCEs |
| `salt` | VARCHAR(32) | NOT NULL | Per-census salt for ID hashing |
| `version` | VARCHAR(20) | NOT NULL | System version at upload |

**Validation Rules**:
- `hce_count + nhce_count = participant_count`
- `plan_year` must be between 2020 and 2100

**State Transitions**: None (immutable after creation)

---

### Participant

An individual plan participant with ACP-relevant attributes.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-generated | Unique identifier |
| `census_id` | UUID | FK → Census.id, NOT NULL | Parent census |
| `internal_id` | VARCHAR(16) | NOT NULL | Hashed employee identifier |
| `is_hce` | BOOLEAN | NOT NULL | HCE classification |
| `compensation_cents` | BIGINT | NOT NULL, > 0 | Annual compensation in cents |
| `deferral_rate` | DECIMAL(5,2) | NOT NULL, 0-100 | Current deferral % |
| `match_rate` | DECIMAL(5,2) | NOT NULL, >= 0 | Employer match % |
| `after_tax_rate` | DECIMAL(5,2) | NOT NULL, >= 0 | Current after-tax % |

**Validation Rules**:
- `internal_id` must be unique within a census
- `compensation_cents` must be positive
- `deferral_rate` must be between 0 and 100

**Derived Fields** (computed, not stored):
- `match_contribution_cents`: `compensation_cents * match_rate / 100`
- `after_tax_contribution_cents`: `compensation_cents * after_tax_rate / 100`
- `individual_acp`: `(match + after_tax) / compensation * 100`

**Note**: Original Employee ID, SSN, names, and other PII are NOT stored. Only the hashed `internal_id` is persisted.

---

### AnalysisResult

The outcome of running one scenario against a census.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-generated | Unique identifier |
| `census_id` | UUID | FK → Census.id, NOT NULL | Census used |
| `grid_analysis_id` | UUID | FK → GridAnalysis.id, NULL | Parent grid (if part of grid) |
| `adoption_rate` | DECIMAL(5,2) | NOT NULL, 0-100 | HCE adoption rate % |
| `contribution_rate` | DECIMAL(5,2) | NOT NULL, 0-15 | Mega-backdoor contribution % |
| `seed` | BIGINT | NOT NULL | Random seed for HCE selection |
| `nhce_acp` | DECIMAL(6,3) | NOT NULL | NHCE group ACP |
| `hce_acp` | DECIMAL(6,3) | NOT NULL | HCE group ACP |
| `threshold` | DECIMAL(6,3) | NOT NULL | Maximum allowed HCE ACP |
| `margin` | DECIMAL(6,3) | NOT NULL | Distance from threshold |
| `result` | VARCHAR(4) | NOT NULL, ENUM | 'PASS' or 'FAIL' |
| `limiting_test` | VARCHAR(10) | NOT NULL | '1.25x' or '+2.0' |
| `run_timestamp` | TIMESTAMP | NOT NULL, auto | When analysis was run |
| `version` | VARCHAR(20) | NOT NULL | System version |

**Validation Rules**:
- `result` must be 'PASS' or 'FAIL'
- `limiting_test` must be '1.25x' or '+2.0'
- `margin` is positive for PASS, negative for FAIL

**Computed at Runtime** (not stored):
- `participating_hce_ids`: List of internal IDs selected for adoption
- `limit_125`: `nhce_acp * 1.25`
- `limit_plus2`: `nhce_acp + 2.0`

---

### GridAnalysis

A collection of analysis results across multiple scenarios.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-generated | Unique identifier |
| `census_id` | UUID | FK → Census.id, NOT NULL | Census used |
| `name` | VARCHAR(255) | NULL | Optional user-provided name |
| `created_timestamp` | TIMESTAMP | NOT NULL, auto | When grid was created |
| `seed` | BIGINT | NOT NULL | Shared seed for all scenarios |
| `adoption_rates` | JSON | NOT NULL | Array of adoption rates |
| `contribution_rates` | JSON | NOT NULL | Array of contribution rates |
| `version` | VARCHAR(20) | NOT NULL | System version |

**Validation Rules**:
- `adoption_rates` must have 2-20 values, each 0-100
- `contribution_rates` must have 2-20 values, each 0-15

**Derived**:
- `scenario_count`: `len(adoption_rates) * len(contribution_rates)`
- `pass_count`: Count of associated AnalysisResults with result='PASS'
- `fail_count`: Count of associated AnalysisResults with result='FAIL'

---

## Indexes

```sql
-- Census lookups
CREATE INDEX idx_census_plan_year ON census(plan_year);
CREATE INDEX idx_census_upload ON census(upload_timestamp DESC);

-- Participant lookups
CREATE INDEX idx_participant_census ON participant(census_id);
CREATE INDEX idx_participant_hce ON participant(census_id, is_hce);

-- Analysis result lookups
CREATE INDEX idx_result_census ON analysis_result(census_id);
CREATE INDEX idx_result_grid ON analysis_result(grid_analysis_id);
CREATE INDEX idx_result_timestamp ON analysis_result(run_timestamp DESC);

-- Grid analysis lookups
CREATE INDEX idx_grid_census ON grid_analysis(census_id);
```

---

## SQLite Schema

```sql
-- Enable WAL mode for concurrent reads
PRAGMA journal_mode=WAL;

CREATE TABLE census (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    plan_year INTEGER NOT NULL CHECK (plan_year BETWEEN 2020 AND 2100),
    upload_timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    participant_count INTEGER NOT NULL CHECK (participant_count >= 0),
    hce_count INTEGER NOT NULL CHECK (hce_count >= 0),
    nhce_count INTEGER NOT NULL CHECK (nhce_count >= 0),
    salt TEXT NOT NULL,
    version TEXT NOT NULL,
    CHECK (hce_count + nhce_count = participant_count)
);

CREATE TABLE participant (
    id TEXT PRIMARY KEY,
    census_id TEXT NOT NULL REFERENCES census(id) ON DELETE CASCADE,
    internal_id TEXT NOT NULL,
    is_hce INTEGER NOT NULL CHECK (is_hce IN (0, 1)),
    compensation_cents INTEGER NOT NULL CHECK (compensation_cents > 0),
    deferral_rate REAL NOT NULL CHECK (deferral_rate BETWEEN 0 AND 100),
    match_rate REAL NOT NULL CHECK (match_rate >= 0),
    after_tax_rate REAL NOT NULL CHECK (after_tax_rate >= 0),
    UNIQUE (census_id, internal_id)
);

CREATE TABLE grid_analysis (
    id TEXT PRIMARY KEY,
    census_id TEXT NOT NULL REFERENCES census(id) ON DELETE CASCADE,
    name TEXT,
    created_timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    seed INTEGER NOT NULL,
    adoption_rates TEXT NOT NULL,  -- JSON array
    contribution_rates TEXT NOT NULL,  -- JSON array
    version TEXT NOT NULL
);

CREATE TABLE analysis_result (
    id TEXT PRIMARY KEY,
    census_id TEXT NOT NULL REFERENCES census(id) ON DELETE CASCADE,
    grid_analysis_id TEXT REFERENCES grid_analysis(id) ON DELETE CASCADE,
    adoption_rate REAL NOT NULL CHECK (adoption_rate BETWEEN 0 AND 100),
    contribution_rate REAL NOT NULL CHECK (contribution_rate BETWEEN 0 AND 15),
    seed INTEGER NOT NULL,
    nhce_acp REAL NOT NULL,
    hce_acp REAL NOT NULL,
    threshold REAL NOT NULL,
    margin REAL NOT NULL,
    result TEXT NOT NULL CHECK (result IN ('PASS', 'FAIL')),
    limiting_test TEXT NOT NULL CHECK (limiting_test IN ('1.25x', '+2.0')),
    run_timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    version TEXT NOT NULL
);

-- Create indexes
CREATE INDEX idx_census_plan_year ON census(plan_year);
CREATE INDEX idx_participant_census ON participant(census_id);
CREATE INDEX idx_participant_hce ON participant(census_id, is_hce);
CREATE INDEX idx_result_census ON analysis_result(census_id);
CREATE INDEX idx_result_grid ON analysis_result(grid_analysis_id);
CREATE INDEX idx_grid_census ON grid_analysis(census_id);
```

---

## Data Flow

### Census Upload Flow
```
CSV File → Parse → Validate → Strip PII → Hash IDs → Store Census + Participants
```

### Single Scenario Analysis Flow
```
Census ID + Params → Load Participants → Select HCEs (seeded) → Calculate ACPs → Apply Test → Store Result
```

### Grid Analysis Flow
```
Census ID + Grid Params → Create GridAnalysis → For each (adoption, contribution): Run Single Scenario → Store Results
```

### Export Flow
```
Census/Grid ID → Load Results → Format (CSV/PDF) → Include Audit Metadata → Return File
```
