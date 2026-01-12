"""
Census API Routes.

Handles census upload, retrieval, listing, and deletion.
"""

import io
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.api.schemas import Census, CensusListResponse, CensusSummary, Error
from src.core.census_parser import CensusValidationError, process_census
from src.core.constants import RATE_LIMIT
from src.storage.database import get_db
from src.storage.repository import (
    CensusRepository,
    ParticipantRepository,
    create_census_from_dataframe,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/census",
    response_model=Census,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new census",
    description=(
        "Upload participant census data in CSV format. PII fields are automatically "
        "stripped and replaced with non-reversible internal identifiers."
    ),
    responses={
        400: {"model": Error, "description": "Invalid census data"},
        429: {"model": Error, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(RATE_LIMIT)
async def upload_census(
    request: Request,
    file: Annotated[UploadFile, File(description="CSV file with participant data")],
    plan_year: Annotated[int, Form(ge=2020, le=2100, description="Plan year for analysis")],
    name: Annotated[str | None, Form(max_length=255, description="Optional name for the census")] = None,
) -> Census:
    """
    T037: Upload census endpoint.

    Upload a census CSV file, parse it, strip PII, and store it.
    """
    # Read file content
    content = await file.read()
    file_like = io.StringIO(content.decode("utf-8"))

    try:
        # Process census (parse, validate, hash IDs)
        df, salt = process_census(file_like)
    except CensusValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV: {str(e)}",
        )

    # Generate name if not provided
    if name is None:
        name = file.filename or f"Census {plan_year}"

    # Create models
    census, participants = create_census_from_dataframe(
        df=df,
        name=name,
        plan_year=plan_year,
        salt=salt,
    )

    # Save to database
    conn = get_db()
    census_repo = CensusRepository(conn)
    participant_repo = ParticipantRepository(conn)

    census_repo.save(census)
    participant_repo.bulk_insert(participants)

    return Census(
        id=census.id,
        name=census.name,
        plan_year=census.plan_year,
        upload_timestamp=census.upload_timestamp,
        participant_count=census.participant_count,
        hce_count=census.hce_count,
        nhce_count=census.nhce_count,
        version=census.version,
    )


@router.get(
    "/census",
    response_model=CensusListResponse,
    summary="List all censuses",
    description="Retrieve a list of all uploaded censuses",
)
@limiter.limit(RATE_LIMIT)
async def list_censuses(
    request: Request,
    plan_year: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> CensusListResponse:
    """T038: List censuses endpoint."""
    conn = get_db()
    repo = CensusRepository(conn)

    censuses, total = repo.list(plan_year=plan_year, limit=limit, offset=offset)

    return CensusListResponse(
        items=[
            CensusSummary(
                id=c.id,
                name=c.name,
                plan_year=c.plan_year,
                participant_count=c.participant_count,
                hce_count=c.hce_count,
                nhce_count=c.nhce_count,
            )
            for c in censuses
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/census/{census_id}",
    response_model=Census,
    summary="Get census details",
    description="Retrieve details for a specific census",
    responses={
        404: {"model": Error, "description": "Census not found"},
    },
)
@limiter.limit(RATE_LIMIT)
async def get_census(request: Request, census_id: str) -> Census:
    """T039: Get census details endpoint."""
    conn = get_db()
    repo = CensusRepository(conn)

    census = repo.get(census_id)
    if census is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {census_id} not found",
        )

    return Census(
        id=census.id,
        name=census.name,
        plan_year=census.plan_year,
        upload_timestamp=census.upload_timestamp,
        participant_count=census.participant_count,
        hce_count=census.hce_count,
        nhce_count=census.nhce_count,
        version=census.version,
    )


@router.delete(
    "/census/{census_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a census",
    description="Delete a census and all associated analysis results",
    responses={
        404: {"model": Error, "description": "Census not found"},
    },
)
@limiter.limit(RATE_LIMIT)
async def delete_census(request: Request, census_id: str) -> None:
    """T040: Delete census endpoint."""
    conn = get_db()
    repo = CensusRepository(conn)

    deleted = repo.delete(census_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Census {census_id} not found",
        )
