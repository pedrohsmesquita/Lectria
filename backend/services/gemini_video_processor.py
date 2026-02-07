"""
Serviço de processamento de vídeo com Google Gemini.

Este módulo é responsável por enviar videoaulas para a API do Gemini 2.0 Flash
e receber de volta uma estrutura JSON com capítulos e seções para o livro didático.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import google.generativeai as genai

logger = logging.getLogger(__name__)

# Extensões de vídeo suportadas
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}

# System instruction para o Gemini (Arquiteto Educacional)
SYSTEM_INSTRUCTION = """Você é um Arquiteto Educacional especializado em transformar videoaulas em estruturas de livros didáticos.

Sua tarefa é assistir ao vídeo fornecido e gerar um JSON com a seguinte estrutura:

{
  "book_title": "string - Título sugerido para o livro",
  "chapters": [
    {
      "chapter_number": 1,
      "title": "string - Título do capítulo",
      "description": "string - Breve descrição do tema",
      "sections": [
        {
          "section_number": 1,
          "title": "string - Título da seção",
          "start_timestamp": "string - Formato HH:MM:SS",
          "end_timestamp": "string - Formato HH:MM:SS",
          "key_concepts": ["array de conceitos principais"],
          "summary": "string - Resumo do conteúdo da seção"
        }
      ]
    }
  ]
}

Diretrizes:
- Identifique mudanças temáticas no vídeo para criar capítulos
- Cada seção deve ter 3-8 minutos de duração
- Priorize clareza e organização pedagógica
- Os timestamps devem ser precisos
- Extraia os conceitos-chave de cada seção
"""

# Prompt do usuário para solicitar a análise
USER_PROMPT = """Analise este vídeo educacional e gere a estrutura do livro didático conforme as diretrizes.

Retorne APENAS o JSON válido, sem texto adicional, sem markdown code blocks, apenas o objeto JSON puro."""


def _validate_video_file(video_path: str) -> Path:
    """
    Valida se o arquivo de vídeo existe e possui extensão suportada.
    
    Args:
        video_path: Caminho para o arquivo de vídeo
        
    Returns:
        Path: Objeto Path do arquivo validado
        
    Raises:
        FileNotFoundError: Se o arquivo não existir
        ValueError: Se a extensão não for suportada
    """
    path = Path(video_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {video_path}")
    
    if not path.is_file():
        raise ValueError(f"O caminho não aponta para um arquivo: {video_path}")
    
    extension = path.suffix.lower()
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValueError(
            f"Extensão de arquivo não suportada: {extension}. "
            f"Extensões permitidas: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        )
    
    return path


def _validate_json_structure(data: dict[str, Any]) -> None:
    """
    Valida se o JSON retornado pelo Gemini possui todos os campos obrigatórios.
    
    Args:
        data: Dicionário parseado da resposta do Gemini
        
    Raises:
        ValueError: Se algum campo obrigatório estiver ausente ou inválido
    """
    # Valida campo book_title
    if "book_title" not in data:
        raise ValueError("Campo obrigatório ausente: 'book_title'")
    
    if not isinstance(data["book_title"], str) or not data["book_title"].strip():
        raise ValueError("Campo 'book_title' deve ser uma string não vazia")
    
    # Valida campo chapters
    if "chapters" not in data:
        raise ValueError("Campo obrigatório ausente: 'chapters'")
    
    if not isinstance(data["chapters"], list):
        raise ValueError("Campo 'chapters' deve ser uma lista")
    
    if len(data["chapters"]) == 0:
        raise ValueError("A lista 'chapters' não pode estar vazia")
    
    # Valida cada capítulo
    for i, chapter in enumerate(data["chapters"]):
        _validate_chapter(chapter, i + 1)


def _validate_chapter(chapter: dict[str, Any], index: int) -> None:
    """
    Valida a estrutura de um capítulo individual.
    
    Args:
        chapter: Dicionário representando um capítulo
        index: Índice do capítulo (para mensagens de erro)
        
    Raises:
        ValueError: Se algum campo obrigatório estiver ausente ou inválido
    """
    required_fields = ["chapter_number", "title", "description", "sections"]
    
    for field in required_fields:
        if field not in chapter:
            raise ValueError(f"Capítulo {index}: campo obrigatório ausente '{field}'")
    
    if not isinstance(chapter["title"], str) or not chapter["title"].strip():
        raise ValueError(f"Capítulo {index}: 'title' deve ser uma string não vazia")
    
    if not isinstance(chapter["sections"], list):
        raise ValueError(f"Capítulo {index}: 'sections' deve ser uma lista")
    
    if len(chapter["sections"]) == 0:
        raise ValueError(f"Capítulo {index}: a lista 'sections' não pode estar vazia")
    
    # Valida cada seção do capítulo
    for j, section in enumerate(chapter["sections"]):
        _validate_section(section, index, j + 1)


def _validate_section(section: dict[str, Any], chapter_index: int, section_index: int) -> None:
    """
    Valida a estrutura de uma seção individual.
    
    Args:
        section: Dicionário representando uma seção
        chapter_index: Índice do capítulo pai
        section_index: Índice da seção
        
    Raises:
        ValueError: Se algum campo obrigatório estiver ausente ou inválido
    """
    required_fields = [
        "section_number", "title", "start_timestamp", 
        "end_timestamp", "key_concepts", "summary"
    ]
    
    prefix = f"Capítulo {chapter_index}, Seção {section_index}"
    
    for field in required_fields:
        if field not in section:
            raise ValueError(f"{prefix}: campo obrigatório ausente '{field}'")
    
    if not isinstance(section["title"], str) or not section["title"].strip():
        raise ValueError(f"{prefix}: 'title' deve ser uma string não vazia")
    
    if not isinstance(section["key_concepts"], list):
        raise ValueError(f"{prefix}: 'key_concepts' deve ser uma lista")
    
    # Valida formato dos timestamps (HH:MM:SS)
    timestamp_pattern = r"^\d{2}:\d{2}:\d{2}$"
    
    for ts_field in ["start_timestamp", "end_timestamp"]:
        ts_value = section[ts_field]
        if not isinstance(ts_value, str) or not re.match(timestamp_pattern, ts_value):
            raise ValueError(
                f"{prefix}: '{ts_field}' deve estar no formato HH:MM:SS, "
                f"recebido: '{ts_value}'"
            )


def _parse_gemini_response(response_text: str) -> dict[str, Any]:
    """
    Faz o parse da resposta do Gemini para extrair o JSON.
    
    O Gemini pode retornar o JSON envolvido em markdown code blocks,
    então precisamos limpar isso antes de fazer o parse.
    
    Args:
        response_text: Texto bruto da resposta do Gemini
        
    Returns:
        dict: JSON parseado
        
    Raises:
        ValueError: Se o JSON for inválido ou malformado
    """
    text = response_text.strip()
    
    # Remove markdown code blocks se presentes
    if text.startswith("```"):
        # Remove a primeira linha (```json ou ```)
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        
        # Remove o ``` final
        if text.endswith("```"):
            text = text[:-3].strip()
    
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Resposta do Gemini não é um JSON válido: {e}. "
            f"Resposta recebida: {response_text[:500]}..."
        )
    
    return data


async def process_video_structure(
    video_path: str,
    api_key: str
) -> dict[str, Any]:
    """
    Processa vídeo com Gemini e retorna estrutura do livro.
    
    Esta função envia um arquivo de vídeo para a API do Google Gemini 2.0 Flash,
    que analisa o conteúdo e retorna uma estrutura JSON com capítulos e seções
    para compor um livro didático.
    
    Args:
        video_path: Caminho local do arquivo de vídeo. Deve ser um arquivo
                   existente com extensão .mp4, .avi, .mov ou .mkv
        api_key: Chave da API do Google Gemini (obtida em makersuite.google.com)
        
    Returns:
        dict: JSON estruturado contendo:
            - book_title (str): Título sugerido para o livro
            - chapters (list): Lista de capítulos, cada um contendo:
                - chapter_number (int): Número sequencial do capítulo
                - title (str): Título do capítulo
                - description (str): Descrição do tema
                - sections (list): Lista de seções com timestamps e resumos
        
    Raises:
        FileNotFoundError: Se o arquivo de vídeo não existir
        ValueError: Se o vídeo tiver extensão inválida ou JSON malformado
        Exception: Se a API do Gemini falhar (timeout, erro de rede, etc.)
        
    Example:
        >>> result = await process_video_structure(
        ...     video_path="/path/to/video.mp4",
        ...     api_key="sua-api-key"
        ... )
        >>> print(result["book_title"])
        "Introdução à Programação em Python"
    """
    logger.info(f"Iniciando processamento do vídeo: {video_path}")
    
    # Etapa 1: Validar arquivo de vídeo
    video_file = _validate_video_file(video_path)
    logger.info(f"Arquivo validado: {video_file.name} ({video_file.stat().st_size / 1024 / 1024:.2f} MB)")
    
    # Etapa 2: Configurar API do Gemini
    genai.configure(api_key=api_key)
    
    # Etapa 3: Fazer upload do vídeo para o File Service
    logger.info("Iniciando upload do vídeo para o Gemini File Service...")
    try:
        uploaded_file = genai.upload_file(
            path=str(video_file),
            display_name=video_file.name
        )
        logger.info(f"Upload concluído. URI: {uploaded_file.uri}")
    except Exception as e:
        logger.error(f"Erro no upload do vídeo: {e}")
        raise Exception(f"Falha no upload do vídeo para o Gemini: {e}")
    
    # Etapa 4: Configurar modelo com system instruction
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        system_instruction=SYSTEM_INSTRUCTION,
        generation_config=genai.GenerationConfig(
            temperature=0.4,
            max_output_tokens=8192
        )
    )
    
    # Etapa 5: Enviar vídeo para análise
    logger.info("Enviando vídeo para análise pelo Gemini...")
    try:
        response = model.generate_content(
            contents=[uploaded_file, USER_PROMPT]
        )
        logger.info("Resposta recebida do Gemini")
    except Exception as e:
        logger.error(f"Erro na chamada da API do Gemini: {e}")
        raise Exception(f"Falha na análise do vídeo pelo Gemini: {e}")
    
    # Etapa 6: Verificar se há resposta válida
    if not response.text:
        logger.error("Gemini retornou resposta vazia")
        raise ValueError("O Gemini não retornou conteúdo. O vídeo pode ser muito longo ou inválido.")
    
    logger.debug(f"Resposta bruta: {response.text[:500]}...")
    
    # Etapa 7: Parsear JSON da resposta
    try:
        result = _parse_gemini_response(response.text)
    except ValueError as e:
        logger.error(f"Erro ao parsear resposta: {e}")
        raise
    
    # Etapa 8: Validar estrutura do JSON
    try:
        _validate_json_structure(result)
    except ValueError as e:
        logger.error(f"JSON inválido: {e}")
        raise
    
    logger.info(
        f"Processamento concluído. Livro: '{result['book_title']}' "
        f"com {len(result['chapters'])} capítulo(s)"
    )
    
    return result
