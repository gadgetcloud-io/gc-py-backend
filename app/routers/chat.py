"""
AI Chat Router - Agent-powered chat interface
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from app.agents.orchestrator import orchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request from frontend"""
    query: str
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response to frontend"""
    response: str
    agent_used: bool
    tool_calls: Optional[list] = None
    model: Optional[str] = None
    iterations: Optional[int] = None
    error: Optional[str] = None


@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest):
    """
    Process a natural language query using the agent

    Example queries:
    - "Show me my devices that need repair"
    - "Book a repair for my iPhone screen"
    - "Check the status of repair booking #12345"
    """

    try:
        # TODO: Extract user_id from JWT token
        user_id = "user-123"  # Mock for MVP

        logger.info(f"Chat query from {user_id}: {request.query}")

        # Execute agent
        result = await orchestrator.execute(
            user_query=request.query,
            user_id=user_id,
            context=request.context
        )

        return ChatResponse(**result)

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def get_capabilities():
    """
    Return information about agent capabilities
    """

    return {
        "enabled": bool(orchestrator.client),
        "model": orchestrator.model if orchestrator.client else None,
        "tools": [
            "search_items",
            "get_item_details",
            "book_repair",
            "check_repair_status"
        ],
        "features": [
            "Natural language search",
            "Repair booking assistance",
            "Status inquiries",
            "Device recommendations"
        ]
    }
