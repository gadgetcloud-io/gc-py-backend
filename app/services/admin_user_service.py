"""
Admin User Service - Administrative user management operations

This service provides admin-only operations for managing users,
including role changes, user deactivation, and bulk operations.
"""

from typing import Dict, Any, List, Optional
from google.cloud import firestore
from datetime import datetime
import logging

from app.core.config import settings
from app.services.user_service import UserService
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

# Initialize Firestore client
db = firestore.Client(project=settings.PROJECT_ID, database=settings.FIRESTORE_DATABASE)


class AdminUserService:
    """Service for administrative user management"""

    COLLECTION = "gc-users"
    VALID_ROLES = ["customer", "partner", "support", "admin"]
    VALID_STATUSES = ["active", "inactive", "suspended"]

    @classmethod
    async def list_users(
        cls,
        limit: int = 50,
        offset: int = 0,
        role: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "createdAt",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        List all users with filtering, pagination, and search

        Args:
            limit: Maximum number of users to return (default 50, max 100)
            offset: Number of users to skip
            role: Filter by role (customer, partner, support, admin)
            status: Filter by status (active, inactive, suspended)
            search: Search by email or name (case-insensitive)
            sort_by: Field to sort by (createdAt, email, role)
            sort_order: Sort order (asc, desc)

        Returns:
            Dictionary with users list and pagination metadata
        """
        # Validate limit
        limit = min(limit, 100)

        # Build query
        query = db.collection(cls.COLLECTION)

        # Apply filters
        if role:
            query = query.where("role", "==", role)
        if status:
            query = query.where("status", "==", status)

        # Get all documents matching filters (we'll do search client-side)
        docs = list(query.stream())

        # Convert to list of dicts for easier processing
        user_docs = []
        for doc in docs:
            user_data = doc.to_dict()
            user_data["id"] = doc.id
            user_docs.append(user_data)

        # Apply search filter client-side
        if search:
            search_lower = search.lower()
            user_docs = [
                doc for doc in user_docs
                if search_lower in doc.get("email", "").lower()
                or search_lower in doc.get("firstName", "").lower()
                or search_lower in doc.get("lastName", "").lower()
            ]

        # Sort client-side
        reverse = sort_order == "desc"
        if sort_by == "createdAt":
            def get_sortable_datetime(doc):
                value = doc.get(sort_by)
                if value is None:
                    return datetime.min
                # Handle both Firestore timestamp and ISO string
                if hasattr(value, 'timestamp'):
                    return value  # Firestore DatetimeWithNanoseconds
                elif isinstance(value, str):
                    try:
                        return datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except:
                        return datetime.min
                return datetime.min

            user_docs.sort(key=get_sortable_datetime, reverse=reverse)
        elif sort_by in ["email", "role", "status"]:
            user_docs.sort(
                key=lambda d: d.get(sort_by, "").lower(),
                reverse=reverse
            )

        # Apply pagination
        total_count = len(user_docs)
        paginated_docs = user_docs[offset:offset + limit]

        # Remove sensitive data from paginated results
        users = []
        for user_data in paginated_docs:
            # Remove sensitive data
            user_data.pop("passwordHash", None)
            users.append(user_data)

        return {
            "users": users,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "hasMore": offset + limit < total_count
        }

    @classmethod
    async def get_user(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed user information by ID

        Args:
            user_id: User document ID

        Returns:
            User data with audit history, or None if not found
        """
        # Get user data
        user = await UserService.get_user_by_id(user_id)

        if not user:
            return None

        # Get user's audit history
        audit_history = await AuditService.get_user_audit_history(
            user_id=user_id,
            limit=20,
            include_as_actor=True,
            include_as_target=True
        )

        user["auditHistory"] = audit_history

        return user

    @classmethod
    async def change_user_role(
        cls,
        user_id: str,
        new_role: str,
        admin_id: str,
        admin_email: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Change a user's role

        Args:
            user_id: User document ID
            new_role: New role (customer, partner, support, admin)
            admin_id: Admin user performing the change
            admin_email: Admin user email
            reason: Reason for the role change (required)

        Returns:
            Updated user data

        Raises:
            ValueError: If role is invalid, user not found, or trying to change own role
        """
        # Validate new role
        if new_role not in cls.VALID_ROLES:
            raise ValueError(f"Invalid role: {new_role}. Must be one of: {', '.join(cls.VALID_ROLES)}")

        # Validate reason
        if not reason or len(reason.strip()) < 10:
            raise ValueError("Reason must be at least 10 characters long")

        # Prevent self-role-change
        if user_id == admin_id:
            raise ValueError("Cannot change your own role")

        # Get current user data
        doc_ref = db.collection(cls.COLLECTION).document(user_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise ValueError(f"User not found: {user_id}")

        user_data = doc.to_dict()
        old_role = user_data.get("role")

        # Check if role is actually changing
        if old_role == new_role:
            raise ValueError(f"User already has role: {new_role}")

        # Update user role
        updates = {
            "role": new_role,
            "previousRole": old_role,
            "roleChangedAt": firestore.SERVER_TIMESTAMP,
            "roleChangedBy": admin_id,
            "updatedAt": firestore.SERVER_TIMESTAMP
        }

        doc_ref.update(updates)

        # Log to audit
        await AuditService.log_event(
            event_type=AuditService.EVENT_USER_ROLE_CHANGED,
            actor_id=admin_id,
            actor_email=admin_email,
            target_id=user_id,
            target_email=user_data.get("email"),
            changes={
                "role": {"old": old_role, "new": new_role}
            },
            reason=reason
        )

        logger.info(
            f"Role changed: {user_data.get('email')} "
            f"from {old_role} to {new_role} by {admin_email}"
        )

        # Return updated user
        return await UserService.get_user_by_id(user_id)

    @classmethod
    async def deactivate_user(
        cls,
        user_id: str,
        admin_id: str,
        admin_email: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deactivate a user account

        Args:
            user_id: User document ID
            admin_id: Admin user performing the action
            admin_email: Admin user email
            reason: Optional reason for deactivation

        Returns:
            Updated user data

        Raises:
            ValueError: If user not found or trying to deactivate another admin
        """
        # Get current user data
        doc_ref = db.collection(cls.COLLECTION).document(user_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise ValueError(f"User not found: {user_id}")

        user_data = doc.to_dict()

        # Prevent deactivating another admin
        if user_data.get("role") == "admin" and user_id != admin_id:
            raise ValueError("Cannot deactivate another admin user")

        # Prevent self-deactivation
        if user_id == admin_id:
            raise ValueError("Cannot deactivate your own account")

        old_status = user_data.get("status", "active")

        # Check if already inactive
        if old_status == "inactive":
            raise ValueError("User is already inactive")

        # Update user status
        updates = {
            "status": "inactive",
            "statusChangedAt": firestore.SERVER_TIMESTAMP,
            "statusChangedBy": admin_id,
            "updatedAt": firestore.SERVER_TIMESTAMP
        }

        doc_ref.update(updates)

        # Log to audit
        await AuditService.log_event(
            event_type=AuditService.EVENT_USER_DEACTIVATED,
            actor_id=admin_id,
            actor_email=admin_email,
            target_id=user_id,
            target_email=user_data.get("email"),
            changes={
                "status": {"old": old_status, "new": "inactive"}
            },
            reason=reason
        )

        logger.info(
            f"User deactivated: {user_data.get('email')} by {admin_email}"
        )

        # Return updated user
        return await UserService.get_user_by_id(user_id)

    @classmethod
    async def reactivate_user(
        cls,
        user_id: str,
        admin_id: str,
        admin_email: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reactivate a user account

        Args:
            user_id: User document ID
            admin_id: Admin user performing the action
            admin_email: Admin user email
            reason: Optional reason for reactivation

        Returns:
            Updated user data

        Raises:
            ValueError: If user not found
        """
        # Get current user data
        doc_ref = db.collection(cls.COLLECTION).document(user_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise ValueError(f"User not found: {user_id}")

        user_data = doc.to_dict()
        old_status = user_data.get("status", "inactive")

        # Check if already active
        if old_status == "active":
            raise ValueError("User is already active")

        # Update user status
        updates = {
            "status": "active",
            "statusChangedAt": firestore.SERVER_TIMESTAMP,
            "statusChangedBy": admin_id,
            "updatedAt": firestore.SERVER_TIMESTAMP
        }

        doc_ref.update(updates)

        # Log to audit
        await AuditService.log_event(
            event_type=AuditService.EVENT_USER_REACTIVATED,
            actor_id=admin_id,
            actor_email=admin_email,
            target_id=user_id,
            target_email=user_data.get("email"),
            changes={
                "status": {"old": old_status, "new": "active"}
            },
            reason=reason
        )

        logger.info(
            f"User reactivated: {user_data.get('email')} by {admin_email}"
        )

        # Return updated user
        return await UserService.get_user_by_id(user_id)

    @classmethod
    async def get_statistics(cls) -> Dict[str, Any]:
        """
        Get user statistics for admin dashboard

        Returns:
            Dictionary with user counts by role, status, etc.
        """
        all_users = db.collection(cls.COLLECTION).stream()

        stats = {
            "total": 0,
            "byRole": {"customer": 0, "partner": 0, "support": 0, "admin": 0},
            "byStatus": {"active": 0, "inactive": 0, "suspended": 0},
            "recentSignups": 0  # Last 7 days
        }

        seven_days_ago = datetime.utcnow().timestamp() - (7 * 24 * 60 * 60)

        for doc in all_users:
            stats["total"] += 1

            user_data = doc.to_dict()

            # Count by role
            role = user_data.get("role", "customer")
            if role in stats["byRole"]:
                stats["byRole"][role] += 1

            # Count by status
            status = user_data.get("status", "active")
            if status in stats["byStatus"]:
                stats["byStatus"][status] += 1

            # Count recent signups
            created_at = user_data.get("createdAt")
            if created_at and hasattr(created_at, "timestamp"):
                if created_at.timestamp() > seven_days_ago:
                    stats["recentSignups"] += 1

        return stats

    @classmethod
    async def update_user(
        cls,
        user_id: str,
        admin_id: str,
        admin_email: str,
        name: Optional[str] = None,
        mobile: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update user details (name, mobile, role, and status)

        Args:
            user_id: User document ID
            admin_id: Admin user performing the action
            admin_email: Admin user email
            name: Full name (will be split into firstName and lastName)
            mobile: Mobile number (optional, can be None to clear)
            role: User role (customer, partner, support, admin)
            status: Account status (active, inactive)
            reason: Reason for role/status change (required if role or status changes)

        Returns:
            Updated user data

        Raises:
            ValueError: If user not found or validation fails
        """
        # Get current user data
        doc_ref = db.collection(cls.COLLECTION).document(user_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise ValueError(f"User not found: {user_id}")

        user_data = doc.to_dict()
        updates = {"updatedAt": firestore.SERVER_TIMESTAMP}
        changes = {}

        # Check if role or status is changing (require reason)
        role_changing = role is not None and role != user_data.get("role")
        status_changing = status is not None and status != user_data.get("status")

        if (role_changing or status_changing) and (not reason or len(reason.strip()) < 10):
            raise ValueError("Reason is required (minimum 10 characters) when changing role or status")

        # Update name if provided
        if name is not None:
            name_parts = name.strip().split(None, 1)  # Split on first whitespace
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            if not first_name:
                raise ValueError("First name is required")

            old_first_name = user_data.get("firstName", "")
            old_last_name = user_data.get("lastName", "")

            if first_name != old_first_name or last_name != old_last_name:
                updates["firstName"] = first_name
                updates["lastName"] = last_name
                changes["name"] = {
                    "old": f"{old_first_name} {old_last_name}".strip(),
                    "new": f"{first_name} {last_name}".strip()
                }

        # Update mobile if provided (can be None to clear)
        if mobile is not None:
            old_mobile = user_data.get("mobile", "")

            # Normalize mobile number (empty string means clear)
            from app.core.validators import validate_indian_mobile
            mobile_normalized = validate_indian_mobile(mobile) if mobile else None

            if mobile_normalized != old_mobile:
                updates["mobile"] = mobile_normalized
                changes["mobile"] = {
                    "old": old_mobile or None,
                    "new": mobile_normalized
                }

        # Update role if provided
        if role_changing:
            # Validate role
            if role not in cls.VALID_ROLES:
                raise ValueError(f"Invalid role: {role}. Must be one of: {', '.join(cls.VALID_ROLES)}")

            # Prevent self-role-change
            if user_id == admin_id:
                raise ValueError("Cannot change your own role")

            old_role = user_data.get("role")
            updates["role"] = role
            updates["previousRole"] = old_role
            updates["roleChangedAt"] = firestore.SERVER_TIMESTAMP
            updates["roleChangedBy"] = admin_id
            changes["role"] = {"old": old_role, "new": role}

        # Update status if provided
        if status_changing:
            # Validate status
            if status not in cls.VALID_STATUSES:
                raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join(cls.VALID_STATUSES)}")

            # Prevent deactivating another admin
            if status == "inactive" and user_data.get("role") == "admin" and user_id != admin_id:
                raise ValueError("Cannot deactivate another admin user")

            # Prevent self-deactivation
            if status == "inactive" and user_id == admin_id:
                raise ValueError("Cannot deactivate your own account")

            old_status = user_data.get("status", "active")
            updates["status"] = status
            updates["statusChangedAt"] = firestore.SERVER_TIMESTAMP
            updates["statusChangedBy"] = admin_id
            changes["status"] = {"old": old_status, "new": status}

        # If no changes, return current user
        if not changes:
            return await UserService.get_user_by_id(user_id)

        # Update user
        doc_ref.update(updates)

        # Determine event type and reason
        event_type = AuditService.EVENT_USER_UPDATED
        audit_reason = reason.strip() if reason else "User details updated by admin"

        if role_changing and status_changing:
            audit_reason = f"Role and status changed: {audit_reason}"
        elif role_changing:
            event_type = AuditService.EVENT_USER_ROLE_CHANGED
            audit_reason = f"Role changed: {audit_reason}"
        elif status_changing:
            if status == "inactive":
                event_type = AuditService.EVENT_USER_DEACTIVATED
                audit_reason = f"User deactivated: {audit_reason}"
            else:
                event_type = AuditService.EVENT_USER_REACTIVATED
                audit_reason = f"User reactivated: {audit_reason}"

        # Log to audit
        await AuditService.log_event(
            event_type=event_type,
            actor_id=admin_id,
            actor_email=admin_email,
            target_id=user_id,
            target_email=user_data.get("email"),
            changes=changes,
            reason=audit_reason
        )

        logger.info(
            f"User updated: {user_data.get('email')} by {admin_email}. "
            f"Changes: {list(changes.keys())}"
        )

        # Return updated user
        return await UserService.get_user_by_id(user_id)
