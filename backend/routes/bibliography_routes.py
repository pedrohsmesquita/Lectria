"""
Bibliography Routes - API endpoints for managing bibliography chapter
"""
import re
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List
from uuid import UUID

from database import get_db
from models.chapters import Chapters
from models.sections import Sections
from models.global_references import GlobalReferences
from schemas.chapter_schemas import BibliographyUpdate, BibliographyUpdateResponse
from security import get_current_user

router = APIRouter(prefix="/books", tags=["bibliography"])
logger = logging.getLogger(__name__)


def _verify_book_ownership(book_id: UUID, user_id: str, db: Session):
    from models.books import Books
    book = db.query(Books).filter(Books.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livro não encontrado")
    if str(book.author_profile_id) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    return book


def _parse_bibliography_markdown(markdown: str) -> Dict[int, str]:
    """
    Parse bibliography markdown into a dict: {reference_number: full_reference_text}.
    Expects lines like: [1] SILVA, João. Título. Editora, 2022.
    """
    pattern = re.compile(r"^\[(\d+)\]\s+(.+)$", re.MULTILINE)
    result = {}
    for match in pattern.finditer(markdown):
        num = int(match.group(1))
        text = match.group(2).strip()
        result[num] = text
    return result


def _replace_citations_in_markdown(markdown: str, old_num: int, temp_marker: str) -> str:
    """Replace [old_num] citation with a temp marker to avoid cascading replacements."""
    # Match [N] but not [IMAGE_N] or similar
    return re.sub(rf"(?<!\w)\[{old_num}\](?!\w)", temp_marker, markdown)


@router.put("/{book_id}/bibliography", response_model=BibliographyUpdateResponse)
async def update_bibliography(
    book_id: UUID,
    update_data: BibliographyUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the bibliography chapter content.

    This endpoint:
    1. Parses the submitted markdown line by line.
    2. Compares each entry with the DB global_references.
    3. Renames/renumbers references atomically.
    4. Removes references that were deleted from the markdown (and cleans citations from all sections).
    5. Updates all section markdowns to reflect renumbering.
    6. Saves the new bibliography markdown content.
    """
    user_id = current_user["id"]
    _verify_book_ownership(book_id, user_id, db)

    # 1. Parse the submitted markdown
    submitted = _parse_bibliography_markdown(update_data.content_markdown)
    if not submitted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma referência encontrada no markdown. Formato esperado: [1] Texto da referência..."
        )

    # 2. Fetch all current references from DB
    current_refs: List[GlobalReferences] = db.query(GlobalReferences).filter(
        GlobalReferences.book_id == book_id
    ).order_by(GlobalReferences.reference_number.asc()).all()

    # Build lookup: number -> ref object
    current_by_number: Dict[int, GlobalReferences] = {r.reference_number: r for r in current_refs}

    # 3. Determine which old reference keys map to new numbers
    # Strategy: match by text similarity OR position (if user reordered)
    # Build reverse lookup: ref_text -> old_number
    old_text_to_number: Dict[str, int] = {r.full_reference_abnt: r.reference_number for r in current_refs}

    # Map: old_number -> new_number (for renumbering citations in sections)
    renumber_map: Dict[int, int] = {}

    # Track which old refs are being kept/updated (by old number)
    kept_old_numbers = set()

    # For each entry in submitted markdown
    for new_num, new_text in submitted.items():
        # Try to find the matching existing ref by text
        if new_text in old_text_to_number:
            old_num = old_text_to_number[new_text]
            kept_old_numbers.add(old_num)
            if old_num != new_num:
                renumber_map[old_num] = new_num
        else:
            # New reference text (not previously in DB): check if there's a ref with this number to update
            if new_num in current_by_number:
                old_ref = current_by_number[new_num]
                kept_old_numbers.add(old_num := old_ref.reference_number)
                # Text changed, update it
                old_ref.full_reference_abnt = new_text
            # If neither exists, this is a brand new reference — add it
            else:
                new_ref = GlobalReferences(
                    book_id=book_id,
                    reference_key=f"REF:MANUAL_{new_num}",
                    reference_number=new_num,
                    full_reference_abnt=new_text
                )
                db.add(new_ref)
                kept_old_numbers.add(new_num)

    # 4. Find deleted references (old numbers NOT present in submitted)
    deleted_old_numbers = set(current_by_number.keys()) - kept_old_numbers
    for old_num in deleted_old_numbers:
        ref = current_by_number[old_num]
        db.delete(ref)
        logger.info(f"Deleted reference [{old_num}] from book {book_id}")

    db.flush()  # Apply deletes and text updates before renumbering

    # 5. Apply renumbering on DB
    # Use temporary negative numbers to avoid unique constraint violations during swap
    for old_num, new_num in renumber_map.items():
        if old_num in current_by_number:
            ref = current_by_number[old_num]
            ref.reference_number = -(new_num)  # temp negative
    db.flush()

    for old_num, new_num in renumber_map.items():
        if old_num in current_by_number:
            ref = current_by_number[old_num]
            ref.reference_number = new_num  # finalize
    db.flush()

    # 6. Update citations in all content sections
    # Collect all non-bibliography sections of this book
    non_bib_sections: List[Sections] = (
        db.query(Sections)
        .join(Chapters)
        .filter(
            Chapters.book_id == book_id,
            Chapters.is_bibliography == False
        )
        .all()
    )

    sections_affected = 0

    if renumber_map or deleted_old_numbers:
        for section in non_bib_sections:
            if not section.content_markdown:
                continue

            original = section.content_markdown
            modified = original

            # Step A: Replace old numbers with temp markers (avoid cascading)
            temp_markers = {}
            for old_num, new_num in renumber_map.items():
                marker = f"[__BIBREF_{old_num}__]"
                temp_markers[marker] = new_num
                modified = _replace_citations_in_markdown(modified, old_num, marker)

            # Step B: Remove deleted citations (replace with empty string)
            for old_num in deleted_old_numbers:
                modified = re.sub(rf"(?<!\w)\[{old_num}\](?!\w)", "", modified)

            # Step C: Replace temp markers with new numbers
            for marker, new_num in temp_markers.items():
                modified = modified.replace(marker, f"[{new_num}]")

            if modified != original:
                section.content_markdown = modified
                sections_affected += 1

    # 7. Update the bibliography chapter section with new content
    bib_chapter = db.query(Chapters).filter(
        Chapters.book_id == book_id,
        Chapters.is_bibliography == True
    ).first()

    if bib_chapter:
        bib_section = db.query(Sections).filter(
            Sections.chapter_id == bib_chapter.id
        ).first()
        if bib_section:
            bib_section.content_markdown = update_data.content_markdown
    else:
        # No bibliography chapter yet — create it
        from sqlalchemy import func as sqlfunc
        max_order = db.query(sqlfunc.max(Chapters.order)).filter(
            Chapters.book_id == book_id
        ).scalar() or 0

        bib_chapter = Chapters(
            book_id=book_id,
            title="Referências",
            order=max_order + 1,
            is_bibliography=True
        )
        db.add(bib_chapter)
        db.flush()

        new_bib_section = Sections(
            chapter_id=bib_chapter.id,
            title="Lista de Referências",
            order=1,
            start_time=0.0,
            end_time=0.0,
            content_markdown=update_data.content_markdown,
            status="SUCESSO"
        )
        db.add(new_bib_section)

    db.commit()

    logger.info(
        f"Bibliography updated for book {book_id}: "
        f"{len(renumber_map)} renumbered, {len(deleted_old_numbers)} deleted, "
        f"{sections_affected} sections updated"
    )

    return BibliographyUpdateResponse(
        message="Bibliografia atualizada com sucesso",
        references_updated=len(renumber_map) + len(deleted_old_numbers),
        sections_affected=sections_affected,
        content_markdown=update_data.content_markdown
    )
