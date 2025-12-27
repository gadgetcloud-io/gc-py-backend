"""
Settings Router

User preference management endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.security import get_current_user
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    """Settings update request"""
    notifications: Dict[str, bool]
    privacy: Dict[str, Any]
    security: Dict[str, Any]


@router.get("", response_model=Dict[str, Any])
async def get_settings(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current user's settings

    Returns default settings if none exist
    """
    try:
        settings = await SettingsService.get_user_settings(current_user["id"])
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve settings: {str(e)}"
        )


@router.put("", response_model=Dict[str, Any])
async def update_settings(
    settings_data: SettingsUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update current user's settings
    """
    try:
        updated_settings = await SettingsService.update_user_settings(
            current_user["id"],
            settings_data.model_dump()
        )
        return updated_settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {str(e)}"
        )
