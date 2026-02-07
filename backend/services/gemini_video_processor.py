"""
Serviço de Processamento de Vídeo com Google Gemini.

Este módulo processa videoaulas usando a API do Google Gemini 2.0 Flash
e retorna a estrutura do livro em formato JSON.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

import google.generativeai as genai

# Configuração de logging
logger = logging.getLogger(__name__)

# Extensões de vídeo permitidas
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}

# System instruction para o modelo Gemini
SYSTEM_INSTRUCTION = """
Você é um Arquiteto Educacional especializado em transformar videoaulas em estruturas de livros didáticos.

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
- Responda APENAS com o JSON, sem texto adicional
"""


def _validate_video_path(video_path: str) -> Path:
    """
    Valida o caminho do arquivo de vídeo.
    
    Args:
        video_path: Caminho local do arquivo de vídeo.
        
    Returns:
        Path: Objeto Path validado.
        
    Raises:
        ValueError: Se a extensão for inválida.
        FileNotFoundError: Se o arquivo não existir.
    """
    path = Path(video_path)
    
    # Verificar se o arquivo existe
    if not path.exists():
        logger.error(f"Arquivo de vídeo não encontrado: {video_path}")
        raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {video_path}")
    
    # Verificar extensão
    extension = path.suffix.lower()
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        logger.error(f"Extensão de vídeo inválida: {extension}")
        raise ValueError(
            f"Extensão de vídeo inválida: {extension}. "
            f"Extensões permitidas: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        )
    
    return path


def _validate_json_structure(data: dict[str, Any]) -> None:
    """
    Valida a estrutura do JSON retornado pelo Gemini.
    
    Args:
        data: Dicionário com a estrutura do livro.
        
    Raises:
        ValueError: Se campos obrigatórios estiverem ausentes.
    """
    # Validar campo book_title
    if "book_title" not in data:
        raise ValueError("Campo obrigatório ausente: 'book_title'")
    
    if not isinstance(data["book_title"], str) or not data["book_title"].strip():
        raise ValueError("O campo 'book_title' deve ser uma string não vazia")
    
    # Validar campo chapters
    if "chapters" not in data:
        raise ValueError("Campo obrigatório ausente: 'chapters'")
    
    if not isinstance(data["chapters"], list) or len(data["chapters"]) == 0:
        raise ValueError("O campo 'chapters' deve ser uma lista não vazia")
    
    # Validar cada capítulo
    for i, chapter in enumerate(data["chapters"]):
        _validate_chapter(chapter, i + 1)


def _validate_chapter(chapter: dict[str, Any], chapter_index: int) -> None:
    """
    Valida a estrutura de um capítulo.
    
    Args:
        chapter: Dicionário representando um capítulo.
        chapter_index: Índice do capítulo para mensagens de erro.
        
    Raises:
        ValueError: Se campos obrigatórios estiverem ausentes.
    """
    required_fields = ["chapter_number", "title", "description", "sections"]
    
    for field in required_fields:
        if field not in chapter:
            raise ValueError(
                f"Campo obrigatório ausente no capítulo {chapter_index}: '{field}'"
            )
    
    # Validar sections
    if not isinstance(chapter["sections"], list) or len(chapter["sections"]) == 0:
        raise ValueError(
            f"O capítulo {chapter_index} deve ter pelo menos uma seção"
        )
    
    # Validar cada seção
    for j, section in enumerate(chapter["sections"]):
        _validate_section(section, chapter_index, j + 1)


def _validate_section(
    section: dict[str, Any], 
    chapter_index: int, 
    section_index: int
) -> None:
    """
    Valida a estrutura de uma seção.
    
    Args:
        section: Dicionário representando uma seção.
        chapter_index: Índice do capítulo pai.
        section_index: Índice da seção para mensagens de erro.
        
    Raises:
        ValueError: Se campos obrigatórios estiverem ausentes.
    """
    required_fields = [
        "section_number", 
        "title", 
        "start_timestamp", 
        "end_timestamp",
        "key_concepts",
        "summary"
    ]
    
    for field in required_fields:
        if field not in section:
            raise ValueError(
                f"Campo obrigatório ausente na seção {section_index} "
                f"do capítulo {chapter_index}: '{field}'"
            )
    
    # Validar key_concepts como lista
    if not isinstance(section["key_concepts"], list):
        raise ValueError(
            f"O campo 'key_concepts' na seção {section_index} "
            f"do capítulo {chapter_index} deve ser uma lista"
        )


def _extract_json_from_response(response_text: str) -> dict[str, Any]:
    """
    Extrai e parseia o JSON da resposta do Gemini.
    
    O Gemini pode retornar o JSON com markdown code blocks,
    então esta função limpa o texto antes de parsear.
    
    Args:
        response_text: Texto da resposta do Gemini.
        
    Returns:
        dict: JSON parseado.
        
    Raises:
        ValueError: Se o JSON for malformado.
    """
    text = response_text.strip()
    
    # Remover markdown code blocks se presentes
    if text.startswith("```json"):
        text = text[7:]  # Remove ```json
    elif text.startswith("```"):
        text = text[3:]  # Remove ```
    
    if text.endswith("```"):
        text = text[:-3]  # Remove ``` final
    
    text = text.strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao parsear JSON da resposta: {e}")
        logger.debug(f"Texto recebido: {response_text[:500]}...")
        raise ValueError(
            f"A resposta do Gemini não é um JSON válido: {str(e)}"
        ) from e


async def process_video_structure(
    video_path: str,
    api_key: str
) -> dict[str, Any]:
    """
    Processa vídeo com Gemini e retorna estrutura do livro.
    
    Esta função envia um arquivo de vídeo para a API do Google Gemini 2.0 Flash,
    que analisa o conteúdo e retorna uma estrutura de livro didático organizada
    em capítulos e seções com timestamps.
    
    Args:
        video_path: Caminho local do arquivo de vídeo.
        api_key: Chave da API do Google Gemini.
        
    Returns:
        dict: JSON estruturado com book_title, chapters e sections.
              
    Raises:
        FileNotFoundError: Se o arquivo de vídeo não existir.
        ValueError: Se o vídeo for inválido ou a resposta for malformada.
        Exception: Se a API falhar por timeout ou erro de conexão.
        
    Example:
        >>> result = await process_video_structure(
        ...     video_path="/path/to/video.mp4",
        ...     api_key="your-api-key"
        ... )
        >>> print(result["book_title"])
        "Introdução à Programação em Python"
    """
    logger.info(f"Iniciando processamento do vídeo: {video_path}")
    
    # Validar caminho do vídeo
    video_file = _validate_video_path(video_path)
    logger.info(f"Arquivo de vídeo validado: {video_file.name}")
    
    # Configurar a API
    genai.configure(api_key=api_key)
    
    # Fazer upload do vídeo para o File Service
    logger.info("Iniciando upload do vídeo para o Gemini File Service...")
    try:
        uploaded_file = genai.upload_file(
            path=str(video_file),
            display_name=video_file.name
        )
        logger.info(
            f"Upload concluído. URI: {uploaded_file.uri}, "
            f"Nome: {uploaded_file.display_name}"
        )
    except Exception as e:
        logger.error(f"Erro no upload do vídeo: {e}")
        raise Exception(f"Falha ao fazer upload do vídeo: {str(e)}") from e
    
    # Aguardar processamento do arquivo (vídeos podem demorar)
    # O Gemini precisa processar o vídeo antes de estar disponível
    logger.info("Aguardando processamento do vídeo pelo Gemini...")
    import time
    max_wait_time = 300  # 5 minutos máximo
    wait_interval = 10   # Verificar a cada 10 segundos
    elapsed_time = 0
    
    while uploaded_file.state.name == "PROCESSING":
        if elapsed_time >= max_wait_time:
            logger.error("Timeout aguardando processamento do vídeo")
            raise Exception(
                f"Timeout: O vídeo demorou mais de {max_wait_time} segundos "
                "para ser processado pelo Gemini."
            )
        
        time.sleep(wait_interval)
        elapsed_time += wait_interval
        uploaded_file = genai.get_file(uploaded_file.name)
        logger.debug(f"Estado do arquivo: {uploaded_file.state.name}")
    
    if uploaded_file.state.name == "FAILED":
        logger.error("Processamento do vídeo falhou no Gemini")
        raise Exception("O Gemini falhou ao processar o vídeo.")
    
    logger.info("Vídeo processado e pronto para análise")
    
    # Configurar o modelo com system instruction
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        system_instruction=SYSTEM_INSTRUCTION,
        generation_config=genai.GenerationConfig(
            temperature=0.4,
            max_output_tokens=8192,
        )
    )
    
    # Enviar vídeo para análise
    logger.info("Enviando vídeo para análise do Gemini...")
    try:
        response = model.generate_content(
            [
                uploaded_file,
                "Analise este vídeo e gere a estrutura do livro didático em JSON."
            ]
        )
        logger.info("Resposta recebida do Gemini")
    except Exception as e:
        logger.error(f"Erro na chamada da API Gemini: {e}")
        raise Exception(f"Falha na API do Gemini: {str(e)}") from e
    
    # Extrair e validar JSON da resposta
    if not response.text:
        logger.error("Resposta do Gemini está vazia")
        raise ValueError("O Gemini retornou uma resposta vazia.")
    
    logger.debug(f"Resposta bruta (primeiros 500 chars): {response.text[:500]}")
    
    # Parsear JSON
    result = _extract_json_from_response(response.text)
    
    # Validar estrutura
    logger.info("Validando estrutura do JSON retornado...")
    _validate_json_structure(result)
    
    # Log de sucesso com estatísticas
    num_chapters = len(result["chapters"])
    num_sections = sum(len(ch["sections"]) for ch in result["chapters"])
    logger.info(
        f"Processamento concluído com sucesso. "
        f"Livro: '{result['book_title']}', "
        f"Capítulos: {num_chapters}, Seções: {num_sections}"
    )
    
    # Limpar arquivo do File Service (opcional, mas recomendado)
    try:
        genai.delete_file(uploaded_file.name)
        logger.debug(f"Arquivo temporário removido: {uploaded_file.name}")
    except Exception as e:
        # Não falhar se a limpeza não funcionar
        logger.warning(f"Não foi possível remover arquivo temporário: {e}")
    
    return result
