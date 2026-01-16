# Implementation Plan: DuckDB Migration

**Branch**: `012-duckdb-migration` | **Date**: 2026-01-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/012-duckdb-migration/spec.md`

## Summary

Replace SQLite with DuckDB for all database operations, creating isolated database files within each workspace folder (`~/.acp-analyzer/workspaces/{uuid}/workspace.duckdb`). This is a complete replacement with no legacy SQLite support.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.104+, DuckDB (new), pandas 2.0+, pydantic 2.0+
**Storage**: DuckDB file per workspace (`workspace.duckdb` in each workspace folder)
**Testing**: pytest with existing test structure (unit/, integration/, contract/)
**Target Platform**: Linux server (also works on macOS/Windows)
**Project Type**: Web application (Python backend + React frontend)
**Performance Goals**: Response times comparable to current SQLite implementation
**Constraints**: Single-user per workspace (no concurrent write conflicts)
**Scale/Scope**: Typical workspace: <10K participants, <1K analysis results

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution file contains template placeholders and has not been customized for this project. No specific gates or principles are defined that would block this feature.

**Status**: PASS (no blocking constraints defined)

## Project Structure

### Documentation (this feature)

```text
specs/012-duckdb-migration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - no new API contracts)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
# Web application structure (existing)
src/
├── api/                 # FastAPI routes
│   ├── routes/
│   └── main.py
├── core/                # Business logic, constants
├── storage/             # Database layer (PRIMARY MODIFICATION TARGET)
│   ├── database.py      # SQLite → DuckDB connection management
│   ├── repository.py    # Repository classes (minimal changes)
│   └── models.py        # Data models (unchanged)
└── __init__.py

backend/                 # Separate backend package
├── app/
│   ├── database.py      # Also needs DuckDB migration
│   └── ...
└── tests/

frontend/                # React frontend (unchanged)
├── src/
└── ...

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Existing web application structure is preserved. Changes are localized to `src/storage/database.py`, `backend/app/database.py`, and related files that import `sqlite3`.

## Complexity Tracking

> No complexity violations to track. This is a direct replacement of one embedded database with another.
