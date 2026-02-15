"""
Book Export Routes - Endpoint for PDF generation and download.
"""

import re
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database import get_db
from services.pdf_service import generate_book_pdf

router = APIRouter(prefix="/books", tags=["books-export"])


def _sanitize_filename(name: str) -> str:
    """Remove caracteres inválidos para nomes de arquivo."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    return clean.strip() or "ebook"


@router.get("/{book_id}/export/pdf")
async def export_book_pdf(
    book_id: UUID,
    db: Session = Depends(get_db),
) -> Response:
    """
    Gera e retorna o PDF completo do livro.
    Erros 404 (livro inexistente) e 409 (seções incompletas)
    propagam naturalmente via HTTPException do service.
    """
    pdf_bytes, book_title = generate_book_pdf(book_id, db)
    safe_title = _sanitize_filename(book_title)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_title}.pdf"'
        },
    )
