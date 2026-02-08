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
