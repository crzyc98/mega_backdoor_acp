# Implementation Plan: Employee-Level Impact Views

**Branch**: `006-employee-level-impact` | **Date**: 2026-01-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-employee-level-impact/spec.md`

## Summary

This feature adds employee-level transparency to ACP scenario analysis, enabling users to drill down from a scenario result to view individual participant details. The implementation provides tabbed views for HCE/NHCE groups showing compensation, contributions, §415(c) limits, available room, computed mega-backdoor amounts, and constraint status. It includes sorting, filtering, summary statistics, and CSV export capabilities. The feature computes employee impact data on-demand from census data and scenario parameters.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.100+, Streamlit 1.28+, pandas 2.0+, pydantic 2.0+
**Storage**: SQLite (via sqlite3) with WAL mode (existing)
**Testing**: pytest
**Target Platform**: Linux server / local development
**Project Type**: single (unified backend + Streamlit UI)
**Performance Goals**: Employee detail view loads within 2 seconds for 10,000 participants; sorting/filtering within 500ms
**Constraints**: Must integrate with existing heatmap detail panel; on-demand computation from census data
**Scale/Scope**: Supports censuses up to 10,000 participants per the existing architecture

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution file uses placeholder content (not project-specific). Based on general best practices:

| Gate | Status | Notes |
|------|--------|-------|
| Library-First | PASS | New models and services are self-contained, independently testable |
| Test-First | PASS | Will define test cases before implementation |
| Integration Testing | PASS | Will include API contract tests and UI component tests |
| Simplicity | PASS | Uses existing patterns (Pydantic models, FastAPI routes, Streamlit components) |

## Project Structure

### Documentation (this feature)

```text
specs/006-employee-level-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI extensions)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── core/
│   ├── models.py              # Extend with EmployeeImpact models
│   ├── employee_impact.py     # NEW: Employee impact calculation service
│   └── constants.py           # Existing §415(c) limit functions
├── api/
│   ├── routes/
│   │   └── analysis.py        # Extend with employee impact endpoint
│   └── schemas.py             # Add EmployeeImpact API schemas
├── storage/
│   ├── models.py              # Participant model (existing)
│   └── repository.py          # ParticipantRepository (existing)
└── ui/
    ├── components/
    │   ├── employee_impact_table.py    # NEW: Tabbed HCE/NHCE table component
    │   ├── employee_impact_filters.py  # NEW: Filter controls
    │   ├── employee_impact_summary.py  # NEW: Summary statistics panel
    │   └── employee_impact_export.py   # NEW: CSV export functionality
    └── pages/
        └── analysis.py                  # Integrate employee impact view

tests/
├── unit/
│   └── core/
│       └── test_employee_impact.py     # NEW: Unit tests for calculation service
├── integration/
│   └── api/
│       └── test_employee_impact_api.py # NEW: API contract tests
└── contract/
    └── test_employee_impact_schema.py  # NEW: Schema validation tests
```

**Structure Decision**: Single project structure following the existing codebase pattern. The feature adds new modules under existing directories and extends existing files where appropriate.

## Constitution Re-Check (Post-Design)

| Gate | Status | Notes |
|------|--------|-------|
| Library-First | PASS | `EmployeeImpactService` is self-contained with clear interface |
| Test-First | PASS | Test files defined in structure; quickstart includes test commands |
| Integration Testing | PASS | API contract tests and schema validation tests planned |
| Simplicity | PASS | Uses existing patterns; no new dependencies; stateless computation |

**No violations requiring justification.**

## Generated Artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| research.md | `specs/006-employee-level-impact/research.md` | Technical decisions and rationale |
| data-model.md | `specs/006-employee-level-impact/data-model.md` | Entity definitions and relationships |
| API Contract | `specs/006-employee-level-impact/contracts/employee-impact-api.yaml` | OpenAPI schema for endpoints |
| quickstart.md | `specs/006-employee-level-impact/quickstart.md` | Implementation guide |

## Next Steps

Run `/speckit.tasks` to generate the implementation task list.
