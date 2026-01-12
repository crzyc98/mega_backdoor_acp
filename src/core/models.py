"""
Pydantic Models for Scenario Analysis (Feature 004).

T002-T012: Core data models for scenario requests, results, grid analysis,
and debug information.
"""

from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# T002: Scenario status enumeration
class ScenarioStatus(str, Enum):
    """
    Status classification for a scenario result.

    - PASS: HCE ACP ≤ threshold AND margin > 0.50 percentage points
    - RISK: HCE ACP ≤ threshold AND margin ≤ 0.50 percentage points (fragile)
    - FAIL: HCE ACP > threshold
    - ERROR: Calculation not possible (e.g., zero HCEs, zero NHCEs)
    """
    PASS = "PASS"
    RISK = "RISK"
    FAIL = "FAIL"
    ERROR = "ERROR"


# T003: Limiting bound enumeration
class LimitingBound(str, Enum):
    """
    Indicates which ACP test formula determined the threshold.

    - MULTIPLE: The 1.25× test is more restrictive
    - ADDITIVE: The +2.0 test is more restrictive
    """
    MULTIPLE = "MULTIPLE"
    ADDITIVE = "ADDITIVE"


# T007: Per-participant contribution breakdown for debug output
class ParticipantContribution(BaseModel):
    """Per-participant contribution breakdown for audit/debugging."""
    id: str = Field(..., description="Participant internal ID")
    compensation_cents: int = Field(..., description="Annual compensation in cents")
    existing_acp_contributions_cents: int = Field(
        ..., description="Match + after-tax contributions in cents"
    )
    simulated_mega_backdoor_cents: int = Field(
        0, description="Simulated contribution in cents (0 for non-adopters)"
    )
    individual_acp: float = Field(..., description="This participant's ACP percentage")


# T008: Intermediate calculation values for debug output
class IntermediateValues(BaseModel):
    """Calculation intermediate values for debugging."""
    hce_acp_sum: float = Field(..., description="Sum of individual HCE ACPs before averaging")
    hce_count: int = Field(..., description="Number of HCEs in calculation")
    nhce_acp_sum: float = Field(..., description="Sum of individual NHCE ACPs before averaging")
    nhce_count: int = Field(..., description="Number of NHCEs in calculation")
    threshold_multiple: float = Field(..., description="NHCE ACP × 1.25")
    threshold_additive: float = Field(..., description="NHCE ACP + 2.0 (capped at 2× NHCE ACP)")


# T006: Debug details for audit/debugging
class DebugDetails(BaseModel):
    """Detailed calculation breakdown; present only when include_debug=true."""
    selected_hce_ids: list[str] = Field(
        ..., description="IDs of HCEs selected for mega-backdoor contributions"
    )
    hce_contributions: list[ParticipantContribution] = Field(
        ..., description="Per-HCE contribution details"
    )
    nhce_contributions: list[ParticipantContribution] = Field(
        ..., description="Per-NHCE contribution details"
    )
    intermediate_values: IntermediateValues = Field(
        ..., description="Calculation intermediates"
    )


# T004: Scenario request input parameters
class ScenarioRequest(BaseModel):
    """Input parameters for running a single scenario analysis."""
    census_id: str = Field(..., description="Reference to loaded census data")
    adoption_rate: float = Field(
        ..., ge=0.0, le=1.0,
        description="Fraction of HCEs participating in mega-backdoor (0.0 to 1.0)"
    )
    contribution_rate: float = Field(
        ..., ge=0.0, le=1.0,
        description="Mega-backdoor contribution as fraction of compensation (0.0 to 1.0)"
    )
    seed: int | None = Field(
        None, ge=1,
        description="Random seed for HCE selection reproducibility"
    )
    include_debug: bool = Field(
        False, description="Include detailed calculation breakdown in response"
    )


# T005: Complete scenario result output
class ScenarioResult(BaseModel):
    """Complete output of a single scenario analysis."""
    status: ScenarioStatus = Field(..., description="PASS, RISK, FAIL, or ERROR")
    nhce_acp: float | None = Field(
        None, description="NHCE Actual Contribution Percentage (null if ERROR)"
    )
    hce_acp: float | None = Field(
        None, description="HCE Actual Contribution Percentage (null if ERROR)"
    )
    max_allowed_acp: float | None = Field(
        None, description="Threshold value HCE ACP must not exceed (null if ERROR)"
    )
    margin: float | None = Field(
        None, description="Distance from threshold; positive=passing, negative=failing (null if ERROR)"
    )
    limiting_bound: LimitingBound | None = Field(
        None, description="Which test formula determined the threshold (null if ERROR)"
    )
    hce_contributor_count: int | None = Field(
        None, description="Number of HCEs receiving simulated mega-backdoor (null if ERROR)"
    )
    nhce_contributor_count: int | None = Field(
        None, description="Number of NHCEs with qualifying contributions (null if ERROR)"
    )
    total_mega_backdoor_amount: float | None = Field(
        None, description="Sum of simulated contributions in dollars (null if ERROR)"
    )
    seed_used: int = Field(..., description="Actual random seed applied for HCE selection")
    adoption_rate: float = Field(..., description="Echo of input adoption rate")
    contribution_rate: float = Field(..., description="Echo of input contribution rate")
    error_message: str | None = Field(
        None, description="Description of error; null if status != ERROR"
    )
    debug_details: DebugDetails | None = Field(
        None, description="Detailed breakdown; present only if include_debug=true"
    )


# T012: Failure point coordinates for grid summary
class FailurePoint(BaseModel):
    """Coordinates of a failure in the grid."""
    adoption_rate: float = Field(..., description="Adoption rate where failure occurred")
    contribution_rate: float = Field(..., description="Contribution rate where failure occurred")


# T011: Grid summary statistics
class GridSummary(BaseModel):
    """Compact summary statistics of a grid analysis."""
    pass_count: int = Field(..., ge=0, description="Number of scenarios with PASS status")
    risk_count: int = Field(..., ge=0, description="Number of scenarios with RISK status")
    fail_count: int = Field(..., ge=0, description="Number of scenarios with FAIL status")
    error_count: int = Field(0, ge=0, description="Number of scenarios with ERROR status")
    total_count: int = Field(..., ge=1, description="Total scenarios in grid")
    first_failure_point: FailurePoint | None = Field(
        None, description="Coordinates of first failure; null if no failures"
    )
    max_safe_contribution: float | None = Field(
        None, description="Highest passing contribution at max adoption; null if none pass"
    )
    worst_margin: float = Field(..., description="Smallest margin value across all scenarios")


# T009: Grid request input parameters
class GridRequest(BaseModel):
    """Input parameters for running a grid of scenarios."""
    census_id: str = Field(..., description="Reference to loaded census data")
    adoption_rates: list[float] = Field(
        ..., min_length=2, max_length=20,
        description="List of adoption rates to test (each 0.0 to 1.0)"
    )
    contribution_rates: list[float] = Field(
        ..., min_length=2, max_length=20,
        description="List of contribution rates to test (each 0.0 to 1.0)"
    )
    seed: int | None = Field(
        None, ge=1,
        description="Base seed for all scenarios"
    )
    include_debug: bool = Field(
        False, description="Include debug details in each scenario result"
    )


# T010: Complete grid result output
class GridResult(BaseModel):
    """Complete output of a grid analysis."""
    scenarios: list[ScenarioResult] = Field(
        ..., description="All scenario results (one per grid cell)"
    )
    summary: GridSummary = Field(..., description="Aggregate metrics")
    seed_used: int = Field(..., description="Base seed used for all scenarios")
