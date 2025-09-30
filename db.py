import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import datetime

# -------------------------
# Database setup
# -------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/mcpdb")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------------
# Models
# -------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default="student")

    libraries = relationship("Library", back_populates="owner")


class Library(Base):
    __tablename__ = "libraries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="libraries")
    references = relationship("Reference", back_populates="library")


class Reference(Base):
    __tablename__ = "references"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    year = Column(Integer)
    doi = Column(String)
    url = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    library_id = Column(Integer, ForeignKey("libraries.id"))
    library = relationship("Library", back_populates="references")

# -------------------------
# Utility
# -------------------------
def init_db():
    Base.metadata.create_all(bind=engine)
