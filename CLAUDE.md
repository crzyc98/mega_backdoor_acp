# mega_backdoor_acp Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-16

## Active Technologies
- Python 3.11+ + FastAPI 0.104+, DuckDB, pandas 2.0+, pydantic 2.0+ (core backend)
- DuckDB file per workspace (`~/.acp-analyzer/workspaces/{uuid}/workspace.duckdb`)
- Python 3.11+ (backend), TypeScript 5.7+ (frontend) + React 19, React Router 7, Vite 6 (009-csv-upload-wizard)
- Python 3.11+ + Streamlit 1.28+, Plotly 5.15+ (legacy UI, if used)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 012-duckdb-migration: Migrated from SQLite to DuckDB with workspace-isolated databases
- 011-fix-acp-exclusion: Added Python 3.11+ + FastAPI 0.104+, pandas 2.0+, pydantic 2.0+, NumPy
- 010-acp-limits-visibility: Added Python 3.11+, TypeScript 5.8+ + FastAPI 0.100+, React 19, Pydantic 2.0+, pandas 2.0+

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
