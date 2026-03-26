# database_manager.py -- Soham Deshpande, Intelligent Clinical Systems Inc.
# Entry point to API and routes all endpoints cleanly


# Imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.main.lifespan import lifespan
from backend.routers import items, rows, racks, system


# API app initialization
database_manager = FastAPI(lifespan=lifespan)

# CORS — allow browser clients (iPad, local dev)
database_manager.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router specifications
database_manager.include_router(items.router, prefix='/items')
database_manager.include_router(rows.router, prefix='/rows')
database_manager.include_router(racks.router, prefix='/racks')
database_manager.include_router(system.router, prefix='/system')


@database_manager.get('/')
def home() -> str:
    return 'Intelligent Clinical Systems Inc. Demo'
