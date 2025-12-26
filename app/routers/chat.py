"""
Chat Router - AI features disabled
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request from frontend"""
    query: str
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response to frontend"""
    response: str
    agent_used: bool = False
    tool_calls: Optional[list] = None
    model: Optional[str] = None
    iterations: Optional[int] = None
    error: Optional[str] = None


@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest):
    """
    Chat endpoint - AI features disabled
    """
    return ChatResponse(
        response="AI features are currently disabled. Please use the REST API endpoints for device and repair management.",
        agent_used=False
    )


@router.get("/capabilities")
async def get_capabilities():
    """
    Return information about agent capabilities
    """
    return {
        "enabled": False,
        "model": None,
        "tools": [],
        "features": []
    }
