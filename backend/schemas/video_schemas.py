"""
Video Schemas - Pydantic models for video upload operations
"""
from pydantic import BaseModel, Field, UUID4
from datetime import datetime
from typing import Optional


class VideoMetadata(BaseModel):
    """Video file metadata"""
    filename: str = Field(..., description="Nome original do arquivo")
    duration: float = Field(..., description="Duração do vídeo em segundos")
    size_bytes: Optional[int] = Field(None, description="Tamanho do arquivo em bytes")
    created_at: datetime = Field(..., description="Data de criação do registro")

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "aula_01.mp4",
                "duration": 1234.5,
                "size_bytes": 52428800,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class VideoUploadResponse(BaseModel):
    """Response after successful video upload"""
    id: UUID4 = Field(..., description="ID único do vídeo no banco de dados")
    book_id: UUID4 = Field(..., description="ID do livro ao qual o vídeo pertence")
    file_uri: str = Field(..., description="URI do arquivo no Gemini File API")
    status: str = Field(..., description="Status do arquivo (PROCESSING, ACTIVE)")
    metadata: VideoMetadata = Field(..., description="Metadados do arquivo")
    message: str = Field(default="Upload realizado com sucesso", description="Mensagem de sucesso")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "book_id": "660e8400-e29b-41d4-a716-446655440001",
                "file_uri": "https://generativelanguage.googleapis.com/v1beta/files/abc123xyz",
                "status": "ACTIVE",
                "metadata": {
                    "filename": "aula_01.mp4",
                    "duration": 1234.5,
                    "size_bytes": 52428800,
                    "created_at": "2024-01-15T10:30:00Z"
                },
                "message": "Upload realizado com sucesso"
            }
        }
