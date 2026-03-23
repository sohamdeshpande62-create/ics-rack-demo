# models.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# Established base model definitions for database
# Item, Row, and Rack describe all the necessary elements for
# a smart rack to operate

# Imports

from sqlalchemy import Boolean, String, Integer, Column, ForeignKey, DateTime
from backend.database import Base


class Item(Base):
    """Model for item table"""

    __tablename__ = 'item'

    # Identifiers
    item_id = Column(Integer, primary_key=True)
    rack_id = Column(Integer, ForeignKey('rack.rack_id'))
    row_id = Column(String(1), ForeignKey('row.row_id')) # Will be assigned based on slot and position chosen.

    name = Column(String(30)) # Actual name of item i.e. Pulse Oximeter
    label = Column(String(30)) # Label used in AI i.e Pulse_Oximeter

    slot = Column(Integer) # Corresponds to number on a row in rack |   [1]   |  2  | 3 |
    position = Column(String(3)) # Represents a position '{row_id}{slot}' i.e. A1, B4

    led_start = Column(Integer)
    led_end = Column(Integer)
    led_length = Column(Integer)

    color_r = Column(Integer, default=58)
    color_g = Column(Integer, default=103)
    color_b = Column(Integer, default=176)

    is_active = Column(Boolean, default=True) # Represents if item is in active use


class Row(Base):
    """Model for row table"""

    __tablename__ = 'row'

    row_id = Column(String(1), primary_key=True) # Indexed by A, B, C...Z
    rack_id = Column(Integer, ForeignKey('rack.rack_id'), primary_key=True)

    total_leds = Column(Integer)
    led_offset = Column(Integer)
    direction = Column(String(3), default='ltr') # References which way the LEDs flow on rack
                                                 # left to right or right to left


class Rack(Base):
    """Model for rack table"""

    __tablename__ = 'rack'

    rack_id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True)
    locked = Column(Boolean, default=False) # True when database updates are in progress
    locked_at = Column(DateTime, default=None)