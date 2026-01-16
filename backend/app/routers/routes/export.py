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
from app.services.constants import RATE_LIMIT
from app.services.export import format_csv_export, generate_pdf_report
from app.storage.database import get_db
from app.storage.repository import (
    AnalysisResultRepository,
    CensusRepository,
    GridAnalysisRepository,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


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

    # Generate CSV
    csv_content = format_csv_export(census_dict, results_dicts, seed)

    # Generate filename
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"acp_results_{date_str}.csv"

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

    # Get grid summary if applicable
    grid_summary = None
    if grid_id:
        grid_repo = GridAnalysisRepository(conn)
        grid = grid_repo.get(grid_id)
        if grid:
            pass_count = sum(1 for r in results if r.result == "PASS")
            grid_summary = {
                "total_scenarios": len(results),
                "pass_count": pass_count,
                "fail_count": len(results) - pass_count,
                "pass_rate": pass_count / len(results) * 100 if results else 0,
            }

    # Generate PDF
    pdf_content = generate_pdf_report(census_dict, results_dicts, grid_summary)

    # Generate filename
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"acp_report_{date_str}.pdf"

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )
