"""
Gemini Service - Ebook Generation
Encapsulates communication with Google Gemini 2.5 Flash for generating educational ebooks.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from google.generativeai import GenerativeModel
from fastapi import HTTPException, status

# Configure logger
logger = logging.getLogger(__name__)

# System Instructions for Phase 1: Discovery (Skeleton Generation)
DISCOVERY_INSTRUCTION = """
Você é um Arquiteto de Estrutura Educacional. Sua missão é analisar múltiplos arquivos de transcrição e slides de um curso e criar um sumário lógico (esqueleto) para um livro didático.

OBJETIVOS:
1. Identificar os tópicos principais e organizá-los em capítulos (`Chapters`).
2. Dividir cada capítulo em seções detalhadas (`Sections`).
3. **Mapeamento Rigoroso de Fontes:** 
   - Para cada seção, você DEVE identificar QUAL transcrição é a fonte principal.
   - Use APENAS os IDs marcados como <TRANSCRIÇÃO> no campo `source_transcription_id`.
   - Use APENAS os IDs marcados como <SLIDE> no campo `source_slide_id`.
   - NUNCA use um ID de slide no campo de transcrição ou vice-versa.

DIRETRIZES:
- Granularidade: Seções de 3 a 10 minutos de leitura.
- Limite de Extensão: Gere no máximo entre 8 a 12 seções para todo o livro.
- Nomenclatura profissional e acadêmica.

**ESPECIFICAÇÃO DA SAÍDA (JSON STRICT):**
Sua resposta deve ser EXCLUSIVAMENTE um objeto JSON válido.
{
  "chapters": [
    {
      "title": "Título do Capítulo",
      "order": 1,
      "sections": [
        {
          "title": "Título da Seção",
          "order": 1,
          "source_transcription_id": "ID_DA_TRANSCRICAO_DA_LISTA_TRANSCRIÇÃO",
          "source_slide_id": "ID_DO_SLIDE_DA_LISTA_SLIDE_OU_NULL"
        }
      ]
    }
  ]
}
"""

# System Instructions for Phase 2: Deep Analysis (Content Generation)
DEEP_ANALYSIS_INSTRUCTION = """
Você é um Editor Acadêmico de Elite. Sua missão é escrever o conteúdo detalhado de uma SEÇÃO específica de um livro didático, baseando-se na transcrição e nos slides fornecidos.

DIRETRIZES:
- Escreva um texto fluido, acadêmico e em português formal.
- Utilize marcadores [IMAGE_N] no texto para indicar onde um slide deve ser inserido.
- Extraia bibliografia e gere legendas técnicas.
- Produza o conteúdo completo para esta seção (3.000 a 8.000 caracteres, dependendo da fonte).

**ESPECIFICAÇÃO DA SAÍDA (JSON STRICT):**
Sua resposta deve ser EXCLUSIVAMENTE um objeto JSON válido. 
NÃO use blocos de código markdown (não use ```json ou ```).
NÃO adicione nenhum texto explicativo antes ou depois do JSON.
NÃO repita o objeto JSON.
{
  "content_markdown": "Texto em Markdown com [IMAGE_N]...",
  "bibliography_found": ["Referência 1", "Referência 2"],
  "section_assets": [
    {
      "placeholder": "[IMAGE_1]",
      "caption": "Legenda da imagem",
      "slide_page": 5,
      "crop_info": { "xmin": 0, "ymin": 0, "xmax": 1000, "ymax": 1000 }
    }
  ]
}
"""

async def generate_book_discovery(
    transcriptions: List[Dict[str, str]],  # List of {"id": uuid, "path": path}
    slides: List[Dict[str, str]] = None     # List of {"id": uuid, "path": path}
) -> Dict[str, Any]:
    """
    Phase 1: Generates the book skeleton using Gemini 1.5 Flash.
    """
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise RuntimeError("GOOGLE_API_KEY missing")

    genai.configure(api_key=google_api_key)
    model = GenerativeModel(model_name="gemini-2.5-flash", system_instruction=DISCOVERY_INSTRUCTION)
    
    prompt_parts = ["Analise estes arquivos e gere o sumário do livro conforme as diretrizes.\n"]
    
    # Upload and add Transcriptions
    for t in transcriptions:
        logger.info(f"Uploading transcription for discovery: {t['path']}")
        file_obj = genai.upload_file(path=t['path'], display_name=f"Transcript_{t['id']}")
        prompt_parts.append(f"ID: {t['id']} <TRANSCRIÇÃO>")
        prompt_parts.append(file_obj)

    # Upload and add Slides
    if slides:
        for s in slides:
            logger.info(f"Uploading slide for discovery: {s['path']}")
            file_obj = genai.upload_file(path=s['path'], display_name=f"Slide_{s['id']}")
            prompt_parts.append(f"ID: {s['id']} <SLIDE>")
            prompt_parts.append(file_obj)

    prompt_parts.append("Gere o JSON do sumário relacionando as seções aos IDs acima.")

    logger.info("Calling Gemini Flash for Discovery...")
    
    generation_config = genai.GenerationConfig(
        temperature=0.2,
        response_mime_type="application/json"
    )
    
    response = model.generate_content(
        prompt_parts,
        generation_config=generation_config
    )
    
    return _parse_json_response(response.text)

async def generate_section_content(
    section_title: str,
    chapter_title: str,
    transcript_path: str,
    slide_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Phase 2: Generates detailed content for a single section using Gemini 1.5 Pro.
    """
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise RuntimeError("GOOGLE_API_KEY missing")

    genai.configure(api_key=google_api_key)
    model = GenerativeModel(model_name="gemini-2.5-flash", system_instruction=DEEP_ANALYSIS_INSTRUCTION)
    
    prompt_parts = [
        f"Escreva o conteúdo para a seção '{section_title}' do capítulo '{chapter_title}'.",
        "Utilize as fontes anexadas abaixo:"
    ]
    
    # Upload transcript context
    transcript_file = genai.upload_file(path=transcript_path, display_name="Context_Transcript")
    prompt_parts.append("Transcrição:")
    prompt_parts.append(transcript_file)
    
    # Upload slide context if provided
    if slide_path:
        slide_file = genai.upload_file(path=slide_path, display_name="Context_Slide")
        prompt_parts.append("Slides:")
        prompt_parts.append(slide_file)
    
    prompt_parts.append("Gere o JSON com content_markdown, bibliography e assets.")

    logger.info(f"Calling Gemini Pro for Section Content: {section_title}...")
    
    generation_config = genai.GenerationConfig(
        temperature=0.3,  # Lower temperature for more stable JSON
        response_mime_type="application/json"
    )
    
    response = model.generate_content(
        prompt_parts,
        generation_config=generation_config
    )
    
    return _parse_json_response(response.text)

def _parse_json_response(text: str) -> Dict[str, Any]:
    """Helper to parse JSON from Gemini response with increased robustness"""
    import re
    
    logger.debug(f"Parsing AI response: {text[:200]}...")
    
    # Try to clean markdown
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    
    cleaned = cleaned.strip()
    
    # Pre-processing: Try to fix common JSON issues in AI output
    # 1. Handle unescaped backslashes (but not the ones for escaping quotes)
    # 2. Handle potential multi-line strings if any (JSON doesn't allow raw newlines in strings)
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as initial_err:
        logger.warning(f"Initial JSON parse failed: {initial_err}. Attempting aggressive recovery.")
        
        # Recovery strategy 1: Find everything between the first { and the last }
        match = re.search(r'(\{.*\})', cleaned, re.DOTALL)
        if match:
            potential_json = match.group(1)
            try:
                return json.loads(potential_json)
            except json.JSONDecodeError:
                # Recovery strategy 2: Try to fix unescaped newlines in markdown strings
                # This regex looks for strings that might contain brand newlines
                fixed = re.sub(r'":\s*"(.*?)"\s*([,}])', 
                               lambda m: '": "' + m.group(1).replace('\n', '\\n').replace('\r', '\\r') + '"' + m.group(2), 
                               potential_json, flags=re.DOTALL)
                try:
                    return json.loads(fixed)
                except json.JSONDecodeError as final_err:
                    logger.error(f"Aggressive recovery failed. Error: {final_err}")
                    logger.error(f"Problematic JSON string: {potential_json[:1000]}...")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Invalid JSON from AI: {str(initial_err)}"
        )
