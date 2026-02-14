"""
Section Routes - API endpoints for specific section actions
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from database import get_db
from models.sections import Sections
from models.chapters import Chapters
from models.books import Books
from security import get_current_user
from tasks.transcript_tasks import process_section_content_task

router = APIRouter(prefix="/sections", tags=["sections"])

@router.post("/{section_id}/generate-content")
async def generate_section_content_endpoint(
    section_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger content generation for a single section.
    Does NOT trigger the next section automatically.
    """
    user_id = current_user["id"]
    
    # Find section and verify ownership through book
    section = db.query(Sections).join(Chapters).join(Books).filter(
        Sections.id == UUID(section_id),
        Books.author_profile_id == user_id
    ).first()
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found or you don't have permission"
        )
    
    # Check if section is already processing or done? 
    # For flexibility, we allow re-generating if requested (e.g. if it was an error)
    
    process_section_content_task.delay(section_id, trigger_next=False)
    
    return {"message": "Geração de conteúdo iniciada para a seção", "section_id": section_id}
