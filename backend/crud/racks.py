# racks.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# Create, Read, Update, Response for Racks
# Routers go through this file to interact with database
# All interactions are async by default


# Imports

from sqlalchemy.ext.asyncio import AsyncSession
from backend.main.models import Rack
from backend.schemas.racks import RackCreate, RackResponse
from sqlalchemy import select, update
from datetime import datetime


# Rack Functions
async def create_rack(db: AsyncSession, rack: RackCreate) -> RackResponse:
    """
    Creates a rack specified by rack schema

    Args:
        db: Database object
        rack: RackCreate schema

    Returns:
        RackResponse: Schema for response
    """

    new_rack = Rack(name=rack.name, locked=rack.locked)
    db.add(new_rack)
    await db.commit()
    await db.refresh(new_rack)
    return RackResponse.model_validate(new_rack)


async def get_lock_status(db: AsyncSession, rack_id: int) -> bool | None:
    """
    Gets lock status for rack specified by rack_id

    Args:
        db: Database object
        rack_id: primary key for rack

    Returns:
        bool: Lock status as True | False
    """

    select_query = select(Rack.locked).where(Rack.rack_id == rack_id)
    res = await db.execute(select_query)
    locked = res.scalar_one_or_none()

    if locked is None:
        return None
    else:
        return locked


async def get_rack(db: AsyncSession, rack_id: int) -> RackResponse | None:
    """Returns the full rack record for rack_id, or None if not found."""
    res = await db.execute(select(Rack).where(Rack.rack_id == rack_id))
    rack = res.scalar_one_or_none()
    if rack is None:
        return None
    return RackResponse.model_validate(rack)


async def get_rack_count(db: AsyncSession) -> int:
    """
    Gets amount of racks in table

    Args:
        db: Database object

    Returns:
        int: Count of racks
    """

    select_query = select(Rack)
    res = await db.execute(select_query)
    response = res.scalars().all()

    return len(response)


async def update_rack_lock_status(db: AsyncSession, rack_id: int, locked: bool) -> RackResponse:
    """
    Updates rack to lock from inference pipeline

    Args:
        db: Database
        rack_id: primary key for rack
        locked: status to lock or unlock

    Returns:
        RackResponse: Schema for response
    """

    locked_at = datetime.now() if locked else None

    update_query = update(Rack).where(Rack.rack_id == rack_id).values(locked=locked, locked_at=locked_at)
    await db.execute(update_query)
    await db.commit()

    select_query = select(Rack).where(Rack.rack_id == rack_id)
    res = await db.execute(select_query)
    response = res.scalar_one_or_none()
    if response is None:
        return None

    return RackResponse.model_validate(response)