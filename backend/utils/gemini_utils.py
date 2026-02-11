"""
Gemini API Utilities - File upload and Discovery phase execution
"""
import google.generativeai as genai
import os
import time
import json
from typing import List, Dict, Any


# System Instruction da Fase 1 (Discovery) - Extraído do contexto.md
DISCOVERY_SYSTEM_INSTRUCTION = """
**ROLE:**
Você é um Engenheiro de Currículo Acadêmico especializado em estruturação de conteúdo pedagógico. Sua tarefa é analisar a transcrição de áudio de uma ou mais aulas e organizar esse conhecimento em uma estrutura lógica de livro didático (Sumário).

**OBJETIVO:**

1. **Identificar Tópicos Principais:** Agrupar o conteúdo em capítulos coesos (`Chapters`).
2. **Refinar Subtópicos:** Dividir cada capítulo em seções detalhadas (`Sections`).
3. **Mapeamento Temporal:** Identificar com precisão os timestamps (`start_time` e `end_time`) de onde cada assunto é discutido no áudio original.
4. **Sequenciamento:** Definir a ordem lógica (`order`) que facilite o aprendizado do aluno.

**DIRETRIZES TÉCNICAS:**

* **Granularidade:** Cada seção deve ter, idealmente, entre 3 a 10 minutos de conteúdo. Seções muito curtas devem ser agrupadas; seções muito longas devem ser divididas. Priorize uma estrutura robusta com mais seções em vez de poucas. Seja exaustivo e detalhado na quebra do conteúdo.
* **Nomenclatura:** Os títulos de capítulos e seções devem ser profissionais, acadêmicos e convidativos, removendo vícios de linguagem do professor. Evite títulos genéricos; use os conceitos técnicos abordados no trecho.
* **Continuidade:** Garanta que o `end_time` de uma seção conecte-se logicamente com o `start_time` da próxima. Evite agrupar muitos tópicos em uma única seção; divida para conquistar.
* **Múltiplos arquivos** Envio de múltiplos arquivos (O envio para o GEMINI deve especificar o arquivo de áudio e seu respectivo vídeo ID).

**ESPECIFICAÇÃO DA SAÍDA (JSON STRICT):**
Sua resposta deve ser EXCLUSIVAMENTE um objeto JSON válido. 
NÃO use blocos de código markdown (não use ```json ou ```).
NÃO adicione nenhum texto explicativo antes ou depois do JSON.
NÃO repita o objeto JSON.
RESPEITE o idioma do vídeo (se for em português, responda em português).
ESTRUTURA DO OBJETO:
{
  "chapters": [
    {
      "title": "Título do Capítulo",
      "order": 1,
      "sections": [
        {
          "title": "Título da Seção",
          "order": 1,
          "video_id": "ID_DO_VIDEO_AQUI",
          "start_time": 0.0,
          "end_time": 345.5
        }
      ]
    }
  ]
}
"""


def upload_audio_to_gemini(audio_path: str, display_name: str) -> str:
    """
    Faz upload de um arquivo de áudio para o Gemini File API.
    
    Args:
        audio_path: Caminho completo do arquivo de áudio
        display_name: UUID do vídeo (recomendado pelo contexto.md)
                      para garantir correlação direta no JSON de retorno
    
    Returns:
        file name (não URI) do arquivo no Gemini File API
        Exemplo: "files/abc123xyz"
    
    Raises:
        Exception: Se o upload falhar
    """
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    print(f"Fazendo upload do áudio: {audio_path} (display_name: {display_name})")
    
    # Upload do arquivo
    audio_file = genai.upload_file(
        path=audio_path,
        display_name=display_name
    )
    
    print(f"Upload iniciado. Aguardando processamento...")
    
    # Aguardar processamento do arquivo
    while audio_file.state.name == "PROCESSING":
        time.sleep(2)
        audio_file = genai.get_file(audio_file.name)
        print(f"Status: {audio_file.state.name}")
    
    if audio_file.state.name == "FAILED":
        raise Exception(f"Falha no upload do arquivo: {audio_file.name}")
    
    print(f"Upload concluído. Name: {audio_file.name}")
    return audio_file.name  # Retorna o name, não a URI


def call_gemini_discovery(audio_files_info: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Chama o Gemini 2.5 Flash para a fase Discovery.
    
    Args:
        audio_files_info: Lista de dicionários com:
                         [{"video_id": "uuid", "file_name": "files/abc123"}]
    
    Returns:
        JSON parseado com a estrutura de chapters e sections
    
    Raises:
        Exception: Se a chamada ao Gemini falhar ou retornar JSON inválido
    """
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    print(f"Iniciando Discovery com {len(audio_files_info)} arquivos de áudio")
    
    # Configurar modelo com system instruction
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=DISCOVERY_SYSTEM_INSTRUCTION
    )
    
    # Construir prompt intercalado (Opção A - mais segura)
    # Cada ID é seguido imediatamente pela URI correspondente
    prompt_parts = [
        "Analise os áudios anexados e gere o sumário do livro conforme as diretrizes.\n"
    ]
    
    for info in audio_files_info:
        prompt_parts.append(f"ID do vídeo: {info['video_id']}")
        prompt_parts.append(genai.get_file(info['file_name']))
    
    print("Enviando requisição ao Gemini 2.5 Flash...")
    
    # Gerar conteúdo com configurações de temperatura reduzida
    generation_config = genai.GenerationConfig(
        temperature=0.2,
        top_p=0.95,
        top_k=40,
        response_mime_type="application/json"
    )
    
    response = model.generate_content(
        prompt_parts,
        generation_config=generation_config
    )
    
    print("Resposta recebida. Parseando JSON...")
    
    # Parse JSON da resposta
    try:
        # Remover markdown code blocks se existirem
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith("```"):
            response_text = response_text[3:]  # Remove ```
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Remove ```
        
        result = json.loads(response_text.strip())
        
        print(f"JSON parseado com sucesso. {len(result.get('chapters', []))} capítulos encontrados.")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"Erro ao parsear JSON: {str(e)}")
        print(f"Resposta do Gemini: {response.text}")
        raise Exception(f"Resposta do Gemini não é um JSON válido: {str(e)}")
