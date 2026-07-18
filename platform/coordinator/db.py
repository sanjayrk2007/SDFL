import uuid
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, 
    CheckConstraint, text, func
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from platform.coordinator.config import get_database_url

Base = declarative_base()

class RegisteredClient(Base):
    __tablename__ = "registered_clients"
    
    hospital_id = Column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4, 
        server_default=text("gen_random_uuid()")
    )
    hospital_name = Column(String(255), nullable=False)
    certificate_fingerprint = Column(String(64), unique=True, nullable=False)
    registered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

class ModelVersion(Base):
    __tablename__ = "model_versions"
    
    round_id = Column(Integer, primary_key=True)
    checkpoint_path = Column(String(512), nullable=False)
    val_dice = Column(Float, nullable=False)
    val_iou = Column(Float, nullable=False)
    epsilon = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)

class RoundSchedule(Base):
    __tablename__ = "round_schedules"
    __table_args__ = (
        CheckConstraint(
            "status IN ('OPEN', 'CLOSED', 'AGGREGATING', 'COMPLETED')",
            name="check_round_schedule_status"
        ),
    )
    
    round_id = Column(Integer, primary_key=True)
    window_seconds = Column(Integer, nullable=False)
    expiry_timestamp = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(100), nullable=False)
    round_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    details = Column(JSONB, nullable=True)

# Async PostgreSQL connection setup
DATABASE_URL = get_database_url()
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
