"""
Agent Tools - Functions that the AI agent can call
Each tool provides access to specific backend functionality
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    Define tools available to the AI agent
    These are presented to Claude in the API call
    """

    return [
        {
            "name": "search_items",
            "description": "Search for gadgets/items in the user's inventory. Use this when the user asks about their devices, gadgets, or items.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (device name, brand, category, etc.)"
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category filter (phone, laptop, tablet, etc.)",
                        "enum": ["phone", "laptop", "tablet", "watch", "camera", "other"]
                    },
                    "status": {
                        "type": "string",
                        "description": "Optional status filter",
                        "enum": ["active", "in_repair", "warranty_expired", "sold"]
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "get_item_details",
            "description": "Get detailed information about a specific item by ID",
            "input_schema": {
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "string",
                        "description": "The unique ID of the item"
                    }
                },
                "required": ["item_id"]
            }
        },
        {
            "name": "book_repair",
            "description": "Book a repair appointment for a device",
            "input_schema": {
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "string",
                        "description": "ID of the item to repair"
                    },
                    "issue_description": {
                        "type": "string",
                        "description": "Description of the issue"
                    },
                    "preferred_date": {
                        "type": "string",
                        "description": "Preferred date for repair (YYYY-MM-DD format)"
                    }
                },
                "required": ["item_id", "issue_description"]
            }
        },
        {
            "name": "check_repair_status",
            "description": "Check the status of a repair booking",
            "input_schema": {
                "type": "object",
                "properties": {
                    "repair_id": {
                        "type": "string",
                        "description": "The repair booking ID"
                    }
                },
                "required": ["repair_id"]
            }
        }
    ]


async def execute_tool(tool_name: str, tool_input: Dict[str, Any], user_id: str = None) -> Any:
    """
    Execute a tool and return the result

    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters for the tool
        user_id: Optional user ID for authentication/context

    Returns:
        Tool execution result
    """

    logger.info(f"Executing tool: {tool_name} with input: {tool_input}")

    # Route to appropriate tool handler
    if tool_name == "search_items":
        return await _search_items(tool_input, user_id)
    elif tool_name == "get_item_details":
        return await _get_item_details(tool_input, user_id)
    elif tool_name == "book_repair":
        return await _book_repair(tool_input, user_id)
    elif tool_name == "check_repair_status":
        return await _check_repair_status(tool_input, user_id)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


# Tool implementations (MVP - returns mock data)
# TODO: Connect to actual Firestore/services

async def _search_items(input: Dict, user_id: str) -> Dict:
    """Search for items - MVP implementation"""

    query = input.get("query", "")
    category = input.get("category")
    status = input.get("status")

    # Mock data for demonstration
    mock_items = [
        {
            "id": "item-001",
            "name": "iPhone 14 Pro",
            "category": "phone",
            "brand": "Apple",
            "status": "active",
            "warranty_expires": "2025-09-15"
        },
        {
            "id": "item-002",
            "name": "MacBook Pro 16\"",
            "category": "laptop",
            "brand": "Apple",
            "status": "in_repair",
            "current_issue": "Screen replacement"
        }
    ]

    # Simple filtering logic
    results = mock_items

    if category:
        results = [item for item in results if item["category"] == category]

    if status:
        results = [item for item in results if item["status"] == status]

    return {
        "items": results,
        "count": len(results),
        "query": query
    }


async def _get_item_details(input: Dict, user_id: str) -> Dict:
    """Get item details - MVP implementation"""

    item_id = input["item_id"]

    # Mock data
    mock_item = {
        "id": item_id,
        "name": "iPhone 14 Pro",
        "category": "phone",
        "brand": "Apple",
        "model": "A2890",
        "purchase_date": "2023-09-15",
        "warranty_expires": "2025-09-15",
        "status": "active",
        "repairs": [
            {
                "id": "repair-001",
                "date": "2024-03-20",
                "issue": "Battery replacement",
                "status": "completed"
            }
        ]
    }

    return mock_item


async def _book_repair(input: Dict, user_id: str) -> Dict:
    """Book repair - MVP implementation"""

    item_id = input["item_id"]
    issue_description = input["issue_description"]
    preferred_date = input.get("preferred_date", "TBD")

    # Mock booking
    booking = {
        "booking_id": "repair-002",
        "item_id": item_id,
        "issue": issue_description,
        "preferred_date": preferred_date,
        "status": "pending",
        "confirmation": "Your repair has been booked. We'll contact you within 24 hours to confirm the appointment."
    }

    return booking


async def _check_repair_status(input: Dict, user_id: str) -> Dict:
    """Check repair status - MVP implementation"""

    repair_id = input["repair_id"]

    # Mock status
    status = {
        "repair_id": repair_id,
        "status": "in_progress",
        "estimated_completion": "2025-12-30",
        "updates": [
            {
                "date": "2025-12-26",
                "message": "Device received and diagnostics started"
            }
        ]
    }

    return status
