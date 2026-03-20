# database.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# Database initialization for ics-rack-demo

# Imports

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from databases import Database


# Load .env variables
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


# Create database entry point
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread' : False}) # Removes sqlite threading limitation
Base = declarative_base()
database = Database(DATABASE_URL)


# Establish dynamic database connection
async def get_db():
    """Creates a fresh database instance for individual API calls"""
    async with database:
        yield database