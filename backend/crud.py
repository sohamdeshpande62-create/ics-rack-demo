# crud.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026


# Imports
from databases import Database
from backend.models import Item, Row, Rack
from backend.schemas import ItemCreate, ItemUpdate, ItemResponse, DeleteResponse
from sqlalchemy import select, insert, update, delete


# Item Functions

"""
database for all
create_item(ItemCreate) -> ItemResponse
get_item(item_id) -> ItemResponse
get_all_items(rack_id) -> list[ItemResponse]
get_item_by_row(row_id) -> list[ItemResponse]
update_item(item_id, ItemUpdate) -> ItemResponse
delete_item(item_id) -> DeleteResponse
"""



async def create_item(db: Database, item: ItemCreate) -> ItemResponse:
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


async def get_item(item_id: int, db: Database) -> ItemResponse:
    pass


async def get_item_by_row(row_id: str, db: Database) -> list[ItemResponse]:
    pass


async def get_all_items(rack_id: int, db: Database) -> list[ItemResponse]:
    pass


async def update_item(item_id: int, update_info: ItemUpdate, db: Database) -> ItemResponse:
    pass


async def delete_item(item_id: int, db: Database) -> DeleteResponse:
    pass