"""
Book Schemas - Pydantic models for API requests/responses
"""
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


# ============================================
# Request Schemas
# ============================================

class BookCreate(BaseModel):
    """Schema for creating a new book"""
    title: str = Field(..., min_length=1, max_length=255, description="Book title")


# ============================================
# Response Schemas
# ============================================

class BookResponse(BaseModel):
    """Schema for book response"""
    id: UUID
    title: str
    author: str
    status: str
    status_display: Optional[str] = Field(None, description="Status traduzido para português")
    processing_progress: int = Field(default=0, description="Progresso do processamento (0-100)")
    current_step: Optional[str] = Field(None, description="Etapa atual do processamento")
    created_at: datetime
    video_count: int = Field(default=0, description="Number of videos in this book")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BookDetailResponse(BaseModel):
    """Schema for detailed book response with videos"""
    id: UUID
    title: str
    author: str
    status: str
    status_display: Optional[str] = Field(None, description="Status traduzido para português")
    processing_progress: int = Field(default=0, description="Progresso do processamento (0-100)")
    current_step: Optional[str] = Field(None, description="Etapa atual do processamento")
    created_at: datetime
    videos: list[dict] = Field(default_factory=list, description="List of videos in this book")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
