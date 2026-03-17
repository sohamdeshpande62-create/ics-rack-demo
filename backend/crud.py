# crud.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# Create, Read, Update, Response for Items Rows and Racks
# Routers go through this file to interact with database
# All interactions are async by default


# Imports
from datetime import datetime
from databases import Database
from backend.models import Item, Row, Rack
from backend.schemas import ItemCreate, ItemUpdate, ItemResponse, DeleteResponse, RowResponse, \
    RowCreate, RackCreate, RackResponse
from sqlalchemy import select, insert, update, delete, func


# Item Functions
async def create_item(db: Database, item: ItemCreate) -> ItemResponse:
    """
    Creates an item specified by item schema
    Creates position dynamically based on row_id and slot

    Args:
        db: Database object
        item: ItemCreate schema

    Returns:
        ItemResponse: Schema for response
    """

    table = Item.__table__
    position = f'{item.row_id}{item.slot}' # Formats the position A1, B4, C2 etc.
    led_length = item.led_end - item.led_start

    insert_query = insert(table).values(rack_id=item.rack_id,
                                        row_id=item.row_id,
                                        name=item.name,
                                        label=item.label,
                                        slot=item.slot,
                                        position=position,
                                        led_start=item.led_start,
                                        led_end=item.led_end,
                                        led_length=led_length,
                                        is_active=item.is_active)

    item_id = await db.execute(insert_query)
    select_query = select(table).where(table.c.item_id == item_id)

    response = await db.fetch_one(select_query)
    return ItemResponse.model_validate(response)


async def get_item(db: Database, item_id: int) -> ItemResponse | None:
    """
    Gets an item specified by item_id

    Args:
        db: Database object
        item_id: primary key for item

    Returns:
        ItemResponse: Schema for response
    """

    table = Item.__table__
    select_query = select(table).where(table.c.item_id == item_id)
    response = await db.fetch_one(select_query)

    if response is None:
        return None
    else:
        return ItemResponse.model_validate(response)


async def get_item_by_row(db: Database, row_id: str) -> list[ItemResponse] | None:
    """
        Gets a list of items specified by row_id

        Args:
            db: Database object
            row_id: foreign key for item

        Returns:
            ItemResponse: Schema for response
        """

    table = Item.__table__
    select_query = select(table).where(table.c.row_id == row_id)
    response = await db.fetch_all(select_query)

    if not response:
        return None

    return [ItemResponse.model_validate(x) for x in response] # Parse response list to create ItemResponse objects


async def get_all_items(db: Database, rack_id: int) -> list[ItemResponse] | None:
    """
    Gets a list of items specified by rack_id

    Args:
        db: Database object
        rack_id: foreign key for item

    Returns:
        ItemResponse: Schema for response
    """

    table = Item.__table__
    select_query = select(table).where(table.c.rack_id == rack_id)
    response = await db.fetch_all(select_query)

    if not response:
        return None

    return [ItemResponse.model_validate(x) for x in response] # Parse response list to create ItemResponse objects


async def update_item(db: Database, item_id: int, update_info: ItemUpdate) -> ItemResponse:
    """
    Updates item specified on item_id and update_info schema

    Args:
        db: Database object
        item_id: primary key for item
        update_info: ItemUpdate schema

    Returns:
        ItemResponse: Schema for response
    """

    table = Item.__table__

    # Reconstruct update_info to not include null values from request
    # optional values allowed
    update_info = {k:v for k, v in update_info.model_dump().items() if v is not None}

    update_query = update(table).where(table.c.item_id == item_id).values(**update_info)
    await db.execute(update_query) # Returns nothing useful

    select_query = select(table).where(table.c.item_id == item_id)
    response = await db.fetch_one(select_query)

    return ItemResponse.model_validate(response)


async def delete_item(db: Database, item_id: int) -> DeleteResponse:
    """
    Deletes item specified by item_id

    Args:
         db: Database object
         item_id: primary key for item

    Returns:
        DeleteResponse: Schema for response
    """

    table = Item.__table__
    delete_query = delete(table).where(table.c.item_id == item_id)

    item = await get_item(db, item_id)
    await db.execute(delete_query)

    delete_response = DeleteResponse(item_id=item_id,
                                     rack_id=item.rack_id,
                                     row_id=item.row_id,
                                     item_name=item.name,
                                     message=f'Item {item_id} deleted')

    return delete_response


# Row Functions
"""
Read row -> for direction
delete row -> duh
"""

async def create_row(db: Database, row: RowCreate) -> RowResponse:
    """
    Creates a row specified by row schema

    Args:
        db: Database object
        row: RowCreate schema

    Returns:
        RowResponse: Schema for response
    """

    table = Row.__table__
    count_query = select(func.count()).where(table.c.rack_id == row.rack_id)
    count = await db.fetch_val(count_query) # Converts amount of rows into letter character [A-Z]

    row_id = chr(65 + count)

    insert_query = insert(table).values(row_id=row_id,
                                        rack_id=row.rack_id,
                                        total_leds=row.total_leds,
                                        led_offset=row.led_offset,
                                        direction=row.direction)
    await db.execute(insert_query)

    select_query = select(table).where(table.c.row_id == row_id)

    response = await db.fetch_one(select_query)
    return RowResponse.model_validate(response)


async def get_row_direction(db: Database, row_id: int) -> str | None:
    """
    Gets row direction specified by row_id

    Args:
        db: Database object
        row_id: primary key for row

    Returns:
        str: Row direction as 'ltr' or 'rtl':
        left to right | right to left
    """

    table = Row.__table__
    select_query = select(table.c.direction).where(table.c.row_id == row_id)
    direction = await db.fetch_one(select_query)

    if direction is None:
        return None

    return direction['direction']


# Rack Functions
async def create_rack(db: Database, rack: RackCreate) -> RackResponse:
    """
    Creates a rack specified by rack schema

    Args:
        db: Database object
        rack: RackCreate schema

    Returns:
        RackResponse: Schema for response
    """

    table = Rack.__table__
    insert_query = insert(table).values(name=rack.name, locked=rack.locked)
    rack_id = await db.execute(insert_query)

    select_query = select(table).where(table.c.rack_id == rack_id)
    response = await db.fetch_one(select_query)

    return RackResponse.model_validate(response)


async def get_lock_status(db: Database, rack_id: int) -> bool | None:
    """
    Gets lock status for rack specified by rack_id

    Args:
        db: Database object
        rack_id: primary key for rack

    Returns:
        bool: Lock status as True | False
    """

    table = Rack.__table__
    select_query = select(table.c.locked).where(table.c.rack_id == rack_id)
    locked = await db.fetch_one(select_query)

    if locked is None:
        return None

    return locked['locked']


async def update_rack_lock_status(db: Database, rack_id: int, locked: bool) -> RackResponse:
    """
    Updates rack to lock from inference pipeline

    Args:
        db: Database
        rack_id: primary key for rack
        locked: status to lock or unlock

    Returns:
        RackResponse: Schema for response
    """

    table = Rack.__table__
    locked_at = datetime.now() if locked else None

    update_query = update(table).where(table.c.rack_id == rack_id).values(locked=locked, locked_at=locked_at)
    await db.execute(update_query)

    select_query = select(table).where(table.c.rack_id == rack_id)
    response = await db.fetch_one(select_query)

    return RackResponse.model_validate(response)