"""
Tag modeli - BLUEPRINT: id, name, type (MANUAL | AI_GENERATED).
"""
import enum
import uuid

from sqlalchemy import Column, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


class TagType(str, enum.Enum):
    MANUAL = "MANUAL"
    AI_GENERATED = "AI_GENERATED"


class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), nullable=False, index=True)
    type = Column(Enum(TagType), nullable=False, default=TagType.MANUAL)

    videos = relationship("VideoTag", back_populates="tag")
