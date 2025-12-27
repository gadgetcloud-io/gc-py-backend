"""
Audit Service - Comprehensive audit logging for admin actions
"""

from typing import Dict, Any, List, Optional
from google.cloud import firestore
from datetime import datetime
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Firestore client
db = firestore.Client(project=settings.PROJECT_ID, database=settings.FIRESTORE_DATABASE)


class AuditService:
    """Service for logging audit events"""

    COLLECTION = "gc-audit-logs"

    # Event types
    EVENT_USER_ROLE_CHANGED = "user.role_changed"
    EVENT_USER_DEACTIVATED = "user.deactivated"
    EVENT_USER_REACTIVATED = "user.reactivated"
    EVENT_USER_CREATED = "user.created"
    EVENT_USER_UPDATED = "user.updated"
    EVENT_USER_DELETED = "user.deleted"
    EVENT_PASSWORD_CHANGED = "user.password_changed"
    EVENT_LOGIN_SUCCESS = "auth.login_success"
    EVENT_LOGIN_FAILED = "auth.login_failed"
    EVENT_PERMISSION_DENIED = "auth.permission_denied"

    @classmethod
    async def log_event(
        cls,
        event_type: str,
        actor_id: str,
        actor_email: str,
        target_id: Optional[str] = None,
        target_email: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an audit event to Firestore

        Args:
            event_type: Type of event (use EVENT_* constants)
            actor_id: ID of user performing the action
            actor_email: Email of user performing the action
            target_id: ID of user being acted upon (optional)
            target_email: Email of user being acted upon (optional)
            changes: Dictionary of changed fields with old and new values
            reason: Reason provided for the action (optional)
            metadata: Additional metadata (optional)

        Returns:
            ID of the created audit log document

        Example:
            await AuditService.log_event(
                event_type=AuditService.EVENT_USER_ROLE_CHANGED,
                actor_id="111A",
                actor_email="admin@example.com",
                target_id="111B",
                target_email="user@example.com",
                changes={
                    "role": {"old": "customer", "new": "partner"}
                },
                reason="User requested partner access",
                metadata={"ip_address": "192.168.1.1"}
            )
        """
        audit_data = {
            "eventType": event_type,
            "actorId": actor_id,
            "actorEmail": actor_email,
            "timestamp": firestore.SERVER_TIMESTAMP,
        }

        # Add optional fields
        if target_id:
            audit_data["targetId"] = target_id
        if target_email:
            audit_data["targetEmail"] = target_email
        if changes:
            audit_data["changes"] = changes
        if reason:
            audit_data["reason"] = reason
        if metadata:
            audit_data["metadata"] = metadata

        # Create audit log document
        doc_ref = db.collection(cls.COLLECTION).add(audit_data)
        audit_id = doc_ref[1].id

        logger.info(
            f"Audit log created: {event_type} by {actor_email} "
            f"(target: {target_email or 'N/A'}, id: {audit_id})"
        )

        return audit_id

    @classmethod
    async def get_audit_log_by_id(cls, log_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single audit log entry by document ID

        Args:
            log_id: Firestore document ID of the audit log

        Returns:
            Audit log document dict or None if not found
        """
        try:
            doc = db.collection(cls.COLLECTION).document(log_id).get()

            if not doc.exists:
                logger.warning(f"Audit log not found: {log_id}")
                return None

            log_data = doc.to_dict()
            log_data["id"] = doc.id

            # Convert Firestore timestamp to ISO string
            if "timestamp" in log_data and log_data["timestamp"]:
                log_data["timestamp"] = log_data["timestamp"].isoformat()

            logger.debug(f"Retrieved audit log: {log_id}")
            return log_data

        except Exception as e:
            logger.error(f"Error retrieving audit log {log_id}: {e}", exc_info=True)
            raise

    @classmethod
    async def get_audit_logs(
        cls,
        limit: int = 50,
        offset: int = 0,
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Query audit logs with filters and pagination

        Args:
            limit: Maximum number of logs to return (default 50, max 100)
            offset: Number of logs to skip
            event_type: Filter by event type
            actor_id: Filter by actor (user who performed action)
            target_id: Filter by target (user who was affected)
            start_date: Filter logs after this date
            end_date: Filter logs before this date

        Returns:
            List of audit log documents
        """
        # Validate limit
        limit = min(limit, 100)

        # Build query
        query = db.collection(cls.COLLECTION)

        # Apply filters
        if event_type:
            query = query.where("eventType", "==", event_type)
        if actor_id:
            query = query.where("actorId", "==", actor_id)
        if target_id:
            query = query.where("targetId", "==", target_id)
        if start_date:
            query = query.where("timestamp", ">=", start_date)
        if end_date:
            query = query.where("timestamp", "<=", end_date)

        # Order by timestamp descending (most recent first)
        query = query.order_by("timestamp", direction=firestore.Query.DESCENDING)

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        docs = query.stream()

        logs = []
        for doc in docs:
            log_data = doc.to_dict()
            log_data["id"] = doc.id

            # Convert Firestore timestamp to ISO string
            if "timestamp" in log_data and log_data["timestamp"]:
                log_data["timestamp"] = log_data["timestamp"].isoformat()

            logs.append(log_data)

        logger.debug(f"Retrieved {len(logs)} audit logs (filters applied: {bool(event_type or actor_id or target_id)})")

        return logs

    @classmethod
    async def get_user_audit_history(
        cls,
        user_id: str,
        limit: int = 50,
        include_as_actor: bool = True,
        include_as_target: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all audit logs related to a specific user

        Args:
            user_id: User ID to search for
            limit: Maximum number of logs to return
            include_as_actor: Include logs where user was the actor
            include_as_target: Include logs where user was the target

        Returns:
            List of audit log documents
        """
        logs = []

        if include_as_actor:
            actor_logs = await cls.get_audit_logs(actor_id=user_id, limit=limit)
            logs.extend(actor_logs)

        if include_as_target:
            target_logs = await cls.get_audit_logs(target_id=user_id, limit=limit)
            logs.extend(target_logs)

        # Remove duplicates and sort by timestamp
        unique_logs = {log["id"]: log for log in logs}.values()
        sorted_logs = sorted(
            unique_logs,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )

        return sorted_logs[:limit]

    @classmethod
    async def get_recent_audit_logs(cls, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get the most recent audit logs (for admin dashboard)

        Args:
            limit: Number of recent logs to return (default 20)

        Returns:
            List of recent audit log documents
        """
        return await cls.get_audit_logs(limit=limit)

    @classmethod
    async def count_audit_logs(
        cls,
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None
    ) -> int:
        """
        Count audit logs matching filters

        Args:
            event_type: Filter by event type
            actor_id: Filter by actor
            target_id: Filter by target

        Returns:
            Number of matching audit logs
        """
        query = db.collection(cls.COLLECTION)

        if event_type:
            query = query.where("eventType", "==", event_type)
        if actor_id:
            query = query.where("actorId", "==", actor_id)
        if target_id:
            query = query.where("targetId", "==", target_id)

        docs = list(query.stream())
        return len(docs)
