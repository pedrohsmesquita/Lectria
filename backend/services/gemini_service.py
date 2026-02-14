"""
Gemini Service - Ebook Generation
Encapsulates communication with Google Gemini 2.5 Flash for generating educational ebooks.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
from google.generativeai import GenerativeModel
from fastapi import HTTPException, status

# Configure logger
logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """
Você é um sistema de inteligência artificial especializado em Engenharia de Conteúdo Acadêmico. Sua missão é receber a transcrição de uma aula gravada (em PDF) e, opcionalmente, o slide correspondente (em PDF), e produzir um ebook didático completo — desde o sumário estruturado até o conteúdo redigido de cada seção, com referências bibliográficas e indicações visuais extraídas dos slides.

Você realizará esse trabalho em uma única resposta, em duas etapas lógicas internas:
1. Estruturação (Discovery): Leitura e organização do conteúdo em capítulos e seções.
2. Redação (Deep Analysis): Geração do texto acadêmico completo para cada seção, com mapeamento de imagens e referências.

DIRETRIZES GERAIS:
- Utilize exclusivamente o conteúdo presente na transcrição e nos slides fornecidos. Não invente, extrapole ou adicione informações externas.
- Escreva em português formal e acadêmico. Elimine vícios de linguagem oral da transcrição.
- Títulos de capítulos e seções devem ser profissionais e convidativos.
- Toda citação a autor, livro, artigo ou fonte deve ser capturada e formatada em ABNT.

DIRETRIZES PARA USO DOS SLIDES (PDF):
- Trate cada página como um slide individual. Realize OCR interno para extrair títulos, tópicos, fórmulas e citações.
- Insira marcadores [IMAGE_N] no content_markdown onde um slide contiver diagrama, gráfico, tabela ou figura útil. N reinicia em 1 a cada nova seção.
- Forneça coordenadas normalizadas [0–1000] para recorte do conteúdo útil do slide: { "xmin": int, "ymin": int, "xmax": int, "ymax": int }.
- Se o slide não for fornecido, retorne section_assets como lista vazia.

ESPECIFICAÇÃO OBRIGATÓRIA DE SAÍDA (JSON STRICT):
Retorne exclusivamente um objeto JSON válido, sem texto antes ou depois, sem blocos de código markdown. Estrutura obrigatória:

{
  "book": {
    "title": "Título principal do ebook",
    "chapters": [
      {
        "title": "Título do Capítulo",
        "order": 1,
        "sections": [
          {
            "title": "Título da Seção",
            "order": 1,
            "content_markdown": "Texto acadêmico completo em Markdown com marcadores [IMAGE_N].",
            "bibliography_found": ["ABNT..."],
            "section_assets": [
              {
                "placeholder": "[IMAGE_1]",
                "caption": "Legenda técnica da imagem.",
                "slide_page": 3,
                "crop_info": { "xmin": 50, "ymin": 80, "xmax": 950, "ymax": 720 }
              }
            ]
          }
        ]
      }
    ]
  }
}

REGRAS DE CONSISTÊNCIA:
1. O placeholder em section_assets deve ser idêntico ao marcador no content_markdown da mesma seção.
2. A numeração [IMAGE_N] reinicia em 1 a cada nova seção.
3. O campo order deve ser inteiro crescente sem lacunas (1, 2, 3...).
4. Se não houver referências numa seção, retorne bibliography_found como [].
5. Se não houver imagens úteis, retorne section_assets como [].
6. Nunca retorne campos extras fora desta estrutura.
"""


async def generate_ebook(
    transcript_pdf_path: str,
    slide_pdf_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates an educational ebook from a transcript PDF and an optional slide PDF using Google Gemini.

    Architectural Decision:
    This function returns a raw dictionary instead of saving directly to the database.
    This separates the concern of "AI Content Generation" from "Data Persistence".
    The caller (likely a background task or route handler) is responsible for transaction management
    and saving the result to the Books, Chapters, Sections, and SectionAssets tables.

    Args:
        transcript_pdf_path (str): Absolute path to the transcript PDF file.
        slide_pdf_path (Optional[str]): Absolute path to the slide PDF file (optional).

    Returns:
        Dict[str, Any]: The generated ebook structure as a dictionary adhering to the specified JSON schema.

    Raises:
        RuntimeError: If GOOGLE_API_KEY is missing.
        HTTPException: If file upload fails, generation fails, or JSON parsing fails.
    """
    
    # 1. Load API Key
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        logger.error("GOOGLE_API_KEY not found in environment variables.")
        raise RuntimeError("GOOGLE_API_KEY not found in environment variables.")

    genai.configure(api_key=google_api_key)

    uploaded_files = []

    try:
        # 2. Upload Files to Gemini File Service
        logger.info(f"Uploading transcript: {transcript_pdf_path}")
        if not os.path.exists(transcript_pdf_path):
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transcript file not found at: {transcript_pdf_path}"
            )

        transcript_file = genai.upload_file(path=transcript_pdf_path, display_name="Transcript PDF")
        uploaded_files.append(transcript_file)
        
        files_for_prompt = [transcript_file]
        user_prompt_text = "Here is the transcript of the lecture (PDF)."

        if slide_pdf_path:
            logger.info(f"Uploading slides: {slide_pdf_path}")
            if not os.path.exists(slide_pdf_path):
                 raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Slide file not found at: {slide_pdf_path}"
                )
            
            slide_file = genai.upload_file(path=slide_pdf_path, display_name="Slide PDF")
            uploaded_files.append(slide_file)
            files_for_prompt.append(slide_file)
            user_prompt_text += " And here are the corresponding slides (PDF)."
        
        user_prompt_text += " Please generate the ebook following the system instructions strictly."

        # 3. Create Generative Model
        model = GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_INSTRUCTION
        )

        # 4. Construct Prompt (Interleaved text and files)
        # The prompt list should be a sequence of content.
        # We put the text prompt first, then the file objects.
        # Actually, best practice often suggests context (files) then instruction.
        # Let's append files then the final instruction text.
        prompt_content = []
        if slide_pdf_path:    
             prompt_content.append("Slides:")
             prompt_content.append(files_for_prompt[1]) # Slide is second if present
        
        prompt_content.append("Transcript:")
        prompt_content.append(files_for_prompt[0]) # Transcript is always first in our list logic above? Wait, let's be explicit.
        
        # Resetting prompt_content to be safer and clearer
        prompt_content = []
        
        # Add Transcript
        prompt_content.append("Arquivo de Transcrição:")
        prompt_content.append(uploaded_files[0]) 

        # Add Slides if present
        if len(uploaded_files) > 1:
            prompt_content.append("Arquivo de Slides:")
            prompt_content.append(uploaded_files[1])
        
        prompt_content.append("Com base nestes arquivos, gere o ebook conforme as instruções do sistema.")

        # 5. Generate Content
        logger.info("Sending request to Gemini...")
        response = model.generate_content(prompt_content)
        
        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        # 6. Parse JSON Response
        response_text = response.text.strip()
        
        # 7. Clean Markdown delimiters if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        response_text = response_text.strip()

        try:
            ebook_data = json.loads(response_text)
            logger.info("Successfully parsed ebook JSON.")
            return ebook_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            logger.debug(f"Raw response: {response_text}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to parse valid JSON from Gemini response."
            )

    except Exception as e:
        logger.exception("Error during ebook generation process.")
        # Re-raise HTTP exceptions as is
        if isinstance(e, HTTPException):
            raise e
        # Wrap other exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during ebook generation: {str(e)}"
        )
    finally:
        # Clean up files from Gemini Storage if needed? 
        # Usually checking 'state' and deleting is good practice to avoid clutter, 
        # but for this specific request, we just need to implement the generation logic.
        # The prompt didn't explicitly ask for cleanup, usually files expire after 48h.
        # We will leave them for now to avoid deleting before processing is complete if async.
        pass
