/**
 * Status Translations - Traduz status para português brasileiro
 */

export const STATUS_TRANSLATIONS: Record<string, string> = {
    // Upload status (frontend)
    pending: 'Aguardando',
    uploading: 'Enviando',
    success: 'Concluído',
    error: 'Erro',

    // Book status (backend) - caso o backend não envie status_display
    PENDING: 'Pendente',
    PENDENTE: 'Pendente',
    PROCESSING: 'Processando',
    PROCESSANDO: 'Processando',
    EXTRACTING_AUDIO: 'Extraindo áudio',
    UPLOADING_TO_GEMINI: 'Enviando para análise',
    ANALYZING_CONTENT: 'Analisando conteúdo',
    GENERATING_STRUCTURE: 'Gerando estrutura',
    DISCOVERY_COMPLETE: 'Estrutura gerada',
    ESTRUTURA_GERADA: 'Estrutura gerada',
    COMPLETED: 'Concluído',
    CONCLUIDO: 'Concluído',
    ERROR: 'Erro',
    ERRO: 'Erro',

    // Section status
    SUCCESS: 'Concluído',
    SUCESSO: 'Concluído',
} as const;

/**
 * Traduz um status do inglês para português
 * @param status - Status em inglês
 * @returns Status traduzido em português
 */
export function translateStatus(status: string): string {
    return STATUS_TRANSLATIONS[status] || status;
}

/**
 * Retorna a classe CSS apropriada para um status
 * @param status - Status em inglês
 * @returns Classe CSS para estilização
 */
export function getStatusColor(status: string): string {
    if (['COMPLETED', 'CONCLUIDO', 'SUCCESS', 'SUCESSO', 'DISCOVERY_COMPLETE', 'ESTRUTURA_GERADA', 'success'].includes(status)) {
        return 'success';
    } else if (['PROCESSING', 'PROCESSANDO', 'EXTRACTING_AUDIO', 'UPLOADING_TO_GEMINI', 'ANALYZING_CONTENT', 'GENERATING_STRUCTURE', 'uploading'].includes(status)) {
        return 'processing';
    } else if (['ERROR', 'ERRO', 'error'].includes(status)) {
        return 'error';
    } else {
        return 'pending';
    }
}
