"""Workspace API endpoints."""

from __future__ import annotations

import io
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID, uuid4

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.models.census import CensusSummary
from app.models.errors import Error
from app.models.workspace import (
    Workspace,
    WorkspaceCreate,
    WorkspaceDetail,
    WorkspaceListResponse,
    WorkspaceUpdate,
)
from app.models.analysis import GridResult, GridSummary, ScenarioResult as ScenarioResultSchema
from app.models.run import Run, RunCreate, RunListResponse, RunStatus
from app.services.census_parser import CensusValidationError, process_census
from app.services.scenario_runner import run_grid_scenarios_v2
from app.services.models import ScenarioResult as ScenarioResultModel, ScenarioStatus
from app.storage.workspace_storage import get_workspace_storage

router = APIRouter(prefix="/api/workspaces", tags=["Workspaces"])


@router.get("", response_model=WorkspaceListResponse)
def list_workspaces() -> WorkspaceListResponse:
    """List all workspaces sorted by updated_at descending."""
    storage = get_workspace_storage()
    workspaces = storage.list_workspaces()
    return WorkspaceListResponse(items=workspaces, total=len(workspaces))


@router.post("", response_model=Workspace, status_code=status.HTTP_201_CREATED)
def create_workspace(data: WorkspaceCreate) -> Workspace:
    """Create a new workspace."""
    storage = get_workspace_storage()
    return storage.create_workspace(data)


@router.get("/{workspace_id}", response_model=WorkspaceDetail)
def get_workspace(workspace_id: UUID) -> WorkspaceDetail:
    """Get workspace details."""
    storage = get_workspace_storage()
    workspace = storage.get_workspace_detail(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Workspace {workspace_id} not found"},
        )
    return workspace


@router.put("/{workspace_id}", response_model=Workspace)
def update_workspace(workspace_id: UUID, data: WorkspaceUpdate) -> Workspace:
    """Update workspace metadata."""
    storage = get_workspace_storage()
    workspace = storage.update_workspace(workspace_id, data)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Workspace {workspace_id} not found"},
        )
    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(workspace_id: UUID) -> None:
    """Delete workspace and all its data."""
    storage = get_workspace_storage()
    deleted = storage.delete_workspace(workspace_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Workspace {workspace_id} not found"},
        )


# --- Census Endpoints ---


@router.post(
    "/{workspace_id}/census",
    response_model=CensusSummary,
    status_code=status.HTTP_201_CREATED,
)
async def upload_census(
    workspace_id: UUID,
    file: UploadFile = File(...),
    plan_year: int = Form(...),
    hce_mode: Literal["explicit", "compensation_threshold"] = Form("explicit"),
) -> CensusSummary:
    """Upload census CSV to workspace."""
    storage = get_workspace_storage()

    # Verify workspace exists
    workspace = storage.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Workspace {workspace_id} not found"},
        )

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_file", "message": "File must be a CSV"},
        )

    try:
        # Read file content
        content = await file.read()
        csv_text = content.decode("utf-8")

        # Process census
        df, census_salt, column_mapping = process_census(
            io.StringIO(csv_text),
            hce_mode=hce_mode,
            plan_year=plan_year,
        )

        # Save census data
        storage.save_census_data(workspace_id, csv_text)

        # Calculate statistics
        hce_count = int(df["is_hce"].sum())
        nhce_count = len(df) - hce_count
        avg_compensation = float(df["compensation"].mean()) if len(df) > 0 else 0.0

        # Create and save summary
        summary = CensusSummary(
            id=str(uuid4()),
            plan_year=plan_year,
            participant_count=len(df),
            hce_count=hce_count,
            nhce_count=nhce_count,
            avg_compensation=avg_compensation,
            upload_timestamp=datetime.utcnow(),
        )
        storage.save_census_summary(workspace_id, summary)

        return summary

    except CensusValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": str(e)},
        )
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_encoding", "message": "File must be UTF-8 encoded"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "processing_error", "message": f"Failed to process census: {str(e)}"},
        )


@router.get("/{workspace_id}/census", response_model=CensusSummary)
def get_census(workspace_id: UUID) -> CensusSummary:
    """Get census summary for workspace."""
    storage = get_workspace_storage()

    # Verify workspace exists
    workspace = storage.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Workspace {workspace_id} not found"},
        )

    summary = storage.get_census_summary(workspace_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "no_census", "message": "No census data uploaded for this workspace"},
        )

    return summary


# --- Run Endpoints ---


@router.get("/{workspace_id}/runs", response_model=RunListResponse)
def list_runs(workspace_id: UUID) -> RunListResponse:
    """List all analysis runs for workspace."""
    storage = get_workspace_storage()

    # Verify workspace exists
    workspace = storage.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Workspace {workspace_id} not found"},
        )

    runs = storage.list_runs(workspace_id)
    return RunListResponse(items=runs, total=len(runs))


@router.post(
    "/{workspace_id}/runs",
    response_model=Run,
    status_code=status.HTTP_201_CREATED,
)
def create_run(workspace_id: UUID, data: RunCreate) -> Run:
    """Execute a new grid analysis run."""
    import random

    storage = get_workspace_storage()

    # Verify workspace exists
    workspace = storage.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Workspace {workspace_id} not found"},
        )

    # Check census exists
    census_path = storage.get_census_data_path(workspace_id)
    if not census_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "no_census", "message": "No census data uploaded. Please upload census first."},
        )

    # Validate rate arrays
    if len(data.adoption_rates) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_rates", "message": "At least 2 adoption rates required"},
        )
    if len(data.contribution_rates) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_rates", "message": "At least 2 contribution rates required"},
        )

    # Generate seed if not provided
    seed = data.seed if data.seed else random.randint(1, 999999)

    # Create run record
    run = Run(
        id=uuid4(),
        workspace_id=workspace_id,
        name=data.name,
        adoption_rates=data.adoption_rates,
        contribution_rates=data.contribution_rates,
        seed=seed,
        status=RunStatus.RUNNING,
    )
    storage.create_run(workspace_id, run)

    try:
        # Load census data
        census_df = pd.read_csv(census_path)

        # Convert to list of participant dicts
        participants = census_df.to_dict("records")

        # Convert rates from percentages to fractions (e.g., 20% -> 0.20)
        adoption_fractions = [r / 100.0 for r in data.adoption_rates]
        contribution_fractions = [r / 100.0 for r in data.contribution_rates]

        # Run grid analysis
        grid_result = run_grid_scenarios_v2(
            participants=participants,
            adoption_rates=adoption_fractions,
            contribution_rates=contribution_fractions,
            seed=seed,
        )

        # Convert to storage format
        results_dict = {
            "scenarios": [
                {
                    "status": s.status.value,
                    "nhce_acp": float(s.nhce_acp) if s.nhce_acp is not None else None,
                    "hce_acp": float(s.hce_acp) if s.hce_acp is not None else None,
                    "limit_125": float(s.limit_125) if s.limit_125 is not None else None,
                    "limit_2pct_uncapped": float(s.limit_2pct_uncapped) if s.limit_2pct_uncapped is not None else None,
                    "cap_2x": float(s.cap_2x) if s.cap_2x is not None else None,
                    "limit_2pct_capped": float(s.limit_2pct_capped) if s.limit_2pct_capped is not None else None,
                    "effective_limit": float(s.effective_limit) if s.effective_limit is not None else None,
                    "max_allowed_acp": float(s.max_allowed_acp) if s.max_allowed_acp is not None else None,
                    "margin": float(s.margin) if s.margin is not None else None,
                    "binding_rule": s.binding_rule if s.binding_rule else None,
                    "adoption_rate": s.adoption_rate,
                    "contribution_rate": s.contribution_rate,
                    "seed_used": s.seed_used,
                }
                for s in grid_result.scenarios
            ],
            "summary": {
                "pass_count": grid_result.summary.pass_count,
                "risk_count": grid_result.summary.risk_count,
                "fail_count": grid_result.summary.fail_count,
                "error_count": grid_result.summary.error_count,
                "total_count": grid_result.summary.total_count,
            },
            "seed_used": grid_result.seed_used,
        }

        # Save results
        storage.save_run_results(workspace_id, run.id, results_dict)

        # Update run status
        run.status = RunStatus.COMPLETED
        run.completed_at = datetime.utcnow()
        storage.update_run(workspace_id, run)

    except Exception as e:
        # Mark run as failed
        run.status = RunStatus.FAILED
        run.completed_at = datetime.utcnow()
        storage.update_run(workspace_id, run)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "analysis_error", "message": f"Analysis failed: {str(e)}"},
        )

    return run


@router.get("/{workspace_id}/runs/{run_id}")
def get_run(workspace_id: UUID, run_id: UUID):
    """Get run details with results."""
    storage = get_workspace_storage()

    # Verify workspace exists
    workspace = storage.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Workspace {workspace_id} not found"},
        )

    run = storage.get_run(workspace_id, run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Run {run_id} not found"},
        )

    # Get results
    results = storage.get_run_results(workspace_id, run_id)

    # Return combined response
    return {
        "id": str(run.id),
        "workspace_id": str(run.workspace_id),
        "name": run.name,
        "adoption_rates": run.adoption_rates,
        "contribution_rates": run.contribution_rates,
        "seed": run.seed,
        "status": run.status.value,
        "created_at": run.created_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "results": results,
    }


@router.delete("/{workspace_id}/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(workspace_id: UUID, run_id: UUID) -> None:
    """Delete a run and its results."""
    storage = get_workspace_storage()

    # Verify workspace exists
    workspace = storage.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Workspace {workspace_id} not found"},
        )

    deleted = storage.delete_run(workspace_id, run_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Run {run_id} not found"},
        )


# --- Employee Impact Endpoints ---


from app.services.models import ConstraintStatus as ConstraintStatusEnum


@router.get("/{workspace_id}/runs/{run_id}/employees")
def get_employee_impact(
    workspace_id: UUID,
    run_id: UUID,
    adoption_rate: float,
    contribution_rate: float,
):
    """
    Get employee-level impact details for a specific scenario.

    Computes per-employee contribution breakdowns and constraint analysis
    based on the specified adoption and contribution rates.
    """
    import random
    from app.services.constants import get_415c_limit

    storage = get_workspace_storage()

    # Verify workspace exists
    workspace = storage.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Workspace {workspace_id} not found"},
        )

    # Get run
    run = storage.get_run(workspace_id, run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Run {run_id} not found"},
        )

    results = storage.get_run_results(workspace_id, run_id)
    scenario_summary = None
    if results:
        # Convert query params from percentages to fractions to match stored scenario format
        # Run metadata stores rates as percentages (e.g., 25.0 for 25%)
        # but scenario results store them as fractions (e.g., 0.25)
        adoption_rate_frac = adoption_rate / 100.0
        contribution_rate_frac = contribution_rate / 100.0
        for scenario in results.get("scenarios", []):
            if (
                abs(scenario.get("adoption_rate", 0) - adoption_rate_frac) < 1e-9
                and abs(scenario.get("contribution_rate", 0) - contribution_rate_frac) < 1e-9
            ):
                scenario_summary = scenario
                break

    # Validate rates are in run's rate arrays
    if adoption_rate not in run.adoption_rates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_rate", "message": f"Adoption rate {adoption_rate} not in run's rate array"},
        )
    if contribution_rate not in run.contribution_rates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_rate", "message": f"Contribution rate {contribution_rate} not in run's rate array"},
        )

    # Load census data
    census_path = storage.get_census_data_path(workspace_id)
    if not census_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "no_census", "message": "No census data found"},
        )

    # Get census summary for plan year
    census_summary = storage.get_census_summary(workspace_id)
    if not census_summary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "no_census", "message": "No census summary found"},
        )

    plan_year = census_summary.plan_year
    limit_415c = get_415c_limit(plan_year)

    # Load participants
    census_df = pd.read_csv(census_path)
    participants = census_df.to_dict("records")

    # Separate HCEs and NHCEs
    hces = [p for p in participants if p.get("is_hce", False)]
    nhces = [p for p in participants if not p.get("is_hce", False)]

    # Select HCEs for mega-backdoor (using same logic as scenario runner)
    seed = run.seed
    hce_ids = [p["internal_id"] for p in hces]

    # Deterministic selection matching scenario_runner.select_adopting_hces
    import numpy as np
    selected_hce_ids = set()
    if hce_ids and adoption_rate > 0:
        if adoption_rate >= 1.0:
            selected_hce_ids = set(hce_ids)
        else:
            rng = np.random.default_rng(seed)
            n_adopters = round(len(hce_ids) * adoption_rate)
            if n_adopters > 0:
                selected = rng.choice(hce_ids, size=n_adopters, replace=False)
                selected_hce_ids = set(selected)

    def compute_employee_impact(p, is_selected):
        """Compute impact for a single employee."""
        compensation = p.get("compensation_cents", 0) / 100
        deferral_rate = p.get("deferral_rate", 0)
        match_rate = p.get("match_rate", 0)
        after_tax_rate = p.get("after_tax_rate", 0)

        # Calculate contribution amounts
        deferral = compensation * deferral_rate / 100
        match = compensation * match_rate / 100
        after_tax = compensation * after_tax_rate / 100

        # Calculate mega-backdoor amounts
        is_hce = p.get("is_hce", False)
        if is_selected and is_hce:
            requested = compensation * contribution_rate
        else:
            requested = 0.0

        # Calculate available room before mega-backdoor
        existing_total = deferral + match + after_tax
        available_before = limit_415c - existing_total

        # Calculate actual mega-backdoor (capped by available room)
        if is_selected:
            actual = min(requested, max(0, available_before))
        else:
            actual = 0.0

        # Calculate available room after mega-backdoor
        available_after = available_before - actual

        # Determine constraint status
        if not is_selected or not is_hce:
            status = "Not Selected"
            detail = "Not selected for mega-backdoor participation"
        elif actual == 0 and requested > 0:
            status = "At §415(c) Limit"
            detail = f"§415(c) limit of ${limit_415c:,} reached with existing contributions"
        elif actual < requested:
            status = "Reduced"
            detail = f"Reduced from ${requested:,.2f} to ${actual:,.2f} due to §415(c) limit"
        else:
            status = "Unconstrained"
            detail = "Received full mega-backdoor amount"

        # Calculate individual ACP
        acp_contributions = match + after_tax + actual
        individual_acp = (acp_contributions / compensation * 100) if compensation > 0 else None

        return {
            "employee_id": p.get("internal_id", ""),
            "is_hce": is_hce,
            "compensation": compensation,
            "deferral_amount": deferral,
            "match_amount": match,
            "after_tax_amount": after_tax,
            "section_415c_limit": limit_415c,
            "available_room": available_after,
            "mega_backdoor_amount": actual,
            "requested_mega_backdoor": requested,
            "individual_acp": individual_acp,
            "constraint_status": status,
            "constraint_detail": detail,
        }

    # Compute impacts for all employees
    hce_impacts = [
        compute_employee_impact(p, p.get("internal_id") in selected_hce_ids)
        for p in hces
    ]
    nhce_impacts = [
        compute_employee_impact(p, False)
        for p in nhces
    ]

    def compute_summary(impacts, group):
        """Compute summary statistics for a group."""
        total_count = len(impacts)
        if total_count == 0:
            return {
                "group": group,
                "total_count": 0,
                "at_limit_count": 0 if group == "HCE" else None,
                "reduced_count": 0 if group == "HCE" else None,
                "average_available_room": 0.0 if group == "HCE" else None,
                "total_mega_backdoor": 0.0 if group == "HCE" else None,
                "average_individual_acp": 0.0,
                "total_match": 0.0,
                "total_after_tax": 0.0,
            }

        total_match = sum(e["match_amount"] for e in impacts)
        total_after_tax = sum(e["after_tax_amount"] for e in impacts)

        valid_acps = [e["individual_acp"] for e in impacts if e["individual_acp"] is not None]
        avg_acp = sum(valid_acps) / len(valid_acps) if valid_acps else 0.0

        if group == "HCE":
            at_limit_count = sum(1 for e in impacts if e["constraint_status"] == "At §415(c) Limit")
            reduced_count = sum(1 for e in impacts if e["constraint_status"] == "Reduced")
            total_mega_backdoor = sum(e["mega_backdoor_amount"] for e in impacts)
            avg_available_room = sum(e["available_room"] for e in impacts) / total_count

            return {
                "group": "HCE",
                "total_count": total_count,
                "at_limit_count": at_limit_count,
                "reduced_count": reduced_count,
                "average_available_room": avg_available_room,
                "total_mega_backdoor": total_mega_backdoor,
                "average_individual_acp": avg_acp,
                "total_match": total_match,
                "total_after_tax": total_after_tax,
            }
        else:
            return {
                "group": "NHCE",
                "total_count": total_count,
                "at_limit_count": None,
                "reduced_count": None,
                "average_available_room": None,
                "total_mega_backdoor": None,
                "average_individual_acp": avg_acp,
                "total_match": total_match,
                "total_after_tax": total_after_tax,
            }

    hce_summary = compute_summary(hce_impacts, "HCE")
    nhce_summary = compute_summary(nhce_impacts, "NHCE")

    return {
        "census_id": census_summary.id,
        "adoption_rate": adoption_rate,
        "contribution_rate": contribution_rate,
        "seed_used": seed,
        "plan_year": plan_year,
        "section_415c_limit": limit_415c,
        "scenario": scenario_summary,
        "hce_employees": hce_impacts,
        "nhce_employees": nhce_impacts,
        "hce_summary": hce_summary,
        "nhce_summary": nhce_summary,
    }


# --- Export Endpoints ---


from fastapi.responses import StreamingResponse


@router.get("/{workspace_id}/runs/{run_id}/export/csv")
def export_csv(workspace_id: UUID, run_id: UUID):
    """Export run results as CSV."""
    storage = get_workspace_storage()
    from decimal import Decimal
    from app.services.acp_calculator import calculate_acp_limits

    # Verify workspace exists
    workspace = storage.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Workspace {workspace_id} not found"},
        )

    run = storage.get_run(workspace_id, run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Run {run_id} not found"},
        )

    results = storage.get_run_results(workspace_id, run_id)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "no_results", "message": "Run has no results"},
        )

    # Get census summary for metadata
    census_summary = storage.get_census_summary(workspace_id)

    # Build CSV content
    lines = []
    lines.append("# ACP Sensitivity Analysis Export")
    lines.append(f"# Workspace: {workspace.name}")
    lines.append(f"# Run Seed: {run.seed}")
    if census_summary:
        lines.append(f"# Plan Year: {census_summary.plan_year}")
        lines.append(f"# Participants: {census_summary.participant_count} (HCE: {census_summary.hce_count}, NHCE: {census_summary.nhce_count})")
    lines.append(f"# Generated: {datetime.utcnow().isoformat()}Z")
    lines.append("#")

    # CSV header
    lines.append(
        "adoption_rate,contribution_rate,status,nhce_acp,hce_acp,"
        "limit_125,limit_2pct_uncapped,cap_2x,limit_2pct_capped,effective_limit,"
        "binding_rule,max_allowed_acp,margin"
    )

    # Data rows
    for scenario in results.get("scenarios", []):
        nhce_acp = scenario.get("nhce_acp")
        if nhce_acp is not None and scenario.get("effective_limit") is None:
            limits = calculate_acp_limits(Decimal(str(nhce_acp)))
            scenario.setdefault("limit_125", float(limits["limit_125"]))
            scenario.setdefault("limit_2pct_uncapped", float(limits["limit_2pct_uncapped"]))
            scenario.setdefault("cap_2x", float(limits["cap_2x"]))
            scenario.setdefault("limit_2pct_capped", float(limits["limit_2pct_capped"]))
            scenario.setdefault("effective_limit", float(limits["effective_limit"]))
            scenario.setdefault(
                "binding_rule",
                "1.25x" if limits["limit_125"] >= limits["limit_2pct_capped"] else "2pct/2x",
            )
            scenario.setdefault("max_allowed_acp", scenario.get("effective_limit"))

        row = [
            f"{scenario['adoption_rate']:.4f}",
            f"{scenario['contribution_rate']:.4f}",
            scenario.get("status", ""),
            f"{scenario.get('nhce_acp', 0):.2f}" if scenario.get("nhce_acp") is not None else "",
            f"{scenario.get('hce_acp', 0):.2f}" if scenario.get("hce_acp") is not None else "",
            f"{scenario.get('limit_125', 0):.2f}" if scenario.get("limit_125") is not None else "",
            f"{scenario.get('limit_2pct_uncapped', 0):.2f}" if scenario.get("limit_2pct_uncapped") is not None else "",
            f"{scenario.get('cap_2x', 0):.2f}" if scenario.get("cap_2x") is not None else "",
            f"{scenario.get('limit_2pct_capped', 0):.2f}" if scenario.get("limit_2pct_capped") is not None else "",
            f"{scenario.get('effective_limit', 0):.2f}" if scenario.get("effective_limit") is not None else "",
            scenario.get("binding_rule", ""),
            f"{scenario.get('max_allowed_acp', 0):.2f}" if scenario.get("max_allowed_acp") is not None else "",
            f"{scenario.get('margin', 0):.2f}" if scenario.get("margin") is not None else "",
        ]
        lines.append(",".join(row))

    csv_content = "\n".join(lines)

    filename = f"acp_analysis_{run.seed}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{workspace_id}/runs/{run_id}/export/pdf")
def export_pdf(workspace_id: UUID, run_id: UUID):
    """Export run results as PDF report."""
    storage = get_workspace_storage()
    from decimal import Decimal
    from app.services.acp_calculator import calculate_acp_limits

    # Verify workspace exists
    workspace = storage.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Workspace {workspace_id} not found"},
        )

    run = storage.get_run(workspace_id, run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Run {run_id} not found"},
        )

    results = storage.get_run_results(workspace_id, run_id)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "no_results", "message": "Run has no results"},
        )

    # Get census summary for metadata
    census_summary = storage.get_census_summary(workspace_id)

    # Build census dict for export function
    census_dict = {
        "id": census_summary.id if census_summary else str(workspace_id),
        "name": workspace.name,
        "plan_year": census_summary.plan_year if census_summary else 2025,
        "participant_count": census_summary.participant_count if census_summary else 0,
        "hce_count": census_summary.hce_count if census_summary else 0,
        "nhce_count": census_summary.nhce_count if census_summary else 0,
    }

    # Convert scenarios to format expected by export function
    export_results = []
    for s in results.get("scenarios", []):
        nhce_acp = s.get("nhce_acp")
        limits = None
        if nhce_acp is not None:
            limits = calculate_acp_limits(Decimal(str(nhce_acp)))
        limit_125 = float(limits["limit_125"]) if limits else 0
        limit_2pct_uncapped = float(limits["limit_2pct_uncapped"]) if limits else 0
        cap_2x = float(limits["cap_2x"]) if limits else 0
        limit_2pct_capped = float(limits["limit_2pct_capped"]) if limits else 0
        effective_limit = float(limits["effective_limit"]) if limits else 0
        export_results.append({
            "adoption_rate": s.get("adoption_rate", 0) * 100,  # Convert to percentage
            "contribution_rate": s.get("contribution_rate", 0) * 100,  # Convert to percentage
            "nhce_acp": s.get("nhce_acp", 0) or 0,
            "hce_acp": s.get("hce_acp", 0) or 0,
            "limit_125": s.get("limit_125", limit_125) or limit_125,
            "limit_2pct_uncapped": s.get("limit_2pct_uncapped", limit_2pct_uncapped) or limit_2pct_uncapped,
            "cap_2x": s.get("cap_2x", cap_2x) or cap_2x,
            "limit_2pct_capped": s.get("limit_2pct_capped", limit_2pct_capped) or limit_2pct_capped,
            "effective_limit": s.get("effective_limit", effective_limit) or effective_limit,
            "binding_rule": s.get(
                "binding_rule",
                "1.25x" if limit_125 >= limit_2pct_capped else "2pct/2x",
            ),
            "threshold": s.get("max_allowed_acp", effective_limit) or effective_limit,
            "margin": s.get("margin", 0) or 0,
            "result": "PASS" if s.get("status") in ["PASS", "RISK"] else "FAIL",
            "limiting_test": "1.25x",  # Simplified
        })

    # Grid summary
    summary = results.get("summary", {})
    grid_summary = {
        "total_scenarios": summary.get("total_count", 0),
        "pass_count": summary.get("pass_count", 0) + summary.get("risk_count", 0),
        "fail_count": summary.get("fail_count", 0),
        "pass_rate": (
            (summary.get("pass_count", 0) + summary.get("risk_count", 0)) /
            summary.get("total_count", 1) * 100
        ) if summary.get("total_count", 0) > 0 else 0,
    }

    try:
        from app.services.export import generate_pdf_report
        pdf_bytes = generate_pdf_report(census_dict, export_results, grid_summary)
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={"error": "dependency_missing", "message": str(e)},
        )

    filename = f"acp_report_{run.seed}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
