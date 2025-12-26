"""
GadgetCloud Backend - Unified API with Agent Layer
FastAPI application serving all API endpoints and AI features
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.routers import auth, items, repairs, chat, health
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="GadgetCloud API",
    description="Unified backend API with built-in agent orchestration",
    version="1.0.0",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(items.router, prefix="/api/items", tags=["Items"])
app.include_router(repairs.router, prefix="/api/repairs", tags=["Repairs"])
app.include_router(chat.router, prefix="/api/chat", tags=["AI Chat"])

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting GadgetCloud Backend - Environment: {settings.ENVIRONMENT}")
    logger.info(f"Agent Layer: {'Enabled' if settings.ANTHROPIC_API_KEY else 'Disabled'}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down GadgetCloud Backend")

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "GadgetCloud Backend",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "agent_enabled": bool(settings.ANTHROPIC_API_KEY)
    }
