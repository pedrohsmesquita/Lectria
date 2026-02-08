"""
Book Routes - API endpoints for book management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID
import os

from database import get_db
from models.books import Books
from models.videos import Videos
from models.user_profiles import UserProfiles
from schemas.book_schemas import BookCreate, BookResponse, BookDetailResponse
from security import get_current_user

router = APIRouter(prefix="/books", tags=["books"])


# ============================================
# Helper Functions
# ============================================

def verify_book_ownership(book_id: UUID, user_id: UUID, db: Session) -> Books:
    """
    Verify that the book belongs to the authenticated user.
    Returns the book if ownership is valid, raises 404 otherwise.
    """
    book = db.query(Books).filter(Books.id == book_id).first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    if str(book.author_profile_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this book"
        )
    
    return book


# ============================================
# Endpoints
# ============================================

@router.get("", response_model=List[BookResponse])
async def list_books(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all books belonging to the authenticated user.
    Returns books with video count.
    """
    user_id = current_user["id"]
    
    # Query books with video count
    books_with_count = (
        db.query(
            Books,
            func.count(Videos.id).label("video_count")
        )
        .outerjoin(Videos, Books.id == Videos.book_id)
        .filter(Books.author_profile_id == user_id)
        .group_by(Books.id)
        .order_by(Books.created_at.desc())
        .all()
    )
    
    # Format response
    result = []
    for book, video_count in books_with_count:
        result.append(BookResponse(
            id=book.id,
            title=book.title,
            author=book.author,
            status=book.status,
            created_at=book.created_at,
            video_count=video_count
        ))
    
    return result


@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book_data: BookCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new book for the authenticated user.
    The author field is automatically filled with the user's full name.
    """
    user_id = current_user["id"]
    
    # Get user profile to retrieve full name
    user_profile = db.query(UserProfiles).filter(
        UserProfiles.user_auth_id == user_id
    ).first()
    
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Create new book
    new_book = Books(
        author_profile_id=user_id,
        title=book_data.title,
        author=user_profile.full_name,
        status="PENDING"
    )
    
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    
    # Create book folder in media_storage/{user_id}/{book_id}
    media_storage_path = os.getenv("MEDIA_STORAGE_PATH", "/app/media")
    book_folder = os.path.join(media_storage_path, str(user_id), str(new_book.id))
    os.makedirs(book_folder, exist_ok=True)
    
    return BookResponse(
        id=new_book.id,
        title=new_book.title,
        author=new_book.author,
        status=new_book.status,
        created_at=new_book.created_at,
        video_count=0
    )


@router.get("/{book_id}", response_model=BookDetailResponse)
async def get_book_details(
    book_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific book, including all associated videos.
    Only the book owner can access this endpoint.
    """
    user_id = current_user["id"]
    
    # Verify ownership
    book = verify_book_ownership(book_id, user_id, db)
    
    # Get all videos for this book
    videos = db.query(Videos).filter(Videos.book_id == book_id).order_by(Videos.created_at.desc()).all()
    
    # Format videos
    videos_list = [
        {
            "id": str(video.id),
            "filename": video.filename,
            "duration": video.duration,
            "storage_path": video.storage_path,
            "created_at": video.created_at.isoformat()
        }
        for video in videos
    ]
    
    return BookDetailResponse(
        id=book.id,
        title=book.title,
        author=book.author,
        status=book.status,
        created_at=book.created_at,
        videos=videos_list
    )
