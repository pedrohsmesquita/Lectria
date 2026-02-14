"""
Transcript Routes - API endpoints for transcription and slide upload
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import os
import uuid
import shutil

from database import get_db
from models.books import Books
from models.transcriptions import Transcription
from models.slides import Slide
from security import get_current_user

router = APIRouter(prefix="/transcripts", tags=["transcripts"])

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_transcripts(
    book_id: UUID = Form(...),
    transcripts: List[UploadFile] = File(...),
    pdfs: Optional[List[UploadFile]] = File(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload transcripts and slide PDFs for a specific book.
    Files are stored in media/user_id/book_id/uploads/
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
            detail="Book not found or you don't have permission"
        )
    
    # Define storage paths
    media_storage_path = os.getenv("MEDIA_STORAGE_PATH", "/app/media")
    # Base structure: media/user_id/book_id/uploads/
    uploads_dir = os.path.join(media_storage_path, str(user_id), str(book_id), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    
    saved_transcripts = []
    saved_slides = []
    
    # Process Transcripts
    for file in transcripts:
        # Generate unique filename to avoid collisions if needed, 
        # but the prompt implies keeping name or at least saving mapping.
        # We'll prepend UUID to avoid overwrite but keep original name in DB.
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        storage_path = os.path.join(uploads_dir, unique_filename)
        
        with open(storage_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        new_transcription = Transcription(
            book_id=book_id,
            filename=file.filename,
            storage_path=storage_path
        )
        db.add(new_transcription)
        saved_transcripts.append({
            "id": str(new_transcription.id),
            "filename": file.filename
        })

    # Process Slides (PDFs)
    if pdfs:
        for file in pdfs:
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            storage_path = os.path.join(uploads_dir, unique_filename)
            
            with open(storage_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            new_slide = Slide(
                book_id=book_id,
                filename=file.filename,
                storage_path=storage_path
            )
            db.add(new_slide)
            saved_slides.append({
                "id": str(new_slide.id),
                "filename": file.filename
            })
            
    db.commit()
    
    return {
        "message": "Files uploaded successfully",
        "book_id": str(book_id),
        "transcripts": saved_transcripts,
        "slides": saved_slides
    }
