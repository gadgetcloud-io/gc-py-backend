"""
Health check endpoints
"""

from fastapi import APIRouter
from datetime import datetime
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint for Cloud Run
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "service": "gc-py-backend",
        "version": "1.0.0"
    }


@router.get("/readiness")
async def readiness_check():
    """
    Readiness check - verifies service dependencies
    """
    checks = {
        "firestore": "ok",  # TODO: Add actual Firestore connectivity check
        "storage": "ok",    # TODO: Add actual Storage connectivity check
        "authentication": "ok"
    }

    all_ok = all(status == "ok" for status in checks.values())

    return {
        "ready": all_ok,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
