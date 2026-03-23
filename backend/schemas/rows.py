# row_schemas -- Soham Deshpande, Intelligent Clinical Systems Inc.
# Schema definitions for API calls for Row objects


# Imports

from pydantic import BaseModel, Field
from typing import Literal


# Row Schemas
class RowCreate(BaseModel):
    """Schema for creating a new Row"""
    rack_id: int = Field(ge = 1, le = 99)  # Dropdown menu
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