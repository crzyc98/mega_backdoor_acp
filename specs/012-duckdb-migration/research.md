# Research: DuckDB Migration

**Feature**: 012-duckdb-migration
**Date**: 2026-01-16

## Research Questions

### 1. DuckDB Python API Compatibility with sqlite3

**Decision**: DuckDB provides a Python DB-API 2.0 compliant interface similar to sqlite3

**Rationale**:
- DuckDB's Python API uses `duckdb.connect()` similar to `sqlite3.connect()`
- Connection objects support `execute()`, `executemany()`, `executescript()`, and cursor operations
- Row factory pattern is supported for dictionary-like row access
- Context managers work identically for connection lifecycle management

**Alternatives Considered**:
- SQLAlchemy abstraction layer: Rejected - adds complexity without benefit for this use case
- Direct SQL only: Rejected - lose the convenience of Python API

**Sources**: [DuckDB Python DB API](https://duckdb.org/docs/stable/clients/python/dbapi), [DuckDB Python Overview](https://duckdb.org/docs/stable/clients/python/overview)

---

### 2. Connection Management Strategy

**Decision**: Use per-workspace persistent connections with workspace-scoped database files

**Rationale**:
- DuckDB performs best when reusing the same database connection
- Disconnecting/reconnecting on every query incurs overhead
- Single connection per workspace is sufficient (single-user assumption)
- File path in `duckdb.connect('/path/to/workspace.duckdb')` creates persistent storage

**Key Differences from SQLite**:
- No `check_same_thread` parameter needed (DuckDB handles this differently)
- No WAL mode pragma needed (DuckDB manages journaling internally)
- Use `read_only=True` parameter if multi-process read access needed

**Implementation Pattern**:
```python
import duckdb
from pathlib import Path

def create_connection(db_path: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(db_path))
    # No PRAGMA statements needed - DuckDB auto-manages
    return conn
```

**Sources**: [DuckDB Connect Overview](https://duckdb.org/docs/stable/connect/overview), [Real Python DuckDB Guide](https://realpython.com/python-duckdb/)

---

### 3. Foreign Key Constraints Behavior

**Decision**: Maintain foreign key constraints but adjust table creation order

**Rationale**:
- DuckDB enforces foreign keys by default (cannot disable like SQLite's `PRAGMA foreign_keys=OFF`)
- Tables must be created in dependency order
- An ART index is automatically created for every foreign key constraint
- This is actually safer than SQLite's optional enforcement

**Migration Impact**:
- Current schema already creates tables in correct dependency order
- No changes needed to constraint definitions
- Foreign keys will be enforced automatically

**Constraint Order** (existing, validated):
1. `census` (no dependencies)
2. `participant` (depends on census)
3. `grid_analysis` (depends on census)
4. `analysis_result` (depends on census, grid_analysis)
5. `import_metadata` (depends on census)
6. `import_log` (no FK dependencies that block creation)
7. `import_session` (depends on import_log)
8. `mapping_profile` (no dependencies)
9. `validation_issue` (depends on import_session)

**Sources**: [DuckDB Constraints](https://duckdb.org/docs/stable/sql/constraints), [DuckDB FK Discussion](https://github.com/duckdb/duckdb/discussions/4205)

---

### 4. SQL Syntax Compatibility

**Decision**: Minor syntax adjustments needed for datetime and CHECK constraints

**Rationale**:
- DuckDB supports standard CHECK constraints (no changes needed)
- Datetime functions differ:
  - SQLite: `datetime('now')` → DuckDB: `current_timestamp` or `now()`
  - DuckDB has native TIMESTAMP types (not stored as TEXT)
- BOOLEAN type is native (not stored as INTEGER 0/1)
- JSON storage works similarly via TEXT columns

**Schema Changes Required**:
| SQLite | DuckDB |
|--------|--------|
| `datetime('now')` | `current_timestamp` |
| `INTEGER CHECK (is_hce IN (0, 1))` | `BOOLEAN` |
| `PRAGMA journal_mode=WAL` | Remove (not needed) |
| `PRAGMA foreign_keys=ON` | Remove (always on) |

**Sources**: [DuckDB Timestamp Types](https://duckdb.org/docs/stable/sql/data_types/timestamp), [DuckDB CREATE TABLE](https://duckdb.org/docs/stable/sql/statements/create_table)

---

### 5. Workspace Database Path Strategy

**Decision**: Store as `workspace.duckdb` in each workspace folder

**Rationale**:
- Follows existing workspace folder pattern: `~/.acp-analyzer/workspaces/{uuid}/`
- File naming is consistent and predictable
- Easy to backup/restore individual workspaces
- Database deleted when workspace folder deleted

**Implementation**:
```python
def get_workspace_db_path(workspace_id: str) -> Path:
    base = Path.home() / ".acp-analyzer" / "workspaces" / workspace_id
    return base / "workspace.duckdb"
```

---

### 6. Schema Version Tracking

**Decision**: Use a `schema_version` table for migration tracking

**Rationale**:
- Simple approach that works across database engines
- Enables future schema migrations
- Can check version on connection and apply migrations as needed

**Implementation**:
```sql
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT current_timestamp,
    description TEXT
);
```

---

## Files Requiring Modification

| File | Change Type | Description |
|------|-------------|-------------|
| `src/storage/database.py` | Major rewrite | Replace sqlite3 with duckdb, update schema SQL |
| `src/storage/repository.py` | Minor changes | Update type hints from `sqlite3.Connection` to `duckdb.DuckDBPyConnection` |
| `src/core/constants.py` | Minor | Update DATABASE_PATH logic for workspace-based paths |
| `backend/app/database.py` | Major rewrite | Same changes as src/storage/database.py |
| `pyproject.toml` | Add dependency | Add `duckdb>=1.0.0` |
| `requirements.txt` | Add dependency | Add `duckdb>=1.0.0` |
| Test files | Update imports | Replace sqlite3 references |

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SQL syntax incompatibility | Medium | Medium | Comprehensive test coverage, verify all queries |
| Performance regression | Low | Medium | DuckDB typically faster for analytical queries |
| Connection behavior differences | Low | Low | Follow DuckDB best practices, test thoroughly |
| Missing feature (e.g., PRAGMA) | Medium | Low | Document alternatives, update code accordingly |
