"""
Image Extraction Service - Extracts cropped images from slide PDFs using PyMuPDF.
"""

import os
import logging
from typing import Dict, Tuple
from uuid import UUID

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def normalize_crop_coordinates(
    crop_info: Dict[str, float], page_width: float, page_height: float
) -> Tuple[float, float, float, float]:
    """
    Converte coordenadas normalizadas (0-1000) para pixels reais da página.
    
    Args:
        crop_info: dict com {xmin, ymin, xmax, ymax} em escala 0-1000
        page_width: largura da página em pixels
        page_height: altura da página em pixels
    
    Returns:
        tuple (x0, y0, x1, y1) em pixels
    """
    x0 = (float(crop_info["xmin"]) / 1000.0) * page_width
    y0 = (float(crop_info["ymin"]) / 1000.0) * page_height
    x1 = (float(crop_info["xmax"]) / 1000.0) * page_width
    y1 = (float(crop_info["ymax"]) / 1000.0) * page_height
    
    return (x0, y0, x1, y1)


def extract_image_from_slide(
    pdf_path: str,
    page_number: int,
    crop_info: Dict[str, float],
    user_id: UUID,
    book_id: UUID,
    placeholder: str,
) -> str:
    """
    Extrai uma região específica de uma página PDF como imagem.
    
    Args:
        pdf_path: caminho para o PDF do slide
        page_number: número da página (1-indexed)
        crop_info: coordenadas de crop {xmin, ymin, xmax, ymax} (0-1000)
        user_id: ID do usuário (para estrutura de diretórios)
        book_id: ID do livro (para estrutura de diretórios)
        placeholder: nome do placeholder (ex: "[IMAGE_1]") para nomear o arquivo
    
    Returns:
        caminho absoluto para a imagem extraída
    
    Raises:
        FileNotFoundError: se o PDF não existir
        ValueError: se a página for inválida ou coordenadas inválidas
        Exception: outros erros de processamento
    """
    # Validar se o PDF existe
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")
    
    try:
        # Abrir o documento PDF
        doc = fitz.open(pdf_path)
        
        # Validar número da página (PyMuPDF usa 0-indexed)
        if page_number < 1 or page_number > len(doc):
            raise ValueError(
                f"Página {page_number} inválida. PDF tem {len(doc)} página(s)."
            )
        
        page = doc[page_number - 1]  # Converter para 0-indexed
        
        # Obter dimensões da página
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height
        
        logger.info(
            f"Extraindo imagem da página {page_number} "
            f"(dimensões: {page_width}x{page_height})"
        )
        
        # Converter coordenadas normalizadas para pixels
        x0, y0, x1, y1 = normalize_crop_coordinates(
            crop_info, page_width, page_height
        )
        
        # Validar coordenadas
        if x0 >= x1 or y0 >= y1:
            raise ValueError(
                f"Coordenadas de crop inválidas: ({x0}, {y0}, {x1}, {y1})"
            )
        
        # Criar retângulo de crop
        crop_rect = fitz.Rect(x0, y0, x1, y1)
        
        # Renderizar a região como imagem com alta qualidade
        # Matriz de transformação para 2x zoom (melhor qualidade)
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat, clip=crop_rect)
        
        # Criar diretório de destino se não existir
        # Estrutura: /app/media/{user_id}/{book_id}/extracted_images/
        media_root = os.getenv("MEDIA_STORAGE_PATH", "/app/media")
        output_dir = os.path.join(
            media_root, str(user_id), str(book_id), "extracted_images"
        )
        os.makedirs(output_dir, exist_ok=True)
        
        # Gerar nome do arquivo baseado no placeholder
        # Remove caracteres especiais do placeholder para usar como nome
        safe_placeholder = placeholder.replace("[", "").replace("]", "").lower()
        output_filename = f"{safe_placeholder}.png"
        output_path = os.path.join(output_dir, output_filename)
        
        # Salvar a imagem
        pix.save(output_path)
        
        # Fechar o documento
        doc.close()
        
        logger.info(f"Imagem extraída com sucesso: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Erro ao extrair imagem do PDF {pdf_path}: {e}")
        raise
