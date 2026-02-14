"""
Processing Routes - API endpoints for video processing
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from database import get_db
from models.books import Books
from security import get_current_user
from tasks.video_processing import process_book_videos
from tasks.transcript_tasks import process_book_transcripts_task, process_book_content_sequential_task
from models.transcriptions import Transcription
from models.chapters import Chapters

router = APIRouter(prefix="/books", tags=["processing"])


@router.post("/{book_id}/process")
async def start_book_processing(
    book_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Inicia o processamento assíncrono de todos os vídeos do livro.
    
    Fluxo:
    1. Verifica se o livro existe e pertence ao usuário
    2. Verifica se já não está em processamento
    3. Dispara task do Celery em background
    4. Retorna imediatamente (usuário pode sair da página)
    
    Returns:
        Dict com mensagem, task_id e book_id
    """
    user_id = current_user["id"]
    
    # Verificar se o livro existe e pertence ao usuário
    book = db.query(Books).filter(Books.id == book_id).first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Livro não encontrado"
        )
    
    if str(book.author_profile_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para processar este livro"
        )
    
    # Verificar se já está em processamento
    if book.status == "PROCESSING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este livro já está sendo processado"
        )
    
    # Disparar task do Celery
    task = process_book_videos.delay(str(book_id))
    
    return {
        "message": "Processamento iniciado com sucesso",
        "task_id": task.id,
        "book_id": str(book_id)
    }

@router.post("/{book_id}/process-transcripts", status_code=status.HTTP_202_ACCEPTED)
async def trigger_transcript_processing(
    book_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers the asynchronous processing of uploaded transcripts and slides.
    """
    user_id = current_user["id"]
    
    # Verify book ownership
    book = db.query(Books).filter(
        Books.id == book_id,
        Books.author_profile_id == user_id
    ).first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Check if transcripts exist
    transcripts_count = db.query(Transcription).filter(Transcription.book_id == book_id).count()
    if transcripts_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transcripts uploaded for this book"
        )
    
    # Trigger Celery task
    task = process_book_transcripts_task.delay(str(book_id))
    
    return {
        "message": "Processing started",
        "book_id": str(book_id),
        "task_id": task.id
    }

@router.post("/{book_id}/generate-content", status_code=status.HTTP_202_ACCEPTED)
async def trigger_content_generation(
    book_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers the sequential generation of section content for the book.
    """
    user_id = current_user["id"]
    
    # Verify book ownership
    book = db.query(Books).filter(
        Books.id == book_id,
        Books.author_profile_id == user_id
    ).first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Livro não encontrado"
        )
    
    # Check if structure exists
    chapters_count = db.query(Chapters).filter(Chapters.book_id == book_id).count()
    if chapters_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A estrutura do livro ainda não foi gerada. Execute o Discovery primeiro."
        )
    
    # Trigger Celery task
    task = process_book_content_sequential_task.delay(str(book_id))
    
    return {
        "message": "Geração de conteúdo iniciada",
        "book_id": str(book_id),
        "task_id": task.id
    }
