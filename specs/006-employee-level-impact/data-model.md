# Data Model: Employee-Level Impact Views

**Feature**: 006-employee-level-impact
**Date**: 2026-01-13

## Overview

This document defines the data models for the Employee-Level Impact feature. These models enable drill-down visibility into individual participant contributions within an ACP scenario.

## New Entities

### ConstraintStatus (Enum)

Classification of how an HCE's mega-backdoor contribution was affected by limits.

```python
class ConstraintStatus(str, Enum):
    """
    Constraint classification for HCE mega-backdoor contributions.
    """
    UNCONSTRAINED = "Unconstrained"      # Received full requested mega-backdoor
    AT_LIMIT = "At §415(c) Limit"        # Capped by annual additions limit
    REDUCED = "Reduced"                   # Received partial mega-backdoor
    NOT_SELECTED = "Not Selected"         # Not chosen for mega-backdoor adoption
```

### EmployeeImpact (Pydantic Model)

Individual employee contribution breakdown for a scenario.

```python
class EmployeeImpact(BaseModel):
    """
    Per-employee contribution breakdown for employee-level impact view.

    Represents a single participant's contribution details within
    a specific scenario, including §415(c) limit analysis.
    """
    employee_id: str = Field(
        ...,
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
```

**Validation Rules**:
- `employee_id` must be non-empty string
- `compensation` must be >= 0
- `individual_acp` is None only when compensation is 0 (avoid division by zero)
- `mega_backdoor_amount` <= `requested_mega_backdoor`
- `available_room` = `section_415c_limit` - (`deferral_amount` + `match_amount` + `after_tax_amount` + `mega_backdoor_amount`)

**State Transitions**:
- `constraint_status` is computed, not user-modifiable
- Status depends on selection and limit calculations

### EmployeeImpactSummary (Pydantic Model)

Aggregated statistics for a participant group (HCE or NHCE).

```python
class EmployeeImpactSummary(BaseModel):
    """
    Aggregated statistics for HCE or NHCE group.

    Provides summary metrics for display in the summary panel.
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
```

**Validation Rules**:
- HCE-specific fields (`at_limit_count`, `reduced_count`, `average_available_room`, `total_mega_backdoor`) are required when `group == "HCE"`, None when `group == "NHCE"`
- All count and total fields must be >= 0
- Averages calculated excluding any participants with zero compensation

### EmployeeImpactRequest (Pydantic Model)

Request parameters for fetching employee impact data.

```python
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
```

### EmployeeImpactView (Pydantic Model)

Container for the complete employee-level impact analysis.

```python
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
```

**Relationships**:
- References `Census` via `census_id`
- Contains lists of `EmployeeImpact` for each group
- Contains `EmployeeImpactSummary` for each group

## Entity Relationship Diagram

```
┌─────────────────────┐
│     Census          │
│  (existing entity)  │
└─────────┬───────────┘
          │ 1
          │
          │ has many
          ▼ *
┌─────────────────────┐
│   Participant       │
│  (existing entity)  │
└─────────┬───────────┘
          │
          │ transforms to
          ▼
┌─────────────────────┐      ┌─────────────────────────┐
│  EmployeeImpact     │◄─────│  EmployeeImpactRequest  │
│   (new model)       │      │     (new model)         │
└─────────┬───────────┘      └─────────────────────────┘
          │                            │
          │ aggregates to              │ produces
          ▼                            ▼
┌─────────────────────┐      ┌─────────────────────────┐
│EmployeeImpactSummary│◄─────│   EmployeeImpactView    │
│    (new model)      │      │     (new model)         │
└─────────────────────┘      └─────────────────────────┘
```

## Existing Entities Used

### Participant (from src/storage/models.py)

```python
@dataclass
class Participant:
    id: str
    census_id: str
    internal_id: str              # → EmployeeImpact.employee_id
    is_hce: bool                  # → EmployeeImpact.is_hce
    compensation_cents: int       # → EmployeeImpact.compensation (÷100)
    deferral_rate: float          # → compute deferral_amount
    match_rate: float             # → compute match_amount
    after_tax_rate: float         # → compute after_tax_amount
```

### Census (from src/storage/models.py)

```python
@dataclass
class Census:
    id: str
    plan_year: int                # → Used for §415(c) limit lookup
    # ... other fields
```

### ScenarioResult (from src/core/models.py)

```python
class ScenarioResult(BaseModel):
    adoption_rate: float          # → EmployeeImpactRequest.adoption_rate
    contribution_rate: float      # → EmployeeImpactRequest.contribution_rate
    seed_used: int                # → EmployeeImpactRequest.seed
    # ... other fields
```

## Data Flow

```
1. User clicks "View Employee Details" in heatmap detail panel
   ↓
2. Frontend extracts ScenarioResult parameters (adoption_rate, contribution_rate, seed_used, census_id)
   ↓
3. Creates EmployeeImpactRequest and calls API or service
   ↓
4. Service fetches Participant data from database via ParticipantRepository
   ↓
5. Service computes EmployeeImpact for each participant:
   - Calculate deferral_amount = compensation × deferral_rate
   - Calculate match_amount = compensation × match_rate
   - Calculate after_tax_amount = compensation × after_tax_rate
   - Reproduce HCE selection using seed
   - Calculate requested_mega_backdoor = compensation × contribution_rate (for selected HCEs)
   - Calculate available_room = 415c_limit - existing contributions
   - Determine actual mega_backdoor_amount = min(requested, available_room)
   - Classify constraint_status
   - Generate constraint_detail message
   ↓
6. Service aggregates EmployeeImpactSummary for each group
   ↓
7. Service returns EmployeeImpactView
   ↓
8. Frontend displays tabbed view with sorting/filtering/export
```

## Storage Notes

- **No new database tables required**: Employee impact is computed on-demand
- **No persistence of computed data**: Results are transient, regenerated on each request
- **Existing tables used**: `census`, `participant`
- **Session state caching**: UI may cache EmployeeImpactView in Streamlit session state to avoid recomputation during the same session
