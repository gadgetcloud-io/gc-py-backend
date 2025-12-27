"""
Admin Audit Log Router

Provides endpoints for querying audit logs.
All endpoints require appropriate permissions.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.core.security import get_current_user, require_permission
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/audit-logs", tags=["admin", "audit"])


@router.get(
    "/{log_id}",
    dependencies=[Depends(require_permission("audit_logs", "view"))],
    response_model=Dict[str, Any]
)
async def get_audit_log(
    log_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a single audit log entry by ID

    **Required Permission:** audit_logs.view

    **Path Parameters:**
    - log_id: The Firestore document ID of the audit log

    **Returns:**
    - Single audit log entry with all details
    """
    try:
        log = await AuditService.get_audit_log_by_id(log_id)

        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit log not found: {log_id}"
            )

        # Support staff can only view logs where they are the actor
        if current_user.get("role") == "support":
            if log.get("actorId") != current_user.get("id"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Support staff can only view their own audit logs"
                )

        return log

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audit log {log_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit log"
        )


@router.get(
    "",
    dependencies=[Depends(require_permission("audit_logs", "view"))],
    response_model=List[Dict[str, Any]]
)
async def get_audit_logs(
    limit: int = Query(50, ge=1, le=100, description="Number of logs per page"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    actor_id: Optional[str] = Query(None, description="Filter by actor (user who performed action)"),
    target_id: Optional[str] = Query(None, description="Filter by target (user affected)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Query audit logs with filtering and pagination

    **Required Permission:** audit_logs.view

    **Query Parameters:**
    - limit: Number of logs per page (1-100, default 50)
    - offset: Number of logs to skip (for pagination)
    - event_type: Filter by event type (e.g., user.role_changed, user.deactivated)
    - actor_id: Filter by actor (user who performed action)
    - target_id: Filter by target (user who was affected)

    **Returns:**
    - List of audit log entries
    """
    try:
        # Support staff can only view their own actions
        if current_user.get("role") == "support":
            actor_id = current_user.get("id")

        logs = await AuditService.get_audit_logs(
            limit=limit,
            offset=offset,
            event_type=event_type,
            actor_id=actor_id,
            target_id=target_id
        )

        return logs

    except Exception as e:
        logger.error(f"Error querying audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query audit logs"
        )


@router.get(
    "/user/{user_id}",
    dependencies=[Depends(require_permission("audit_logs", "view"))],
    response_model=List[Dict[str, Any]]
)
async def get_user_audit_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of logs to return"),
    include_as_actor: bool = Query(True, description="Include logs where user was the actor"),
    include_as_target: bool = Query(True, description="Include logs where user was the target"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all audit logs related to a specific user

    **Required Permission:** audit_logs.view

    **Query Parameters:**
    - limit: Maximum number of logs to return (1-100, default 50)
    - include_as_actor: Include logs where user was the actor (default true)
    - include_as_target: Include logs where user was the target (default true)

    **Returns:**
    - List of audit log entries related to the user
    """
    try:
        # Support staff can only view their own audit history
        if current_user.get("role") == "support" and user_id != current_user.get("id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Support staff can only view their own audit history"
            )

        logs = await AuditService.get_user_audit_history(
            user_id=user_id,
            limit=limit,
            include_as_actor=include_as_actor,
            include_as_target=include_as_target
        )

        return logs

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit history for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user audit history"
        )


@router.get(
    "/recent",
    dependencies=[Depends(require_permission("audit_logs", "view"))],
    response_model=List[Dict[str, Any]]
)
async def get_recent_audit_logs(
    limit: int = Query(20, ge=1, le=50, description="Number of recent logs to return"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the most recent audit logs (for admin dashboard)

    **Required Permission:** audit_logs.view

    **Query Parameters:**
    - limit: Number of recent logs to return (1-50, default 20)

    **Returns:**
    - List of recent audit log entries
    """
    try:
        # Support staff can only view their own actions
        if current_user.get("role") == "support":
            logs = await AuditService.get_audit_logs(
                actor_id=current_user.get("id"),
                limit=limit
            )
        else:
            logs = await AuditService.get_recent_audit_logs(limit=limit)

        return logs

    except Exception as e:
        logger.error(f"Error getting recent audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recent audit logs"
        )


@router.get(
    "/statistics",
    dependencies=[Depends(require_permission("audit_logs", "view"))],
    response_model=Dict[str, Any]
)
async def get_audit_statistics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get audit log statistics for admin dashboard

    **Required Permission:** audit_logs.view

    **Returns:**
    - Statistics about audit logs (counts by event type, recent activity, etc.)
    """
    try:
        # Count different event types
        stats = {
            "roleChanges": await AuditService.count_audit_logs(
                event_type=AuditService.EVENT_USER_ROLE_CHANGED
            ),
            "deactivations": await AuditService.count_audit_logs(
                event_type=AuditService.EVENT_USER_DEACTIVATED
            ),
            "reactivations": await AuditService.count_audit_logs(
                event_type=AuditService.EVENT_USER_REACTIVATED
            ),
            "permissionDenials": await AuditService.count_audit_logs(
                event_type=AuditService.EVENT_PERMISSION_DENIED
            ),
            "total": await AuditService.count_audit_logs()
        }

        return stats

    except Exception as e:
        logger.error(f"Error getting audit statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit statistics"
        )
