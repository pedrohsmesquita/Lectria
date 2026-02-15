"""
PDF Service - Generates a complete PDF ebook from a Book's chapters and sections.
Uses ReportLab for PDF rendering and markdown+BeautifulSoup for content conversion.
"""

import io
import os
import re
import logging
from uuid import UUID
from typing import List, Tuple

import markdown
from bs4 import BeautifulSoup
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    Table,
    TableStyle,
)

from models.books import Books
from models.chapters import Chapters
from models.sections import Sections
from models.section_assets import SectionAssets

logger = logging.getLogger(__name__)

# ============================================
# Estilos personalizados do PDF
# ============================================

def _build_styles() -> dict:
    """Cria a paleta de estilos reutilizáveis para o documento."""
    base = getSampleStyleSheet()

    styles = {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=base["Title"],
            fontSize=28,
            leading=34,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=HexColor("#1a1a2e"),
        ),
        "cover_author": ParagraphStyle(
            "CoverAuthor",
            parent=base["Normal"],
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            textColor=HexColor("#555555"),
        ),
        "chapter_title": ParagraphStyle(
            "ChapterTitle",
            parent=base["Heading1"],
            fontSize=22,
            leading=28,
            spaceBefore=30,
            spaceAfter=14,
            textColor=HexColor("#16213e"),
        ),
        "section_title": ParagraphStyle(
            "SectionTitle",
            parent=base["Heading2"],
            fontSize=16,
            leading=20,
            spaceBefore=20,
            spaceAfter=10,
            textColor=HexColor("#0f3460"),
        ),
        "body": ParagraphStyle(
            "BodyText",
            parent=base["Normal"],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ),
        "caption": ParagraphStyle(
            "ImageCaption",
            parent=base["Italic"],
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            spaceAfter=12,
            textColor=HexColor("#666666"),
        ),
    }
    return styles


# ============================================
# Conversão Markdown → texto limpo
# ============================================

def _markdown_to_paragraphs(md_text: str) -> List[str]:
    """
    Converte Markdown para uma lista de parágrafos em texto limpo,
    preservando quebras de linha entre blocos.
    """
    html = markdown.markdown(md_text or "", extensions=["extra"])
    soup = BeautifulSoup(html, "html.parser")

    paragraphs: List[str] = []
    for element in soup.find_all(["p", "li", "h1", "h2", "h3", "h4"]):
        text = element.get_text(separator=" ", strip=True)
        if text:
            paragraphs.append(text)

    # Fallback: se o parser não produziu parágrafos, dividir por linhas vazias
    if not paragraphs:
        raw = BeautifulSoup(html, "html.parser").get_text()
        paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]

    return paragraphs


# ============================================
# Numeração de página no rodapé
# ============================================

def _footer(canvas, doc):
    """Desenha o número da página centralizado no rodapé."""
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(HexColor("#888888"))
    page_num = canvas.getPageNumber()
    canvas.drawCentredString(A4[0] / 2, 15 * mm, f"— {page_num} —")
    canvas.restoreState()


# ============================================
# Função principal
# ============================================

def generate_book_pdf(book_id: UUID, db: Session) -> Tuple[bytes, str]:
    """
    Gera o PDF completo de um livro.

    Returns:
        Tuple de (pdf_bytes, book_title) para que a rota possa montar
        o header Content-Disposition com o título original.

    Raises:
        HTTPException 404 – livro não encontrado.
        HTTPException 409 – nem todas as seções estão com status SUCCESS.
    """

    # 1. Buscar livro
    book: Books | None = db.query(Books).filter(Books.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Livro não encontrado.",
        )

    # 2. Capítulos ordenados
    chapters: List[Chapters] = (
        db.query(Chapters)
        .filter(Chapters.book_id == book_id)
        .order_by(Chapters.order.asc())
        .all()
    )

    # 3. Seções por capítulo + verificação de prontidão
    chapter_sections: list[Tuple[Chapters, List[Sections]]] = []
    not_ready_count = 0

    for chapter in chapters:
        sections: List[Sections] = (
            db.query(Sections)
            .filter(Sections.chapter_id == chapter.id)
            .order_by(Sections.order.asc())
            .all()
        )
        for section in sections:
            if section.status not in ["SUCCESS", "SUCESSO"]:
                not_ready_count += 1
        chapter_sections.append((chapter, sections))

    if not_ready_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"O livro ainda não está pronto. "
                f"{not_ready_count} seção(ões) pendentes ou com erro."
            ),
        )

    # 4. Montar o PDF
    styles = _build_styles()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        title=book.title,
        author=book.author,
    )

    story: list = []

    # --- Capa ---
    story.append(Spacer(1, 6 * cm))
    story.append(Paragraph(book.title, styles["cover_title"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(book.author, styles["cover_author"]))
    story.append(PageBreak())

    # --- Conteúdo por capítulo ---
    for chapter, sections in chapter_sections:
        story.append(Paragraph(f"Capítulo {chapter.order} — {chapter.title}", styles["chapter_title"]))

        for section in sections:
            story.append(Paragraph(section.title, styles["section_title"]))

            # Buscar assets da seção para substituir placeholders
            assets: List[SectionAssets] = (
                db.query(SectionAssets)
                .filter(SectionAssets.section_id == section.id)
                .order_by(SectionAssets.placeholder.asc())
                .all()
            )
            assets_map = {a.placeholder: a for a in assets}

            # Converter markdown em parágrafos
            paragraphs = _markdown_to_paragraphs(section.content_markdown)

            for para_text in paragraphs:
                # Verificar se o parágrafo contém algum placeholder de imagem
                placeholder_pattern = re.compile(r"\[IMAGE_\d+\]")
                found_placeholders = placeholder_pattern.findall(para_text)

                if found_placeholders:
                    # Separar o texto ao redor dos placeholders
                    parts = placeholder_pattern.split(para_text)

                    for i, part in enumerate(parts):
                        clean = part.strip()
                        if clean:
                            story.append(Paragraph(clean, styles["body"]))

                        # Inserir a imagem correspondente ao placeholder
                        if i < len(found_placeholders):
                            ph = found_placeholders[i]
                            asset = assets_map.get(ph)
                            if asset and asset.storage_path:
                                img_path = asset.storage_path
                                # Suportar caminhos relativos ao media_storage
                                if not os.path.isabs(img_path):
                                    media_root = os.getenv("MEDIA_STORAGE_PATH", "/app/media")
                                    img_path = os.path.join(media_root, img_path)

                                if os.path.isfile(img_path):
                                    try:
                                        img = Image(img_path, width=14 * cm, height=9 * cm)
                                        img.hAlign = "CENTER"
                                        story.append(img)
                                    except Exception as e:
                                        logger.warning(f"Falha ao inserir imagem {img_path}: {e}")
                                        story.append(Paragraph(f"[imagem indisponível: {ph}]", styles["caption"]))
                                else:
                                    logger.warning(f"Arquivo de imagem não encontrado: {img_path}")
                                    story.append(Paragraph(f"[imagem não encontrada: {ph}]", styles["caption"]))

                                # Legenda
                                if asset.caption:
                                    story.append(Paragraph(asset.caption, styles["caption"]))
                else:
                    story.append(Paragraph(para_text, styles["body"]))

        # Quebra de página entre capítulos
        story.append(PageBreak())

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    logger.info(f"PDF gerado para o livro '{book.title}' ({len(pdf_bytes)} bytes)")
    return pdf_bytes, book.title
