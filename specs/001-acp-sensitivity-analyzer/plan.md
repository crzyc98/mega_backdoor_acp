# Implementation Plan: ACP Sensitivity Analyzer

**Branch**: `001-acp-sensitivity-analyzer` | **Date**: 2026-01-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-acp-sensitivity-analyzer/spec.md`

## Summary

Build a production web application for ACP sensitivity analysis that enables retirement-plan analysts to upload census data, run single or grid scenarios modeling mega-backdoor Roth adoption, and see PASS/FAIL results with margins. The system builds on existing Python/pandas calculation logic in `legacy/` and adds a modern web frontend with Streamlit, persistent storage with SQLite, PII masking, and a REST API for programmatic access.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Streamlit 1.28+, pandas 2.0+, numpy, plotly 5.15+, FastAPI (API layer), SQLite (via sqlite3), pydantic
**Storage**: SQLite for persistent census/results storage with PII-stripped data
**Testing**: pytest with pytest-cov for coverage
**Target Platform**: Linux server (containerized), modern web browsers
**Project Type**: Web application (monorepo with shared backend)
**Performance Goals**: Single scenario <10s for 10K participants; Grid (100 scenarios) <60s for 10K participants
**Constraints**: PII must be stripped on import; reproducible results via configurable seed; audit trail for all calculations
**Scale/Scope**: 10 concurrent users; unlimited census size (performance degrades gracefully beyond 10K)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution is currently a template without defined principles. For this implementation:

- **No violations**: Constitution does not define specific constraints
- **Adopted principles** (self-imposed for this feature):
  - Test coverage for all ACP calculation logic (domain correctness is critical)
  - Audit trail for reproducibility
  - PII protection by design

## Project Structure

### Documentation (this feature)

```text
specs/001-acp-sensitivity-analyzer/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI spec)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── core/                    # Domain logic (calculation engine)
│   ├── __init__.py
│   ├── acp_calculator.py    # ACP test calculations
│   ├── census_parser.py     # CSV parsing with PII stripping
│   ├── scenario_runner.py   # Single/grid scenario execution
│   └── constants.py         # IRS limits, test thresholds
│
├── storage/                 # Persistence layer
│   ├── __init__.py
│   ├── database.py          # SQLite connection/setup
│   ├── models.py            # SQLAlchemy/dataclass models
│   └── repository.py        # Data access layer
│
├── api/                     # REST API (FastAPI)
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry
│   ├── routes/
│   │   ├── census.py        # Census upload/retrieve
│   │   ├── analysis.py      # Run scenarios
│   │   └── export.py        # Export results
│   └── schemas.py           # Pydantic request/response models
│
└── ui/                      # Streamlit frontend
    ├── __init__.py
    ├── app.py               # Main Streamlit app
    ├── pages/
    │   ├── upload.py        # Census upload page
    │   ├── analysis.py      # Scenario configuration & results
    │   └── export.py        # Export page
    └── components/
        ├── heatmap.py       # Grid visualization
        └── results_table.py # Results display

tests/
├── unit/
│   ├── test_acp_calculator.py
│   ├── test_census_parser.py
│   └── test_scenario_runner.py
├── integration/
│   ├── test_api_routes.py
│   └── test_storage.py
└── contract/
    └── test_api_schemas.py
```

**Structure Decision**: Web application with shared Python backend. Streamlit serves as the interactive UI while FastAPI provides the programmatic API. Both share the same core calculation engine and storage layer.

## Complexity Tracking

> No constitution violations requiring justification.

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| SQLite over PostgreSQL | MVP scope, no multi-tenancy, simpler deployment | PostgreSQL would add operational complexity |
| Streamlit over React | Existing team familiarity (legacy code), faster iteration | React SPA would require additional frontend expertise |
| FastAPI alongside Streamlit | Clean API layer for integrations, separate concerns | Streamlit-only would limit programmatic access |
