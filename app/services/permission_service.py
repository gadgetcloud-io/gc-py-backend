"""
Permission Service - Role-based permission management
"""

from typing import Dict, Any, List, Optional
from google.cloud import firestore
import logging
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Firestore client
db = firestore.Client(project=settings.PROJECT_ID, database=settings.FIRESTORE_DATABASE)


class PermissionService:
    """Service for managing role-based permissions"""

    COLLECTION = "gc-permissions"

    # In-memory cache for permissions (invalidates after 5 minutes)
    _permissions_cache: Dict[str, Dict[str, Any]] = {}
    _cache_timestamp: Optional[datetime] = None
    _cache_ttl_seconds = 300  # 5 minutes

    @classmethod
    async def get_role_permissions(cls, role: str) -> Optional[Dict[str, Any]]:
        """
        Get permissions for a specific role

        Args:
            role: Role name (customer, partner, support, admin)

        Returns:
            Permission data for the role, or None if not found
        """
        # Check cache first
        if cls._is_cache_valid() and role in cls._permissions_cache:
            logger.debug(f"Cache hit for role: {role}")
            return cls._permissions_cache[role]

        # Fetch from Firestore
        doc_ref = db.collection(cls.COLLECTION).document(role)
        doc = doc_ref.get()

        if doc.exists:
            permissions = doc.to_dict()

            # Update cache
            cls._permissions_cache[role] = permissions
            if not cls._cache_timestamp:
                cls._cache_timestamp = datetime.utcnow()

            logger.debug(f"Loaded permissions for role: {role}")
            return permissions

        logger.warning(f"No permissions found for role: {role}")
        return None

    @classmethod
    async def check_permission(cls, role: str, resource: str, action: str) -> bool:
        """
        Check if a role has permission to perform an action on a resource

        Args:
            role: User role (customer, partner, support, admin)
            resource: Resource name (users, items, audit_logs, etc.)
            action: Action name (view, create, edit, delete, etc.)

        Returns:
            True if permission granted, False otherwise

        Example:
            has_perm = await PermissionService.check_permission("admin", "users", "edit")
        """
        permissions = await cls.get_role_permissions(role)

        if not permissions:
            logger.warning(f"Permission denied: role '{role}' not found")
            return False

        # Get resource permissions
        resource_perms = permissions.get("resources", {}).get(resource, {})

        if not resource_perms:
            logger.debug(f"Permission denied: role '{role}' has no access to resource '{resource}'")
            return False

        # Check if action is allowed
        allowed_actions = resource_perms.get("actions", [])

        if action in allowed_actions or "*" in allowed_actions:
            logger.debug(f"Permission granted: {role} can {action} {resource}")
            return True

        logger.debug(f"Permission denied: {role} cannot {action} {resource}")
        return False

    @classmethod
    async def get_all_permissions(cls) -> List[Dict[str, Any]]:
        """
        Get all role permissions from Firestore

        Returns:
            List of all permission documents
        """
        docs = db.collection(cls.COLLECTION).stream()

        permissions = []
        for doc in docs:
            perm_data = doc.to_dict()
            perm_data["role"] = doc.id
            permissions.append(perm_data)

        return permissions

    @classmethod
    def invalidate_cache(cls):
        """
        Invalidate the permissions cache

        Call this after updating permissions in Firestore
        """
        cls._permissions_cache.clear()
        cls._cache_timestamp = None
        logger.info("Permission cache invalidated")

    @classmethod
    def _is_cache_valid(cls) -> bool:
        """
        Check if the permission cache is still valid

        Returns:
            True if cache is valid, False if expired
        """
        if not cls._cache_timestamp:
            return False

        age = datetime.utcnow() - cls._cache_timestamp
        return age.total_seconds() < cls._cache_ttl_seconds

    @classmethod
    async def create_role_permissions(
        cls,
        role: str,
        description: str,
        resources: Dict[str, Dict[str, List[str]]]
    ) -> Dict[str, Any]:
        """
        Create or update permissions for a role

        Args:
            role: Role name (customer, partner, support, admin)
            description: Human-readable description of the role
            resources: Dictionary mapping resources to allowed actions

        Example:
            await PermissionService.create_role_permissions(
                role="admin",
                description="Full system access",
                resources={
                    "users": {"actions": ["view", "create", "edit", "delete"]},
                    "items": {"actions": ["view", "create", "edit", "delete"]},
                    "audit_logs": {"actions": ["view"]}
                }
            )

        Returns:
            Created permission data
        """
        permission_data = {
            "role": role,
            "description": description,
            "resources": resources,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP
        }

        doc_ref = db.collection(cls.COLLECTION).document(role)
        doc_ref.set(permission_data)

        # Invalidate cache
        cls.invalidate_cache()

        logger.info(f"Created/updated permissions for role: {role}")

        return permission_data
