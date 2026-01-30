"""
Videos Model - Video file metadata
"""
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


class Videos(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    storage_path = Column(String, nullable=False)
    duration = Column(Float, nullable=False)  # Duration in seconds
    filename = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to Books (many-to-one)
    book = relationship("Books", back_populates="videos")

    # Relationship to Sections (one-to-many)
    sections = relationship("Sections", back_populates="video", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Videos(id={self.id}, filename={self.filename}, duration={self.duration})>"
