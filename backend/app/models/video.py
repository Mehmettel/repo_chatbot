"""
Video modeli - BLUEPRINT: id, source_url, s3_key, file_hash, description_manual, description_ai, embedding, duration, created_at.
ADR: folder_id eklendi (Video–Folder ilişkisi).
MVP: status eklendi (PENDING/PROCESSING/COMPLETED/FAILED).
V2: title, transcript eklendi (arama doğruluğu iyileştirmesi).
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship

from app.core.db import Base

# pgvector tipi; PostgreSQL'de CREATE EXTENSION vector gerekli
from pgvector.sqlalchemy import Vector as PgVector

VECTOR_SIZE = 1536  # text-embedding-3-small


class VideoStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_url = Column(String(2048), nullable=True)
    s3_key = Column(String(512), nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 duplicate check
    
    # V2: Video başlığı (yt-dlp'den)
    title = Column(Text, nullable=True)
    
    description_manual = Column(Text, nullable=True)
    description_ai = Column(Text, nullable=True)
    
    # V2: Ses transkripti (Whisper'dan)
    transcript = Column(Text, nullable=True)
    
    embedding = Column(PgVector(VECTOR_SIZE), nullable=True)
    
    # V2: Full-text search için tsvector
    search_vector = Column(TSVECTOR, nullable=True)
    
    duration = Column(Integer, nullable=True)  # saniye
    folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)
    status = Column(Enum(VideoStatus), nullable=False, default=VideoStatus.PENDING)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    folder = relationship("Folder", back_populates="videos", foreign_keys=[folder_id])
    tags = relationship("VideoTag", back_populates="video", cascade="all, delete-orphan")
