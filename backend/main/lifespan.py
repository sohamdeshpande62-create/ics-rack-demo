# lifespan.py -- Soham Deshpande, Intelligent Clinical Systems Inc.
# Specifies startup and shutdown procedure for API and creates tables


# Imports
from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend import crud
from backend.main.events import pipeline_event
from backend.main.database import Base, engine, session
import asyncio
from backend.main.inference_pipeline import run_pipeline


# Lifespan function defining startup and shutdown sequence for API app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    async with engine.begin() as db:
        await db.run_sync(Base.metadata.create_all)

    pipeline_task = asyncio.create_task(run_pipeline())

    async with session() as db:
        if await crud.get_rack_count(db) > 0:
            pipeline_event.set()

    yield

    pipeline_task.cancel()
    await asyncio.gather(pipeline_task, return_exceptions = True)