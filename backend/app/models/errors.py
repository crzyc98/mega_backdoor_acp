"""Error response models."""

from __future__ import annotations

from pydantic import BaseModel


class Error(BaseModel):
    """Standard error response."""

    error: str
    message: str
