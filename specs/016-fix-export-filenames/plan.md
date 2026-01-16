# Implementation Plan: Fix Export Filenames

**Branch**: `016-fix-export-filenames` | **Date**: 2026-01-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/016-fix-export-filenames/spec.md`

## Summary

Fix the export filename bug where CSV and PDF downloads show generic names (`export.csv`, `export.pdf`) instead of descriptive names containing workspace, plan year, and run information. The backend already generates correct filenames in the `Content-Disposition` header, but the browser blocks frontend JavaScript from accessing this header due to missing CORS `expose_headers` configuration.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.7+ (frontend)
**Primary Dependencies**: FastAPI 0.104+, React 19, Vite 6
**Storage**: N/A (bug fix, no storage changes)
**Testing**: pytest (backend), manual browser testing (frontend header access)
**Target Platform**: Web application (Linux server backend, browser frontend)
**Project Type**: web (frontend + backend)
**Performance Goals**: N/A (bug fix)
**Constraints**: Must work with CORS cross-origin requests from localhost:5173 to localhost:8000
**Scale/Scope**: Single configuration change

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution file contains template placeholders and no specific project constraints are defined. This bug fix:
- Does not introduce new dependencies
- Does not change architecture
- Is a minimal, focused fix (one line change)
- Follows existing patterns in the codebase

**Status**: PASS (no violations)

## Project Structure

### Documentation (this feature)

```text
specs/016-fix-export-filenames/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output - root cause analysis
├── data-model.md        # N/A - no data model changes
├── quickstart.md        # Phase 1 output - testing instructions
├── contracts/           # N/A - no contract changes
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   └── routers/
│       └── main.py          # CORS configuration (FIX LOCATION)
└── tests/

frontend/
├── src/
│   └── services/
│       └── exportService.ts # Frontend download logic (NO CHANGES NEEDED)
└── tests/
```

**Structure Decision**: Web application structure. The fix is isolated to `backend/app/routers/main.py` CORS middleware configuration.

## Complexity Tracking

> No violations - this is a minimal bug fix requiring one configuration change.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Root Cause Analysis

### Problem Flow

1. User clicks "Download CSV" or "Download PDF" button
2. Frontend (`exportService.ts`) fetches from `/api/workspaces/{id}/runs/{id}/export/{format}`
3. Backend generates descriptive filename and sets `Content-Disposition` header
4. **CORS blocks header access**: Browser doesn't expose `Content-Disposition` to JavaScript
5. Frontend `response.headers.get('Content-Disposition')` returns `null`
6. Frontend falls back to generic `export.{format}` filename

### Root Cause

The CORS middleware in `backend/app/routers/main.py` (lines 42-54) is missing:
```python
expose_headers=["Content-Disposition"]
```

Without this, browsers block JavaScript access to the `Content-Disposition` header for security reasons, even though the header is present in the response.

### Verification Points

| Component | Status | Location |
|-----------|--------|----------|
| Backend CSV filename generation | CORRECT | `workspaces.py:1053-1063` |
| Backend PDF filename generation | CORRECT | `workspaces.py:1182-1191` |
| Frontend header parsing regex | CORRECT | `exportService.ts:29` |
| CORS expose_headers | **MISSING** | `main.py:42-54` |

## Implementation Approach

### Single Change Required

Add `expose_headers=["Content-Disposition"]` to the CORSMiddleware configuration in `backend/app/routers/main.py`.

**Before:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[...],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**After:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[...],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)
```

## Testing Strategy

### Manual Testing

1. Start backend: `cd backend && uvicorn app.routers.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Navigate to a workspace with a completed run
4. Click "Download CSV" - verify filename is NOT `export.csv`
5. Click "Download PDF" - verify filename is NOT `export.pdf`
6. Expected filename format: `{WorkspaceName}_{PlanYear}_Run{Seed}_{MonthYear}.{ext}`

### Browser DevTools Verification

1. Open Network tab in browser DevTools
2. Trigger a CSV or PDF download
3. Check response headers for `Content-Disposition`
4. Verify header value contains descriptive filename
5. Verify `Access-Control-Expose-Headers: Content-Disposition` is present

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| CORS change breaks other functionality | Low | Medium | Only exposing Content-Disposition, not modifying other CORS settings |
| Browser caching old CORS policy | Low | Low | Hard refresh or incognito window for testing |

## Dependencies

None - this is a self-contained bug fix.
