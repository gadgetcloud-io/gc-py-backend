"""
Authentication Router
JWT-based authentication endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    User login endpoint

    TODO: Implement actual authentication with Firestore
    TODO: Generate JWT token
    """

    logger.info(f"Login attempt: {request.email}")

    # Mock response for MVP
    return TokenResponse(
        access_token="mock_jwt_token_12345",
        user={
            "id": "user-123",
            "email": request.email,
            "name": "Test User",
            "role": "customer"
        }
    )


@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest):
    """
    User signup endpoint

    TODO: Implement user creation in Firestore
    TODO: Hash password
    TODO: Generate JWT token
    """

    logger.info(f"Signup attempt: {request.email}")

    # Mock response for MVP
    return TokenResponse(
        access_token="mock_jwt_token_12345",
        user={
            "id": "user-new",
            "email": request.email,
            "name": request.name,
            "role": "customer"
        }
    )


@router.post("/logout")
async def logout():
    """
    User logout endpoint

    TODO: Invalidate token (add to blacklist)
    """

    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user():
    """
    Get current user profile

    TODO: Extract from JWT token
    TODO: Fetch from Firestore
    """

    # Mock response for MVP
    return {
        "id": "user-123",
        "email": "user@example.com",
        "name": "Test User",
        "role": "customer"
    }
