"""
Permissions Router

Provides endpoints for accessing role permissions.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging

from app.services.permission_service import PermissionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/permissions", tags=["admin", "permissions"])


@router.get("/{role}", response_model=Dict[str, Any])
async def get_role_permissions(role: str):
    """
    Get permissions for a specific role

    **Path Parameters:**
    - role: Role name (customer, partner, support, admin)

    **Returns:**
    - Role permissions including resource access and allowed actions

    This endpoint is public (no auth required) because the frontend needs
    to load permissions after login to configure the UI.
    """
    try:
        # Validate role
        valid_roles = ["customer", "partner", "support", "admin"]
        if role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )

        permissions = await PermissionService.get_role_permissions(role)

        if not permissions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permissions not found for role: {role}"
            )

        return permissions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting permissions for role {role}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get role permissions"
        )
