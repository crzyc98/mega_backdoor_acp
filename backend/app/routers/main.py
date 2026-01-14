"""
FastAPI Application Entry Point.

This module provides the main FastAPI application with health endpoint,
rate limiting, and route registration.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.routers.schemas import Error, HealthResponse
from app.services.constants import RATE_LIMIT, SYSTEM_VERSION
from app.storage.database import init_database

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="ACP Sensitivity Analyzer API",
    description=(
        "REST API for ACP (Actual Contribution Percentage) sensitivity analysis. "
        "Enables programmatic census upload, scenario analysis, and results export "
        "for mega-backdoor Roth compliance testing."
    ),
    version=SYSTEM_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*",  # In production, remove this and specify exact origins
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database on startup."""
    init_database()


@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check",
    description="Check API health and version",
)
@limiter.limit(RATE_LIMIT)
async def health_check(request: Request) -> HealthResponse:
    """
    Health check endpoint.

    Returns the API health status and version information.
    """
    return HealthResponse(status="healthy", version=SYSTEM_VERSION)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=500,
        content=Error(
            error="internal_server_error",
            message="An unexpected error occurred"
        ).model_dump()
    )


# Import and register routes
from app.routers.routes import census, analysis, export, import_wizard
from app.routers import workspaces

app.include_router(workspaces.router)  # Workspace management (React frontend)
app.include_router(census.router, prefix="/api/v1", tags=["Census"])
app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(export.router, prefix="/api/v1", tags=["Export"])
app.include_router(import_wizard.router, prefix="/api", tags=["Import Wizard"])
app.include_router(import_wizard.workspace_router, prefix="/api", tags=["Import Wizard"])  # T009: Workspace-scoped import
