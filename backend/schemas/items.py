# items.py -- Soham Deshpande, Intelligent Clinical Systems Inc.
# Schema definitions for API calls for Item objects


# Imports

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional


# Item Schemas
class ItemCreate(BaseModel):
    """Schema for creating a new Item"""
    rack_id: int = Field(ge=1, le=99)
    row_id: str = Field(min_length=1, max_length=1)

    name: str = Field(min_length=1, max_length=30)
    label: str = Field(min_length=1, max_length=30)

    led_start: int
    led_end: int

    is_active: Optional[bool] = True


    @field_validator('row_id')
    def validate_row_id(cls, v) -> str:
        return v.upper()


    @model_validator(mode='after')
    def validate_led_range(self) -> 'ItemCreate':
        if self.led_start < 0:
            raise ValueError('led_start cannot be negative')
        if self.led_end < self.led_start:
            raise ValueError('led_end cannot be less than led_start')
        return self


class ItemUpdate(BaseModel):
    """Schema for updating existing item, all fields are optional"""
    row_id: Optional[str] = None
    name: Optional[str] = None
    led_start: Optional[int] = None
    led_end: Optional[int] = None
    led_start_b: Optional[int] = None
    led_end_b: Optional[int] = None
    is_active: Optional[bool] = None


    @model_validator(mode='after')
    def validate_led_range(self) -> 'ItemUpdate':
        if self.led_start is not None and self.led_start < 0:
            raise ValueError('led_start cannot be negative')
        if self.led_start is not None and self.led_end is not None:
            if self.led_end < self.led_start:
                raise ValueError('led_end cannot be less than led_start')
        return self


class ItemResponse(BaseModel):
    """Schema for response returned when item is created or updated"""
    item_id: int
    rack_id: int
    row_id: str
    name: str
    label: str
    led_start: int
    led_end: int
    led_start_b: int
    led_end_b: int
    led_length: int
    color_r: int
    color_g: int
    color_b: int
    is_active: bool


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

    message: str  # Deletion message human-readable
