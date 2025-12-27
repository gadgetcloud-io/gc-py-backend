"""
Admin User Management Router

Provides administrative endpoints for managing users.
All endpoints require admin role and appropriate permissions.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, validator
from typing import Dict, Any, Optional, List
import logging

from app.core.security import get_current_user, require_permission
from app.services.admin_user_service import AdminUserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/users", tags=["admin", "users"])


class ChangeRoleRequest(BaseModel):
    """Request model for changing user role"""
    newRole: str
    reason: str

    @validator("newRole")
    def validate_role(cls, v):
        valid_roles = ["customer", "partner", "support", "admin"]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v

    @validator("reason")
    def validate_reason(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("Reason must be at least 10 characters long")
        return v.strip()


class DeactivateUserRequest(BaseModel):
    """Request model for deactivating user"""
    reason: Optional[str] = None


class ReactivateUserRequest(BaseModel):
    """Request model for reactivating user"""
    reason: Optional[str] = None


class UpdateUserRequest(BaseModel):
    """Request model for updating user details"""
    name: Optional[str] = None
    mobile: Optional[str] = None

    @validator("name")
    def validate_name(cls, v):
        if v is not None:
            name_stripped = v.strip()
            if len(name_stripped) < 1:
                raise ValueError("Name cannot be empty")
            # Split name to check first name exists
            name_parts = name_stripped.split(None, 1)
            if not name_parts[0]:
                raise ValueError("First name is required")
        return v


@router.get(
    "",
    dependencies=[Depends(require_permission("users", "view"))],
    response_model=Dict[str, Any]
)
async def list_users(
    limit: int = Query(50, ge=1, le=100, description="Number of users per page"),
    offset: int = Query(0, ge=0, description="Number of users to skip"),
    role: Optional[str] = Query(None, description="Filter by role"),
    user_status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    sort_by: str = Query("createdAt", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List all users with filtering, pagination, and search

    **Required Permission:** users.view

    **Query Parameters:**
    - limit: Number of users per page (1-100, default 50)
    - offset: Number of users to skip (for pagination)
    - role: Filter by role (customer, partner, support, admin)
    - status: Filter by status (active, inactive, suspended)
    - search: Search by email or name (case-insensitive)
    - sort_by: Field to sort by (createdAt, email, role)
    - sort_order: Sort order (asc, desc)

    **Returns:**
    - users: List of user objects
    - total: Total number of users matching filters
    - limit: Page size
    - offset: Current offset
    - hasMore: Whether there are more results
    """
    try:
        result = await AdminUserService.list_users(
            limit=limit,
            offset=offset,
            role=role,
            status=user_status,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return result

    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.get(
    "/statistics",
    dependencies=[Depends(require_permission("users", "view"))],
    response_model=Dict[str, Any]
)
async def get_user_statistics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get user statistics for admin dashboard

    **Required Permission:** users.view

    **Returns:**
    - total: Total number of users
    - byRole: User counts by role
    - byStatus: User counts by status
    - recentSignups: Number of signups in last 7 days
    """
    try:
        stats = await AdminUserService.get_statistics()
        return stats

    except Exception as e:
        logger.error(f"Error getting user statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )


@router.get(
    "/{user_id}",
    dependencies=[Depends(require_permission("users", "view"))],
    response_model=Dict[str, Any]
)
async def get_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get detailed user information by ID

    **Required Permission:** users.view

    **Returns:**
    - User data including audit history
    """
    try:
        user = await AdminUserService.get_user(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )


@router.put(
    "/{user_id}",
    dependencies=[Depends(require_permission("users", "edit"))],
    response_model=Dict[str, Any]
)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update user details (name and mobile)

    **Required Permission:** users.edit

    **Request Body:**
    - name: Full name (first and last name)
    - mobile: Mobile number (optional, can be null to clear)

    **Returns:**
    - Updated user data
    """
    try:
        updated_user = await AdminUserService.update_user(
            user_id=user_id,
            admin_id=current_user["id"],
            admin_email=current_user["email"],
            name=request.name,
            mobile=request.mobile
        )

        return updated_user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.put(
    "/{user_id}/role",
    dependencies=[Depends(require_permission("users", "change_role"))],
    response_model=Dict[str, Any]
)
async def change_user_role(
    user_id: str,
    request: ChangeRoleRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Change a user's role

    **Required Permission:** users.change_role

    **Request Body:**
    - newRole: New role (customer, partner, support, admin)
    - reason: Reason for the role change (min 10 characters)

    **Validations:**
    - Cannot change your own role
    - Reason must be at least 10 characters
    - New role must be valid

    **Returns:**
    - Updated user data
    """
    try:
        updated_user = await AdminUserService.change_user_role(
            user_id=user_id,
            new_role=request.newRole,
            admin_id=current_user["id"],
            admin_email=current_user["email"],
            reason=request.reason
        )

        return updated_user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error changing role for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change user role"
        )


@router.put(
    "/{user_id}/deactivate",
    dependencies=[Depends(require_permission("users", "deactivate"))],
    response_model=Dict[str, Any]
)
async def deactivate_user(
    user_id: str,
    request: DeactivateUserRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Deactivate a user account

    **Required Permission:** users.deactivate

    **Request Body:**
    - reason: Optional reason for deactivation

    **Validations:**
    - Cannot deactivate your own account
    - Cannot deactivate another admin

    **Returns:**
    - Updated user data
    """
    try:
        updated_user = await AdminUserService.deactivate_user(
            user_id=user_id,
            admin_id=current_user["id"],
            admin_email=current_user["email"],
            reason=request.reason
        )

        return updated_user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deactivating user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )


@router.put(
    "/{user_id}/reactivate",
    dependencies=[Depends(require_permission("users", "deactivate"))],
    response_model=Dict[str, Any]
)
async def reactivate_user(
    user_id: str,
    request: ReactivateUserRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Reactivate a user account

    **Required Permission:** users.deactivate (same as deactivate)

    **Request Body:**
    - reason: Optional reason for reactivation

    **Returns:**
    - Updated user data
    """
    try:
        updated_user = await AdminUserService.reactivate_user(
            user_id=user_id,
            admin_id=current_user["id"],
            admin_email=current_user["email"],
            reason=request.reason
        )

        return updated_user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error reactivating user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate user"
        )
