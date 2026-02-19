"""
Chapter and Section Schemas - Request/Response validation for chapter endpoints
"""
from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional
from datetime import datetime


class SectionAssetResponse(BaseModel):
    """Response schema for section asset (image)"""
    id: UUID
    placeholder: str
    caption: Optional[str] = None
    source_type: str
    storage_path: str
    slide_page: Optional[int] = None
    crop_info: Optional[dict] = None

    class Config:
        from_attributes = True


class SectionResponse(BaseModel):
    """Response schema for section data"""
    id: UUID = Field(..., description="Section unique identifier")
    chapter_id: UUID = Field(..., description="Parent chapter ID")
    video_id: Optional[UUID] = Field(None, description="Source video ID")
    title: str = Field(..., description="Section title")
    order: int = Field(..., description="Position within chapter")
    start_time: float = Field(..., description="Start timestamp in seconds")
    end_time: float = Field(..., description="End timestamp in seconds")
    content_markdown: Optional[str] = Field(None, description="Generated markdown content")
    status: str = Field(..., description="Processing status (PENDING, SUCCESS, ERROR)")
    video_filename: Optional[str] = Field(None, description="Source video filename")
    assets: List[SectionAssetResponse] = Field(default_factory=list, description="List of assets (images) for this section")
    
    class Config:
        from_attributes = True


class ChapterResponse(BaseModel):
    """Response schema for chapter data with nested sections"""
    id: UUID = Field(..., description="Chapter unique identifier")
    book_id: UUID = Field(..., description="Parent book ID")
    title: str = Field(..., description="Chapter title")
    order: int = Field(..., description="Position within book")
    created_at: datetime = Field(..., description="Creation timestamp")
    sections: List[SectionResponse] = Field(default_factory=list, description="List of sections in this chapter")
    
    class Config:
        from_attributes = True


class ChapterUpdate(BaseModel):
    """Request schema for updating chapter"""
    title: str = Field(..., min_length=1, max_length=500, description="New chapter title")


class SectionUpdate(BaseModel):
    """Request schema for updating section"""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="New section title")
    content_markdown: Optional[str] = Field(None, description="Updated markdown content")


class SectionReorder(BaseModel):
    """Request schema for reordering a section"""
    id: UUID
    order: int
    chapter_id: UUID


class ChapterReorder(BaseModel):
    """Request schema for reordering a chapter and its sections"""
    id: UUID
    order: int
    sections: List[SectionReorder]


class BookStructureUpdate(BaseModel):
    """Request schema for bulk updating the entire book structure"""
    chapters: List[ChapterReorder]
