# Implementation Plan: Normalize Rate Inputs & HCE/NHCE Validation

**Branch**: `014-normalize-rate-inputs` | **Date**: 2026-01-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-normalize-rate-inputs/spec.md`

## Summary

Standardize all rate inputs (adoption_rate, contribution_rate) to decimal format (0.0-1.0) across the API, removing V1 percentage-based endpoints. Implement compensation-based HCE determination using IRS thresholds by plan year (2024: $155k, 2025-2028: $160k), with validation to ensure census data contains both HCE and NHCE participants.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.7+ (frontend)
**Primary Dependencies**: FastAPI >=0.104.0, Pydantic >=2.0.0, DuckDB >=1.0.0, pandas >=2.0.0, React 19, React Router 7, Vite 6
**Storage**: DuckDB (workspace-isolated databases at `~/.acp-analyzer/workspaces/{uuid}/workspace.duckdb`)
**Testing**: pytest >=7.4.0 (backend), Vitest 2.1.8 (frontend)
**Target Platform**: Linux server (backend), Web browser (frontend)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Standard API response times (<500ms for census parsing)
**Constraints**: Breaking change - V1 API removal requires frontend coordination
**Scale/Scope**: Single workspace per request, census files up to 10k participants

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution template has placeholder values. Applying standard software engineering principles:

| Gate | Status | Notes |
|------|--------|-------|
| Clear requirements | ✅ PASS | Spec has 12 functional requirements with acceptance criteria |
| Testable criteria | ✅ PASS | All requirements have measurable success criteria |
| Breaking changes documented | ✅ PASS | V1 removal explicitly marked as breaking change |
| Data integrity | ✅ PASS | HCE thresholds are IRS-defined, validation prevents invalid distributions |

## Project Structure

### Documentation (this feature)

```text
specs/014-normalize-rate-inputs/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI schemas)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/          # Pydantic models (update rate field constraints)
│   ├── routers/
│   │   ├── schemas.py   # API request/response schemas (primary changes)
│   │   └── routes/
│   │       └── analysis.py  # Remove V1 endpoints, update V2
│   ├── services/
│   │   ├── census_parser.py    # HCE threshold calculation
│   │   └── hce_thresholds.py   # New: IRS threshold lookup
│   └── storage/
│       └── models.py    # Participant model (is_hce field)
└── tests/
    ├── contract/        # API contract tests
    ├── integration/     # Census parsing integration tests
    └── unit/            # Unit tests for threshold logic

frontend/
├── src/
│   ├── components/      # Rate input components (percentage display)
│   ├── pages/           # Forms that submit rates
│   ├── services/        # API client (decimal conversion)
│   └── types/           # TypeScript types for rate values
└── tests/               # Frontend tests
```

**Structure Decision**: Web application structure (backend + frontend) - this feature modifies both layers with API contract changes and frontend form handling.

## Complexity Tracking

No constitution violations requiring justification. The implementation follows existing patterns:
- Pydantic Field constraints for validation (existing pattern)
- Census parser modifications (existing service)
- Frontend form handling (existing components)
