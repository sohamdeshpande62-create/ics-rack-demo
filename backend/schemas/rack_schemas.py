# rack_schemas.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# Schema definitions for API calls for Rack objects


# Imports

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Rack Schemas
class RackCreate(BaseModel):
    """Schema for creating a new Rack"""
    name: str = Field(min_length=1, max_length=20)
    locked: bool = False


class RackResponse(RackCreate):
    """Schema for response returned when Rack is created"""
    rack_id: int
    locked_at: Optional[datetime] = None


    class Config:
        """Allows for reading data from ORM object not plain dict"""
        from_attributes = True