"""
SectionAssets Model - Images extracted from video sections or slide PDFs
"""
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from database import Base


class SectionAssets(Base):
    __tablename__ = "section_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False)
    placeholder = Column(String, nullable=False)  # e.g., "[IMAGE_1]"
    caption = Column(Text, nullable=True)  # AI-generated caption
    
    # Source type: 'VIDEO' or 'SLIDE'
    source_type = Column(String, nullable=False, default='SLIDE')
    
    # For VIDEO sources: timestamp in seconds
    timestamp = Column(Float, nullable=True)  # Exact second in the video (only for VIDEO type)
    
    # For SLIDE sources: page number and crop coordinates
    slide_page = Column(Integer, nullable=True)  # Page number if extracted from a slide PDF
    crop_info = Column(JSONB, nullable=True)  # Crop coordinates: {xmin, ymin, xmax, ymax} (0-1000)
    
    storage_path = Column(String, nullable=False)  # Path to cropped image file

    # Relationship to Sections (many-to-one)
    section = relationship("Sections", back_populates="assets")

    def __repr__(self):
        if self.source_type == 'SLIDE':
            return f"<SectionAssets(id={self.id}, placeholder={self.placeholder}, slide_page={self.slide_page})>"
        else:
            return f"<SectionAssets(id={self.id}, placeholder={self.placeholder}, timestamp={self.timestamp})>"
