"""
Pydantic Models for Scenario Analysis (Feature 004) and Employee Impact (Feature 006).

T002-T012: Core data models for scenario requests, results, grid analysis,
and debug information.
T007-T011 (Feature 006): Employee impact models for drill-down views.
"""

from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


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


# Exclusion reason enumeration
class ACPExclusionReason(str, Enum):
    """Reason a participant was excluded from ACP calculations."""
    TERMINATED_BEFORE_ENTRY = "TERMINATED_BEFORE_ENTRY"
    NOT_ELIGIBLE_DURING_YEAR = "NOT_ELIGIBLE_DURING_YEAR"
    MISSING_DOB = "MISSING_DOB"
    MISSING_HIRE_DATE = "MISSING_HIRE_DATE"


# Exclusion tracking models
class ExclusionInfo(BaseModel):
    """Summary of excluded participants with breakdown by reason."""
    total_excluded: int = Field(..., ge=0, description="Total participants excluded from ACP")
    terminated_before_entry_count: int = Field(
        ..., ge=0, description="Excluded: terminated before entry date"
    )
    not_eligible_during_year_count: int = Field(
        ..., ge=0, description="Excluded: not eligible during plan year"
    )
    missing_dob_count: int = Field(
        0, ge=0, description="Excluded: missing date of birth"
    )
    missing_hire_date_count: int = Field(
        0, ge=0, description="Excluded: missing hire date"
    )


class ExcludedParticipant(BaseModel):
    """Details of an excluded participant for export/display."""
    employee_id: str = Field(..., description="Participant employee ID")
    is_hce: bool = Field(..., description="Whether participant is HCE")
    exclusion_reason: Literal[
        "TERMINATED_BEFORE_ENTRY",
        "NOT_ELIGIBLE_DURING_YEAR",
        "MISSING_DOB",
        "MISSING_HIRE_DATE",
    ] = Field(..., description="Reason for exclusion")
    eligibility_date: str | None = Field(None, description="Calculated eligibility date")
    entry_date: str | None = Field(None, description="Calculated entry date")
    termination_date: str | None = Field(None, description="Termination date if applicable")


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
    excluded_count: int | None = Field(
        None, ge=0, description="Participants excluded from ACP test"
    )
    exclusion_breakdown: ExclusionInfo | None = Field(
        None, description="Breakdown of exclusion reasons"
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
    excluded_count: int = Field(
        0, ge=0, description="Total participants excluded from ACP (same across all scenarios)"
    )
    exclusion_breakdown: ExclusionInfo | None = Field(
        None, description="Breakdown of exclusion reasons"
    )


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


# =============================================================================
# Employee-Level Impact Models (Feature 006-employee-level-impact)
# =============================================================================


# T007: Constraint status enumeration for HCE mega-backdoor contributions
class ConstraintStatus(str, Enum):
    """
    Constraint classification for HCE mega-backdoor contributions.

    - UNCONSTRAINED: Received full requested mega-backdoor amount
    - AT_LIMIT: Capped by §415(c) annual additions limit
    - REDUCED: Received partial mega-backdoor due to §415(c) limit
    - NOT_SELECTED: Not chosen for mega-backdoor adoption in this scenario
    """
    UNCONSTRAINED = "Unconstrained"
    AT_LIMIT = "At §415(c) Limit"
    REDUCED = "Reduced"
    NOT_SELECTED = "Not Selected"


# T008: Per-employee contribution breakdown model
class EmployeeImpact(BaseModel):
    """
    Per-employee contribution breakdown for employee-level impact view.

    Represents a single participant's contribution details within
    a specific scenario, including §415(c) limit analysis.
    """
    employee_id: str = Field(
        ...,
        min_length=1,
        description="Anonymized identifier from census (internal_id)"
    )
    is_hce: bool = Field(
        ...,
        description="True if HCE, False if NHCE"
    )
    compensation: float = Field(
        ...,
        ge=0,
        description="Annual compensation in dollars"
    )
    deferral_amount: float = Field(
        ...,
        ge=0,
        description="Employee deferral contributions in dollars"
    )
    match_amount: float = Field(
        ...,
        ge=0,
        description="Employer match contributions in dollars"
    )
    after_tax_amount: float = Field(
        ...,
        ge=0,
        description="Existing after-tax contributions in dollars"
    )
    section_415c_limit: int = Field(
        ...,
        ge=0,
        description="Applicable §415(c) limit for plan year in dollars"
    )
    available_room: float = Field(
        ...,
        description="Remaining capacity before hitting §415(c) limit (can be negative)"
    )
    mega_backdoor_amount: float = Field(
        ...,
        ge=0,
        description="Computed mega-backdoor contribution for this scenario"
    )
    requested_mega_backdoor: float = Field(
        ...,
        ge=0,
        description="Full mega-backdoor amount before any constraints"
    )
    individual_acp: float | None = Field(
        None,
        ge=0,
        description="This employee's ACP percentage (None if zero compensation)"
    )
    constraint_status: ConstraintStatus = Field(
        ...,
        description="Classification of constraint impact"
    )
    constraint_detail: str = Field(
        ...,
        description="Human-readable explanation of constraint"
    )


# T009: Aggregated summary model for HCE/NHCE groups
class EmployeeImpactSummary(BaseModel):
    """
    Aggregated statistics for HCE or NHCE group.

    Provides summary metrics for display in the summary panel.
    HCE-specific fields are None for NHCE groups.
    """
    group: Literal["HCE", "NHCE"] = Field(
        ...,
        description="Which participant group this summarizes"
    )
    total_count: int = Field(
        ...,
        ge=0,
        description="Total participants in group"
    )
    # HCE-specific fields (None for NHCE)
    at_limit_count: int | None = Field(
        None,
        ge=0,
        description="Number at §415(c) limit (HCE only)"
    )
    reduced_count: int | None = Field(
        None,
        ge=0,
        description="Number with reduced mega-backdoor (HCE only)"
    )
    average_available_room: float | None = Field(
        None,
        description="Mean available room in dollars (HCE only)"
    )
    total_mega_backdoor: float | None = Field(
        None,
        ge=0,
        description="Sum of mega-backdoor amounts (HCE only)"
    )
    # Shared fields
    average_individual_acp: float = Field(
        ...,
        ge=0,
        description="Mean individual ACP percentage"
    )
    total_match: float = Field(
        ...,
        ge=0,
        description="Sum of match contributions"
    )
    total_after_tax: float = Field(
        ...,
        ge=0,
        description="Sum of after-tax contributions"
    )


# T010: Request model for employee impact computation
class EmployeeImpactRequest(BaseModel):
    """
    Request parameters for computing employee impact view.

    Contains the scenario parameters needed to reproduce
    HCE selection and compute individual contributions.
    """
    census_id: str = Field(
        ...,
        description="Reference to census data"
    )
    adoption_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fraction of HCEs participating (0.0 to 1.0)"
    )
    contribution_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Mega-backdoor contribution as fraction of compensation"
    )
    seed: int = Field(
        ...,
        ge=1,
        description="Random seed for HCE selection reproducibility"
    )


# T011: Container model for complete employee impact view
class EmployeeImpactView(BaseModel):
    """
    Complete employee-level impact view for a scenario.

    Contains all participant details and summary statistics
    for display in the UI.
    """
    # Scenario context
    census_id: str = Field(
        ...,
        description="Census this analysis is for"
    )
    adoption_rate: float = Field(
        ...,
        description="Adoption rate used"
    )
    contribution_rate: float = Field(
        ...,
        description="Contribution rate used"
    )
    seed_used: int = Field(
        ...,
        description="Seed used for HCE selection"
    )
    plan_year: int = Field(
        ...,
        description="Plan year for §415(c) limit lookup"
    )
    section_415c_limit: int = Field(
        ...,
        description="§415(c) limit applied"
    )
    excluded_count: int = Field(
        ...,
        ge=0,
        description="Number of participants excluded from ACP"
    )
    exclusion_breakdown: ExclusionInfo | None = Field(
        None,
        description="Breakdown of exclusion reasons"
    )
    excluded_participants: list[ExcludedParticipant] | None = Field(
        None,
        description="List of excluded participants for export/display"
    )

    # Employee data
    hce_employees: list[EmployeeImpact] = Field(
        default_factory=list,
        description="HCE participant details"
    )
    nhce_employees: list[EmployeeImpact] = Field(
        default_factory=list,
        description="NHCE participant details"
    )

    # Summary statistics
    hce_summary: EmployeeImpactSummary = Field(
        ...,
        description="HCE group summary"
    )
    nhce_summary: EmployeeImpactSummary = Field(
        ...,
        description="NHCE group summary"
    )
