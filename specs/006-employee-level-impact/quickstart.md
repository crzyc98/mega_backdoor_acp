# Quickstart: Employee-Level Impact Views

**Feature**: 006-employee-level-impact
**Date**: 2026-01-13

## Overview

This guide covers how to implement and use the Employee-Level Impact feature, which provides drill-down visibility into individual participant contributions within ACP scenarios.

## Prerequisites

- Python 3.11+
- Existing ACP Sensitivity Analyzer codebase
- Census data loaded (via spec 002)
- Scenario analysis working (via spec 004)
- Heatmap exploration working (via spec 005)

## Quick Implementation Guide

### 1. Add Core Models

Add to `src/core/models.py`:

```python
from enum import Enum

class ConstraintStatus(str, Enum):
    UNCONSTRAINED = "Unconstrained"
    AT_LIMIT = "At §415(c) Limit"
    REDUCED = "Reduced"
    NOT_SELECTED = "Not Selected"

class EmployeeImpact(BaseModel):
    employee_id: str
    is_hce: bool
    compensation: float
    deferral_amount: float
    match_amount: float
    after_tax_amount: float
    section_415c_limit: int
    available_room: float
    mega_backdoor_amount: float
    requested_mega_backdoor: float
    individual_acp: float | None
    constraint_status: ConstraintStatus
    constraint_detail: str

class EmployeeImpactSummary(BaseModel):
    group: Literal["HCE", "NHCE"]
    total_count: int
    at_limit_count: int | None = None
    reduced_count: int | None = None
    average_available_room: float | None = None
    total_mega_backdoor: float | None = None
    average_individual_acp: float
    total_match: float
    total_after_tax: float

class EmployeeImpactView(BaseModel):
    census_id: str
    adoption_rate: float
    contribution_rate: float
    seed_used: int
    plan_year: int
    section_415c_limit: int
    hce_employees: list[EmployeeImpact]
    nhce_employees: list[EmployeeImpact]
    hce_summary: EmployeeImpactSummary
    nhce_summary: EmployeeImpactSummary
```

### 2. Create Employee Impact Service

Create `src/core/employee_impact.py`:

```python
import random
from src.core.constants import get_415c_limit
from src.core.models import (
    ConstraintStatus, EmployeeImpact,
    EmployeeImpactSummary, EmployeeImpactView
)
from src.storage.repository import ParticipantRepository, CensusRepository

class EmployeeImpactService:
    def __init__(self, participant_repo: ParticipantRepository, census_repo: CensusRepository):
        self.participant_repo = participant_repo
        self.census_repo = census_repo

    def compute_impact(
        self,
        census_id: str,
        adoption_rate: float,
        contribution_rate: float,
        seed: int
    ) -> EmployeeImpactView:
        # 1. Get census and participants
        census = self.census_repo.get(census_id)
        participants = self.participant_repo.get_by_census_id(census_id)

        # 2. Get §415(c) limit
        limit_415c = get_415c_limit(census.plan_year)

        # 3. Separate HCEs and NHCEs
        hces = [p for p in participants if p.is_hce]
        nhces = [p for p in participants if not p.is_hce]

        # 4. Select HCEs for mega-backdoor (reproduce with seed)
        random.seed(seed)
        num_selected = int(len(hces) * adoption_rate + 0.5)
        selected_ids = set(p.internal_id for p in random.sample(hces, num_selected))

        # 5. Compute impact for each participant
        hce_impacts = [
            self._compute_employee_impact(p, limit_415c, contribution_rate, p.internal_id in selected_ids)
            for p in hces
        ]
        nhce_impacts = [
            self._compute_employee_impact(p, limit_415c, 0, False)
            for p in nhces
        ]

        # 6. Compute summaries
        hce_summary = self._compute_summary(hce_impacts, "HCE")
        nhce_summary = self._compute_summary(nhce_impacts, "NHCE")

        return EmployeeImpactView(
            census_id=census_id,
            adoption_rate=adoption_rate,
            contribution_rate=contribution_rate,
            seed_used=seed,
            plan_year=census.plan_year,
            section_415c_limit=limit_415c,
            hce_employees=hce_impacts,
            nhce_employees=nhce_impacts,
            hce_summary=hce_summary,
            nhce_summary=nhce_summary
        )

    def _compute_employee_impact(self, participant, limit_415c, contribution_rate, is_selected):
        compensation = participant.compensation_cents / 100
        deferral = compensation * participant.deferral_rate / 100
        match = compensation * participant.match_rate / 100
        after_tax = compensation * participant.after_tax_rate / 100

        requested = compensation * contribution_rate if is_selected else 0
        existing_total = deferral + match + after_tax
        available = limit_415c - existing_total
        actual = min(requested, max(0, available)) if is_selected else 0

        # Determine constraint status
        if not is_selected:
            status = ConstraintStatus.NOT_SELECTED
            detail = "Not selected for mega-backdoor participation"
        elif actual == 0 and requested > 0:
            status = ConstraintStatus.AT_LIMIT
            detail = f"§415(c) limit of ${limit_415c:,} reached with existing contributions"
        elif actual < requested:
            status = ConstraintStatus.REDUCED
            detail = f"Reduced from ${requested:,.2f} to ${actual:,.2f} due to §415(c) limit"
        else:
            status = ConstraintStatus.UNCONSTRAINED
            detail = "Received full mega-backdoor amount"

        # Calculate ACP
        acp_contributions = match + after_tax + actual
        individual_acp = (acp_contributions / compensation * 100) if compensation > 0 else None

        return EmployeeImpact(
            employee_id=participant.internal_id,
            is_hce=participant.is_hce,
            compensation=compensation,
            deferral_amount=deferral,
            match_amount=match,
            after_tax_amount=after_tax,
            section_415c_limit=limit_415c,
            available_room=available - actual,
            mega_backdoor_amount=actual,
            requested_mega_backdoor=requested,
            individual_acp=individual_acp,
            constraint_status=status,
            constraint_detail=detail
        )

    def _compute_summary(self, impacts, group):
        # Implementation details...
        pass
```

### 3. Add API Endpoint

Add to `src/api/routes/analysis.py`:

```python
@router.post("/v2/scenario/{census_id}/employee-impact")
async def get_employee_impact(
    census_id: str,
    request: EmployeeImpactRequest
) -> EmployeeImpactView:
    conn = get_db()
    service = EmployeeImpactService(
        ParticipantRepository(conn),
        CensusRepository(conn)
    )
    return service.compute_impact(
        census_id=census_id,
        adoption_rate=request.adoption_rate,
        contribution_rate=request.contribution_rate,
        seed=request.seed
    )
```

### 4. Create UI Components

Create `src/ui/components/employee_impact_table.py`:

```python
import streamlit as st
import pandas as pd

def render_employee_impact_view(impact_view):
    # Tab navigation
    tab_hce, tab_nhce = st.tabs(["HCEs", "NHCEs"])

    with tab_hce:
        render_summary(impact_view.hce_summary)
        render_filter_controls("hce")
        render_employee_table(impact_view.hce_employees, "hce")

    with tab_nhce:
        render_summary(impact_view.nhce_summary)
        render_filter_controls("nhce")
        render_employee_table(impact_view.nhce_employees, "nhce")

def render_employee_table(employees, group_key):
    df = pd.DataFrame([e.model_dump() for e in employees])

    # Apply filters from session state
    filtered_df = apply_filters(df, group_key)

    # Display count
    st.caption(f"Showing {len(filtered_df)} of {len(df)} employees")

    # Display sortable dataframe
    st.dataframe(filtered_df, use_container_width=True)

    # Export button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Export to CSV",
        data=csv,
        file_name=f"{group_key}_details.csv",
        mime="text/csv"
    )
```

### 5. Integrate with Heatmap Detail Panel

Modify `src/ui/components/heatmap_detail.py`:

```python
def render_detail_panel(scenario):
    # ... existing code ...

    # Add View Employee Details button
    st.divider()
    if st.button("View Employee Details", use_container_width=True):
        st.session_state.selected_scenario = scenario
        st.session_state.show_employee_impact = True
        st.rerun()
```

## Testing

Run tests:

```bash
pytest tests/unit/core/test_employee_impact.py -v
pytest tests/integration/api/test_employee_impact_api.py -v
```

## Usage Example

1. Navigate to heatmap view
2. Click on any scenario cell
3. In the detail panel, click "View Employee Details"
4. Use tabs to switch between HCE and NHCE views
5. Apply filters to focus on specific employees
6. Export data using the "Export to CSV" button

## Performance Notes

- For censuses up to 10,000 participants, expect <2 second load times
- Sorting and filtering operate on in-memory DataFrame
- Consider pagination for very large displays (>1000 visible rows)
