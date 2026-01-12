"""
SQLite Database Connection and Schema Management.

This module provides database connectivity with WAL mode for concurrent reads
and schema initialization for the ACP Sensitivity Analyzer.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from src.core.constants import DATABASE_PATH

# SQL Schema Definition per data-model.md
SCHEMA_SQL = """
-- Enable WAL mode for concurrent reads
PRAGMA journal_mode=WAL;

-- Census table: Collection of participant records for a plan
CREATE TABLE IF NOT EXISTS census (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    plan_year INTEGER NOT NULL CHECK (plan_year BETWEEN 2020 AND 2100),
    upload_timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    participant_count INTEGER NOT NULL CHECK (participant_count >= 0),
    hce_count INTEGER NOT NULL CHECK (hce_count >= 0),
    nhce_count INTEGER NOT NULL CHECK (nhce_count >= 0),
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

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_census_plan_year ON census(plan_year);
CREATE INDEX IF NOT EXISTS idx_census_upload ON census(upload_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_participant_census ON participant(census_id);
CREATE INDEX IF NOT EXISTS idx_participant_hce ON participant(census_id, is_hce);
CREATE INDEX IF NOT EXISTS idx_result_census ON analysis_result(census_id);
CREATE INDEX IF NOT EXISTS idx_result_grid ON analysis_result(grid_analysis_id);
CREATE INDEX IF NOT EXISTS idx_result_timestamp ON analysis_result(run_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_grid_census ON grid_analysis(census_id);
"""


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
