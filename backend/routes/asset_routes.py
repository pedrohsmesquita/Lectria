"""
Asset Routes - API endpoints for managing section assets (images)
"""
import os
import shutil
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID

from database import get_db
from models.section_assets import SectionAssets
from models.sections import Sections
from models.chapters import Chapters
from models.books import Books
from security import get_current_user
from routes.chapter_routes import verify_book_ownership

router = APIRouter(prefix="/assets", tags=["assets"])

@router.post("/{section_id}")
async def upload_manual_asset(
    section_id: UUID,
    caption: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a manual image for a section and insert its placeholder into the markdown.
    """
    user_id = current_user["id"]
    
    # Verify section and ownership
    section = db.query(Sections).filter(Sections.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Seção não encontrada")
    
    chapter = section.chapter
    book = chapter.book
    verify_book_ownership(book.id, user_id, db)
    
    # Check status (optional, but keep consistent with structure updates)
    if section.status == "PROCESSANDO":
        raise HTTPException(
            status_code=400, 
            detail="Não é possível adicionar imagens enquanto a seção está sendo processada."
        )

    # Calculate next placeholder
    existing_assets = db.query(SectionAssets).filter(SectionAssets.section_id == section_id).all()
    max_n = 0
    import re
    for asset in existing_assets:
        match = re.search(r'\[IMAGE_(\d+)\]', asset.placeholder)
        if match:
            max_n = max(max_n, int(match.group(1)))
    
    new_n = max_n + 1
    placeholder = f"[IMAGE_{new_n}]"
    
    # Save file
    media_root = os.getenv("MEDIA_STORAGE_PATH", "/app/media")
    upload_dir = os.path.join(media_root, str(user_id), str(book.id), "extracted_images", str(section_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    file_extension = os.path.splitext(file.filename)[1] or ".png"
    safe_filename = f"manual_{new_n}{file_extension}"
    file_path = os.path.join(upload_dir, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create DB entry
    new_asset = SectionAssets(
        section_id=section_id,
        placeholder=placeholder,
        caption=caption,
        source_type='MANUAL',
        storage_path=file_path
    )
    db.add(new_asset)
    
    # Append to markdown
    # Ensure it's surrounded by \n\n
    if section.content_markdown:
        # Add newlines if not already there
        content = section.content_markdown.strip()
        section.content_markdown = f"{content}\n\n{placeholder}\n\n"
    else:
        section.content_markdown = f"\n\n{placeholder}\n\n"
    
    db.commit()
    db.refresh(new_asset)
    
    return {
        "message": "Imagem enviada com sucesso",
        "asset": {
            "id": new_asset.id,
            "placeholder": new_asset.placeholder,
            "caption": new_asset.caption,
            "storage_path": new_asset.storage_path
        }
    }

@router.put("/{asset_id}")
async def update_asset(
    asset_id: UUID,
    caption: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update metadata (caption) or replace the image file of an asset"""
    asset = db.query(SectionAssets).filter(SectionAssets.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")
    
    section = asset.section
    verify_book_ownership(section.chapter.book_id, current_user["id"], db)
    
    if caption is not None:
        asset.caption = caption
        
    if file:
        # Replace existing file
        old_path = asset.storage_path
        
        # We reuse the directory and filename logic from upload
        upload_dir = os.path.dirname(old_path)
        os.makedirs(upload_dir, exist_ok=True)
        
        # To avoid caching issues and be safe, we can generate a new unique name 
        # or just overwrite. Overwriting might be better to keep the same name,
        # but the browser might cache it. Let's use a timestamp or uuid in name.
        file_extension = os.path.splitext(file.filename)[1] or ".png"
        new_filename = f"replaced_{uuid.uuid4().hex[:8]}{file_extension}"
        new_path = os.path.join(upload_dir, new_filename)
        
        with open(new_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Update path in DB
        asset.storage_path = new_path
        
        # Delete old file
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception as e:
                print(f"Error deleting old file during replacement: {e}")

    db.commit()
    return {
        "message": "Recurso atualizado", 
        "caption": asset.caption,
        "storage_path": asset.storage_path
    }

@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an asset and remove its placeholder from markdown"""
    asset = db.query(SectionAssets).filter(SectionAssets.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")
    
    section = asset.section
    verify_book_ownership(section.chapter.book_id, current_user["id"], db)
    
    placeholder = asset.placeholder
    file_path = asset.storage_path
    
    # Remove from markdown
    if section.content_markdown:
        import re
        # Pattern to find the placeholder and surrounding blank lines
        pattern = re.compile(r'\n*\s*' + re.escape(placeholder) + r'\s*\n*')
        section.content_markdown = pattern.sub('\n\n', section.content_markdown).strip()
    
    # Delete file if it exists
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
            
    # Delete from DB
    db.delete(asset)
    db.commit()
    
    return {"message": "Imagem removida com sucesso"}
