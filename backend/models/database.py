"""
DeadList Database Models
SQLAlchemy 2.0 async models for analyses, processes, connections, and memory regions.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean, Text, DateTime,
    Float, ForeignKey, Enum as SAEnum, create_engine
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from config import settings

Base = declarative_base()


class Analysis(Base):
    """Represents a single memory dump analysis run."""
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False)
    md5_hash = Column(String(32), nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending/running/complete/failed
    risk_level = Column(String(20), nullable=True)  # clean/low/medium/high/critical
    hidden_process_count = Column(Integer, nullable=True, default=0)
    total_process_count = Column(Integer, nullable=True, default=0)
    suspicious_connection_count = Column(Integer, nullable=True, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    os_profile = Column(String(100), nullable=True)

    # Relationships
    processes = relationship("Process", back_populates="analysis", cascade="all, delete-orphan")
    connections = relationship("NetworkConnection", back_populates="analysis", cascade="all, delete-orphan")
    memory_regions = relationship("MemoryRegion", back_populates="analysis", cascade="all, delete-orphan")


class Process(Base):
    """Represents a process discovered during analysis."""
    __tablename__ = "processes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    pid = Column(Integer, nullable=False)
    ppid = Column(Integer, nullable=True)
    name = Column(String(255), nullable=False)
    in_pslist = Column(Boolean, nullable=False, default=False)
    in_psscan = Column(Boolean, nullable=False, default=False)
    is_hidden = Column(Boolean, nullable=False, default=False)
    cmdline = Column(Text, nullable=True)
    suspicion_score = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="clean")  # hidden/anomalous/suspicious/clean
    has_injected_code = Column(Boolean, nullable=False, default=False)
    create_time = Column(String(50), nullable=True)
    offset = Column(String(20), nullable=True)

    # Relationships
    analysis = relationship("Analysis", back_populates="processes")


class NetworkConnection(Base):
    """Represents a network connection found by netscan."""
    __tablename__ = "network_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    pid = Column(Integer, nullable=False)
    process_name = Column(String(255), nullable=True)
    protocol = Column(String(10), nullable=False)  # TCP/UDP
    local_addr = Column(String(45), nullable=True, default="")
    local_port = Column(Integer, nullable=True, default=0)
    remote_addr = Column(String(45), nullable=True)
    remote_port = Column(Integer, nullable=True)
    state = Column(String(20), nullable=True)  # ESTABLISHED, LISTENING, etc.
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    is_suspicious_port = Column(Boolean, nullable=False, default=False)

    # Relationships
    analysis = relationship("Analysis", back_populates="connections")


class MemoryRegion(Base):
    """Represents a suspicious memory region found by malfind."""
    __tablename__ = "memory_regions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    pid = Column(Integer, nullable=False)
    process_name = Column(String(255), nullable=True)
    address = Column(String(20), nullable=False)
    size = Column(Integer, nullable=True)
    protection = Column(String(20), nullable=True)  # e.g. PAGE_EXECUTE_READWRITE
    hex_dump = Column(Text, nullable=True)
    disassembly = Column(Text, nullable=True)
    tag = Column(String(50), nullable=True)

    # Relationships
    analysis = relationship("Analysis", back_populates="memory_regions")


class GeoIPCache(Base):
    """Cache for GeoIP lookups to stay within rate limits."""
    __tablename__ = "geoip_cache"

    ip_address = Column(String(45), primary_key=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    cached_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# Async engine and session factory
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Dependency that yields a database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
