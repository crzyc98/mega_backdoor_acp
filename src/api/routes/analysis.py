"""
Analysis API Routes.

Handles single scenario analysis, grid analysis, and results retrieval.
"""

import time
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.api.schemas import (
    AnalysisResult,
    AnalysisResultListResponse,
    Error,
    GridAnalysisResult,
    GridScenarioRequest,
    GridSummary,
    SingleScenarioRequest,
)
from src.core.constants import RATE_LIMIT, SYSTEM_VERSION
from src.core.scenario_runner import run_single_scenario, run_grid_scenarios
from src.storage.database import get_db
from src.storage.models import AnalysisResult as AnalysisResultModel
from src.storage.models import GridAnalysis as GridAnalysisModel
from src.storage.repository import (
    AnalysisResultRepository,
    CensusRepository,
    GridAnalysisRepository,
    ParticipantRepository,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/census/{census_id}/analysis",
    response_model=AnalysisResult,
    summary="Run single scenario analysis",
    description=(
        "Run a single ACP test scenario for the specified census. "
        "Returns PASS/FAIL result with margin and detailed breakdown."
    ),
    responses={
        400: {"model": Error, "description": "Invalid parameters"},
        404: {"model": Error, "description": "Census not found"},
        429: {"model": Error, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(RATE_LIMIT)
async def run_analysis(
    request: Request,
    census_id: str,
    scenario: SingleScenarioRequest,
) -> AnalysisResult:
    """T041: Run single scenario analysis endpoint."""
    conn = get_db()

    # Verify census exists
    census_repo = CensusRepository(conn)
    census = census_repo.get(census_id)
    if census is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {census_id} not found",
        )

    # Get participants for calculation
    participant_repo = ParticipantRepository(conn)
    participants = participant_repo.get_as_calculation_dicts(census_id)

    # Generate seed if not provided
    seed = scenario.seed if scenario.seed is not None else int(time.time() * 1000) % (2**31)

    # Convert adoption rate from percentage to fraction
    adoption_rate_fraction = scenario.adoption_rate / 100.0

    # Run the scenario
    result = run_single_scenario(
        participants=participants,
        adoption_rate=adoption_rate_fraction,
        contribution_rate=scenario.contribution_rate,
        seed=seed,
    )

    # Create result model
    result_model = AnalysisResultModel(
        id=str(uuid.uuid4()),
        census_id=census_id,
        grid_analysis_id=None,
        adoption_rate=scenario.adoption_rate,  # Store as percentage
        contribution_rate=scenario.contribution_rate,
        seed=seed,
        nhce_acp=round(result.nhce_acp, 3),
        hce_acp=round(result.hce_acp, 3),
        threshold=round(result.threshold, 3),
        margin=round(result.margin, 3),
        result=result.result,
        limiting_test=result.limiting_test,
        run_timestamp=datetime.utcnow(),
        version=SYSTEM_VERSION,
    )

    # Save to database
    result_repo = AnalysisResultRepository(conn)
    result_repo.save(result_model)

    return AnalysisResult(
        id=result_model.id,
        census_id=result_model.census_id,
        grid_analysis_id=result_model.grid_analysis_id,
        adoption_rate=result_model.adoption_rate,
        contribution_rate=result_model.contribution_rate,
        seed=result_model.seed,
        nhce_acp=result_model.nhce_acp,
        hce_acp=result_model.hce_acp,
        threshold=result_model.threshold,
        margin=result_model.margin,
        result=result_model.result,
        limiting_test=result_model.limiting_test,
        run_timestamp=result_model.run_timestamp,
        version=result_model.version,
    )


@router.post(
    "/census/{census_id}/grid",
    response_model=GridAnalysisResult,
    summary="Run grid scenario analysis",
    description=(
        "Run multiple ACP test scenarios across a grid of adoption rates "
        "and contribution rates. Returns heatmap-ready results."
    ),
    responses={
        400: {"model": Error, "description": "Invalid parameters"},
        404: {"model": Error, "description": "Census not found"},
        429: {"model": Error, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(RATE_LIMIT)
async def run_grid_analysis(
    request: Request,
    census_id: str,
    grid_request: GridScenarioRequest,
) -> GridAnalysisResult:
    """T058 (Phase 4): Run grid scenario analysis endpoint."""
    conn = get_db()

    # Verify census exists
    census_repo = CensusRepository(conn)
    census = census_repo.get(census_id)
    if census is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {census_id} not found",
        )

    # Get participants for calculation
    participant_repo = ParticipantRepository(conn)
    participants = participant_repo.get_as_calculation_dicts(census_id)

    # Generate seed if not provided
    seed = grid_request.seed if grid_request.seed is not None else int(time.time() * 1000) % (2**31)

    # Create grid analysis record
    grid_id = str(uuid.uuid4())
    grid_model = GridAnalysisModel(
        id=grid_id,
        census_id=census_id,
        name=grid_request.name,
        created_timestamp=datetime.utcnow(),
        seed=seed,
        adoption_rates=grid_request.adoption_rates,
        contribution_rates=grid_request.contribution_rates,
        version=SYSTEM_VERSION,
    )

    # Save grid analysis
    grid_repo = GridAnalysisRepository(conn)
    grid_repo.save(grid_model)

    # Convert adoption rates to fractions for calculation
    adoption_fractions = [r / 100.0 for r in grid_request.adoption_rates]

    # Run all scenarios
    scenario_results = run_grid_scenarios(
        participants=participants,
        adoption_rates=adoption_fractions,
        contribution_rates=grid_request.contribution_rates,
        seed=seed,
    )

    # Save individual results
    result_repo = AnalysisResultRepository(conn)
    api_results = []

    for i, scenario_result in enumerate(scenario_results):
        # Convert adoption rate back to percentage for storage
        adoption_pct = scenario_result.adoption_rate * 100

        result_model = AnalysisResultModel(
            id=str(uuid.uuid4()),
            census_id=census_id,
            grid_analysis_id=grid_id,
            adoption_rate=adoption_pct,
            contribution_rate=scenario_result.contribution_rate,
            seed=scenario_result.seed,
            nhce_acp=round(scenario_result.nhce_acp, 3),
            hce_acp=round(scenario_result.hce_acp, 3),
            threshold=round(scenario_result.threshold, 3),
            margin=round(scenario_result.margin, 3),
            result=scenario_result.result,
            limiting_test=scenario_result.limiting_test,
            run_timestamp=datetime.utcnow(),
            version=SYSTEM_VERSION,
        )
        result_repo.save(result_model)

        api_results.append(AnalysisResult(
            id=result_model.id,
            census_id=result_model.census_id,
            grid_analysis_id=result_model.grid_analysis_id,
            adoption_rate=result_model.adoption_rate,
            contribution_rate=result_model.contribution_rate,
            seed=result_model.seed,
            nhce_acp=result_model.nhce_acp,
            hce_acp=result_model.hce_acp,
            threshold=result_model.threshold,
            margin=result_model.margin,
            result=result_model.result,
            limiting_test=result_model.limiting_test,
            run_timestamp=result_model.run_timestamp,
            version=result_model.version,
        ))

    # Calculate summary
    pass_count = sum(1 for r in api_results if r.result == "PASS")
    fail_count = len(api_results) - pass_count
    pass_rate = pass_count / len(api_results) * 100 if api_results else 0

    return GridAnalysisResult(
        id=grid_id,
        census_id=census_id,
        name=grid_request.name,
        adoption_rates=grid_request.adoption_rates,
        contribution_rates=grid_request.contribution_rates,
        seed=seed,
        results=api_results,
        summary=GridSummary(
            total_scenarios=len(api_results),
            pass_count=pass_count,
            fail_count=fail_count,
            pass_rate=pass_rate,
        ),
        created_timestamp=grid_model.created_timestamp,
        version=SYSTEM_VERSION,
    )


@router.get(
    "/census/{census_id}/results",
    response_model=AnalysisResultListResponse,
    summary="List analysis results",
    description="Retrieve all analysis results for a census",
)
@limiter.limit(RATE_LIMIT)
async def list_results(
    request: Request,
    census_id: str,
    grid_id: str | None = None,
) -> AnalysisResultListResponse:
    """T042: List analysis results endpoint."""
    conn = get_db()

    # Verify census exists
    census_repo = CensusRepository(conn)
    if census_repo.get(census_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {census_id} not found",
        )

    # Get results
    result_repo = AnalysisResultRepository(conn)
    results, total = result_repo.list_by_census(census_id, grid_id=grid_id)

    return AnalysisResultListResponse(
        items=[
            AnalysisResult(
                id=r.id,
                census_id=r.census_id,
                grid_analysis_id=r.grid_analysis_id,
                adoption_rate=r.adoption_rate,
                contribution_rate=r.contribution_rate,
                seed=r.seed,
                nhce_acp=r.nhce_acp,
                hce_acp=r.hce_acp,
                threshold=r.threshold,
                margin=r.margin,
                result=r.result,
                limiting_test=r.limiting_test,
                run_timestamp=r.run_timestamp,
                version=r.version,
            )
            for r in results
        ],
        total=total,
    )
