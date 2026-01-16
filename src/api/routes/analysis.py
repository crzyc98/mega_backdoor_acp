"""
Analysis API Routes.

Handles single scenario analysis, grid analysis, results retrieval,
and employee-level impact views.
"""

import io
import time
import uuid
from datetime import datetime
from typing import Annotated

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
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
    # T026-T028: V2 schemas
    ScenarioRequestV2,
    ScenarioResultV2,
    GridRequestV2,
    GridResultV2,
    GridSummaryV2,
    FailurePointResponse,
    DebugDetailsResponse,
    ParticipantContributionResponse,
    IntermediateValuesResponse,
    # T022: Employee impact schemas
    EmployeeImpactRequest,
    EmployeeImpactResponse,
    EmployeeImpactSummaryResponse,
    EmployeeImpactViewResponse,
    EmployeeImpactExportRequest,
)
from src.core.constants import RATE_LIMIT, SYSTEM_VERSION
from src.core.acp_eligibility import ACPInclusionError
from src.core.scenario_runner import run_single_scenario, run_grid_scenarios, run_single_scenario_v2, run_grid_scenarios_v2
from src.core.models import ScenarioStatus
from src.api.dependencies import get_database
from src.storage.models import AnalysisResult as AnalysisResultModel
from src.storage.models import GridAnalysis as GridAnalysisModel
from src.storage.repository import (
    AnalysisResultRepository,
    CensusRepository,
    GridAnalysisRepository,
    ParticipantRepository,
)
from src.core.employee_impact import EmployeeImpactService

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
    conn: Annotated[duckdb.DuckDBPyConnection, Depends(get_database)],
) -> AnalysisResult:
    """T041: Run single scenario analysis endpoint."""

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
    try:
        participants = participant_repo.get_as_calculation_dicts(census_id)
    except ACPInclusionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

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
    conn: Annotated[duckdb.DuckDBPyConnection, Depends(get_database)],
) -> GridAnalysisResult:
    """T058 (Phase 4): Run grid scenario analysis endpoint."""

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
    try:
        participants = participant_repo.get_as_calculation_dicts(census_id)
    except ACPInclusionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

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
    conn: Annotated[duckdb.DuckDBPyConnection, Depends(get_database)],
    grid_id: str | None = None,
) -> AnalysisResultListResponse:
    """T042: List analysis results endpoint."""

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


# ============================================================================
# V2 API Endpoints (Feature 004-scenario-analysis)
# ============================================================================

# T027: V2 single scenario endpoint with PASS/RISK/FAIL/ERROR status
@router.post(
    "/v2/scenario",
    response_model=ScenarioResultV2,
    summary="Run single scenario analysis (v2)",
    description=(
        "Run a single ACP test scenario with enhanced result data. "
        "Returns PASS/RISK/FAIL/ERROR status with full outcome details."
    ),
    responses={
        400: {"model": Error, "description": "Invalid parameters"},
        404: {"model": Error, "description": "Census not found"},
        429: {"model": Error, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(RATE_LIMIT)
async def run_scenario_v2(
    request: Request,
    scenario: ScenarioRequestV2,
    conn: Annotated[duckdb.DuckDBPyConnection, Depends(get_database)],
) -> ScenarioResultV2:
    """T027: Run v2 single scenario analysis endpoint."""

    # T028: Validate census exists
    census_repo = CensusRepository(conn)
    census = census_repo.get(scenario.census_id)
    if census is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {scenario.census_id} not found",
        )

    # Generate seed if not provided
    seed = scenario.seed if scenario.seed is not None else int(time.time() * 1000) % (2**31)

    # Get participants for calculation
    participant_repo = ParticipantRepository(conn)
    try:
        participants = participant_repo.get_as_calculation_dicts(scenario.census_id)
    except ACPInclusionError as exc:
        return ScenarioResultV2(
            status=ScenarioStatus.ERROR,
            seed_used=seed,
            adoption_rate=scenario.adoption_rate,
            contribution_rate=scenario.contribution_rate,
            error_message=str(exc),
        )

    # Run the v2 scenario
    result = run_single_scenario_v2(
        participants=participants,
        adoption_rate=scenario.adoption_rate,
        contribution_rate=scenario.contribution_rate,
        seed=seed,
        include_debug=scenario.include_debug,
    )

    # Convert to API response schema
    debug_response = None
    if result.debug_details:
        debug_response = DebugDetailsResponse(
            selected_hce_ids=result.debug_details.selected_hce_ids,
            hce_contributions=[
                ParticipantContributionResponse(
                    id=c.id,
                    compensation_cents=c.compensation_cents,
                    existing_acp_contributions_cents=c.existing_acp_contributions_cents,
                    simulated_mega_backdoor_cents=c.simulated_mega_backdoor_cents,
                    individual_acp=c.individual_acp,
                )
                for c in result.debug_details.hce_contributions
            ],
            nhce_contributions=[
                ParticipantContributionResponse(
                    id=c.id,
                    compensation_cents=c.compensation_cents,
                    existing_acp_contributions_cents=c.existing_acp_contributions_cents,
                    simulated_mega_backdoor_cents=c.simulated_mega_backdoor_cents,
                    individual_acp=c.individual_acp,
                )
                for c in result.debug_details.nhce_contributions
            ],
            intermediate_values=IntermediateValuesResponse(
                hce_acp_sum=result.debug_details.intermediate_values.hce_acp_sum,
                hce_count=result.debug_details.intermediate_values.hce_count,
                nhce_acp_sum=result.debug_details.intermediate_values.nhce_acp_sum,
                nhce_count=result.debug_details.intermediate_values.nhce_count,
                threshold_multiple=result.debug_details.intermediate_values.threshold_multiple,
                threshold_additive=result.debug_details.intermediate_values.threshold_additive,
            ),
        )

    return ScenarioResultV2(
        status=result.status.value,
        nhce_acp=result.nhce_acp,
        hce_acp=result.hce_acp,
        max_allowed_acp=result.max_allowed_acp,
        margin=result.margin,
        limiting_bound=result.limiting_bound.value if result.limiting_bound else None,
        hce_contributor_count=result.hce_contributor_count,
        nhce_contributor_count=result.nhce_contributor_count,
        total_mega_backdoor_amount=result.total_mega_backdoor_amount,
        seed_used=result.seed_used,
        adoption_rate=result.adoption_rate,
        contribution_rate=result.contribution_rate,
        error_message=result.error_message,
        debug_details=debug_response,
    )


# T035: V2 grid analysis endpoint
@router.post(
    "/v2/grid",
    response_model=GridResultV2,
    summary="Run grid scenario analysis (v2)",
    description=(
        "Run multiple ACP test scenarios across a grid of adoption and contribution rates. "
        "Returns all scenario results with comprehensive summary statistics."
    ),
    responses={
        400: {"model": Error, "description": "Invalid parameters"},
        404: {"model": Error, "description": "Census not found"},
        429: {"model": Error, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(RATE_LIMIT)
async def run_grid_v2(
    request: Request,
    grid_request: GridRequestV2,
    conn: Annotated[duckdb.DuckDBPyConnection, Depends(get_database)],
) -> GridResultV2:
    """T035: Run v2 grid scenario analysis endpoint."""

    # T036: Validate census exists
    census_repo = CensusRepository(conn)
    census = census_repo.get(grid_request.census_id)
    if census is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {grid_request.census_id} not found",
        )

    # Get participants for calculation
    participant_repo = ParticipantRepository(conn)
    try:
        participants = participant_repo.get_as_calculation_dicts(grid_request.census_id)
    except ACPInclusionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # Generate seed if not provided
    seed = grid_request.seed if grid_request.seed is not None else int(time.time() * 1000) % (2**31)

    # Run the v2 grid analysis
    result = run_grid_scenarios_v2(
        participants=participants,
        adoption_rates=grid_request.adoption_rates,
        contribution_rates=grid_request.contribution_rates,
        seed=seed,
        include_debug=grid_request.include_debug,
    )

    # Convert scenarios to API response format
    api_scenarios = []
    for scenario in result.scenarios:
        debug_response = None
        if scenario.debug_details:
            debug_response = DebugDetailsResponse(
                selected_hce_ids=scenario.debug_details.selected_hce_ids,
                hce_contributions=[
                    ParticipantContributionResponse(
                        id=c.id,
                        compensation_cents=c.compensation_cents,
                        existing_acp_contributions_cents=c.existing_acp_contributions_cents,
                        simulated_mega_backdoor_cents=c.simulated_mega_backdoor_cents,
                        individual_acp=c.individual_acp,
                    )
                    for c in scenario.debug_details.hce_contributions
                ],
                nhce_contributions=[
                    ParticipantContributionResponse(
                        id=c.id,
                        compensation_cents=c.compensation_cents,
                        existing_acp_contributions_cents=c.existing_acp_contributions_cents,
                        simulated_mega_backdoor_cents=c.simulated_mega_backdoor_cents,
                        individual_acp=c.individual_acp,
                    )
                    for c in scenario.debug_details.nhce_contributions
                ],
                intermediate_values=IntermediateValuesResponse(
                    hce_acp_sum=scenario.debug_details.intermediate_values.hce_acp_sum,
                    hce_count=scenario.debug_details.intermediate_values.hce_count,
                    nhce_acp_sum=scenario.debug_details.intermediate_values.nhce_acp_sum,
                    nhce_count=scenario.debug_details.intermediate_values.nhce_count,
                    threshold_multiple=scenario.debug_details.intermediate_values.threshold_multiple,
                    threshold_additive=scenario.debug_details.intermediate_values.threshold_additive,
                ),
            )

        api_scenarios.append(ScenarioResultV2(
            status=scenario.status.value,
            nhce_acp=scenario.nhce_acp,
            hce_acp=scenario.hce_acp,
            max_allowed_acp=scenario.max_allowed_acp,
            margin=scenario.margin,
            limiting_bound=scenario.limiting_bound.value if scenario.limiting_bound else None,
            hce_contributor_count=scenario.hce_contributor_count,
            nhce_contributor_count=scenario.nhce_contributor_count,
            total_mega_backdoor_amount=scenario.total_mega_backdoor_amount,
            seed_used=scenario.seed_used,
            adoption_rate=scenario.adoption_rate,
            contribution_rate=scenario.contribution_rate,
            error_message=scenario.error_message,
            debug_details=debug_response,
        ))

    # Convert summary to API response format
    first_failure_response = None
    if result.summary.first_failure_point:
        first_failure_response = FailurePointResponse(
            adoption_rate=result.summary.first_failure_point.adoption_rate,
            contribution_rate=result.summary.first_failure_point.contribution_rate,
        )

    return GridResultV2(
        scenarios=api_scenarios,
        summary=GridSummaryV2(
            pass_count=result.summary.pass_count,
            risk_count=result.summary.risk_count,
            fail_count=result.summary.fail_count,
            error_count=result.summary.error_count,
            total_count=result.summary.total_count,
            first_failure_point=first_failure_response,
            max_safe_contribution=result.summary.max_safe_contribution,
            worst_margin=result.summary.worst_margin,
        ),
        seed_used=result.seed_used,
    )


# ============================================================================
# Employee Impact Endpoints (Feature 006-employee-level-impact)
# ============================================================================


@router.post(
    "/v2/scenario/{census_id}/employee-impact",
    response_model=EmployeeImpactViewResponse,
    summary="Get employee-level impact view",
    description=(
        "Compute and return employee-level contribution breakdown for a scenario. "
        "Shows individual ACP contributions, constraint status, and group summaries."
    ),
    responses={
        400: {"model": Error, "description": "Invalid parameters"},
        404: {"model": Error, "description": "Census not found"},
        429: {"model": Error, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(RATE_LIMIT)
async def get_employee_impact(
    request: Request,
    census_id: str,
    impact_request: EmployeeImpactRequest,
    conn: Annotated[duckdb.DuckDBPyConnection, Depends(get_database)],
) -> EmployeeImpactViewResponse:
    """T023: Get employee-level impact view endpoint."""

    # Initialize repositories
    census_repo = CensusRepository(conn)
    participant_repo = ParticipantRepository(conn)

    # Verify census exists
    census = census_repo.get(census_id)
    if census is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {census_id} not found",
        )

    # Compute employee impact
    service = EmployeeImpactService(participant_repo, census_repo)
    try:
        result = service.compute_impact(
            census_id=census_id,
            adoption_rate=impact_request.adoption_rate,
            contribution_rate=impact_request.contribution_rate,
            seed=impact_request.seed,
        )
    except ACPInclusionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # Convert to API response format
    return EmployeeImpactViewResponse(
        census_id=result.census_id,
        adoption_rate=result.adoption_rate,
        contribution_rate=result.contribution_rate,
        seed_used=result.seed_used,
        plan_year=result.plan_year,
        section_415c_limit=result.section_415c_limit,
        excluded_count=result.excluded_count,
        hce_employees=[
            EmployeeImpactResponse(
                employee_id=e.employee_id,
                is_hce=e.is_hce,
                compensation=e.compensation,
                deferral_amount=e.deferral_amount,
                match_amount=e.match_amount,
                after_tax_amount=e.after_tax_amount,
                section_415c_limit=e.section_415c_limit,
                available_room=e.available_room,
                mega_backdoor_amount=e.mega_backdoor_amount,
                requested_mega_backdoor=e.requested_mega_backdoor,
                individual_acp=e.individual_acp,
                constraint_status=e.constraint_status.value,
                constraint_detail=e.constraint_detail,
            )
            for e in result.hce_employees
        ],
        nhce_employees=[
            EmployeeImpactResponse(
                employee_id=e.employee_id,
                is_hce=e.is_hce,
                compensation=e.compensation,
                deferral_amount=e.deferral_amount,
                match_amount=e.match_amount,
                after_tax_amount=e.after_tax_amount,
                section_415c_limit=e.section_415c_limit,
                available_room=e.available_room,
                mega_backdoor_amount=e.mega_backdoor_amount,
                requested_mega_backdoor=e.requested_mega_backdoor,
                individual_acp=e.individual_acp,
                constraint_status=e.constraint_status.value,
                constraint_detail=e.constraint_detail,
            )
            for e in result.nhce_employees
        ],
        hce_summary=EmployeeImpactSummaryResponse(
            group=result.hce_summary.group,
            total_count=result.hce_summary.total_count,
            at_limit_count=result.hce_summary.at_limit_count,
            reduced_count=result.hce_summary.reduced_count,
            average_available_room=result.hce_summary.average_available_room,
            total_mega_backdoor=result.hce_summary.total_mega_backdoor,
            average_individual_acp=result.hce_summary.average_individual_acp,
            total_match=result.hce_summary.total_match,
            total_after_tax=result.hce_summary.total_after_tax,
        ),
        nhce_summary=EmployeeImpactSummaryResponse(
            group=result.nhce_summary.group,
            total_count=result.nhce_summary.total_count,
            at_limit_count=result.nhce_summary.at_limit_count,
            reduced_count=result.nhce_summary.reduced_count,
            average_available_room=result.nhce_summary.average_available_room,
            total_mega_backdoor=result.nhce_summary.total_mega_backdoor,
            average_individual_acp=result.nhce_summary.average_individual_acp,
            total_match=result.nhce_summary.total_match,
            total_after_tax=result.nhce_summary.total_after_tax,
        ),
    )


@router.post(
    "/v2/scenario/{census_id}/employee-impact/export",
    summary="Export employee-level impact to CSV",
    description=(
        "Export employee-level impact data as a CSV file. "
        "Supports filtering by group and optional Group column."
    ),
    responses={
        400: {"model": Error, "description": "Invalid parameters"},
        404: {"model": Error, "description": "Census not found"},
        429: {"model": Error, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(RATE_LIMIT)
async def export_employee_impact(
    request: Request,
    census_id: str,
    export_request: EmployeeImpactExportRequest,
    conn: Annotated[duckdb.DuckDBPyConnection, Depends(get_database)],
) -> StreamingResponse:
    """T059: Export employee-level impact to CSV endpoint."""

    # Initialize repositories
    census_repo = CensusRepository(conn)
    participant_repo = ParticipantRepository(conn)

    # Verify census exists
    census = census_repo.get(census_id)
    if census is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {census_id} not found",
        )

    # Compute employee impact
    service = EmployeeImpactService(participant_repo, census_repo)
    result = service.compute_impact(
        census_id=census_id,
        adoption_rate=export_request.adoption_rate,
        contribution_rate=export_request.contribution_rate,
        seed=export_request.seed,
    )

    # Determine which employees to include
    employees = []
    if export_request.export_group in ("hce", "all"):
        employees.extend(result.hce_employees)
    if export_request.export_group in ("nhce", "all"):
        employees.extend(result.nhce_employees)

    # Generate CSV content
    csv_buffer = io.StringIO()

    # Build header
    headers = ["Employee ID"]
    if export_request.include_group_column and export_request.export_group == "all":
        headers.append("Group")
    headers.extend([
        "Compensation",
        "Deferral",
        "Match",
        "After-Tax",
        "Mega-Backdoor",
        "Individual ACP (%)",
        "Available Room",
        "Constraint Status",
    ])

    csv_buffer.write(",".join(headers) + "\n")

    # Write employee rows
    for emp in employees:
        row = [emp.employee_id]
        if export_request.include_group_column and export_request.export_group == "all":
            row.append("HCE" if emp.is_hce else "NHCE")
        row.extend([
            f"{emp.compensation:.2f}",
            f"{emp.deferral_amount:.2f}",
            f"{emp.match_amount:.2f}",
            f"{emp.after_tax_amount:.2f}",
            f"{emp.mega_backdoor_amount:.2f}",
            f"{emp.individual_acp:.2f}" if emp.individual_acp is not None else "",
            f"{emp.available_room:.2f}",
            emp.constraint_status.value,
        ])
        csv_buffer.write(",".join(row) + "\n")

    # Return CSV as streaming response
    csv_buffer.seek(0)
    return StreamingResponse(
        iter([csv_buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=employee_impact_{census_id}.csv"
        },
    )
