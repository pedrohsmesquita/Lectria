"""
Sections Model - Chapter sections with video content mapping
"""
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from database import Base


class Sections(Base):
    __tablename__ = "sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    order = Column(Integer, nullable=False)  # Sequential position within the chapter
    start_time = Column(Float, nullable=False)  # Timestamp in seconds
    end_time = Column(Float, nullable=False)  # Timestamp in seconds
    content_markdown = Column(Text, nullable=True)  # Generated content from Gemini 3.0 Pro
    status = Column(String, nullable=False, default="PENDING")  # PENDING, SUCCESS, ERROR

    # Relationship to Chapters (many-to-one)
    chapter = relationship("Chapters", back_populates="sections")

    # Relationship to Videos (many-to-one)
    video = relationship("Videos", back_populates="sections")

    # Relationship to SectionAssets (one-to-many)
    assets = relationship("SectionAssets", back_populates="section", cascade="all, delete-orphan", order_by="SectionAssets.timestamp")

    def __repr__(self):
        return f"<Sections(id={self.id}, title={self.title}, start_time={self.start_time}, end_time={self.end_time})>"
