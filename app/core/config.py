"""
Application configuration
Loads settings from environment variables
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""

    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # GCP Project
    PROJECT_ID: str = os.getenv("GCP_PROJECT", "gadgetcloud-prd")
    REGION: str = "asia-south1"

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60 * 24  # 24 hours

    # Anthropic AI
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # Firestore
    FIRESTORE_DATABASE: str = "(default)"

    # Cloud Storage
    STORAGE_BUCKET: str = f"{PROJECT_ID}-user-documents"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:4200",  # Local Angular dev
        "http://localhost:5000",  # Local Firebase hosting
        "https://app.gadgetcloud.io",  # Production
        "https://gadgetcloud-app-prd.web.app",  # Firebase default
    ]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
