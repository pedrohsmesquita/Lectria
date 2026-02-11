"""
Books Model - Book information
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


class Books(Base):
    __tablename__ = "books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.user_auth_id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDING")  # PENDING, PROCESSING, COMPLETED
    processing_progress = Column(Integer, nullable=False, default=0)  # 0-100
    current_step = Column(String(50), nullable=True)  # Current processing step
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to UserProfiles (many-to-one)
    author_profile = relationship("UserProfiles", back_populates="books")

    # Relationship to Videos (one-to-many)
    videos = relationship("Videos", back_populates="book", cascade="all, delete-orphan")

    # Relationship to Chapters (one-to-many)
    chapters = relationship("Chapters", back_populates="book", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Books(id={self.id}, title={self.title}, status={self.status})>"
