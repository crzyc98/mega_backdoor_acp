# Implementation Plan: Fix PDF/CSV Export Counts

**Branch**: `015-pdf-export-counts-fix` | **Date**: 2026-01-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/015-pdf-export-counts-fix/spec.md`

## Summary

Fix legacy PDF and CSV export routes to use post-eligibility filter counts instead of raw census counts. The workspace PDF export route was recently fixed (commit 7925ea6), but legacy routes at `/export/{census_id}/pdf` and `/export/{census_id}/csv` still hardcode `excluded_count=0` and use raw census counts. This fix will ensure all export endpoints consistently show post-exclusion HCE/NHCE counts that match the Employee Impact page display.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.104+, pandas 2.0+, pydantic 2.0+, reportlab 4.0+
**Storage**: DuckDB 1.0+ (workspace-isolated databases at `~/.acp-analyzer/workspaces/{uuid}/workspace.duckdb`)
**Testing**: pytest 7.4+, pytest-asyncio 0.21+, httpx 0.25+
**Target Platform**: Linux server (Docker container)
**Project Type**: Web application (FastAPI backend + React frontend)
**Performance Goals**: Export generation < 5 seconds for typical census sizes
**Constraints**: Must maintain backward compatibility with legacy export URLs
**Scale/Scope**: Bug fix affecting 2 legacy routes, 1 service file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution file contains template placeholders, indicating no specific gates are enforced. This is a focused bug fix that:
- Does not introduce new dependencies
- Does not add new services or abstractions
- Modifies existing code paths only
- Maintains existing API contracts

**Status**: PASS (no violations)

## Project Structure

### Documentation (this feature)

```text
specs/015-pdf-export-counts-fix/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── routers/
│   │   ├── routes/
│   │   │   └── export.py      # Legacy export routes (MODIFY)
│   │   └── workspaces.py      # Workspace export routes (reference)
│   └── services/
│       ├── export.py          # PDF/CSV generation service
│       └── acp_eligibility.py # ACP inclusion logic (reuse)
└── tests/
    └── test_export.py         # Export route tests (ADD/MODIFY)
```

**Structure Decision**: Web application structure. This fix modifies the legacy export routes in `backend/app/routers/routes/export.py` to use the same post-exclusion count retrieval pattern already implemented in `backend/app/routers/workspaces.py`.

## Complexity Tracking

No violations to justify. This is a minimal bug fix that:
- Reuses existing `determine_acp_inclusion()` function from `acp_eligibility.py`
- Follows the established pattern from the workspace export routes
- Does not introduce new abstractions or dependencies
