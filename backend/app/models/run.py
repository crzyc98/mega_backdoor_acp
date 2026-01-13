"""Run Pydantic models for analysis execution."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    """Run execution status."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RunCreate(BaseModel):
    """Model for creating a new analysis run."""

    name: Optional[str] = Field(None, max_length=255)
    adoption_rates: list[float] = Field(..., min_length=2, max_length=20)
    contribution_rates: list[float] = Field(..., min_length=2, max_length=20)
    seed: Optional[int] = Field(None, ge=1)


class Run(BaseModel):
    """Full run model."""

    id: UUID = Field(default_factory=uuid4)
    workspace_id: UUID
    name: Optional[str] = None
    adoption_rates: list[float]
    contribution_rates: list[float]
    seed: int
    status: RunStatus = RunStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RunListResponse(BaseModel):
    """Response model for run list."""

    items: list[Run]
    total: int
