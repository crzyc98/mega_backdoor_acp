"""
Export API Routes.

Handles CSV and PDF export of analysis results.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.routers.dependencies import get_workspace_id_from_header
from app.routers.schemas import Error
from app.services.acp_eligibility import determine_acp_inclusion, plan_year_bounds
from app.services.constants import RATE_LIMIT
from app.services.export import format_csv_export, generate_pdf_report
from app.storage.database import get_db
from app.storage.models import Participant
from app.storage.repository import (
    AnalysisResultRepository,
    CensusRepository,
    GridAnalysisRepository,
    ParticipantRepository,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def compute_post_exclusion_counts(
    plan_year: int,
    participants: list[Participant],
) -> tuple[int, int, int]:
    """
    Compute post-eligibility filter counts for export.

    Applies ACP eligibility filtering to determine which participants
    are includable vs excluded for the given plan year.

    Args:
        plan_year: The plan year for eligibility determination
        participants: List of Participant objects from the census

    Returns:
        Tuple of (included_hce_count, included_nhce_count, excluded_count)
    """
    plan_year_start, plan_year_end = plan_year_bounds(plan_year)

    included_hce_count = 0
    included_nhce_count = 0
    excluded_count = 0

    for p in participants:
        # Skip eligibility check if missing required dates (fail open)
        if p.dob is None or p.hire_date is None:
            if p.is_hce:
                included_hce_count += 1
            else:
                included_nhce_count += 1
            continue

        try:
            result = determine_acp_inclusion(
                dob=p.dob,
                hire_date=p.hire_date,
                termination_date=p.termination_date,
                plan_year_start=plan_year_start,
                plan_year_end=plan_year_end,
            )
            if result.acp_includable:
                if p.is_hce:
                    included_hce_count += 1
                else:
                    included_nhce_count += 1
            else:
                excluded_count += 1
        except Exception:
            # On any error, include participant (fail open)
            if p.is_hce:
                included_hce_count += 1
            else:
                included_nhce_count += 1

    return included_hce_count, included_nhce_count, excluded_count


@router.get(
    "/export/{census_id}/csv",
    summary="Export results as CSV",
    description=(
        "Export analysis results to CSV format with full audit metadata. "
        "Includes all input parameters, calculation details, and timestamps."
    ),
    responses={
        200: {
            "description": "CSV file",
            "content": {"text/csv": {}},
        },
        404: {"model": Error, "description": "Census or results not found"},
    },
)
@limiter.limit(RATE_LIMIT)
async def export_csv(
    request: Request,
    census_id: str,
    grid_id: str | None = None,
    workspace_id: str = Depends(get_workspace_id_from_header),
) -> Response:
    """T072: Export results as CSV endpoint."""
    conn = get_db(workspace_id)

    # Get census
    census_repo = CensusRepository(conn)
    census = census_repo.get(census_id)
    if census is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {census_id} not found",
        )

    # Get results
    result_repo = AnalysisResultRepository(conn)
    results, total = result_repo.list_by_census(census_id, grid_id=grid_id)

    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis results found for this census",
        )

    # Get seed from grid if applicable
    seed = None
    if grid_id:
        grid_repo = GridAnalysisRepository(conn)
        grid = grid_repo.get(grid_id)
        if grid:
            seed = grid.seed

    # Convert to dicts
    census_dict = {
        "id": census.id,
        "name": census.name,
        "plan_year": census.plan_year,
        "participant_count": census.participant_count,
        "hce_count": census.hce_count,
        "nhce_count": census.nhce_count,
    }
    results_dicts = [
        {
            "adoption_rate": r.adoption_rate,
            "contribution_rate": r.contribution_rate,
            "nhce_acp": r.nhce_acp,
            "hce_acp": r.hce_acp,
            "threshold": r.threshold,
            "margin": r.margin,
            "result": r.result,
            "limiting_test": r.limiting_test,
            "seed": r.seed,
            "run_timestamp": r.run_timestamp.isoformat(),
        }
        for r in results
    ]

    # Compute post-exclusion counts for accurate reporting
    participant_repo = ParticipantRepository(conn)
    participants = participant_repo.get_by_census(census_id)
    included_hce_count, included_nhce_count, excluded_count = compute_post_exclusion_counts(
        census.plan_year, participants
    )

    # Generate CSV with post-exclusion counts
    csv_content = format_csv_export(
        census_dict,
        results_dicts,
        seed,
        included_hce_count=included_hce_count,
        included_nhce_count=included_nhce_count,
        excluded_count=excluded_count,
    )

    # Build descriptive filename: CensusName_PlanYear_Run#_MonthYear.csv
    safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in census.name).strip()
    safe_name = safe_name.replace(" ", "_")
    export_date = datetime.utcnow().strftime("%b%Y")
    seed_part = f"_Run{seed}" if seed else ""
    filename = f"{safe_name}_{census.plan_year}{seed_part}_{export_date}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )


@router.get(
    "/export/{census_id}/pdf",
    summary="Export results as PDF",
    description=(
        "Export analysis results as a formatted PDF report suitable for "
        "compliance documentation."
    ),
    responses={
        200: {
            "description": "PDF file",
            "content": {"application/pdf": {}},
        },
        404: {"model": Error, "description": "Census or results not found"},
    },
)
@limiter.limit(RATE_LIMIT)
async def export_pdf(
    request: Request,
    census_id: str,
    grid_id: str | None = None,
    workspace_id: str = Depends(get_workspace_id_from_header),
) -> Response:
    """T073: Export results as PDF endpoint."""
    conn = get_db(workspace_id)

    # Get census
    census_repo = CensusRepository(conn)
    census = census_repo.get(census_id)
    if census is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {census_id} not found",
        )

    # Get results
    result_repo = AnalysisResultRepository(conn)
    results, total = result_repo.list_by_census(census_id, grid_id=grid_id)

    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis results found for this census",
        )

    # Convert to dicts
    census_dict = {
        "id": census.id,
        "name": census.name,
        "plan_year": census.plan_year,
        "participant_count": census.participant_count,
        "hce_count": census.hce_count,
        "nhce_count": census.nhce_count,
    }
    results_dicts = [
        {
            "adoption_rate": r.adoption_rate,
            "contribution_rate": r.contribution_rate,
            "nhce_acp": r.nhce_acp,
            "hce_acp": r.hce_acp,
            "threshold": r.threshold,
            "margin": r.margin,
            "result": r.result,
            "limiting_test": r.limiting_test,
            "seed": r.seed,
            "run_timestamp": r.run_timestamp.isoformat(),
        }
        for r in results
    ]

    # Get grid summary and seed if applicable
    grid_summary = None
    seed = None
    if grid_id:
        grid_repo = GridAnalysisRepository(conn)
        grid = grid_repo.get(grid_id)
        if grid:
            seed = grid.seed
            pass_count = sum(1 for r in results if r.result == "PASS")
            grid_summary = {
                "total_scenarios": len(results),
                "pass_count": pass_count,
                "fail_count": len(results) - pass_count,
                "pass_rate": pass_count / len(results) * 100 if results else 0,
            }

    # Compute post-exclusion counts for accurate reporting
    participant_repo = ParticipantRepository(conn)
    participants = participant_repo.get_by_census(census_id)
    included_hce_count, included_nhce_count, excluded_count = compute_post_exclusion_counts(
        census.plan_year, participants
    )

    # Generate PDF with post-exclusion counts
    pdf_content = generate_pdf_report(
        census_dict,
        results_dicts,
        grid_summary,
        excluded_count=excluded_count,
        hce_count=included_hce_count,
        nhce_count=included_nhce_count,
    )

    # Build descriptive filename: CensusName_PlanYear_Run#_MonthYear.pdf
    safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in census.name).strip()
    safe_name = safe_name.replace(" ", "_")
    export_date = datetime.utcnow().strftime("%b%Y")
    seed_part = f"_Run{seed}" if seed else ""
    filename = f"{safe_name}_{census.plan_year}{seed_part}_{export_date}.pdf"

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )
