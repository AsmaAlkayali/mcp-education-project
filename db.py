# db.py
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# -------------------------
# Database URL
# -------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@db:5432/mcp_db"
)

# -------------------------
# Engine & Session
# -------------------------
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -------------------------
# Base model
# -------------------------
Base = declarative_base()

# -------------------------
# Audit Log Table
# -------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=True)
    inputs_hash = Column(String, nullable=True)
    output_hash = Column(String, nullable=True)
    details = Column(JSON, nullable=True)

# -------------------------
# Initialize DB
# -------------------------
def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")
