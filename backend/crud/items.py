# items.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# Create, Read, Update, Response for Items
# Routers go through this file to interact with database
# All interactions are async by default


# Imports

from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import Item, Row
from backend.schemas.items import ItemCreate, ItemUpdate, ItemResponse, DeleteResponse
from sqlalchemy import select, update, delete
from pydantic import ValidationError


# Item Functions
async def create_item(db: AsyncSession, item: ItemCreate) -> ItemResponse:
    """
    Creates an item specified by item schema
    Creates position dynamically based on row_id and slot

    Args:
        db: Database object
        item: ItemCreate schema

    Returns:
        ItemResponse: Schema for response
    """

    position = f'{item.row_id}{item.slot}' # Formats the position A1, B4, C2 etc.
    led_length = item.led_end - item.led_start + 1

    row_check = await db.execute(
        select(Row).where(Row.row_id == item.row_id, Row.rack_id == item.rack_id)
    )
    row = row_check.scalar_one_or_none()
    if row is None:
        return None

    new_item = Item(rack_id=item.rack_id,
                    row_id=item.row_id,
                    name=item.name,
                    label=item.label,
                    slot=item.slot,
                    position=position,
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

    return [ItemResponse.model_validate(x) for x in response] # Parse response list to create ItemResponse objects


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

    return [ItemResponse.model_validate(x) for x in response] # Parse response list to create ItemResponse objects


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

    update_info = {k: v for k, v in update_info.model_dump().items() if v is not None}

    # Validate new position and led_length before updating
    current = await get_item(db, item_id)
    if current is None:
        return None

    if 'row_id' in update_info or 'slot' in update_info:
        new_row_id = update_info.get('row_id', current.row_id)
        new_slot = update_info.get('slot', current.slot)
        update_info['position'] = f'{new_row_id}{new_slot}'

    if 'led_start' in update_info or 'led_end' in update_info:
        new_start = update_info.get('led_start', current.led_start)
        new_end = update_info.get('led_end', current.led_end)
        update_info['led_length'] = new_end - new_start + 1


    update_query = update(Item).where(Item.item_id == item_id).values(**update_info)
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

    delete_query = delete(Item).where(Item.item_id == item_id)

    item = await get_item(db, item_id)
    if item is None:
        return None

    await db.execute(delete_query)
    await db.commit()

    delete_response = DeleteResponse(item_id=item_id,
                                     rack_id=item.rack_id,
                                     row_id=item.row_id,
                                     item_name=item.name,
                                     message=f'Item {item_id} deleted')

    return delete_response