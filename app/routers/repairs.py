"""
Repairs Router - Repair booking and management
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class RepairBooking(BaseModel):
    id: str
    item_id: str
    issue: str
    status: str
    created_at: str
    estimated_completion: Optional[str] = None


@router.get("/", response_model=List[RepairBooking])
async def list_repairs():
    """List user's repair bookings"""

    # Mock data
    repairs = [
        RepairBooking(
            id="repair-001",
            item_id="item-001",
            issue="Screen replacement",
            status="in_progress",
            created_at=datetime.utcnow().isoformat(),
            estimated_completion="2025-12-30"
        )
    ]

    return repairs


@router.get("/{repair_id}", response_model=RepairBooking)
async def get_repair(repair_id: str):
    """Get repair booking details"""

    # Mock data
    return RepairBooking(
        id=repair_id,
        item_id="item-001",
        issue="Screen replacement",
        status="in_progress",
        created_at=datetime.utcnow().isoformat(),
        estimated_completion="2025-12-30"
    )


@router.post("/", response_model=RepairBooking)
async def create_repair(booking: RepairBooking):
    """Create new repair booking"""

    logger.info(f"Creating repair booking for item: {booking.item_id}")
    booking.created_at = datetime.utcnow().isoformat()
    booking.status = "pending"
    return booking
