# schemas.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# Schema definitions for API calls for Item, Row, Rack objects

# Imports

import re
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal


# Item Schemas
class ItemCreate(BaseModel):
    """Schema for creating a new Item"""
    name: str = Field(min_length=1, max_length=30)
    label: str = Field(min_length = 1, max_length = 30)
    slot: int
    position: str = Field(min_length=2, max_length=3)
    led_start: int
    led_end: int
    is_active: bool = True


    @field_validator('position')
    def validate_position(self, v):
        if not re.match(r'^[A-Z]\d+$', v):
            raise ValueError('Position must be in format A1, B2 etc')
        return v.upper()


class ItemUpdate(BaseModel): # Inherits from BaseModel not ItemBase due to optional parameters
    """Schema for updating existing item, all fields are optional"""
    name: Optional[str] = None
    slot: Optional[int] = None
    position: Optional[str] = None
    led_start: Optional[int] = None
    led_end: Optional[int] = None
    is_active: Optional[bool] = None


class ItemResponse(ItemCreate):
    """Schema for response returned when item is created or updated"""
    item_id: int
    rack_id: int
    row_id: str = Field(min_length=1, max_length=1)
    led_length: int
    color_r: int
    color_g: int
    color_b: int

    class Config:
        """Allows for reading data from ORM object not plain dict"""
        from_attributes = True


# Row Schemas
class RowCreate(BaseModel):
    """Schema for creating a new Row"""
    total_leds: int
    led_offset: int
    direction: Literal['ltr', 'rtl'] = 'ltr'

# No update schema for Row as LED strip configuration will not change on racks once setup

class RowResponse(RowCreate):
    row_id: str = Field(min_length=1, max_length=1)

    class Config:
        """Allows for reading data from ORM object not plain dict"""
        from_attributes = True