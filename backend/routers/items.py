# items.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# API endpoints for items. Communication layer for requests to crud.py to database
# handling and modification. Router handling is implemented in main.py
# and item path /items is binding there rather than specifying here


# Imports

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.exc import IntegrityError, OperationalError, InterfaceError, DatabaseError
from backend import crud
from backend.database import get_db
from databases import Database
from backend.schemas import *


# Bind router into FastAPI app with /items path defaulted
router = APIRouter()


# POST for /items
@router.post('', status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate, db: Database=Depends(get_db)) -> ItemResponse:
    """POST endpoint for creating an item"""
    try:
        return await crud.create_item(db, item)

    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Item already exists')

    except (OperationalError, InterfaceError, DatabaseError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f'Database error: {str(e)}')


# GET for /items
@router.get('/row/{row_id}', status_code=status.HTTP_200_OK)
async def get_item_by_row(row_id: str, db: Database=Depends(get_db)) -> list[ItemResponse]:
    """GET endpoint for getting all items in a row by specifying the row_id"""
    try:
        item = await crud.get_item_by_row(db, row_id)

        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Item not found')
        else:
            return item

    except (OperationalError, InterfaceError, DatabaseError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail = f'Database error: {str(e)}')


@router.get('/rack/{rack_id}', status_code=status.HTTP_200_OK)
async def get_all_items(rack_id: int, db: Database=Depends(get_db)) -> list[ItemResponse]:
    """GET endpoint for getting all items on a rack by specifying the rack_id"""
    try:
        item = await crud.get_all_items(db, rack_id)

        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Item not found')
        else:
            return item

    except (OperationalError, InterfaceError, DatabaseError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail = f'Database error: {str(e)}')


@router.get('/{item_id}', status_code=status.HTTP_200_OK)
async def get_item(item_id: int, db: Database=Depends(get_db)) -> ItemResponse:
    """GET endpoint for getting one item specified by item_id"""
    try:
        item = await crud.get_item(db, item_id)

        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Item not found')
        else:
            return item

    except (OperationalError, InterfaceError, DatabaseError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail = f'Database error: {str(e)}')


# PUT for /items
@router.put('/{item_id}', status_code=status.HTTP_200_OK)
async def update_item(item_id: int, update_info: ItemUpdate, db: Database=Depends(get_db)) -> ItemResponse:
    """PUT endpoint for updating an item"""
    try:
        return await crud.update_item(db, item_id, update_info)

    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Update item failed')

    except (OperationalError, InterfaceError, DatabaseError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail = f'Database error: {str(e)}')


@router.delete('/{item_id}', status_code=status.HTTP_200_OK)
async def delete_item(item_id: int, db: Database=Depends(get_db)) -> DeleteResponse:
    """DELETE endpoint for deleting an item"""
    try:
        return await crud.delete_item(db, item_id)

    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Delete item failed')

    except (OperationalError, InterfaceError, DatabaseError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail = f'Database error: {str(e)}')