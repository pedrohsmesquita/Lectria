"""
Status Translator - Traduz status do banco de dados para português brasileiro
"""

# Dicionário de tradução de status
STATUS_PT_BR = {
    # Book status
    "PENDING": "Pendente",
    "PROCESSING": "Processando",  # Deprecated - usar status mais específicos
    "EXTRACTING_AUDIO": "Extraindo áudio",
    "UPLOADING_TO_GEMINI": "Enviando para análise",
    "ANALYZING_CONTENT": "Analisando conteúdo",
    "GENERATING_STRUCTURE": "Gerando estrutura",
    "DISCOVERY_COMPLETE": "Estrutura gerada",
    "COMPLETED": "Concluído",
    "ERROR": "Erro",
    
    # Section status
    "SUCCESS": "Concluído",
}


def translate_status(status: str) -> str:
    """
    Traduz um status do inglês (banco de dados) para português (UI).
    
    Args:
        status: Status em inglês (ex: "PENDING", "PROCESSING")
    
    Returns:
        Status traduzido em português (ex: "Pendente", "Processando")
        Se o status não estiver no dicionário, retorna o status original.
    """
    return STATUS_PT_BR.get(status, status)


def get_status_color(status: str) -> str:
    """
    Retorna a cor/classe CSS apropriada para um status.
    
    Args:
        status: Status em inglês
    
    Returns:
        String com classes CSS para estilização
    """
    if status in ["COMPLETED", "SUCCESS", "DISCOVERY_COMPLETE"]:
        return "success"
    elif status in ["PROCESSING", "EXTRACTING_AUDIO", "UPLOADING_TO_GEMINI", "ANALYZING_CONTENT", "GENERATING_STRUCTURE"]:
        return "processing"
    elif status == "ERROR":
        return "error"
    else:  # PENDING
        return "pending"
