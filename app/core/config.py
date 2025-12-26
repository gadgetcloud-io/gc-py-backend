"""
Application configuration
Loads settings from environment variables and Secret Manager
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
from google.cloud import secretmanager
import os
import logging

logger = logging.getLogger(__name__)


def get_secret(project_id: str, secret_id: str, version: str = "latest") -> Optional[str]:
    """
    Get secret from Google Cloud Secret Manager

    Args:
        project_id: GCP project ID
        secret_id: Secret name
        version: Secret version (default: latest)

    Returns:
        Secret value or None if not found
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.warning(f"Failed to get secret {secret_id}: {e}")
        return None


class Settings(BaseSettings):
    """Application settings"""

    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # GCP Project
    PROJECT_ID: str = os.getenv("GCP_PROJECT", "gadgetcloud-prd")
    REGION: str = "asia-south1"

    # JWT Configuration
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60 * 24  # 24 hours

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load JWT secret from Secret Manager or environment
        if not self.JWT_SECRET_KEY:
            # Try to load from Secret Manager
            secret = get_secret(self.PROJECT_ID, "jwt-signing-key")
            if secret:
                self.JWT_SECRET_KEY = secret
                logger.info("Loaded JWT secret from Secret Manager")
            else:
                # Fallback to environment variable
                self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
                logger.warning("Using JWT secret from environment variable or default")

    # Firestore
    FIRESTORE_DATABASE: str = "gcdb"

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
