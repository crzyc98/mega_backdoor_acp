"""Error response models."""

from pydantic import BaseModel


class Error(BaseModel):
    """Standard error response."""

    error: str
    message: str
