import os
from sqlalchemy import create_engine, MetaData

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/mcp_db")
engine = create_engine(DATABASE_URL)
metadata = MetaData()

def init_db():
    metadata.create_all(engine)
