# database.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# Database initialization for ics-rack-demo

# Imports

from backend.core.config import DATABASE_URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.engine import Engine
from sqlalchemy import event


# Create database entry point and session
engine = create_async_engine(DATABASE_URL)
Base = declarative_base()
session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Establish dynamic database connection
async def get_db():
    async with session() as db:
        try:
            yield db
        except Exception:
            await db.rollback()
            raise


# Enforces foreign key constraints with every database connection
@event.listens_for(Engine, 'connect')
def set_sqlite_pragma(db, _):
    cursor = db.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()