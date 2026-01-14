"""
SQLite Database Connection and Schema Management.

This module provides database connectivity with WAL mode for concurrent reads
and schema initialization for the ACP Sensitivity Analyzer.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from app.services.constants import DATABASE_PATH

# SQL Schema Definition per data-model.md
SCHEMA_SQL = """
-- Enable WAL mode for concurrent reads
PRAGMA journal_mode=WAL;

-- Census table: Collection of participant records for a plan
CREATE TABLE IF NOT EXISTS census (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    client_name TEXT,
    plan_year INTEGER NOT NULL CHECK (plan_year BETWEEN 2020 AND 2100),
    hce_mode TEXT NOT NULL DEFAULT 'explicit' CHECK (hce_mode IN ('explicit', 'compensation_threshold')),
    upload_timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    participant_count INTEGER NOT NULL CHECK (participant_count >= 0),
    hce_count INTEGER NOT NULL CHECK (hce_count >= 0),
    nhce_count INTEGER NOT NULL CHECK (nhce_count >= 0),
    avg_compensation_cents INTEGER,
    avg_deferral_rate REAL,
    salt TEXT NOT NULL,
    version TEXT NOT NULL,
    CHECK (hce_count + nhce_count = participant_count)
);

-- Participant table: Individual plan participants with ACP-relevant attributes
CREATE TABLE IF NOT EXISTS participant (
    id TEXT PRIMARY KEY,
    census_id TEXT NOT NULL REFERENCES census(id) ON DELETE CASCADE,
    internal_id TEXT NOT NULL,
    is_hce INTEGER NOT NULL CHECK (is_hce IN (0, 1)),
    compensation_cents INTEGER NOT NULL CHECK (compensation_cents > 0),
    deferral_rate REAL NOT NULL CHECK (deferral_rate BETWEEN 0 AND 100),
    match_rate REAL NOT NULL CHECK (match_rate >= 0),
    after_tax_rate REAL NOT NULL CHECK (after_tax_rate >= 0),
    UNIQUE (census_id, internal_id)
);

-- Grid analysis table: Collection of analysis results across multiple scenarios
CREATE TABLE IF NOT EXISTS grid_analysis (
    id TEXT PRIMARY KEY,
    census_id TEXT NOT NULL REFERENCES census(id) ON DELETE CASCADE,
    name TEXT,
    created_timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    seed INTEGER NOT NULL,
    adoption_rates TEXT NOT NULL,  -- JSON array
    contribution_rates TEXT NOT NULL,  -- JSON array
    version TEXT NOT NULL
);

-- Analysis result table: Outcome of running one scenario against a census
CREATE TABLE IF NOT EXISTS analysis_result (
    id TEXT PRIMARY KEY,
    census_id TEXT NOT NULL REFERENCES census(id) ON DELETE CASCADE,
    grid_analysis_id TEXT REFERENCES grid_analysis(id) ON DELETE CASCADE,
    adoption_rate REAL NOT NULL CHECK (adoption_rate BETWEEN 0 AND 100),
    contribution_rate REAL NOT NULL CHECK (contribution_rate BETWEEN 0 AND 15),
    seed INTEGER NOT NULL,
    nhce_acp REAL NOT NULL,
    hce_acp REAL NOT NULL,
    threshold REAL NOT NULL,
    margin REAL NOT NULL,
    result TEXT NOT NULL CHECK (result IN ('PASS', 'FAIL')),
    limiting_test TEXT NOT NULL CHECK (limiting_test IN ('1.25x', '+2.0')),
    run_timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    version TEXT NOT NULL
);

-- Import metadata table: Stores column mapping and import details for each census
CREATE TABLE IF NOT EXISTS import_metadata (
    id TEXT PRIMARY KEY,
    census_id TEXT NOT NULL UNIQUE REFERENCES census(id) ON DELETE CASCADE,
    source_filename TEXT NOT NULL,
    column_mapping TEXT NOT NULL,  -- JSON object
    row_count INTEGER NOT NULL CHECK (row_count >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_census_plan_year ON census(plan_year);
CREATE INDEX IF NOT EXISTS idx_census_upload ON census(upload_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_census_client ON census(client_name);
CREATE INDEX IF NOT EXISTS idx_participant_census ON participant(census_id);
CREATE INDEX IF NOT EXISTS idx_participant_hce ON participant(census_id, is_hce);
CREATE INDEX IF NOT EXISTS idx_result_census ON analysis_result(census_id);
CREATE INDEX IF NOT EXISTS idx_result_grid ON analysis_result(grid_analysis_id);
CREATE INDEX IF NOT EXISTS idx_result_timestamp ON analysis_result(run_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_grid_census ON grid_analysis(census_id);
CREATE INDEX IF NOT EXISTS idx_import_metadata_census ON import_metadata(census_id);

-- ============================================================================
-- CSV Import Wizard Tables (Feature 003-csv-import-wizard)
-- ============================================================================

-- Import wizard session state
CREATE TABLE IF NOT EXISTS import_session (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL,
    current_step TEXT NOT NULL DEFAULT 'upload'
        CHECK (current_step IN ('upload', 'map', 'validate', 'preview', 'confirm', 'completed')),
    file_reference TEXT,
    original_filename TEXT,
    file_size_bytes INTEGER,
    row_count INTEGER,
    headers TEXT,  -- JSON array
    column_mapping TEXT,  -- JSON object
    validation_results TEXT,  -- JSON object
    duplicate_resolution TEXT,  -- JSON object
    import_result_id TEXT REFERENCES import_log(id)
);

-- Saved column mapping profiles
CREATE TABLE IF NOT EXISTS mapping_profile (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    column_mapping TEXT NOT NULL,  -- JSON object
    expected_headers TEXT,  -- JSON array
    UNIQUE (user_id, name)
);

-- Validation issues (denormalized for query performance)
CREATE TABLE IF NOT EXISTS validation_issue (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES import_session(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL CHECK (row_number > 0),
    field_name TEXT NOT NULL,
    source_column TEXT,
    severity TEXT NOT NULL CHECK (severity IN ('error', 'warning', 'info')),
    issue_code TEXT NOT NULL,
    message TEXT NOT NULL,
    suggestion TEXT,
    raw_value TEXT,
    related_row INTEGER
);

-- Import logs with indefinite retention
CREATE TABLE IF NOT EXISTS import_log (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES import_session(id),
    census_id TEXT REFERENCES census(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    original_filename TEXT NOT NULL,
    total_rows INTEGER NOT NULL,
    imported_count INTEGER NOT NULL DEFAULT 0,
    rejected_count INTEGER NOT NULL DEFAULT 0,
    warning_count INTEGER NOT NULL DEFAULT 0,
    replaced_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,
    column_mapping_used TEXT NOT NULL,  -- JSON object
    detailed_results TEXT,  -- JSON array
    deleted_at TEXT  -- soft delete
);

-- Wizard indexes
CREATE INDEX IF NOT EXISTS idx_import_session_expires ON import_session(expires_at);
CREATE INDEX IF NOT EXISTS idx_import_session_user ON import_session(user_id);
CREATE INDEX IF NOT EXISTS idx_mapping_profile_user ON mapping_profile(user_id);
CREATE INDEX IF NOT EXISTS idx_validation_issue_session ON validation_issue(session_id);
CREATE INDEX IF NOT EXISTS idx_validation_issue_severity ON validation_issue(session_id, severity);
CREATE INDEX IF NOT EXISTS idx_import_log_census ON import_log(census_id);
CREATE INDEX IF NOT EXISTS idx_import_log_created ON import_log(created_at DESC);
"""

# Additional SQL for extending participant table with wizard fields
PARTICIPANT_EXTENSION_SQL = """
-- Add new columns for census import wizard (if not exist)
-- Note: SQLite doesn't support IF NOT EXISTS for ALTER TABLE,
-- so we check programmatically before adding columns
"""


def _add_column_if_not_exists(conn, table: str, column: str, col_type: str, default: str | None = None) -> None:
    """Add a column to a table if it doesn't already exist."""
    cursor = conn.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        default_clause = f" DEFAULT {default}" if default is not None else ""
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}{default_clause}")


def extend_participant_table(conn) -> None:
    """
    Extend the participant table with additional fields for the import wizard.

    New fields:
    - ssn_hash: Hashed SSN for duplicate detection
    - dob: Date of birth
    - hire_date: Hire date
    - employee_pre_tax_cents: Employee pre-tax contribution amount
    - employee_after_tax_cents: Employee after-tax contribution amount
    - employee_roth_cents: Employee Roth contribution amount
    - employer_match_cents: Employer match contribution amount
    - employer_non_elective_cents: Employer non-elective contribution amount
    """
    _add_column_if_not_exists(conn, "participant", "ssn_hash", "TEXT")
    _add_column_if_not_exists(conn, "participant", "dob", "TEXT")
    _add_column_if_not_exists(conn, "participant", "hire_date", "TEXT")
    _add_column_if_not_exists(conn, "participant", "employee_pre_tax_cents", "INTEGER", "0")
    _add_column_if_not_exists(conn, "participant", "employee_after_tax_cents", "INTEGER", "0")
    _add_column_if_not_exists(conn, "participant", "employee_roth_cents", "INTEGER", "0")
    _add_column_if_not_exists(conn, "participant", "employer_match_cents", "INTEGER", "0")
    _add_column_if_not_exists(conn, "participant", "employer_non_elective_cents", "INTEGER", "0")

    # Add index for SSN hash duplicate detection
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_participant_ssn_hash
        ON participant(ssn_hash)
    """)
    conn.commit()


def extend_import_session_table(conn) -> None:
    """
    Extend the import_session table with workspace_id and date_format fields.

    T004: Add date_format field for date parsing
    """
    _add_column_if_not_exists(conn, "import_session", "workspace_id", "TEXT")
    _add_column_if_not_exists(conn, "import_session", "date_format", "TEXT")

    # Add index for workspace
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_import_session_workspace
        ON import_session(workspace_id)
    """)
    conn.commit()


def extend_mapping_profile_table(conn) -> None:
    """
    Extend the mapping_profile table with workspace_id, date_format, and is_default fields.

    T005: Add workspace-scoped fields for mapping profiles
    """
    _add_column_if_not_exists(conn, "mapping_profile", "workspace_id", "TEXT")
    _add_column_if_not_exists(conn, "mapping_profile", "date_format", "TEXT")
    _add_column_if_not_exists(conn, "mapping_profile", "is_default", "INTEGER", "0")

    # Add index for workspace
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_mapping_profile_workspace
        ON mapping_profile(workspace_id)
    """)
    conn.commit()


def get_database_path() -> Path:
    """Get the database file path, creating parent directories if needed."""
    db_path = DATABASE_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def create_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """
    Create a database connection with WAL mode and foreign keys enabled.

    Args:
        db_path: Optional path to database file. Uses default if not provided.

    Returns:
        SQLite connection configured for the application
    """
    if db_path is None:
        db_path = get_database_path()

    conn = sqlite3.Connection(
        db_path,
        check_same_thread=False,
        timeout=30.0
    )

    # Enable WAL mode and foreign keys
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # Return rows as dictionaries
    conn.row_factory = sqlite3.Row

    return conn


def init_database(db_path: Path | None = None) -> None:
    """
    Initialize the database schema.

    Creates all tables and indexes if they don't exist.

    Args:
        db_path: Optional path to database file. Uses default if not provided.
    """
    conn = create_connection(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        # Extend participant table with wizard fields
        extend_participant_table(conn)
        # Extend import_session table with workspace_id and date_format
        extend_import_session_table(conn)
        # Extend mapping_profile table with workspace_id, date_format, is_default
        extend_mapping_profile_table(conn)
    finally:
        conn.close()


@contextmanager
def get_connection(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.

    Handles connection lifecycle and ensures proper cleanup.

    Args:
        db_path: Optional path to database file. Uses default if not provided.

    Yields:
        SQLite connection
    """
    conn = create_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


# Connection pool for FastAPI (simple implementation)
_connection: sqlite3.Connection | None = None


def get_db() -> sqlite3.Connection:
    """
    Get a database connection for dependency injection.

    This is intended for use with FastAPI's Depends() mechanism.
    For single-threaded Streamlit use, a shared connection is acceptable.

    Returns:
        SQLite connection
    """
    global _connection
    if _connection is None:
        init_database()
        _connection = create_connection()
    return _connection


def close_db() -> None:
    """Close the shared database connection."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None


def reset_database(db_path: Path | None = None) -> None:
    """
    Reset the database by dropping and recreating all tables.

    WARNING: This deletes all data!

    Args:
        db_path: Optional path to database file. Uses default if not provided.
    """
    close_db()

    if db_path is None:
        db_path = get_database_path()

    if db_path.exists():
        db_path.unlink()

    init_database(db_path)
