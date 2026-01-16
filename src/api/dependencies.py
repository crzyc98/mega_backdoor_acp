"""
FastAPI Dependencies for API Routes.

Provides reusable dependency injection functions for database access,
workspace identification, and other shared functionality.
"""

from typing import Annotated

import duckdb
from fastapi import Depends, Header

from src.storage.database import get_db

# Default workspace ID for backwards compatibility
DEFAULT_WORKSPACE_ID = "default"


def get_workspace_id(
    x_workspace_id: Annotated[str | None, Header()] = None
) -> str:
    """
    Extract workspace ID from request header.

    Falls back to default workspace if not provided.
    """
    return x_workspace_id or DEFAULT_WORKSPACE_ID


def get_database(
    workspace_id: Annotated[str, Depends(get_workspace_id)]
) -> duckdb.DuckDBPyConnection:
    """
    Get database connection for the current workspace.

    This is a FastAPI dependency that provides workspace-isolated database access.
    """
    return get_db(workspace_id)
