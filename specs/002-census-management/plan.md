# Implementation Plan: Census Management

**Branch**: `002-census-management` | **Date**: 2026-01-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-census-management/spec.md`

## Summary

Add Census Management as a first-class capability with full CRUD operations (create, list, view, edit metadata, delete), column mapping support, dual HCE determination modes (explicit flag vs. compensation-threshold by plan year), import metadata persistence, and summary statistics calculation. The feature extends the existing census infrastructure to support client naming, editable metadata, configurable HCE classification, and enhanced import validation with user-friendly error messages.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.100+, pandas 2.0+, pydantic 2.0+, Streamlit 1.28+
**Storage**: SQLite (via sqlite3) with WAL mode
**Testing**: pytest with pytest-asyncio for API tests
**Target Platform**: Linux server (web application)
**Project Type**: Web application (FastAPI backend + Streamlit frontend)
**Performance Goals**: 10,000-row census import with summary stats in <30 seconds (SC-001)
**Constraints**: Participant data immutable after import; metadata editable
**Scale/Scope**: Small team/single organization (shared data model, no multi-tenancy)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution file contains template placeholders only (not yet customized for this project). No specific gates are defined. Proceeding with standard software engineering best practices:

- [x] **Library-First**: Census management extends existing `src/core/` and `src/storage/` modules
- [x] **Test-First**: Tests will be written for new functionality
- [x] **Integration Testing**: Contract tests for new API endpoints
- [x] **Simplicity**: Minimal changes to existing architecture; extend, don't replace

## Project Structure

### Documentation (this feature)

```text
specs/002-census-management/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── api/
│   ├── routes/
│   │   └── census.py        # Extend with PATCH endpoint, column mapping
│   └── schemas.py           # Add new request/response schemas
├── core/
│   ├── census_parser.py     # Extend with column mapping, HCE modes
│   ├── constants.py         # Add HCE thresholds by year
│   └── hce_thresholds.py    # NEW: Historical IRS thresholds lookup
├── storage/
│   ├── models.py            # Extend Census with client_name, hce_mode, etc.
│   ├── database.py          # Add new columns, import_metadata table
│   └── repository.py        # Add update methods, metadata queries
└── ui/
    └── pages/
        └── census_list.py   # NEW: Census list/view/edit UI

tests/
├── unit/
│   ├── test_census_parser.py    # Extend with column mapping tests
│   └── test_hce_thresholds.py   # NEW: Threshold lookup tests
├── integration/
│   └── test_census_api.py       # Extend with PATCH, metadata tests
└── contract/
    └── test_census_contracts.py # API contract validation
```

**Structure Decision**: Extending existing single-project structure under `src/`. No new top-level directories needed. The existing layered architecture (api → core → storage) is maintained.

## Complexity Tracking

No constitution violations requiring justification. The implementation extends existing patterns.
