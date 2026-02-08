"""
Chapter Routes - API endpoints for chapter and section management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from database import get_db
from models.chapters import Chapters
from models.sections import Sections
from models.books import Books
from models.videos import Videos
from schemas.chapter_schemas import ChapterResponse, SectionResponse, ChapterUpdate, SectionUpdate
from security import get_current_user

router = APIRouter(prefix="/books", tags=["chapters"])


def verify_book_ownership(book_id: UUID, user_id: str, db: Session) -> Books:
    """
    Verify that the book belongs to the authenticated user.
    Returns the book if ownership is valid, raises 404/403 otherwise.
    """
    book = db.query(Books).filter(Books.id == book_id).first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Livro não encontrado"
        )
    
    if str(book.author_profile_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar este livro"
        )
    
    return book


@router.get("/{book_id}/chapters", response_model=List[ChapterResponse])
async def get_book_chapters(
    book_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all chapters and sections for a specific book.
    
    Returns chapters ordered by 'order' field, with nested sections also ordered.
    Only the book owner can access this endpoint.
    """
    user_id = current_user["id"]
    
    # Verify ownership
    verify_book_ownership(book_id, user_id, db)
    
    # Get all chapters for this book, ordered
    chapters = db.query(Chapters).filter(
        Chapters.book_id == book_id
    ).order_by(Chapters.order).all()
    
    # Build response with sections
    result = []
    for chapter in chapters:
        # Get sections for this chapter with video info
        sections_data = []
        for section in chapter.sections:
            # Get video filename
            video = db.query(Videos).filter(Videos.id == section.video_id).first()
            video_filename = video.filename if video else None
            
            sections_data.append(SectionResponse(
                id=section.id,
                chapter_id=section.chapter_id,
                video_id=section.video_id,
                title=section.title,
                order=section.order,
                start_time=section.start_time,
                end_time=section.end_time,
                content_markdown=section.content_markdown,
                status=section.status,
                video_filename=video_filename
            ))
        
        result.append(ChapterResponse(
            id=chapter.id,
            book_id=chapter.book_id,
            title=chapter.title,
            order=chapter.order,
            created_at=chapter.created_at,
            sections=sections_data
        ))
    
    return result


@router.put("/chapters/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(
    chapter_id: UUID,
    update_data: ChapterUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a chapter's title.
    
    Only the book owner can update chapters.
    """
    user_id = current_user["id"]
    
    # Get chapter
    chapter = db.query(Chapters).filter(Chapters.id == chapter_id).first()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capítulo não encontrado"
        )
    
    # Verify book ownership
    verify_book_ownership(chapter.book_id, user_id, db)
    
    # Update title
    chapter.title = update_data.title
    db.commit()
    db.refresh(chapter)
    
    # Build response with sections
    sections_data = []
    for section in chapter.sections:
        video = db.query(Videos).filter(Videos.id == section.video_id).first()
        video_filename = video.filename if video else None
        
        sections_data.append(SectionResponse(
            id=section.id,
            chapter_id=section.chapter_id,
            video_id=section.video_id,
            title=section.title,
            order=section.order,
            start_time=section.start_time,
            end_time=section.end_time,
            content_markdown=section.content_markdown,
            status=section.status,
            video_filename=video_filename
        ))
    
    return ChapterResponse(
        id=chapter.id,
        book_id=chapter.book_id,
        title=chapter.title,
        order=chapter.order,
        created_at=chapter.created_at,
        sections=sections_data
    )


@router.put("/sections/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: UUID,
    update_data: SectionUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a section's title and/or content_markdown.
    
    Only the book owner can update sections.
    """
    user_id = current_user["id"]
    
    # Get section
    section = db.query(Sections).filter(Sections.id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seção não encontrada"
        )
    
    # Get chapter to verify book ownership
    chapter = db.query(Chapters).filter(Chapters.id == section.chapter_id).first()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capítulo não encontrado"
        )
    
    # Verify book ownership
    verify_book_ownership(chapter.book_id, user_id, db)
    
    # Update fields if provided
    if update_data.title is not None:
        section.title = update_data.title
    if update_data.content_markdown is not None:
        section.content_markdown = update_data.content_markdown
    
    db.commit()
    db.refresh(section)
    
    # Get video filename
    video = db.query(Videos).filter(Videos.id == section.video_id).first()
    video_filename = video.filename if video else None
    
    return SectionResponse(
        id=section.id,
        chapter_id=section.chapter_id,
        video_id=section.video_id,
        title=section.title,
        order=section.order,
        start_time=section.start_time,
        end_time=section.end_time,
        content_markdown=section.content_markdown,
        status=section.status,
        video_filename=video_filename
    )
