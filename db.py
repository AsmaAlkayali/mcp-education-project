from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os, datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@mcp-db:5432/mcp_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)
    action = Column(String)
    resource = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(JSON, default={})

def init_db():
    Base.metadata.create_all(bind=engine)
