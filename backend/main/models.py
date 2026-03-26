# models.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# Established base model definitions for database
# Item, Row, and Rack describe all the necessary elements for
# a smart rack to operate

# Imports

from sqlalchemy import Boolean, String, Integer, Column, ForeignKey, DateTime, ForeignKeyConstraint
from backend.main.database import Base


class Item(Base):
    """Model for item table"""

    __tablename__ = 'item'

    # Identifiers
    item_id = Column(Integer, primary_key=True, autoincrement=True)

    rack_id = Column(Integer)
    row_id = Column(String(1))

    name = Column(String(30)) # Actual name of item i.e. Pulse Oximeter
    label = Column(String(30)) # Label used in AI i.e Pulse_Oximeter

    led_start = Column(Integer)
    led_end = Column(Integer)
    led_length = Column(Integer)

    # Bottom divider strip LEDs (the shelf below the item)
    # Derived at placement time: offset = row.led_offset + row.total_leds, direction reversed
    led_start_b = Column(Integer, default=0)
    led_end_b   = Column(Integer, default=0)

    color_r = Column(Integer, default=58)
    color_g = Column(Integer, default=103)
    color_b = Column(Integer, default=176)

    is_active = Column(Boolean, default=True) # Represents if item is in active use

    __table_args__ = (
        ForeignKeyConstraint(
            ['rack_id', 'row_id'],
            ['row.rack_id', 'row.row_id']
        ),
    )

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