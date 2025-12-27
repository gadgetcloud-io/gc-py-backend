"""
Settings Service

Handles user preference storage and retrieval
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging
from google.cloud import firestore

from app.core.config import settings

db = firestore.Client(project=settings.PROJECT_ID, database=settings.FIRESTORE_DATABASE)
logger = logging.getLogger(__name__)


class SettingsService:
    """Service for managing user settings"""

    COLLECTION = "gc-users"

    @classmethod
    def _get_default_settings(cls) -> Dict[str, Any]:
        """Return default settings structure"""
        return {
            "notifications": {
                "email": True,
                "sms": False,
                "push": True,
                "updates": True
            },
            "privacy": {
                "profileVisibility": "private",
                "showEmail": False,
                "showMobile": False
            },
            "security": {
                "twoFactorAuth": False,
                "sessionTimeout": 30
            },
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }

    @classmethod
    async def get_user_settings(cls, user_id: str) -> Dict[str, Any]:
        """
        Get user settings from Firestore

        Args:
            user_id: User document ID

        Returns:
            User settings or default settings
        """
        try:
            user_doc = db.collection(cls.COLLECTION).document(user_id).get()

            if not user_doc.exists:
                logger.warning(f"User not found: {user_id}")
                return cls._get_default_settings()

            user_data = user_doc.to_dict()

            # Check if settings exist in user document
            if "settings" in user_data and user_data["settings"]:
                return user_data["settings"]

            # Return defaults if no settings exist
            return cls._get_default_settings()

        except Exception as e:
            logger.error(f"Error retrieving settings for user {user_id}: {e}", exc_info=True)
            # Return defaults on error to avoid breaking the UI
            return cls._get_default_settings()

    @classmethod
    async def update_user_settings(
        cls,
        user_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user settings in Firestore

        Args:
            user_id: User document ID
            settings: Settings data to save

        Returns:
            Updated settings
        """
        try:
            # Add timestamp
            settings["updatedAt"] = datetime.now(timezone.utc).isoformat()

            # Update user document with settings
            user_ref = db.collection(cls.COLLECTION).document(user_id)
            user_ref.update({
                "settings": settings
            })

            logger.info(f"Updated settings for user: {user_id}")
            return settings

        except Exception as e:
            logger.error(f"Error updating settings for user {user_id}: {e}", exc_info=True)
            raise
