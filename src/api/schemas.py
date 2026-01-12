"""
Pydantic Schemas for API Request/Response Models.

These schemas match the OpenAPI specification in contracts/openapi.yaml.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# Census Schemas
class CensusCreate(BaseModel):
    """Request model for census creation (form data fields)."""
    plan_year: int = Field(..., ge=2020, le=2100, description="Plan year for analysis")
    name: str | None = Field(None, max_length=255, description="Optional name for the census")


class CensusSummary(BaseModel):
    """Summary view of a census."""
    id: str
    name: str
    plan_year: int
    participant_count: int
    hce_count: int
    nhce_count: int


class Census(CensusSummary):
    """Full census details."""
    upload_timestamp: datetime
    version: str


class CensusListResponse(BaseModel):
    """Response model for census list endpoint."""
    items: list[CensusSummary]
    total: int
    limit: int
    offset: int


# Analysis Request Schemas
class SingleScenarioRequest(BaseModel):
    """Request model for single scenario analysis."""
    adoption_rate: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of HCEs adopting mega-backdoor (0-100)"
    )
    contribution_rate: float = Field(
        ...,
        ge=0,
        le=15,
        description="Mega-backdoor contribution rate as % of compensation (0-15)"
    )
    seed: int | None = Field(
        None,
        description="Random seed for HCE selection (auto-generated if omitted)"
    )


class GridScenarioRequest(BaseModel):
    """Request model for grid scenario analysis."""
    adoption_rates: list[float] = Field(
        ...,
        min_length=2,
        max_length=20,
        description="List of adoption rates to test (0-100)"
    )
    contribution_rates: list[float] = Field(
        ...,
        min_length=2,
        max_length=20,
        description="List of contribution rates to test (0-15)"
    )
    seed: int | None = Field(
        None,
        description="Random seed for HCE selection (shared across all scenarios)"
    )
    name: str | None = Field(
        None,
        max_length=255,
        description="Optional name for the grid analysis"
    )


# Analysis Result Schemas
class AnalysisResult(BaseModel):
    """Result of a single scenario analysis."""
    id: str
    census_id: str
    grid_analysis_id: str | None = None
    adoption_rate: float
    contribution_rate: float
    seed: int
    nhce_acp: float
    hce_acp: float
    threshold: float
    margin: float
    result: Literal["PASS", "FAIL"]
    limiting_test: Literal["1.25x", "+2.0"]
    run_timestamp: datetime
    version: str


class AnalysisResultListResponse(BaseModel):
    """Response model for analysis results list endpoint."""
    items: list[AnalysisResult]
    total: int


class GridSummary(BaseModel):
    """Summary statistics for a grid analysis."""
    total_scenarios: int
    pass_count: int
    fail_count: int
    pass_rate: float


class GridAnalysisResult(BaseModel):
    """Result of a grid scenario analysis."""
    id: str
    census_id: str
    name: str | None = None
    adoption_rates: list[float]
    contribution_rates: list[float]
    seed: int
    results: list[AnalysisResult]
    summary: GridSummary
    created_timestamp: datetime
    version: str


# Error Schemas
class ValidationErrorDetail(BaseModel):
    """Detail of a validation error."""
    loc: list[str]
    msg: str
    type: str


class ValidationError(BaseModel):
    """Response model for validation errors."""
    detail: list[ValidationErrorDetail]


class Error(BaseModel):
    """Response model for general errors."""
    error: str
    message: str


# Health Check Schema
class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = "healthy"
    version: str
