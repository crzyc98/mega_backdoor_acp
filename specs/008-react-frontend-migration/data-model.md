# Data Model: React Frontend Migration

**Date**: 2026-01-13
**Feature**: 008-react-frontend-migration

## Overview

Data models for workspace management and React frontend. Extends existing models with new workspace-related entities.

---

## New Entities

### Workspace

Top-level organizational container for ACP analysis projects.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique workspace identifier |
| name | string | max 255 chars, required | User-provided workspace name |
| description | string | max 1000 chars, optional | User-provided description |
| created_at | datetime | auto-set | Creation timestamp |
| updated_at | datetime | auto-update | Last modification timestamp |

**Storage**: `~/.acp-analyzer/workspaces/{id}/workspace.json`

**Relationships**:
- Has one CensusData (optional)
- Has many Run

---

### Run

Analysis execution record within a workspace.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique run identifier |
| workspace_id | UUID | FK to Workspace | Parent workspace |
| name | string | max 255 chars, optional | User-provided run name |
| adoption_rates | float[] | 2-20 items, each 0.0-1.0 | Adoption rate parameters |
| contribution_rates | float[] | 2-20 items, each 0.0-1.0 | Contribution rate parameters |
| seed | int | >= 1 | Random seed used |
| status | enum | PENDING, RUNNING, COMPLETED, FAILED | Execution status |
| created_at | datetime | auto-set | Run initiation timestamp |
| completed_at | datetime | nullable | Completion timestamp |

**Storage**: `~/.acp-analyzer/workspaces/{workspace_id}/runs/{id}/run_metadata.json`

**Relationships**:
- Belongs to Workspace
- Has one GridResult

**State Transitions**:
```
PENDING → RUNNING → COMPLETED
                  → FAILED
```

---

## Existing Entities (Reference)

These entities exist in the current codebase and remain unchanged.

### CensusData

Collection of employee records loaded from CSV.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Census identifier |
| name | string | User-provided census name |
| plan_year | int | Plan year (2020-2100) |
| participant_count | int | Total employees |
| hce_count | int | HCE count |
| nhce_count | int | NHCE count |
| upload_timestamp | datetime | When uploaded |

**Storage**: `~/.acp-analyzer/workspaces/{workspace_id}/data/census.csv`

---

### ScenarioResult

Result of a single scenario analysis (existing model, no changes).

| Field | Type | Description |
|-------|------|-------------|
| status | enum | PASS, RISK, FAIL, ERROR |
| nhce_acp | float | NHCE ACP percentage |
| hce_acp | float | HCE ACP percentage |
| max_allowed_acp | float | Threshold value |
| margin | float | Distance from threshold |
| adoption_rate | float | Input adoption rate |
| contribution_rate | float | Input contribution rate |
| seed_used | int | Random seed applied |

---

### GridResult

Collection of ScenarioResults (existing model, stored per run).

| Field | Type | Description |
|-------|------|-------------|
| scenarios | ScenarioResult[] | All scenario results |
| summary | GridSummary | Aggregate metrics |
| seed_used | int | Base seed |

**Storage**: `~/.acp-analyzer/workspaces/{workspace_id}/runs/{run_id}/grid_results.json`

---

### EmployeeImpact

Per-employee contribution breakdown (existing model, no changes).

| Field | Type | Description |
|-------|------|-------------|
| employee_id | string | Anonymized identifier |
| is_hce | bool | HCE status |
| compensation | float | Annual compensation |
| mega_backdoor_amount | float | Computed contribution |
| constraint_status | enum | UNCONSTRAINED, AT_LIMIT, REDUCED, NOT_SELECTED |

---

## TypeScript Types (Frontend)

```typescript
// types/workspace.ts
interface Workspace {
  id: string;
  name: string;
  description?: string;
  created_at: string;  // ISO datetime
  updated_at: string;
  has_census: boolean;
  run_count: number;
}

interface WorkspaceCreate {
  name: string;
  description?: string;
}

interface WorkspaceUpdate {
  name?: string;
  description?: string;
}

// types/run.ts
type RunStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

interface Run {
  id: string;
  workspace_id: string;
  name?: string;
  adoption_rates: number[];
  contribution_rates: number[];
  seed: number;
  status: RunStatus;
  created_at: string;
  completed_at?: string;
}

// types/analysis.ts (existing types from ui-example)
type AnalysisStatus = 'PASS' | 'RISK' | 'FAIL' | 'ERROR';
type ViewMode = 'PASS_FAIL' | 'MARGIN' | 'RISK_ZONE';

interface ScenarioResult {
  status: AnalysisStatus;
  nhce_acp: number | null;
  hce_acp: number | null;
  max_allowed_acp: number | null;
  margin: number | null;
  adoption_rate: number;
  contribution_rate: number;
  seed_used: number;
}

interface GridResult {
  scenarios: ScenarioResult[];
  summary: GridSummary;
  seed_used: number;
}

// types/employee.ts
type ConstraintStatus = 'Unconstrained' | 'At §415(c) Limit' | 'Reduced' | 'Not Selected';

interface EmployeeImpact {
  employee_id: string;
  is_hce: boolean;
  compensation: number;
  deferral_amount: number;
  match_amount: number;
  after_tax_amount: number;
  mega_backdoor_amount: number;
  constraint_status: ConstraintStatus;
}
```

---

## Validation Rules

### Workspace
- `name`: Required, 1-255 characters, trimmed
- `description`: Optional, max 1000 characters

### Run
- `adoption_rates`: 2-20 values, each between 0.0 and 1.0
- `contribution_rates`: 2-20 values, each between 0.0 and 1.0
- `seed`: Positive integer (auto-generated if not provided)

### Census (on upload)
- Required columns: employee_id, compensation, is_hce (or compensation threshold)
- Compensation: Non-negative
- At least 1 HCE and 1 NHCE required

---

## File Storage Schema

### workspace.json
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Q4 2026 Analysis",
  "description": "Year-end compliance testing",
  "created_at": "2026-01-13T10:30:00Z",
  "updated_at": "2026-01-13T14:45:00Z"
}
```

### run_metadata.json
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Standard 5x6 Grid",
  "adoption_rates": [0.2, 0.4, 0.6, 0.8, 1.0],
  "contribution_rates": [0.02, 0.04, 0.06, 0.08, 0.10, 0.12],
  "seed": 42,
  "status": "COMPLETED",
  "created_at": "2026-01-13T14:00:00Z",
  "completed_at": "2026-01-13T14:00:05Z"
}
```

### grid_results.json
```json
{
  "scenarios": [
    {
      "status": "PASS",
      "nhce_acp": 3.25,
      "hce_acp": 4.06,
      "max_allowed_acp": 5.25,
      "margin": 1.19,
      "adoption_rate": 0.2,
      "contribution_rate": 0.02,
      "seed_used": 42
    }
  ],
  "summary": {
    "pass_count": 25,
    "risk_count": 3,
    "fail_count": 2,
    "error_count": 0,
    "total_count": 30
  },
  "seed_used": 42
}
```
