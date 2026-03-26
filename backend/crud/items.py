# items.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# Create, Read, Update, Response for Items
# Routers go through this file to interact with database
# All interactions are async by default


# Imports

from sqlalchemy.ext.asyncio import AsyncSession
from backend.main.models import Item, Row
from backend.schemas.items import ItemCreate, ItemUpdate, ItemResponse, DeleteResponse
from sqlalchemy import select, update, delete
from pydantic import ValidationError


# Helper

async def check_led_overlap(
    db: AsyncSession,
    rack_id: int,
    row_id: str,
    led_start: int,
    led_end: int,
    exclude_item_id: int = None
) -> bool:
    """
    Returns True if the given LED range overlaps any existing item
    on the same row. Optionally excludes an item (for updates).
    """
    query = select(Item).where(
        Item.rack_id == rack_id,
        Item.row_id == row_id,
        Item.led_end >= led_start,
        Item.led_start <= led_end
    )
    if exclude_item_id:
        query = query.where(Item.item_id != exclude_item_id)
    res = await db.execute(query)
    return res.scalar_one_or_none() is not None


# Item Functions
async def create_item(db: AsyncSession, item: ItemCreate) -> ItemResponse:
    """
    Creates an item specified by item schema

    Args:
        db: Database object
        item: ItemCreate schema

    Returns:
        ItemResponse: Schema for response
    """

    led_length = item.led_end - item.led_start + 1

    row_check = await db.execute(
        select(Row).where(Row.row_id == item.row_id, Row.rack_id == item.rack_id)
    )
    row = row_check.scalar_one_or_none()
    if row is None:
        return None

    # Skip overlap check for staging placeholder (led_start=0, led_end=0)
    if item.led_start != 0 or item.led_end != 0:
        if await check_led_overlap(db, item.rack_id, item.row_id, item.led_start, item.led_end):
            return None

    new_item = Item(rack_id=item.rack_id,
                    row_id=item.row_id,
                    name=item.name,
                    label=item.label,
                    led_start=item.led_start,
                    led_end=item.led_end,
                    led_length=led_length,
                    color_r=58,
                    color_g=103,
                    color_b=176,
                    is_active=item.is_active)

    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return ItemResponse.model_validate(new_item)


async def get_item(db: AsyncSession, item_id: int) -> ItemResponse | None:
    """
    Gets an item specified by item_id

    Args:
        db: Database object
        item_id: primary key for item

    Returns:
        ItemResponse: Schema for response
    """

    select_query = select(Item).where(Item.item_id == item_id)
    res = await db.execute(select_query)
    response = res.scalar_one_or_none()

    if response is None:
        return None
    else:
        return ItemResponse.model_validate(response)


async def get_item_by_row(db: AsyncSession, row_id: str) -> list[ItemResponse] | None:
    """
    Gets a list of items specified by row_id

    Args:
        db: Database object
        row_id: foreign key for item

    Returns:
        ItemResponse: Schema for response
    """

    select_query = select(Item).where(Item.row_id == row_id)
    res = await db.execute(select_query)
    response = res.scalars().all()

    if not response:
        return None

    return [ItemResponse.model_validate(x) for x in response]


async def get_item_by_label(db: AsyncSession, label: str) -> list[ItemResponse] | None:
    """
    Gets a list of items specified by label

    Args:
        db: Database object
        label: item label from inference model

    Returns:
        ItemResponse: Schema for response
    """

    select_query = select(Item).where(Item.label == label)
    res = await db.execute(select_query)
    response = res.scalars().all()

    if not response:
        return None

    return [ItemResponse.model_validate(x) for x in response]


async def get_all_items(db: AsyncSession, rack_id: int) -> list[ItemResponse] | None:
    """
    Gets a list of items specified by rack_id

    Args:
        db: Database object
        rack_id: foreign key for item

    Returns:
        ItemResponse: Schema for response
    """

    select_query = select(Item).where(Item.rack_id == rack_id)
    res = await db.execute(select_query)
    response = res.scalars().all()

    if not response:
        return None

    return [ItemResponse.model_validate(x) for x in response]


async def update_item(db: AsyncSession, item_id: int, update_info: ItemUpdate) -> ItemResponse:
    """
    Updates item specified on item_id and update_info schema

    Args:
        db: Database object
        item_id: primary key for item
        update_info: ItemUpdate schema

    Returns:
        ItemResponse: Schema for response
    """

    update_dict = {k: v for k, v in update_info.model_dump().items() if v is not None}

    current = await get_item(db, item_id)
    if current is None:
        return None

    if 'led_start' in update_dict or 'led_end' in update_dict:
        new_start = update_dict.get('led_start', current.led_start)
        new_end = update_dict.get('led_end', current.led_end)

        # Staging placeholder: skip overlap check, zero out length
        if new_start == 0 and new_end == 0:
            update_dict['led_length'] = 0
        else:
            update_dict['led_length'] = new_end - new_start + 1
            new_row_id = update_dict.get('row_id', current.row_id)
            if await check_led_overlap(db, current.rack_id, new_row_id, new_start, new_end, exclude_item_id=item_id):
                return None

    update_query = update(Item).where(Item.item_id == item_id).values(**update_dict)
    await db.execute(update_query)

    select_query = select(Item).where(Item.item_id == item_id)
    res = await db.execute(select_query)
    response = res.scalar_one_or_none()

    try:
        ret = ItemResponse.model_validate(response)
        await db.commit()
        return ret

    except ValidationError:
        await db.rollback()
        return None


async def delete_item(db: AsyncSession, item_id: int) -> DeleteResponse:
    """
    Deletes item specified by item_id

    Args:
         db: Database object
         item_id: primary key for item

    Returns:
        DeleteResponse: Schema for response
    """

    item = await get_item(db, item_id)
    if item is None:
        return None

    delete_query = delete(Item).where(Item.item_id == item_id)
    await db.execute(delete_query)
    await db.commit()

    return DeleteResponse(item_id=item_id,
                          rack_id=item.rack_id,
                          row_id=item.row_id,
                          item_name=item.name,
                          message=f'Item {item_id} deleted')