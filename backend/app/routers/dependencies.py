"""
Shared FastAPI dependencies for workspace-aware database access.

This module provides dependency injection functions that extract the workspace ID
from the X-Workspace-ID header and return workspace-scoped database connections.
"""

from __future__ import annotations

import duckdb
from fastapi import Header

from app.storage.database import get_db


def get_workspace_id_from_header(
    x_workspace_id: str = Header(..., alias="X-Workspace-ID")
) -> str:
    """
    Extract workspace ID from the X-Workspace-ID request header.

    This dependency is required for all routes that need database access,
    ensuring workspace isolation for DuckDB connections.

    Args:
        x_workspace_id: The workspace UUID from the request header

    Returns:
        The workspace ID string
    """
    return x_workspace_id


def get_workspace_db(
    workspace_id: str,
) -> duckdb.DuckDBPyConnection:
    """
    Get a DuckDB connection for the specified workspace.

    Args:
        workspace_id: The workspace UUID

    Returns:
        DuckDB connection for the workspace's database
    """
    return get_db(workspace_id)
