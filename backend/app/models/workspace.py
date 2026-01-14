"""Workspace Pydantic models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class WorkspaceBase(BaseModel):
    """Base workspace model with common fields."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class WorkspaceCreate(WorkspaceBase):
    """Model for creating a new workspace."""

    pass


class WorkspaceUpdate(BaseModel):
    """Model for updating a workspace."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class Workspace(WorkspaceBase):
    """Full workspace model with all fields."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


class WorkspaceDetail(Workspace):
    """Workspace with additional computed fields."""

    has_census: bool = False
    run_count: int = 0


class WorkspaceListResponse(BaseModel):
    """Response model for workspace list."""

    items: list[Workspace]
    total: int
