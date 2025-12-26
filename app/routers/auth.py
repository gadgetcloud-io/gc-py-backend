"""
Authentication Router
JWT-based authentication endpoints with Firestore integration
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, validator
from typing import Dict, Any
import logging

from app.core.security import (
    create_access_token,
    get_current_user,
    get_current_active_user
)
from app.core.validators import validate_indian_mobile
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    firstName: str
    lastName: str = ""
    mobile: str = ""

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    @validator("firstName")
    def validate_first_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("First name must be at least 2 characters long")
        return v.strip()

    @validator("lastName")
    def validate_last_name(cls, v):
        return v.strip()

    @validator("mobile")
    def validate_mobile(cls, v):
        """Validate Indian mobile number using shared validator"""
        return validate_indian_mobile(v)

    @property
    def name(self) -> str:
        """Compute full name from firstName and lastName"""
        if self.lastName:
            return f"{self.firstName} {self.lastName}"
        return self.firstName


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @validator("new_password")
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long")
        return v


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    User login endpoint

    Authenticates user with email and password, returns JWT token
    """
    logger.info(f"Login attempt: {request.email}")

    # Authenticate user
    user = await UserService.authenticate_user(request.email, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token
    token_data = {
        "sub": user["id"],
        "email": user["email"],
        "firstName": user.get("firstName", ""),
        "lastName": user.get("lastName", ""),
        "role": user["role"]
    }
    access_token = create_access_token(token_data)

    logger.info(f"Login successful: {request.email}")

    return TokenResponse(
        access_token=access_token,
        user={
            "id": user["id"],
            "email": user["email"],
            "firstName": user.get("firstName", ""),
            "lastName": user.get("lastName", ""),
            "role": user["role"],
            "status": user.get("status", "active")
        }
    )


@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest):
    """
    User signup endpoint

    Creates new user account and returns JWT token
    """
    logger.info(f"Signup attempt: {request.email}")

    try:
        # Create user in Firestore
        user = await UserService.create_user(
            email=request.email,
            password=request.password,
            first_name=request.firstName,
            last_name=request.lastName,
            mobile=request.mobile,
            role="customer"  # Default role for self-registration
        )

        # Create JWT token
        token_data = {
            "sub": user["id"],
            "email": user["email"],
            "firstName": user["firstName"],
            "lastName": user.get("lastName", ""),
            "role": user["role"]
        }
        access_token = create_access_token(token_data)

        logger.info(f"Signup successful: {request.email}")

        return TokenResponse(
            access_token=access_token,
            user={
                "id": user["id"],
                "email": user["email"],
                "firstName": user["firstName"],
                "lastName": user.get("lastName", ""),
                "role": user["role"],
                "status": user.get("status", "active")
            }
        )

    except ValueError as e:
        # User already exists
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Signup error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )


@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    User logout endpoint

    In a stateless JWT system, logout is handled client-side by removing the token.
    This endpoint can be used for audit logging.
    """
    logger.info(f"Logout: {current_user.get('email')}")

    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Get current user profile

    Returns user data from JWT token and Firestore
    """
    # Fetch fresh data from Firestore
    user_id = current_user.get("id")
    user = await UserService.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.put("/me")
async def update_current_user_profile(
    updates: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Update current user profile

    Allowed fields: name
    """
    user_id = current_user.get("id")

    # Only allow updating certain fields
    allowed_fields = {"name", "firstName", "lastName", "mobile"}
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

    if not filtered_updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )

    updated_user = await UserService.update_user(user_id, filtered_updates)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    logger.info(f"Profile updated: {current_user.get('email')}")

    return updated_user


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Change user password

    Requires old password for verification
    """
    user_id = current_user.get("id")

    success = await UserService.change_password(
        user_id,
        request.old_password,
        request.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )

    logger.info(f"Password changed: {current_user.get('email')}")

    return {"message": "Password changed successfully"}
