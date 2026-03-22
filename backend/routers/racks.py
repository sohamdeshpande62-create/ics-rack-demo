# racks.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# API endpoints for racks. Communication layer for requests to crud.py to database
# handling and modification. Router handling is implemented in main.py
# and rack path /racks is binding there rather than specifying here


# Imports

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.exc import IntegrityError, OperationalError, InterfaceError, DatabaseError
from backend import crud
from backend.database import get_db
from databases import Database
from backend.schemas import *


# Bind router into FastAPI app with /items path defaulted
router = APIRouter()


# POST for /racks
@router.post('', status_code=status.HTTP_201_CREATED)
async def create_rack(rack: RackCreate, db: Database=Depends(get_db)) -> RackResponse:
    """POST endpoint for creating a rack"""
    try:
        return await crud.create_rack(db, rack)

    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Rack already exists')

    except (OperationalError, InterfaceError, DatabaseError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f'Database error: {str(e)}')


# GET for /racks
@router.get('/{rack_id}/lock-status', status_code=status.HTTP_200_OK)
async def get_lock_status(rack_id: int, db: Database=Depends(get_db)) -> bool | None:
    """GET endpoint for seeing lock status for specified rack"""
    try:
        lock_status = await crud.get_lock_status(db, rack_id)

        if lock_status is None:
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = 'Rack lock status not found')
        else:
            return lock_status

    except (OperationalError, InterfaceError, DatabaseError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail = f'Database error: {str(e)}')


# PUT for /racks
@router.put('/{rack_id}/update-lock-status', status_code=status.HTTP_200_OK)
async def update_rack_lock_status(rack_id: int, locked: bool, db: Database=Depends(get_db)) -> RackResponse:
    """PUT endpoint for updating lock status of specified rack"""
    try:
        return await crud.update_rack_lock_status(db, rack_id, locked)

    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Rack lock status update failed')

    except (OperationalError, InterfaceError, DatabaseError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail = f'Database error: {str(e)}')