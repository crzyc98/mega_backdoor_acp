"""
Census API Routes.

Handles census upload, retrieval, listing, and deletion.
Supports column mapping detection, HCE determination modes, and import metadata.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Annotated

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, Request, Response, UploadFile, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.routers.dependencies import get_workspace_id_from_header

from app.routers.schemas import (
    Census,
    CensusDetail,
    CensusListResponse,
    CensusSummary,
    CensusUpdateRequest,
    CensusValidationError as CensusValidationErrorSchema,
    CensusValidationErrorDetail,
    ColumnMappingDetection,
    Error,
    HCEMode,
    ImportMetadataResponse,
    ParticipantListResponse,
    ParticipantResponse,
)
from app.services.census_parser import (
    CensusValidationError,
    detect_column_mapping,
    process_census_bytes,
)
from app.services.constants import RATE_LIMIT
from app.services.hce_thresholds import HCE_THRESHOLDS, get_threshold_for_year
from app.storage.database import get_db
from app.storage.models import ImportMetadata
from app.storage.repository import (
    CensusRepository,
    ImportMetadataRepository,
    ParticipantRepository,
    create_census_from_dataframe,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# T013: Column mapping detection endpoint
@router.post(
    "/census/column-mapping/detect",
    response_model=ColumnMappingDetection,
    summary="Detect column mapping from CSV headers",
    description=(
        "Upload a CSV file to detect column mapping suggestions. "
        "Returns suggested mappings for required fields based on column names."
    ),
    responses={
        400: {"model": Error, "description": "Invalid CSV file"},
    },
)
@limiter.limit(RATE_LIMIT)
async def detect_column_mapping_endpoint(
    request: Request,
    file: Annotated[UploadFile, File(description="CSV file to analyze")],
    hce_mode: Annotated[HCEMode, Form(description="HCE determination mode")] = "explicit",
) -> ColumnMappingDetection:
    """Detect column mappings from CSV headers."""
    import pandas as pd

    content = await file.read()
    try:
        file_like = io.StringIO(content.decode("utf-8"))
        df = pd.read_csv(file_like, nrows=0)  # Only read headers
        columns = list(df.columns)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read CSV headers: {str(e)}",
        )

    result = detect_column_mapping(columns, hce_mode)
    return ColumnMappingDetection(**result)


# T014, T015, T016, T017: Extended upload census endpoint
@router.post(
    "/census",
    response_model=Census,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new census",
    description=(
        "Upload participant census data in CSV format. PII fields are automatically "
        "stripped and replaced with non-reversible internal identifiers. "
        "Supports column mapping and HCE determination modes."
    ),
    responses={
        400: {"model": CensusValidationErrorSchema, "description": "Invalid census data"},
        429: {"model": Error, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(RATE_LIMIT)
async def upload_census(
    request: Request,
    file: Annotated[UploadFile, File(description="CSV or XLSX file with participant data")],
    plan_year: Annotated[int, Form(ge=2020, le=2100, description="Plan year for analysis")],
    name: Annotated[str | None, Form(max_length=255, description="Name for the census")] = None,
    client_name: Annotated[str | None, Form(max_length=255, description="Client/organization name")] = None,
    hce_mode: Annotated[HCEMode, Form(description="HCE determination method")] = "explicit",
    column_mapping: Annotated[str | None, Form(description="JSON string mapping target fields to source columns")] = None,
    workspace_id: str = Depends(get_workspace_id_from_header),
) -> Census:
    """
    Upload census endpoint with column mapping and HCE mode support.

    T014: Accept name, client_name, hce_mode, column_mapping parameters
    T015: Use column mapping and HCE mode from request
    T016: Store ImportMetadata after successful import
    T017: Return extended census response with summary statistics
    """
    # Read file content
    content = await file.read()
    source_filename = file.filename or "unknown.csv"

    if not source_filename.lower().endswith((".csv", ".xlsx")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV or XLSX",
        )

    # Parse column mapping if provided
    parsed_column_mapping = None
    if column_mapping:
        try:
            parsed_column_mapping = json.loads(column_mapping)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid column_mapping JSON: {str(e)}",
            )

    try:
        # Process census (parse, validate, hash IDs)
        df, salt, used_column_mapping = process_census_bytes(
            file_content=content,
            filename=source_filename,
            census_salt=None,
            hce_mode=hce_mode,
            plan_year=plan_year,
            column_mapping=parsed_column_mapping,
        )
    except CensusValidationError as e:
        # T019: Return validation error with details
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse file: {str(e)}",
        )

    # Generate name if not provided
    if name is None:
        name = source_filename.rsplit(".", 1)[0] if "." in source_filename else source_filename

    # T018: Create models with summary statistics
    census, participants = create_census_from_dataframe(
        df=df,
        name=name,
        plan_year=plan_year,
        salt=salt,
        client_name=client_name,
        hce_mode=hce_mode,
    )

    # Save to database
    conn = get_db(workspace_id)
    census_repo = CensusRepository(conn)
    participant_repo = ParticipantRepository(conn)
    import_metadata_repo = ImportMetadataRepository(conn)

    census_repo.save(census)
    participant_repo.bulk_insert(participants)

    # T016: Store import metadata
    import_metadata = ImportMetadata(
        id=str(uuid.uuid4()),
        census_id=census.id,
        source_filename=source_filename,
        column_mapping=used_column_mapping,
        row_count=len(participants),
        created_at=datetime.utcnow(),
    )
    import_metadata_repo.save(import_metadata)

    # T037: Log census creation
    logger.info(
        f"Census created: id={census.id}, name={census.name}, "
        f"participants={census.participant_count}, hce_mode={census.hce_mode}"
    )

    # T017: Return extended response with summary statistics
    return Census(
        id=census.id,
        name=census.name,
        client_name=census.client_name,
        plan_year=census.plan_year,
        hce_mode=census.hce_mode,
        upload_timestamp=census.upload_timestamp,
        participant_count=census.participant_count,
        hce_count=census.hce_count,
        nhce_count=census.nhce_count,
        avg_compensation=census.avg_compensation,
        avg_deferral_rate=census.avg_deferral_rate,
        version=census.version,
    )


# T020, T021: Extended list censuses endpoint with client_name filter
@router.get(
    "/census",
    response_model=CensusListResponse,
    summary="List all censuses",
    description="Retrieve a list of all uploaded censuses with optional filtering",
)
@limiter.limit(RATE_LIMIT)
async def list_censuses(
    request: Request,
    plan_year: int | None = None,
    client_name: str | None = Query(None, description="Filter by client name (partial match)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    workspace_id: str = Depends(get_workspace_id_from_header),
) -> CensusListResponse:
    """List censuses with client_name filter support."""
    conn = get_db(workspace_id)
    repo = CensusRepository(conn)

    censuses, total = repo.list(
        plan_year=plan_year,
        client_name=client_name,
        limit=limit,
        offset=offset,
    )

    # T021: Include client_name and hce_mode in summary
    return CensusListResponse(
        items=[
            CensusSummary(
                id=c.id,
                name=c.name,
                client_name=c.client_name,
                plan_year=c.plan_year,
                hce_mode=c.hce_mode,
                participant_count=c.participant_count,
                hce_count=c.hce_count,
                nhce_count=c.nhce_count,
                upload_timestamp=c.upload_timestamp,
            )
            for c in censuses
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


# T022: Census detail endpoint with metadata and analysis info
@router.get(
    "/census/{census_id}",
    response_model=CensusDetail,
    summary="Get census details",
    description="Retrieve full details for a specific census including import metadata",
    responses={
        404: {"model": Error, "description": "Census not found"},
    },
)
@limiter.limit(RATE_LIMIT)
async def get_census(
    request: Request,
    census_id: str,
    workspace_id: str = Depends(get_workspace_id_from_header),
) -> CensusDetail:
    """Get census details with import metadata and analysis info."""
    conn = get_db(workspace_id)
    census_repo = CensusRepository(conn)
    import_metadata_repo = ImportMetadataRepository(conn)

    census = census_repo.get(census_id)
    if census is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {census_id} not found",
        )

    # Get import metadata
    import_metadata = import_metadata_repo.get_by_census(census_id)
    import_metadata_response = None
    if import_metadata:
        import_metadata_response = ImportMetadataResponse(
            id=import_metadata.id,
            census_id=import_metadata.census_id,
            source_filename=import_metadata.source_filename,
            column_mapping=import_metadata.column_mapping,
            row_count=import_metadata.row_count,
            created_at=import_metadata.created_at,
        )

    # Check for associated analyses
    has_analyses = census_repo.has_analyses(census_id)

    return CensusDetail(
        id=census.id,
        name=census.name,
        client_name=census.client_name,
        plan_year=census.plan_year,
        hce_mode=census.hce_mode,
        upload_timestamp=census.upload_timestamp,
        participant_count=census.participant_count,
        hce_count=census.hce_count,
        nhce_count=census.nhce_count,
        avg_compensation=census.avg_compensation,
        avg_deferral_rate=census.avg_deferral_rate,
        version=census.version,
        import_metadata=import_metadata_response,
        has_analyses=has_analyses,
    )


# T023: Get import metadata endpoint
@router.get(
    "/census/{census_id}/metadata",
    response_model=ImportMetadataResponse,
    summary="Get census import metadata",
    description="Retrieve import metadata for a specific census",
    responses={
        404: {"model": Error, "description": "Census or metadata not found"},
    },
)
@limiter.limit(RATE_LIMIT)
async def get_census_metadata(
    request: Request,
    census_id: str,
    workspace_id: str = Depends(get_workspace_id_from_header),
) -> ImportMetadataResponse:
    """Get import metadata for a census."""
    conn = get_db(workspace_id)
    census_repo = CensusRepository(conn)
    import_metadata_repo = ImportMetadataRepository(conn)

    # Verify census exists
    census = census_repo.get(census_id)
    if census is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {census_id} not found",
        )

    import_metadata = import_metadata_repo.get_by_census(census_id)
    if import_metadata is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import metadata not found for census {census_id}",
        )

    return ImportMetadataResponse(
        id=import_metadata.id,
        census_id=import_metadata.census_id,
        source_filename=import_metadata.source_filename,
        column_mapping=import_metadata.column_mapping,
        row_count=import_metadata.row_count,
        created_at=import_metadata.created_at,
    )


# T024: Get participants endpoint with pagination and HCE filter
@router.get(
    "/census/{census_id}/participants",
    response_model=ParticipantListResponse,
    summary="List census participants",
    description="Retrieve participants for a census with pagination and HCE filtering",
    responses={
        404: {"model": Error, "description": "Census not found"},
    },
)
@limiter.limit(RATE_LIMIT)
async def list_census_participants(
    request: Request,
    census_id: str,
    hce_only: bool = Query(False, description="Return only HCE participants"),
    nhce_only: bool = Query(False, description="Return only NHCE participants"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    workspace_id: str = Depends(get_workspace_id_from_header),
) -> ParticipantListResponse:
    """List participants for a census with filtering."""
    conn = get_db(workspace_id)
    census_repo = CensusRepository(conn)
    participant_repo = ParticipantRepository(conn)

    # Verify census exists
    census = census_repo.get(census_id)
    if census is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {census_id} not found",
        )

    # Get participants with filtering
    participants, total = participant_repo.list_participants(
        census_id=census_id,
        hce_only=hce_only,
        nhce_only=nhce_only,
        limit=limit,
        offset=offset,
    )

    return ParticipantListResponse(
        items=[
            ParticipantResponse(
                id=p.id,
                internal_id=p.internal_id,
                is_hce=p.is_hce,
                compensation=p.compensation_cents / 100,
                deferral_rate=p.deferral_rate,
                match_rate=p.match_rate,
                after_tax_rate=p.after_tax_rate,
            )
            for p in participants
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


# T027: Delete census with analysis warning
@router.delete(
    "/census/{census_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a census",
    description="Delete a census and all associated analysis results. Returns X-Warning header if analyses exist.",
    responses={
        404: {"model": Error, "description": "Census not found"},
    },
)
@limiter.limit(RATE_LIMIT)
async def delete_census(
    request: Request,
    census_id: str,
    response: Response,
    workspace_id: str = Depends(get_workspace_id_from_header),
) -> None:
    """Delete census with warning for associated analyses."""
    conn = get_db(workspace_id)
    repo = CensusRepository(conn)

    # Check if census exists
    census = repo.get(census_id)
    if census is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {census_id} not found",
        )

    # Check for associated analyses and add warning header
    if repo.has_analyses(census_id):
        response.headers["X-Warning"] = "Census has associated analyses that will also be deleted"

    deleted = repo.delete(census_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {census_id} not found",
        )

    logger.info(f"Census deleted: id={census_id}")


# T029: HCE thresholds endpoint
@router.get(
    "/hce-thresholds",
    response_model=dict,
    summary="Get HCE thresholds",
    description="Retrieve historical IRS HCE compensation thresholds by year",
)
@limiter.limit(RATE_LIMIT)
async def get_hce_thresholds(request: Request) -> dict:
    """Return historical HCE thresholds."""
    return {"thresholds": {str(year): amount for year, amount in HCE_THRESHOLDS.items()}}


# T032: PATCH endpoint for census metadata updates
@router.patch(
    "/census/{census_id}",
    response_model=Census,
    summary="Update census metadata",
    description="Update editable census metadata (name, client_name only)",
    responses={
        404: {"model": Error, "description": "Census not found"},
        400: {"model": Error, "description": "Invalid update request"},
    },
)
@limiter.limit(RATE_LIMIT)
async def update_census_metadata(
    request: Request,
    census_id: str,
    update: CensusUpdateRequest,
    workspace_id: str = Depends(get_workspace_id_from_header),
) -> Census:
    """
    Update census metadata (name and client_name only).

    T032: Create PATCH endpoint for metadata updates
    T033: Validate only name and client_name can be modified
    """
    conn = get_db(workspace_id)
    repo = CensusRepository(conn)

    # Check if census exists
    census = repo.get(census_id)
    if census is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {census_id} not found",
        )

    # T033: Only allow name and client_name updates (enforced by schema)
    # The CensusUpdateRequest schema only has name and client_name fields

    # Update census
    updated_census = repo.update(
        census_id=census_id,
        name=update.name,
        client_name=update.client_name,
    )

    if updated_census is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {census_id} not found",
        )

    logger.info(f"Census updated: id={census_id}, name={update.name}, client_name={update.client_name}")

    return Census(
        id=updated_census.id,
        name=updated_census.name,
        client_name=updated_census.client_name,
        plan_year=updated_census.plan_year,
        hce_mode=updated_census.hce_mode,
        upload_timestamp=updated_census.upload_timestamp,
        participant_count=updated_census.participant_count,
        hce_count=updated_census.hce_count,
        nhce_count=updated_census.nhce_count,
        avg_compensation=updated_census.avg_compensation,
        avg_deferral_rate=updated_census.avg_deferral_rate,
        version=updated_census.version,
    )
