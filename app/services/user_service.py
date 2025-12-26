"""
User Service - Firestore user management
"""

from typing import Optional, Dict, Any
from google.cloud import firestore
from datetime import datetime
import logging

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.core.id_generator import generate_encoded_sequential_id
from app.core.validators import validate_indian_mobile

logger = logging.getLogger(__name__)

# Initialize Firestore client
db = firestore.Client(project=settings.PROJECT_ID, database=settings.FIRESTORE_DATABASE)


class UserService:
    """Service for managing users in Firestore"""

    COLLECTION = "gc-users"

    @classmethod
    async def create_user(
        cls,
        email: str,
        password: str,
        name: str,
        role: str = "customer",
        first_name: str = "",
        last_name: str = "",
        mobile: str = ""
    ) -> Dict[str, Any]:
        """
        Create a new user in Firestore

        Args:
            email: User email (must be unique)
            password: Plain text password (will be hashed)
            name: User's display name (full name)
            role: User role (customer, partner, support, admin)
            first_name: User's first name (optional)
            last_name: User's last name (optional)
            mobile: User's mobile/phone number (optional)

        Returns:
            Created user data (without password hash)

        Raises:
            ValueError: If user with email already exists
        """
        # Check if user already exists
        existing_user = await cls.get_user_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Hash password
        password_hash = hash_password(password)

        # Validate and normalize mobile number
        mobile_normalized = validate_indian_mobile(mobile)

        # Generate encoded sequential user ID (4-6 chars, e.g., "1112", "112j", "11JF")
        user_id = generate_encoded_sequential_id(db, "user_id", min_length=4)

        # Create user document
        user_data = {
            "email": email,
            "passwordHash": password_hash,
            "name": name,
            "firstName": first_name,
            "lastName": last_name,
            "mobile": mobile_normalized,
            "role": role,
            "status": "active",
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP
        }

        # Add to Firestore with ULID as document ID
        doc_ref = db.collection(cls.COLLECTION).document(user_id)
        doc_ref.set(user_data)

        logger.info(f"Created user: {email} with ID: {user_id}")

        # Return user data without password
        return {
            "id": doc_ref.id,
            "email": email,
            "name": name,
            "firstName": first_name,
            "lastName": last_name,
            "mobile": mobile_normalized,
            "role": role,
            "status": "active",
            "createdAt": datetime.utcnow().isoformat()
        }

    @classmethod
    async def get_user_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email

        Args:
            email: User email

        Returns:
            User data including ID and password hash, or None if not found
        """
        users_ref = db.collection(cls.COLLECTION)
        query = users_ref.where("email", "==", email).limit(1)
        docs = query.stream()

        for doc in docs:
            user_data = doc.to_dict()
            user_data["id"] = doc.id
            return user_data

        return None

    @classmethod
    async def get_user_by_id(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID

        Args:
            user_id: User document ID

        Returns:
            User data without password hash, or None if not found
        """
        doc_ref = db.collection(cls.COLLECTION).document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            user_data = doc.to_dict()
            user_data["id"] = doc.id

            # Remove password hash from response
            user_data.pop("passwordHash", None)

            return user_data

        return None

    @classmethod
    async def authenticate_user(cls, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with email and password

        Args:
            email: User email
            password: Plain text password

        Returns:
            User data (without password hash) if authenticated, None otherwise
        """
        user = await cls.get_user_by_email(email)

        if not user:
            logger.warning(f"Authentication failed: user not found - {email}")
            return None

        password_hash = user.get("passwordHash")
        if not password_hash:
            logger.error(f"User {email} has no password hash")
            return None

        if not verify_password(password, password_hash):
            logger.warning(f"Authentication failed: invalid password - {email}")
            return None

        # Check user status
        if user.get("status") != "active":
            logger.warning(f"Authentication failed: user not active - {email}")
            return None

        logger.info(f"User authenticated successfully: {email}")

        # Remove password hash before returning
        user.pop("passwordHash", None)

        return user

    @classmethod
    async def update_user(cls, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update user data

        Args:
            user_id: User document ID
            updates: Dictionary of fields to update

        Returns:
            Updated user data, or None if user not found
        """
        doc_ref = db.collection(cls.COLLECTION).document(user_id)

        # Add timestamp
        updates["updatedAt"] = firestore.SERVER_TIMESTAMP

        # Don't allow updating certain fields
        forbidden_fields = ["id", "createdAt", "passwordHash"]
        for field in forbidden_fields:
            updates.pop(field, None)

        doc_ref.update(updates)
        logger.info(f"Updated user: {user_id}")

        return await cls.get_user_by_id(user_id)

    @classmethod
    async def change_password(cls, user_id: str, old_password: str, new_password: str) -> bool:
        """
        Change user password

        Args:
            user_id: User document ID
            old_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully, False otherwise
        """
        # Get user with password hash
        doc_ref = db.collection(cls.COLLECTION).document(user_id)
        doc = doc_ref.get()

        if not doc.exists:
            return False

        user_data = doc.to_dict()
        password_hash = user_data.get("passwordHash")

        # Verify old password
        if not verify_password(old_password, password_hash):
            logger.warning(f"Password change failed: invalid old password - {user_id}")
            return False

        # Hash new password
        new_password_hash = hash_password(new_password)

        # Update password
        doc_ref.update({
            "passwordHash": new_password_hash,
            "updatedAt": firestore.SERVER_TIMESTAMP
        })

        logger.info(f"Password changed successfully for user: {user_id}")
        return True

    @classmethod
    async def delete_user(cls, user_id: str) -> bool:
        """
        Soft delete user (set status to 'deleted')

        Args:
            user_id: User document ID

        Returns:
            True if deleted successfully, False otherwise
        """
        doc_ref = db.collection(cls.COLLECTION).document(user_id)

        if not doc_ref.get().exists:
            return False

        doc_ref.update({
            "status": "deleted",
            "updatedAt": firestore.SERVER_TIMESTAMP
        })

        logger.info(f"User soft-deleted: {user_id}")
        return True
