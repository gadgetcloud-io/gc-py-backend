"""
Items Router - Device/gadget management
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class Item(BaseModel):
    id: str
    name: str
    category: str
    brand: str
    status: str


@router.get("/", response_model=List[Item])
async def list_items(category: Optional[str] = None):
    """List user's items/devices"""

    # Mock data for MVP
    items = [
        Item(id="1", name="iPhone 14 Pro", category="phone", brand="Apple", status="active"),
        Item(id="2", name="MacBook Pro", category="laptop", brand="Apple", status="active"),
    ]

    return items


@router.get("/{item_id}", response_model=Item)
async def get_item(item_id: str):
    """Get item details"""

    # Mock data
    return Item(id=item_id, name="iPhone 14 Pro", category="phone", brand="Apple", status="active")


@router.post("/", response_model=Item)
async def create_item(item: Item):
    """Create new item"""

    logger.info(f"Creating item: {item.name}")
    return item


@router.put("/{item_id}", response_model=Item)
async def update_item(item_id: str, item: Item):
    """Update item"""

    logger.info(f"Updating item: {item_id}")
    return item


@router.delete("/{item_id}")
async def delete_item(item_id: str):
    """Delete item"""

    logger.info(f"Deleting item: {item_id}")
    return {"message": "Item deleted"}
