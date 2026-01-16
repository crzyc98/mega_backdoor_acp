# Quickstart: DuckDB Migration

**Feature**: 012-duckdb-migration

## Prerequisites

- Python 3.11+
- Existing ACP Sensitivity Analyzer codebase
- pip or uv for package management

## Setup

### 1. Install DuckDB Dependency

```bash
# Using pip
pip install duckdb>=1.0.0

# Using uv
uv pip install duckdb>=1.0.0
```

### 2. Verify Installation

```python
import duckdb
print(duckdb.__version__)  # Should be 1.0.0 or higher
```

## Key Concepts

### Connection Management

DuckDB connections are created per workspace:

```python
import duckdb
from pathlib import Path

def get_workspace_connection(workspace_id: str) -> duckdb.DuckDBPyConnection:
    """Get database connection for a workspace."""
    db_path = Path.home() / ".acp-analyzer" / "workspaces" / workspace_id / "workspace.duckdb"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))
```

### Schema Initialization

```python
def init_database(conn: duckdb.DuckDBPyConnection) -> None:
    """Initialize database schema."""
    conn.execute(SCHEMA_SQL)  # Execute the full schema
    conn.commit()
```

### Query Execution

DuckDB API is similar to sqlite3:

```python
# Execute query
conn.execute("SELECT * FROM census WHERE id = ?", [census_id])

# Fetch results
rows = conn.fetchall()

# Execute many
conn.executemany("INSERT INTO participant VALUES (?, ?, ...)", data)

# Commit changes
conn.commit()
```

### Row Factory Pattern

For dictionary-like row access:

```python
# DuckDB returns named tuples by default when using fetchdf() or fetchnumpy()
# For dict-like access, convert results:
result = conn.execute("SELECT * FROM census").fetchdf()
rows = result.to_dict('records')
```

## Migration Checklist

1. **Replace imports**:
   ```python
   # Before
   import sqlite3

   # After
   import duckdb
   ```

2. **Update type hints**:
   ```python
   # Before
   def get_db() -> sqlite3.Connection:

   # After
   def get_db() -> duckdb.DuckDBPyConnection:
   ```

3. **Remove SQLite PRAGMAs**:
   ```python
   # Remove these lines (not needed in DuckDB):
   # conn.execute("PRAGMA journal_mode=WAL")
   # conn.execute("PRAGMA foreign_keys=ON")
   ```

4. **Update datetime functions in SQL**:
   ```sql
   -- Before (SQLite)
   DEFAULT (datetime('now'))

   -- After (DuckDB)
   DEFAULT current_timestamp
   ```

5. **Update boolean handling**:
   ```sql
   -- Before (SQLite)
   is_hce INTEGER NOT NULL CHECK (is_hce IN (0, 1))

   -- After (DuckDB)
   is_hce BOOLEAN NOT NULL
   ```

## Testing

### Unit Test Example

```python
import pytest
import duckdb

@pytest.fixture
def db_connection():
    """Create in-memory database for testing."""
    conn = duckdb.connect(":memory:")
    conn.execute(SCHEMA_SQL)
    yield conn
    conn.close()

def test_census_creation(db_connection):
    db_connection.execute(
        "INSERT INTO census (id, name, ...) VALUES (?, ?, ...)",
        ["test-id", "Test Census", ...]
    )
    result = db_connection.execute(
        "SELECT name FROM census WHERE id = ?",
        ["test-id"]
    ).fetchone()
    assert result[0] == "Test Census"
```

### Integration Test Example

```python
def test_workspace_isolation(tmp_path):
    """Verify data isolation between workspaces."""
    ws1 = tmp_path / "workspace1" / "workspace.duckdb"
    ws2 = tmp_path / "workspace2" / "workspace.duckdb"

    ws1.parent.mkdir(parents=True)
    ws2.parent.mkdir(parents=True)

    conn1 = duckdb.connect(str(ws1))
    conn2 = duckdb.connect(str(ws2))

    # Initialize both
    conn1.execute(SCHEMA_SQL)
    conn2.execute(SCHEMA_SQL)

    # Add data to workspace 1 only
    conn1.execute("INSERT INTO census (...) VALUES (...)")
    conn1.commit()

    # Verify workspace 2 is empty
    count = conn2.execute("SELECT COUNT(*) FROM census").fetchone()[0]
    assert count == 0

    conn1.close()
    conn2.close()
```

## Common Patterns

### Context Manager

```python
from contextlib import contextmanager
from typing import Generator

@contextmanager
def get_connection(workspace_id: str) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Context manager for workspace connections."""
    conn = get_workspace_connection(workspace_id)
    try:
        yield conn
    finally:
        conn.close()

# Usage
with get_connection("workspace-uuid") as conn:
    conn.execute("SELECT * FROM census")
```

### FastAPI Dependency

```python
from fastapi import Depends, Header

def get_workspace_db(
    x_workspace_id: str = Header(...)
) -> duckdb.DuckDBPyConnection:
    """FastAPI dependency for workspace database."""
    return get_workspace_connection(x_workspace_id)

@app.get("/api/census")
def list_censuses(db: duckdb.DuckDBPyConnection = Depends(get_workspace_db)):
    result = db.execute("SELECT * FROM census").fetchdf()
    return result.to_dict('records')
```

## Resources

- [DuckDB Python API Documentation](https://duckdb.org/docs/stable/clients/python/overview)
- [DuckDB DB-API 2.0 Reference](https://duckdb.org/docs/stable/clients/python/dbapi)
- [DuckDB SQL Reference](https://duckdb.org/docs/stable/sql/introduction)
