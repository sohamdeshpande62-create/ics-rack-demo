# items.py -- Soham Deshpande, Intelligent Clinical Systems Inc.
# Schema definitions for API calls for Item objects


# Imports

import re
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional


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

    is_active: Optional[bool] = True


    @field_validator('row_id')
    def validate_row_id(cls, v) -> str:
        return v.upper()


    @model_validator(mode = 'after')
    def validate_led_range(self) -> ItemCreate:
        if self.led_start < 0:
            raise ValueError('led_start cannot be negative')
        if self.led_end < self.led_start:
            raise ValueError('led_end cannot be less than led_start')
        return self


class ItemUpdate(BaseModel): # Inherits from BaseModel due to optional parameters
    """Schema for updating existing item, all fields are optional"""
    row_id: Optional[str] = None
    name: Optional[str] = None
    slot: Optional[int] = Field(default=None, ge=1, le=99)
    led_start: Optional[int] = None
    led_end: Optional[int] = None
    is_active: Optional[bool] = None


    # Includes None validation as fields are optional
    @model_validator(mode = 'after')
    def validate_led_range(self) -> ItemCreate:
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
    def validate_position(cls, v) -> str:
        if not re.match(r'^[A-Z]\d+$', v):
            raise ValueError('Position must be in format A1, B2 etc')
        return v.upper()


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

    message: str # Deletion message human-readable