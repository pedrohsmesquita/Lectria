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
from models.global_references import GlobalReferences
from services.image_extraction_service import extract_image_from_slide

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
        "reference": ParagraphStyle(
            "Reference",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leftIndent=0.5 * cm,
            firstLineIndent=-0.5 * cm,
        ),
        "toc_title": ParagraphStyle(
            "TocTitle",
            parent=base["Heading1"],
            fontSize=22,
            leading=28,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=HexColor("#16213e"),
        ),
        "toc_chapter": ParagraphStyle(
            "TocChapter",
            parent=base["Normal"],
            fontSize=12,
            leading=16,
            spaceBefore=10,
            textColor=HexColor("#16213e"),
            fontName="Helvetica-Bold",
        ),
        "toc_section": ParagraphStyle(
            "TocSection",
            parent=base["Normal"],
            fontSize=11,
            leading=14,
            leftIndent=1 * cm,
            textColor=HexColor("#333333"),
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

    # 4. Buscar referências bibliográficas (se existirem)
    references: List[GlobalReferences] = (
        db.query(GlobalReferences)
        .filter(GlobalReferences.book_id == book_id)
        .order_by(GlobalReferences.reference_number.asc())
        .all()
    )

    # 5. Montar o PDF
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

    # --- Sumário (TOC) ---
    story.append(Paragraph("Sumário", styles["toc_title"]))
    story.append(Spacer(1, 1 * cm))

    for chapter, sections in chapter_sections:
        # Linha do capítulo no sumário
        story.append(Paragraph(f"Capítulo {chapter.order} — {chapter.title}", styles["toc_chapter"]))
        
        for section in sections:
            # Linha da seção no sumário (com recuo e numeração X.Y)
            section_number = f"{chapter.order}.{section.order}"
            story.append(Paragraph(f"{section_number} {section.title}", styles["toc_section"]))
            
    # Incluir Referências no sumário se existirem
    if references:
        next_chapter_number = len(chapters) + 1
        story.append(Paragraph(f"Capítulo {next_chapter_number} — Referências", styles["toc_chapter"]))

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

            
            # Código para inserir imagem no pdf
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
                            
                            if asset:
                                img_path = None
                                
                                # Verificar o tipo de fonte do asset
                                if asset.source_type == "SLIDE":
                                    # Extrair imagem do PDF do slide
                                    if asset.slide_page is not None and asset.crop_info:
                                        try:
                                            # storage_path aponta para o PDF do slide
                                            slide_pdf_path = asset.storage_path
                                            if not os.path.isabs(slide_pdf_path):
                                                media_root = os.getenv("MEDIA_STORAGE_PATH", "/app/media")
                                                slide_pdf_path = os.path.join(media_root, slide_pdf_path)
                                            
                                            # Extrair a imagem usando o serviço
                                            img_path = extract_image_from_slide(
                                                pdf_path=slide_pdf_path,
                                                page_number=asset.slide_page,
                                                crop_info=asset.crop_info,
                                                user_id=book.author_profile_id,
                                                book_id=book.id,
                                                placeholder=ph,
                                            )
                                        except Exception as e:
                                            logger.error(f"Erro ao extrair imagem do slide para {ph}: {e}")
                                            img_path = None
                                    else:
                                        logger.warning(f"Asset {ph} do tipo SLIDE sem slide_page ou crop_info")
                                
                                elif asset.source_type == "VIDEO":
                                    # Usar caminho direto para imagens já extraídas de vídeo
                                    img_path = asset.storage_path
                                    if not os.path.isabs(img_path):
                                        media_root = os.getenv("MEDIA_STORAGE_PATH", "/app/media")
                                        img_path = os.path.join(media_root, img_path)
                                
                                else:
                                    logger.warning(f"Asset {ph} com source_type desconhecido: {asset.source_type}")
                                
                                # Inserir a imagem se o caminho foi obtido
                                if img_path and os.path.isfile(img_path):
                                    try:
                                        img = Image(img_path, width=14 * cm, height=9 * cm)
                                        img.hAlign = "CENTER"
                                        story.append(img)
                                        
                                        # Adicionar legenda se disponível
                                        if asset.caption:
                                            story.append(Paragraph(asset.caption, styles["caption"]))
                                    except Exception as e:
                                        logger.warning(f"Falha ao inserir imagem {img_path}: {e}")
                                elif img_path:
                                    logger.warning(f"Arquivo de imagem não encontrado: {img_path}")
                else:
                    story.append(Paragraph(para_text, styles["body"]))

        # Quebra de página entre capítulos
        story.append(PageBreak())

    # --- Capítulo de Referências (se existirem) ---
    if references:
        # Calcular o número do próximo capítulo
        next_chapter_number = len(chapters) + 1
        
        story.append(
            Paragraph(
                f"Capítulo {next_chapter_number} — Referências",
                styles["chapter_title"]
            )
        )
        story.append(Spacer(1, 0.5 * cm))
        
        # Listar cada referência
        for ref in references:
            ref_text = f"[{ref.reference_number}] {ref.full_reference_abnt}"
            story.append(Paragraph(ref_text, styles["reference"]))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    logger.info(f"PDF gerado para o livro '{book.title}' ({len(pdf_bytes)} bytes)")
    return pdf_bytes, book.title
