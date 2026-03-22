# lifespan.py -- Soham Deshpande, Intelligent Clinical Systems Inc.
# Specifies startup and shutdown procedure for API and creates tables


# Imports
from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.database import Base, engine, database


# Lifespan function defining startup and shutdown sequence for API app
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    await database.connect()
    yield
    await database.disconnect()