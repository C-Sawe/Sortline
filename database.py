from sqlalchemy import Column, String, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import ForeignKey
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sortline.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, index=True)
    status = Column(String, default="processing")
    progress_msg = Column(String, default="")
    groups = relationship("Group", back_populates="job", cascade="all, delete-orphan")

class Group(Base):
    __tablename__ = "groups"
    id = Column(String, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"))
    name = Column(String)
    images = Column(JSON)
    
    job = relationship("Job", back_populates="groups")

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
