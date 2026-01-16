# Implementation Plan: Source Directory Migration to Backend

**Branch**: `013-src-to-backend-migration` | **Date**: 2026-01-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/013-src-to-backend-migration/spec.md`

## Summary

Consolidate all application code from `/src` directory into `/backend` directory, update all import references, configuration files, and documentation, then delete the `/src` directory. The `/backend` directory already contains the more complete and up-to-date codebase (58 Python files vs 26 in `/src`).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.104+, pandas 2.0+, pydantic 2.0+, DuckDB 1.0+, NumPy 1.24+
**Storage**: DuckDB (workspace-isolated databases at `~/.acp-analyzer/workspaces/{uuid}/workspace.duckdb`)
**Testing**: pytest 7.4+, pytest-cov, pytest-asyncio
**Target Platform**: Linux server (web application backend)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Standard web API response times
**Constraints**: Must maintain backward compatibility with existing functionality
**Scale/Scope**: 26 files in `/src` to be analyzed, 31 Python files with `src.` imports to be updated

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution template is not populated for this project. Proceeding with standard best practices:
- Test-first validation: All tests must pass after migration
- Simplicity: Direct file operations, no over-engineering
- Observability: Clear verification steps at each phase

**Status**: PASS (no violations)

## Project Structure

### Documentation (this feature)

```text
specs/013-src-to-backend-migration/
├── plan.md              # This file
├── research.md          # Phase 0 output - file mapping analysis
├── data-model.md        # Phase 1 output - N/A (no data model changes)
├── quickstart.md        # Phase 1 output - migration steps
├── contracts/           # Phase 1 output - N/A (no API contract changes)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
# CURRENT STATE (before migration)
src/                          # TO BE DELETED
├── api/                      # Legacy API code
│   ├── routes/
│   └── main.py
├── core/                     # Legacy business logic
├── storage/                  # Legacy storage layer
└── __init__.py

backend/                      # TARGET (authoritative)
├── app/
│   ├── routers/              # API routes
│   ├── models/               # Pydantic models
│   ├── services/             # Business logic
│   └── storage/              # Database layer
├── tests/                    # Backend tests
├── data/                     # Data files
└── pyproject.toml            # Backend-specific config

tests/                        # Root-level tests (reference src.*)
frontend/                     # React frontend (separate)
```

```text
# TARGET STATE (after migration)
backend/                      # SINGLE SOURCE OF TRUTH
├── app/
│   ├── routers/
│   ├── models/
│   ├── services/
│   └── storage/
├── tests/
├── data/
└── pyproject.toml

tests/                        # Updated to reference backend.app.*
frontend/                     # React frontend (unchanged)
```

**Structure Decision**: The `/backend` directory is already the authoritative source with a more complete structure. The migration involves:
1. Verifying `/src` functionality exists in `/backend`
2. Moving any unique `/src` code to appropriate `/backend` locations
3. Updating all imports from `src.*` to `backend.app.*`
4. Updating configuration files (pyproject.toml, CLAUDE.md)
5. Deleting `/src`

## Complexity Tracking

No constitution violations to justify.

## Migration Analysis

### Files Requiring Import Updates

| Location | File Count | Current Import Pattern | New Import Pattern |
|----------|------------|------------------------|-------------------|
| `/tests/` (root) | ~31 files | `from src.core.*` | `from backend.app.services.*` |
| `/src/` (internal) | 26 files | `from src.*` | Will be deleted |

### Configuration Files to Update

| File | Change Required |
|------|-----------------|
| `/pyproject.toml` | Update `source = ["src"]` → `source = ["backend"]`, `known-first-party = ["src"]` → `known-first-party = ["backend", "app"]` |
| `/CLAUDE.md` | Update project structure section, remove `src/` references |
| `/backend/pyproject.toml` | May need path adjustments |

### Mapping: `/src` → `/backend`

| Source Path | Target Path | Notes |
|-------------|-------------|-------|
| `src/api/` | `backend/app/routers/` | API routes |
| `src/core/` | `backend/app/services/` | Business logic |
| `src/storage/` | `backend/app/storage/` | Database layer |
| `src/__init__.py` | N/A | Not needed |
