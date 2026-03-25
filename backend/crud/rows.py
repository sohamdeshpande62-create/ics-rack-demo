# rows.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# Create, Read, Update, Response for Rows
# Routers go through this file to interact with database
# All interactions are async by default


# Imports

from sqlalchemy.ext.asyncio import AsyncSession
from backend.main.models import Row
from backend.schemas.rows import RowCreate, RowResponse
from sqlalchemy import select, func


# Row Functions
async def create_row(db: AsyncSession, row: RowCreate) -> RowResponse:
    """
    Creates a row specified by row schema

    Args:
        db: Database object
        row: RowCreate schema

    Returns:
        RowResponse: Schema for response
    """

    count_query = select(func.count()).where(Row.rack_id == row.rack_id)
    res = await db.execute(count_query) # Converts amount of rows into letter character [A-Z]
    count = res.scalar()


    row_id = chr(65 + count)

    new_row = Row(row_id=row_id,
                  rack_id=row.rack_id,
                  total_leds=row.total_leds,
                  led_offset=row.led_offset,
                  direction=row.direction)

    db.add(new_row)
    await db.commit()
    await db.refresh(new_row)
    return RowResponse.model_validate(new_row)


async def get_row_direction(db: AsyncSession, row_id: str, rack_id: int) -> str | None:
    """
    Gets row direction specified by row_id

    Args:
        db: Database object
        row_id: primary key for row
        rack_id: primary key for rack

    Returns:
        str: Row direction as 'ltr' or 'rtl':
        left to right | right to left
    """

    select_query = select(Row.direction).where(Row.row_id == row_id, Row.rack_id == rack_id)
    res = await db.execute(select_query)
    direction = res.scalar_one_or_none()

    if direction is None:
        return None
    else:
        return direction