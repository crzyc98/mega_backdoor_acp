"""Census Pydantic models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CensusSummary(BaseModel):
    """Summary statistics for uploaded census data."""

    id: str
    plan_year: int = Field(..., ge=2020, le=2100)
    participant_count: int
    hce_count: int
    nhce_count: int
    avg_compensation: Optional[float] = None
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
