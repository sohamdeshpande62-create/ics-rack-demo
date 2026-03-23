# lifespan.py -- Soham Deshpande, Intelligent Clinical Systems Inc.
# Specifies startup and shutdown procedure for API and creates tables


# Imports
from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.database import Base, engine


# Lifespan function defining startup and shutdown sequence for API app
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as db:
        await db.run_sync(Base.metadata.create_all)
    yield