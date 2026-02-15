"""
Transcription Model - Stores metadata for uploaded transcriptions
"""
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base

class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to Books (many-to-one)
    book = relationship("Books", back_populates="transcriptions")

    def __repr__(self):
        return f"<Transcription(id={self.id}, filename={self.filename})>"
