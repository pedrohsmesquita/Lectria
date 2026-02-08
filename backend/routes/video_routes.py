"""
Video Routes - Endpoints for video upload and management
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID, uuid4
from typing import Optional
import os
import shutil

from database import get_db
from models.videos import Videos
from models.books import Books
from schemas.video_schemas import VideoUploadResponse, VideoMetadata
from security import get_current_user

router = APIRouter(prefix="/videos", tags=["Videos"])

# File validation constants
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB in bytes
ALLOWED_VIDEO_TYPES = [
    "video/mp4",
    "video/mpeg",
    "video/quicktime",
    "video/x-msvideo",
    "video/webm",
    "video/x-matroska"  # .mkv
]


@router.post("/upload", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(..., description="Arquivo de vídeo para upload"),
    book_id: str = Form(..., description="UUID do livro ao qual o vídeo pertence"),
    authorization: str = Header(..., description="Bearer token JWT"),
    db: Session = Depends(get_db)
):
    """
    Upload de vídeo para armazenamento local e registro no banco de dados.
    
    **Fluxo:**
    1. Valida autenticação JWT
    2. Valida tipo e tamanho do arquivo
    3. Valida propriedade do livro
    4. Salva arquivo localmente em media_storage
    5. Salva metadados no banco de dados
    
    **Requisitos:**
    - Token JWT válido no header Authorization
    - Arquivo de vídeo (máx 2GB)
    - book_id válido pertencente ao usuário autenticado
    
    **Retorna:**
    - ID do vídeo criado
    - Caminho local do arquivo
    - Status do upload
    - Metadados do vídeo
    
    **Erros:**
    - 401: Token inválido ou expirado
    - 400: Tipo de arquivo inválido ou tamanho excedido
    - 403: Livro não pertence ao usuário
    - 404: Livro não encontrado
    - 500: Erro no upload ou salvamento
    """
    # Step 1: Authenticate user
    current_user = get_current_user(authorization)
    user_id = current_user["id"]
    
    # Step 2: Validate file type
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de arquivo não suportado. Tipos aceitos: {', '.join(ALLOWED_VIDEO_TYPES)}"
        )
    
    # Step 3: Validate file size (read file to get size)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        max_size_gb = MAX_FILE_SIZE / (1024 * 1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Arquivo muito grande. Tamanho máximo: {max_size_gb}GB"
        )
    
    # Step 4: Validate book_id format
    try:
        book_uuid = UUID(book_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="book_id inválido (formato UUID esperado)"
        )
    
    # Step 5: Validate book exists and belongs to user
    book = db.query(Books).filter(Books.id == book_uuid).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Livro não encontrado"
        )
    
    if str(book.author_profile_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para adicionar vídeos a este livro"
        )
    
    # Step 6: Create video record ID
    video_id = uuid4()
    
    try:
        # Step 7: Get media storage path and create hierarchical structure
        media_storage_path = os.getenv("MEDIA_STORAGE_PATH", "/app/media")
        
        # Create directory structure: media_storage/{user_id}/{book_id}/
        book_folder = os.path.join(media_storage_path, str(user_id), str(book_uuid))
        os.makedirs(book_folder, exist_ok=True)
        
        # Step 8: Generate unique filename using video_id to avoid conflicts
        file_extension = os.path.splitext(file.filename)[1]  # Get original extension
        unique_filename = f"{video_id}{file_extension}"
        local_file_path = os.path.join(book_folder, unique_filename)
        
        # Step 9: Save file to local storage
        with open(local_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Step 10: Save to database
        video_record = Videos(
            id=video_id,
            book_id=book_uuid,
            storage_path=local_file_path,
            duration=0,  # Will be calculated during processing phase
            filename=file.filename
        )
        db.add(video_record)
        db.commit()
        db.refresh(video_record)
        
        # Step 11: Prepare response
        metadata = VideoMetadata(
            filename=video_record.filename,
            duration=video_record.duration,
            size_bytes=file_size,
            created_at=video_record.created_at
        )
        
        return VideoUploadResponse(
            id=video_record.id,
            book_id=video_record.book_id,
            file_uri=video_record.storage_path,
            status="SAVED",
            metadata=metadata,
            message="Upload realizado com sucesso"
        )
        
    except Exception as e:
        db.rollback()
        # Try to clean up file if it was created
        if 'local_file_path' in locals() and os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar upload: {str(e)}"
        )
