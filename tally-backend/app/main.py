import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings
from app.middleware.tracing import add_tracing_middleware
from app.routes import api_router
from app.schemas import ErrorResponse, HealthCheckResponse
from app.services.storage_service import storage_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Initialize Supabase storage service
    await storage_service.initialize()
    yield
    # Shutdown


def create_application() -> FastAPI:
    app = FastAPI(
        title="Tally Tabular Review API",
        description="API for managing audit controls, documents, and AI responses",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Add tracing middleware
    add_tracing_middleware(app)

    # Include routers
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_application()


@app.get("/health", response_model=HealthCheckResponse, summary="Health Check")
async def health_check():
    """
    Comprehensive health check endpoint demonstrating enhanced Pydantic validation.
    
    Returns detailed health status with individual service checks.
    """
    start_time = time.time()
    checks = {}

    # Supabase storage check
    try:
        storage_status = await storage_service.verify_connection()
        checks["storage"] = storage_status["connected"]
    except Exception:
        checks["storage"] = False

    # Additional service checks could be added here
    checks["api_server"] = True
    checks["response_time"] = (time.time() - start_time) < 1.0  # Under 1 second

    # The HealthCheckResponse schema will automatically validate:
    # - status is a non-empty string
    # - version follows expected format
    # - timestamp is properly formatted
    # - computed field 'is_healthy' will be calculated
    return HealthCheckResponse(
        status="healthy" if all(checks.values()) else "degraded",
        version="1.0.0",
        timestamp=datetime.now(),
        checks=checks
    )


@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Tally Tabular Review API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Error handlers demonstrating Pydantic error schemas
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom error handler using Pydantic ErrorResponse schema."""
    return ErrorResponse(
        error=f"HTTP_{exc.status_code}",
        detail=exc.detail,
        timestamp=datetime.now()
    ).model_dump()
