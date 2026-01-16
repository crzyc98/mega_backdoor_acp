# mega_backdoor_acp Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-12

## Active Technologies
- Python 3.11+ + FastAPI 0.100+, pandas 2.0+, pydantic 2.0+, Streamlit 1.28+ (002-census-management)
- SQLite (via sqlite3) with WAL mode (002-census-management)
- Python 3.11+ + FastAPI 0.100+, Streamlit 1.28+, pandas 2.0+, pydantic 2.0+ (003-csv-import-wizard)
- SQLite (via sqlite3) with WAL mode (existing) (003-csv-import-wizard)
- Python 3.11+ + FastAPI 0.100+, pandas 2.0+, pydantic 2.0+, numpy (004-scenario-analysis)
- N/A (stateless calculation engine; results not persisted by this feature) (004-scenario-analysis)
- Python 3.11+ + Streamlit 1.28+, Plotly 5.15+, pandas 2.0+, pydantic 2.0+ (005-heatmap-exploration)
- N/A (visualization only; reads GridResult from API or session state) (005-heatmap-exploration)
- N/A (styling only, no data persistence changes) (007-ui-style-update)
- File-based workspace storage (~/.acp-analyzer/workspaces/{uuid}/) (008-react-frontend-migration)
- Python 3.11+ (backend), TypeScript 5.7+ (frontend) + FastAPI 0.104+, React 19, React Router 7, Vite 6, pandas 2.0+, pydantic 2.0+ (009-csv-upload-wizard)
- File-based workspace storage (~/.acp-analyzer/workspaces/{uuid}/), SQLite for sessions (009-csv-upload-wizard)
- Python 3.11+, TypeScript 5.8+ + FastAPI 0.100+, React 19, Pydantic 2.0+, pandas 2.0+ (010-acp-limits-visibility)
- File-based JSON workspaces (~/.acp-analyzer/workspaces/{uuid}/) (010-acp-limits-visibility)
- Python 3.11+ + FastAPI 0.104+, pandas 2.0+, pydantic 2.0+, NumPy (011-fix-acp-exclusion)

- Python 3.11+ + Streamlit 1.28+, pandas 2.0+, numpy, plotly 5.15+, FastAPI (API layer), SQLite (via sqlite3), pydantic (001-acp-sensitivity-analyzer)

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
- 011-fix-acp-exclusion: Added Python 3.11+ + FastAPI 0.104+, pandas 2.0+, pydantic 2.0+, NumPy
- 010-acp-limits-visibility: Added Python 3.11+, TypeScript 5.8+ + FastAPI 0.100+, React 19, Pydantic 2.0+, pandas 2.0+
- 009-csv-upload-wizard: Added Python 3.11+ (backend), TypeScript 5.7+ (frontend) + FastAPI 0.104+, React 19, React Router 7, Vite 6, pandas 2.0+, pydantic 2.0+


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
