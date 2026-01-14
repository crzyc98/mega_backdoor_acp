"""Analysis result Pydantic models."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class AnalysisStatus(str, Enum):
    """Scenario analysis status."""

    PASS = "PASS"
    RISK = "RISK"
    FAIL = "FAIL"
    ERROR = "ERROR"


class ScenarioResult(BaseModel):
    """Result of a single scenario analysis."""

    status: AnalysisStatus
    nhce_acp: Optional[float] = None
    hce_acp: Optional[float] = None
    limit_125: Optional[float] = None
    limit_2pct_uncapped: Optional[float] = None
    cap_2x: Optional[float] = None
    limit_2pct_capped: Optional[float] = None
    effective_limit: Optional[float] = None
    max_allowed_acp: Optional[float] = None
    margin: Optional[float] = None
    binding_rule: Optional[str] = None
    adoption_rate: float
    contribution_rate: float
    seed_used: int


class GridSummary(BaseModel):
    """Aggregate metrics for grid analysis."""

    pass_count: int
    risk_count: int
    fail_count: int
    error_count: int
    total_count: int
    first_failure_point: Optional[dict] = None
    max_safe_contribution: Optional[float] = None
    worst_margin: Optional[float] = None


class GridResult(BaseModel):
    """Collection of scenario results."""

    scenarios: list[ScenarioResult]
    summary: GridSummary
    seed_used: int


class RunDetail(BaseModel):
    """Run with full results."""

    # Include all Run fields plus results
    id: str
    workspace_id: str
    name: Optional[str] = None
    adoption_rates: list[float]
    contribution_rates: list[float]
    seed: int
    status: str
    created_at: str
    completed_at: Optional[str] = None
    results: Optional[GridResult] = None
