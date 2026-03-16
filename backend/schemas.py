# schemas.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# Schema definitions for API calls for Item, Row, Rack objects

# Imports

import re
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal
from datetime import datetime


# Item Schemas
class ItemCreate(BaseModel):
    """Schema for creating a new Item"""
    rack_id: int = Field(ge=1, le=99) # Dropdown menu
    row_id: str = Field(min_length = 1, max_length = 1) # Dropdown menu

    name: str = Field(min_length=1, max_length=30)
    label: str = Field(min_length = 1, max_length = 30) # Dropdown menu

    slot: int = Field(ge=1, le=99)
    led_start: int
    led_end: int

    is_active: bool = True


    @model_validator(mode = 'after')
    def validate_led_range(self):
        if self.led_start < 0:
            raise ValueError('led_start cannot be negative')
        if self.led_end < self.led_start:
            raise ValueError('led_end cannot be less than led_start')
        return self


class ItemUpdate(BaseModel): # Inherits from BaseModel due to optional parameters
    """Schema for updating existing item, all fields are optional"""
    name: Optional[str] = None
    slot: Optional[int] = None
    led_start: Optional[int] = None
    led_end: Optional[int] = None
    is_active: Optional[bool] = None


    # Includes None validation as fields are optional
    @model_validator(mode = 'after')
    def validate_led_range(self):
        if self.led_start is not None and self.led_start < 0:
            raise ValueError('led_start cannot be negative')
        if self.led_start is not None and self.led_end is not None:
            if self.led_end < self.led_start:
                raise ValueError('led_end cannot be less than led_start')
        return self


class ItemResponse(ItemCreate):
    """Schema for response returned when item is created or updated"""
    item_id: int
    position: str = Field(min_length = 2, max_length = 3) # Calculated from row_id and slot

    led_length: int
    color_r: int
    color_g: int
    color_b: int


    @field_validator('position')
    def validate_position(cls, v):
        if not re.match(r'^[A-Z]\d+$', v):
            raise ValueError('Position must be in format A1, B2 etc')
        return v.upper()


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
    """Schema for response returned when Row is created"""
    row_id: str


    class Config:
        """Allows for reading data from ORM object not plain dict"""
        from_attributes = True


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


# Delete Schema
class DeleteResponse(BaseModel):
    """Schema for response when deleting Item, Rack, or Row"""
    item_id: Optional[int] = None
    rack_id: Optional[int] = None
    row_id: Optional[str] = None

    item_name: Optional[str] = None
    rack_name: Optional[str] = None

    message: str # Deletion message human-readable