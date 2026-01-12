# mega_backdoor_acp Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-12

## Active Technologies
- Python 3.11+ + FastAPI 0.100+, pandas 2.0+, pydantic 2.0+, Streamlit 1.28+ (002-census-management)
- SQLite (via sqlite3) with WAL mode (002-census-management)
- Python 3.11+ + FastAPI 0.100+, Streamlit 1.28+, pandas 2.0+, pydantic 2.0+ (003-csv-import-wizard)
- SQLite (via sqlite3) with WAL mode (existing) (003-csv-import-wizard)
- Python 3.11+ + FastAPI 0.100+, pandas 2.0+, pydantic 2.0+, numpy (004-scenario-analysis)
- N/A (stateless calculation engine; results not persisted by this feature) (004-scenario-analysis)

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
- 004-scenario-analysis: Added Python 3.11+ + FastAPI 0.100+, pandas 2.0+, pydantic 2.0+, numpy
- 003-csv-import-wizard: Added Python 3.11+ + FastAPI 0.100+, Streamlit 1.28+, pandas 2.0+, pydantic 2.0+
- 002-census-management: Added Python 3.11+ + FastAPI 0.100+, pandas 2.0+, pydantic 2.0+, Streamlit 1.28+


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
