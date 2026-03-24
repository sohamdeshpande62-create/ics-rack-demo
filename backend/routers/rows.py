# rows.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# API endpoints for racks. Communication layer for requests to crud.py to database
# handling and modification. Router handling is implemented in database_manager.py
# and row path /rows is binding there rather than specifying here


# Imports

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.exc import IntegrityError, OperationalError, InterfaceError, DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession
from backend import crud
from backend.database import get_db
from backend.schemas.rows import RowCreate, RowResponse


# Bind router into FastAPI app with /items path defaulted
router = APIRouter()


# POST for /rows
@router.post('', status_code=status.HTTP_201_CREATED)
async def create_row(row: RowCreate, db: AsyncSession=Depends(get_db)) -> RowResponse:
    """POST endpoint for creating a row"""
    try:
        return await crud.create_row(db, row)

    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Row creation failed: check inputs')

    except (OperationalError, InterfaceError, DatabaseError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f'Database error: {str(e)}')


# GET for /rows
@router.get('/{row_id}/{rack_id}', status_code=status.HTTP_200_OK)
async def get_row_direction(row_id: str, rack_id: int, db: AsyncSession=Depends(get_db)) -> str | None:
    """GET endpoint for getting row direction specified by row_id"""
    try:
        direction = await crud.get_row_direction(db, row_id, rack_id)

        if direction is None:
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = 'Row direction not found')
        else:
            return direction

    except (OperationalError, InterfaceError, DatabaseError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail = f'Database error: {str(e)}')