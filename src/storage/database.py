"""
DuckDB Database Connection and Schema Management.

This module provides workspace-isolated database connectivity using DuckDB
for the ACP Sensitivity Analyzer. Each workspace has its own database file.
"""

import duckdb
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from src.core.constants import WORKSPACE_BASE_DIR, WORKSPACE_DB_FILENAME

# Current schema version for migrations
SCHEMA_VERSION = 1

# DuckDB Schema Definition
# Note: DuckDB enforces foreign keys by default, no PRAGMA needed
# Note: DuckDB does NOT support ON DELETE CASCADE/SET NULL - delete dependent records manually
# Tables must be created in dependency order
SCHEMA_SQL = """
-- Schema version tracking for migrations
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT current_timestamp,
    description VARCHAR NOT NULL
);

-- Census table: Collection of participant records for a plan
CREATE TABLE IF NOT EXISTS census (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    client_name VARCHAR,
    plan_year INTEGER NOT NULL CHECK (plan_year BETWEEN 2020 AND 2100),
    hce_mode VARCHAR NOT NULL DEFAULT 'explicit' CHECK (hce_mode IN ('explicit', 'compensation_threshold')),
    upload_timestamp TIMESTAMP NOT NULL DEFAULT current_timestamp,
    participant_count INTEGER NOT NULL CHECK (participant_count >= 0),
    hce_count INTEGER NOT NULL CHECK (hce_count >= 0),
    nhce_count INTEGER NOT NULL CHECK (nhce_count >= 0),
    avg_compensation_cents BIGINT,
    avg_deferral_rate DOUBLE,
    salt VARCHAR NOT NULL,
    version VARCHAR NOT NULL,
    CHECK (hce_count + nhce_count = participant_count)
);

-- Participant table: Individual plan participants with ACP-relevant attributes
CREATE TABLE IF NOT EXISTS participant (
    id VARCHAR PRIMARY KEY,
    census_id VARCHAR NOT NULL REFERENCES census(id),
    internal_id VARCHAR NOT NULL,
    is_hce BOOLEAN NOT NULL,
    compensation_cents BIGINT NOT NULL CHECK (compensation_cents > 0),
    deferral_rate DOUBLE NOT NULL CHECK (deferral_rate BETWEEN 0 AND 100),
    match_rate DOUBLE NOT NULL CHECK (match_rate >= 0),
    after_tax_rate DOUBLE NOT NULL CHECK (after_tax_rate >= 0),
    ssn_hash VARCHAR,
    dob DATE,
    hire_date DATE,
    termination_date DATE,
    employee_pre_tax_cents BIGINT DEFAULT 0,
    employee_after_tax_cents BIGINT DEFAULT 0,
    employee_roth_cents BIGINT DEFAULT 0,
    employer_match_cents BIGINT DEFAULT 0,
    employer_non_elective_cents BIGINT DEFAULT 0,
    UNIQUE (census_id, internal_id)
);

-- Grid analysis table: Collection of analysis results across multiple scenarios
CREATE TABLE IF NOT EXISTS grid_analysis (
    id VARCHAR PRIMARY KEY,
    census_id VARCHAR NOT NULL REFERENCES census(id),
    name VARCHAR,
    created_timestamp TIMESTAMP NOT NULL DEFAULT current_timestamp,
    seed INTEGER NOT NULL,
    adoption_rates VARCHAR NOT NULL,
    contribution_rates VARCHAR NOT NULL,
    version VARCHAR NOT NULL
);

-- Analysis result table: Outcome of running one scenario against a census
CREATE TABLE IF NOT EXISTS analysis_result (
    id VARCHAR PRIMARY KEY,
    census_id VARCHAR NOT NULL REFERENCES census(id),
    grid_analysis_id VARCHAR REFERENCES grid_analysis(id),
    adoption_rate DOUBLE NOT NULL CHECK (adoption_rate BETWEEN 0 AND 100),
    contribution_rate DOUBLE NOT NULL CHECK (contribution_rate BETWEEN 0 AND 15),
    seed INTEGER NOT NULL,
    nhce_acp DOUBLE NOT NULL,
    hce_acp DOUBLE NOT NULL,
    threshold DOUBLE NOT NULL,
    margin DOUBLE NOT NULL,
    result VARCHAR NOT NULL CHECK (result IN ('PASS', 'FAIL')),
    limiting_test VARCHAR NOT NULL CHECK (limiting_test IN ('1.25x', '+2.0')),
    run_timestamp TIMESTAMP NOT NULL DEFAULT current_timestamp,
    version VARCHAR NOT NULL
);

-- Import metadata table: Stores column mapping and import details for each census
CREATE TABLE IF NOT EXISTS import_metadata (
    id VARCHAR PRIMARY KEY,
    census_id VARCHAR NOT NULL UNIQUE REFERENCES census(id),
    source_filename VARCHAR NOT NULL,
    column_mapping VARCHAR NOT NULL,
    row_count INTEGER NOT NULL CHECK (row_count >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);

-- Import logs with indefinite retention (created before import_session due to FK)
CREATE TABLE IF NOT EXISTS import_log (
    id VARCHAR PRIMARY KEY,
    session_id VARCHAR,
    census_id VARCHAR REFERENCES census(id),
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    completed_at TIMESTAMP,
    original_filename VARCHAR NOT NULL,
    total_rows INTEGER NOT NULL,
    imported_count INTEGER NOT NULL DEFAULT 0,
    rejected_count INTEGER NOT NULL DEFAULT 0,
    warning_count INTEGER NOT NULL DEFAULT 0,
    replaced_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,
    column_mapping_used VARCHAR NOT NULL,
    detailed_results VARCHAR,
    deleted_at TIMESTAMP
);

-- Import wizard session state
CREATE TABLE IF NOT EXISTS import_session (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    expires_at TIMESTAMP NOT NULL,
    current_step VARCHAR NOT NULL DEFAULT 'upload'
        CHECK (current_step IN ('upload', 'map', 'validate', 'preview', 'confirm', 'completed')),
    file_reference VARCHAR,
    original_filename VARCHAR,
    file_size_bytes BIGINT,
    row_count INTEGER,
    headers VARCHAR,
    column_mapping VARCHAR,
    validation_results VARCHAR,
    duplicate_resolution VARCHAR,
    import_result_id VARCHAR REFERENCES import_log(id)
);

-- Saved column mapping profiles
CREATE TABLE IF NOT EXISTS mapping_profile (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR,
    name VARCHAR NOT NULL,
    description VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    column_mapping VARCHAR NOT NULL,
    expected_headers VARCHAR,
    UNIQUE (user_id, name)
);

-- Validation issues (denormalized for query performance)
CREATE TABLE IF NOT EXISTS validation_issue (
    id VARCHAR PRIMARY KEY,
    session_id VARCHAR NOT NULL REFERENCES import_session(id),
    row_number INTEGER NOT NULL CHECK (row_number > 0),
    field_name VARCHAR NOT NULL,
    source_column VARCHAR,
    severity VARCHAR NOT NULL CHECK (severity IN ('error', 'warning', 'info')),
    issue_code VARCHAR NOT NULL,
    message VARCHAR NOT NULL,
    suggestion VARCHAR,
    raw_value VARCHAR,
    related_row INTEGER
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_census_plan_year ON census(plan_year);
CREATE INDEX IF NOT EXISTS idx_census_upload ON census(upload_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_census_client ON census(client_name);
CREATE INDEX IF NOT EXISTS idx_participant_census ON participant(census_id);
CREATE INDEX IF NOT EXISTS idx_participant_hce ON participant(census_id, is_hce);
CREATE INDEX IF NOT EXISTS idx_participant_ssn_hash ON participant(ssn_hash);
CREATE INDEX IF NOT EXISTS idx_result_census ON analysis_result(census_id);
CREATE INDEX IF NOT EXISTS idx_result_grid ON analysis_result(grid_analysis_id);
CREATE INDEX IF NOT EXISTS idx_result_timestamp ON analysis_result(run_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_grid_census ON grid_analysis(census_id);
CREATE INDEX IF NOT EXISTS idx_import_metadata_census ON import_metadata(census_id);
CREATE INDEX IF NOT EXISTS idx_import_session_expires ON import_session(expires_at);
CREATE INDEX IF NOT EXISTS idx_import_session_user ON import_session(user_id);
CREATE INDEX IF NOT EXISTS idx_mapping_profile_user ON mapping_profile(user_id);
CREATE INDEX IF NOT EXISTS idx_validation_issue_session ON validation_issue(session_id);
CREATE INDEX IF NOT EXISTS idx_validation_issue_severity ON validation_issue(session_id, severity);
CREATE INDEX IF NOT EXISTS idx_import_log_census ON import_log(census_id);
CREATE INDEX IF NOT EXISTS idx_import_log_created ON import_log(created_at DESC);
"""


class DatabaseError(Exception):
    """Exception raised for database-related errors."""
    pass


def get_workspace_db_path(workspace_id: str) -> Path:
    """
    Get the database file path for a workspace.

    Args:
        workspace_id: UUID of the workspace

    Returns:
        Path to the workspace's DuckDB database file
    """
    workspace_dir = WORKSPACE_BASE_DIR / workspace_id
    workspace_dir.mkdir(parents=True, exist_ok=True)
    return workspace_dir / WORKSPACE_DB_FILENAME


def create_connection(db_path: Path) -> duckdb.DuckDBPyConnection:
    """
    Create a DuckDB database connection.

    Args:
        db_path: Path to database file

    Returns:
        DuckDB connection configured for the application

    Raises:
        DatabaseError: If connection cannot be established
    """
    try:
        conn = duckdb.connect(str(db_path))
        return conn
    except Exception as e:
        raise DatabaseError(f"Failed to connect to database at {db_path}: {e}")


def init_database(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Initialize the database schema.

    Creates all tables and indexes if they don't exist.
    Records schema version for migration tracking.

    Args:
        conn: DuckDB connection
    """
    # Execute schema creation
    conn.execute(SCHEMA_SQL)

    # Record schema version if not exists
    existing = conn.execute(
        "SELECT version FROM schema_version WHERE version = ?",
        [SCHEMA_VERSION]
    ).fetchone()

    if not existing:
        conn.execute(
            "INSERT INTO schema_version (version, description) VALUES (?, ?)",
            [SCHEMA_VERSION, "Initial DuckDB schema"]
        )

    conn.commit()


@contextmanager
def get_connection(workspace_id: str) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """
    Context manager for workspace database connections.

    Handles connection lifecycle and ensures proper cleanup.
    Initializes database schema on first access.

    Args:
        workspace_id: UUID of the workspace

    Yields:
        DuckDB connection for the workspace
    """
    db_path = get_workspace_db_path(workspace_id)
    conn = create_connection(db_path)
    try:
        # Ensure schema is initialized
        init_database(conn)
        yield conn
    finally:
        conn.close()


# Connection cache for FastAPI (workspace-aware)
_connections: dict[str, duckdb.DuckDBPyConnection] = {}


def get_db(workspace_id: str) -> duckdb.DuckDBPyConnection:
    """
    Get a database connection for dependency injection.

    This is intended for use with FastAPI's Depends() mechanism.
    Caches connections per workspace for performance.

    Args:
        workspace_id: UUID of the workspace

    Returns:
        DuckDB connection for the workspace
    """
    global _connections

    if workspace_id not in _connections:
        db_path = get_workspace_db_path(workspace_id)
        conn = create_connection(db_path)
        init_database(conn)
        _connections[workspace_id] = conn

    return _connections[workspace_id]


def close_db(workspace_id: str | None = None) -> None:
    """
    Close database connection(s).

    Args:
        workspace_id: If provided, close only that workspace's connection.
                     If None, close all cached connections.
    """
    global _connections

    if workspace_id is not None:
        if workspace_id in _connections:
            _connections[workspace_id].close()
            del _connections[workspace_id]
    else:
        # Close all connections
        for conn in _connections.values():
            conn.close()
        _connections.clear()


def reset_database(workspace_id: str) -> None:
    """
    Reset the database by dropping and recreating all tables.

    WARNING: This deletes all data in the workspace!

    Args:
        workspace_id: UUID of the workspace
    """
    close_db(workspace_id)

    db_path = get_workspace_db_path(workspace_id)

    if db_path.exists():
        db_path.unlink()

    # Reinitialize
    conn = create_connection(db_path)
    try:
        init_database(conn)
    finally:
        conn.close()


def check_database_health(workspace_id: str) -> dict:
    """
    Check the health of a workspace database.

    Args:
        workspace_id: UUID of the workspace

    Returns:
        Dictionary with health status information
    """
    db_path = get_workspace_db_path(workspace_id)

    result = {
        "workspace_id": workspace_id,
        "database_path": str(db_path),
        "exists": db_path.exists(),
        "healthy": False,
        "schema_version": None,
        "table_count": 0,
        "error": None
    }

    if not db_path.exists():
        result["error"] = "Database file does not exist"
        return result

    try:
        conn = create_connection(db_path)
        try:
            # Check schema version
            version_row = conn.execute(
                "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
            ).fetchone()
            if version_row:
                result["schema_version"] = version_row[0]

            # Count tables
            tables = conn.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchone()
            result["table_count"] = tables[0] if tables else 0

            result["healthy"] = True
        finally:
            conn.close()
    except Exception as e:
        result["error"] = str(e)

    return result
