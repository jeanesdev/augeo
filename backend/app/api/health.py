"""Health check and monitoring endpoints."""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.redis import get_redis

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> JSONResponse:
    """
    Basic health check endpoint.

    Returns:
        JSONResponse with status, version, and timestamp
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.environment,
        }
    )


@router.get("/health/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check() -> JSONResponse:
    """
    Detailed health check endpoint that checks all services.

    Checks:
    - Database connectivity (PostgreSQL)
    - Redis connectivity
    - Email service configuration

    Returns:
        JSONResponse with detailed status of all services
    """
    health_status: dict[str, Any] = {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "services": {},
    }

    overall_healthy = True

    # Check database
    try:
        async for db in get_db():
            result = await db.execute(text("SELECT 1"))
            result.scalar()
            health_status["services"]["database"] = {
                "status": "healthy",
                "type": "postgresql",
            }
            break
    except Exception as e:
        logger.error("Database health check failed", extra={"error": str(e)})
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "type": "postgresql",
            "error": str(e),
        }
        overall_healthy = False

    # Check Redis
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        health_status["services"]["redis"] = {
            "status": "healthy",
            "type": "redis",
        }
    except Exception as e:
        logger.error("Redis health check failed", extra={"error": str(e)})
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "type": "redis",
            "error": str(e),
        }
        overall_healthy = False

    # Check email service configuration
    try:
        email_configured = bool(
            settings.azure_communication_connection_string and settings.email_from_address
        )
        health_status["services"]["email"] = {
            "status": "configured" if email_configured else "not_configured",
            "type": "azure_communication_services",
            "mode": "production" if email_configured else "mock",
        }
    except Exception as e:
        logger.error("Email health check failed", extra={"error": str(e)})
        health_status["services"]["email"] = {
            "status": "error",
            "type": "azure_communication_services",
            "error": str(e),
        }

    # Update overall status
    if not overall_healthy:
        health_status["status"] = "degraded"
        return JSONResponse(
            content=health_status,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return JSONResponse(content=health_status)


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> JSONResponse:
    """
    Kubernetes readiness probe endpoint.

    Checks if the application is ready to receive traffic.

    Returns:
        JSONResponse with ready status
    """
    # Check critical services
    try:
        async for db in get_db():
            await db.execute(text("SELECT 1"))
            break

        redis_client = await get_redis()
        await redis_client.ping()

        return JSONResponse(content={"status": "ready", "timestamp": datetime.utcnow().isoformat()})
    except Exception as e:
        logger.error("Readiness check failed", extra={"error": str(e)})
        return JSONResponse(
            content={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> JSONResponse:
    """
    Kubernetes liveness probe endpoint.

    Simple check to verify the application is running.

    Returns:
        JSONResponse with alive status
    """
    return JSONResponse(content={"status": "alive", "timestamp": datetime.utcnow().isoformat()})
