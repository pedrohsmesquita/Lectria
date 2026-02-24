"""
Chapters Model - Book chapters
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


class Chapters(Base):
    __tablename__ = "chapters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    order = Column(Integer, nullable=False)  # Sequential position in the book
    is_bibliography = Column(Boolean, nullable=False, default=False)  # Special bibliography chapter flag
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to Books (many-to-one)
    book = relationship("Books", back_populates="chapters")

    # Relationship to Sections (one-to-many)
    sections = relationship("Sections", back_populates="chapter", cascade="all, delete-orphan", order_by="Sections.order")

    def __repr__(self):
        return f"<Chapters(id={self.id}, title={self.title}, order={self.order}, is_bibliography={self.is_bibliography})>"
