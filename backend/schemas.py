# schemas.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# Schema definitions for API calls for Item, Row, Rack objects

# Imports

from pydantic import BaseModel
from typing import Optional


# Item Schemas
class ItemBase(BaseModel):
    """Base schema for all Item API requests"""
    name: str
    slot: int
    position: str
    led_start: int
    led_end: int
    is_active: bool


class ItemCreate(ItemBase):
    """Schema for creating a new Item"""
    label: str


class ItemUpdate(BaseModel): # Inherits from BaseModel not ItemBase due to optional parameters
    """Schema for updating existing item, all fields are optional"""
    name: Optional[str] = None
    slot: Optional[int] = None
    position: Optional[str] = None
    led_start: Optional[int] = None
    led_end: Optional[int] = None
    is_active: Optional[bool] = None


class ItemResponse(ItemBase):
    """Schema for response returned when item is created or updated"""
    item_id: int
    rack_id: int
    row_id: str
    led_length: int
    color_r: int
    color_g: int
    color_b: int

    class Config:
        """Allows for reading data from ORM object not plain dict"""
        from_attributes = True