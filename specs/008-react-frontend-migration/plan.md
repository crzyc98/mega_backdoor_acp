# Implementation Plan: React Frontend Migration

**Branch**: `008-react-frontend-migration` | **Date**: 2026-01-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-react-frontend-migration/spec.md`

## Summary

Migrate from Streamlit to a modern React 19 + TypeScript + Vite frontend with full workspace management. The migration includes:
1. Repository restructure (backend/, frontend/, specs/)
2. New workspace CRUD API and file-based storage
3. React SPA mirroring existing Streamlit functionality
4. Full replacement of Streamlit UI after React implementation

## Technical Context

**Language/Version**:
- Backend: Python 3.11+
- Frontend: TypeScript 5.8, React 19.2.3

**Primary Dependencies**:
- Backend: FastAPI 0.104+, Pydantic 2.0+, uvicorn
- Frontend: React 19.2.3, React-DOM 19.2.3, Vite 6.2.0

**Storage**: File-based workspace storage (~/.acp-analyzer/workspaces/{uuid}/)

**Testing**:
- Backend: pytest (existing)
- Frontend: Vitest (to be added)

**Target Platform**: Web (modern evergreen browsers)

**Project Type**: Web application (backend + frontend)

**Performance Goals**:
- Navigation < 1s
- Heatmap interaction < 200ms
- Census upload (10k records) < 5s

**Constraints**:
- Responsive 320px-2560px
- Lighthouse accessibility ≥ 90
- No external database

**Scale/Scope**: Single-user local application, ~10k employee records

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution file contains placeholder content. Proceeding with standard best practices:

| Principle | Status | Notes |
|-----------|--------|-------|
| Test-First | FOLLOW | Backend tests exist; frontend tests to be added |
| Simplicity | FOLLOW | Custom components, no heavy UI libraries |
| File-based Storage | FOLLOW | No external database per spec |

**Gate Status**: PASS (no blocking violations)

## Project Structure

### Documentation (this feature)

```text
specs/008-react-frontend-migration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/          # Pydantic models (from src/core/models.py, src/api/schemas.py)
│   ├── services/        # Business logic (from src/core/)
│   ├── routers/         # API endpoints (from src/api/routes/)
│   └── storage/         # File storage (from src/storage/ + new workspace storage)
└── tests/               # pytest tests (from tests/)

frontend/
├── src/
│   ├── components/      # React components (Layout, Heatmap, etc.)
│   ├── pages/           # View components (WorkspaceManager, Analysis, etc.)
│   ├── services/        # API client services
│   ├── hooks/           # Custom React hooks
│   ├── types/           # TypeScript type definitions
│   └── utils/           # Utility functions
├── public/
└── tests/               # Vitest tests

specs/                   # Feature specifications (unchanged)
```

**Structure Decision**: Web application structure with clear backend/frontend separation. Backend consolidates existing src/ code; frontend is new React implementation following ui-example patterns.

## Complexity Tracking

No constitution violations requiring justification. The workspace architecture adds complexity but is explicitly requested and serves a clear purpose (data persistence, project organization).
