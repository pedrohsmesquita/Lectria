"""
SectionAssets Model - Images extracted from video sections
"""
from sqlalchemy import Column, String, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from database import Base


class SectionAssets(Base):
    __tablename__ = "section_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False)
    placeholder = Column(String, nullable=False)  # e.g., "[IMAGE_1]"
    storage_path = Column(String, nullable=False)  # Path to cropped image file
    caption = Column(Text, nullable=True)  # AI-generated caption
    timestamp = Column(Float, nullable=False)  # Exact second in the video
    crop_info = Column(JSONB, nullable=True)  # Crop coordinates: {xmin, ymin, xmax, ymax}

    # Relationship to Sections (many-to-one)
    section = relationship("Sections", back_populates="assets")

    def __repr__(self):
        return f"<SectionAssets(id={self.id}, placeholder={self.placeholder}, timestamp={self.timestamp})>"
