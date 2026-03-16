# crud.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026


# Imports
from databases import Database
from backend.models import Item, Row, Rack
from backend.schemas import ItemCreate, ItemUpdate, ItemResponse, DeleteResponse
from sqlalchemy import select, insert, update, delete


# Item Functions

"""
update_item(item_id, ItemUpdate) -> ItemResponse
delete_item(item_id) -> DeleteResponse
"""


async def create_item(db: Database, item: ItemCreate) -> ItemResponse:
    """
    Creates an item specified by ItemCreate schema
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

    insert_query = insert(table).values(
                                 rack_id=item.rack_id,
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

    response_list = [ItemResponse.model_validate(x) for x in response]
    return response_list


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

    response_list = [ItemResponse.model_validate(x) for x in response]
    return response_list


async def update_item(db: Database, item_id: int, update_info: ItemUpdate) -> ItemResponse:
    pass


async def delete_item(db: Database, item_id: int) -> DeleteResponse:
    pass