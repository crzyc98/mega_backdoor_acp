# mega_backdoor_acp Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-16

## Active Technologies
- Python 3.11+ + FastAPI 0.104+, DuckDB, pandas 2.0+, pydantic 2.0+ (core backend)
- DuckDB file per workspace (`~/.acp-analyzer/workspaces/{uuid}/workspace.duckdb`)
- Python 3.11+ (backend), TypeScript 5.7+ (frontend) + React 19, React Router 7, Vite 6 (009-csv-upload-wizard)
- Python 3.11+ + Streamlit 1.28+, Plotly 5.15+ (legacy UI, if used)
- Python 3.11+ + FastAPI 0.104+, pandas 2.0+, pydantic 2.0+, DuckDB 1.0+, NumPy 1.24+ (013-src-to-backend-migration)
- DuckDB (workspace-isolated databases at `~/.acp-analyzer/workspaces/{uuid}/workspace.duckdb`) (013-src-to-backend-migration)
- Python 3.11+ (backend), TypeScript 5.7+ (frontend) + FastAPI >=0.104.0, Pydantic >=2.0.0, DuckDB >=1.0.0, pandas >=2.0.0, React 19, React Router 7, Vite 6 (014-normalize-rate-inputs)
- Python 3.11+ + FastAPI 0.104+, pandas 2.0+, pydantic 2.0+, reportlab 4.0+ (015-pdf-export-counts-fix)
- DuckDB 1.0+ (workspace-isolated databases at `~/.acp-analyzer/workspaces/{uuid}/workspace.duckdb`) (015-pdf-export-counts-fix)

## Project Structure

```text
backend/
  app/
    routers/     # API routes (FastAPI)
    models/      # Pydantic models
    services/    # Business logic
    storage/     # Database layer (DuckDB)
  tests/         # Backend tests
frontend/        # React frontend
tests/           # Root-level integration tests
```

## Commands

```bash
cd backend && pytest tests/ -v    # Run backend tests
pytest tests/ -v                   # Run root-level tests
cd backend && uvicorn app.routers.main:app --reload  # Start API server
ruff check .                       # Lint code
```

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 015-pdf-export-counts-fix: Added Python 3.11+ + FastAPI 0.104+, pandas 2.0+, pydantic 2.0+, reportlab 4.0+
- 014-normalize-rate-inputs: Added Python 3.11+ (backend), TypeScript 5.7+ (frontend) + FastAPI >=0.104.0, Pydantic >=2.0.0, DuckDB >=1.0.0, pandas >=2.0.0, React 19, React Router 7, Vite 6
- 013-src-to-backend-migration: Added Python 3.11+ + FastAPI 0.104+, pandas 2.0+, pydantic 2.0+, DuckDB 1.0+, NumPy 1.24+

## Database Notes (DuckDB Migration)
- **No more SQLite**: The codebase now uses DuckDB exclusively for all data persistence
- **Workspace isolation**: Each workspace gets its own `workspace.duckdb` file in `~/.acp-analyzer/workspaces/{uuid}/`
- **API Workspace Header**: API routes use `X-Workspace-ID` header to determine which database to use
- **DuckDB specifics**:
  - Uses native `BOOLEAN` type (not INTEGER 0/1)
  - Uses `current_timestamp` for timestamps (not `datetime('now')`)
  - Foreign keys enforced by default (no PRAGMA needed)
  - Does NOT support `ON DELETE CASCADE/SET NULL` - cascade deletes are manual
  - Returns tuples, not Row objects - use `row_to_dict()` helper
  - Returns datetime objects directly, not ISO strings - use `_parse_datetime()` helper


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
