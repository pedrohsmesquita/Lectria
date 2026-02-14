import React, { useState, useRef, useCallback, useEffect } from 'react';
import { FileText, FilePlus, CheckCircle, XCircle, Loader2, X, ArrowLeft, BookOpen, Play, File } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';

// ============================================
// TranscriptUploadDashboard Component - Transcript & PDF Upload
// ============================================

interface UploadFile {
    id: string;
    file: File;
    type: 'transcript' | 'pdf';
    status: 'pending' | 'uploading' | 'success' | 'error';
    progress: number;
    error?: string;
}

interface BookInfo {
    id: string;
    title: string;
    author: string;
}

const TranscriptUploadDashboard: React.FC = () => {
    const navigate = useNavigate();
    const { bookId } = useParams<{ bookId: string }>();
    const [files, setFiles] = useState<UploadFile[]>([]);
    const [isDraggingTranscript, setIsDraggingTranscript] = useState(false);
    const [isDraggingPdf, setIsDraggingPdf] = useState(false);
    const [bookInfo, setBookInfo] = useState<BookInfo | null>(null);
    const [processing, setProcessing] = useState(false);
    const transcriptInputRef = useRef<HTMLInputElement>(null);
    const pdfInputRef = useRef<HTMLInputElement>(null);

    const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
    const ALLOWED_TRANSCRIPT_TYPES = ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    const ALLOWED_PDF_TYPES = ['application/pdf'];

    // Fetch book information
    const fetchBookInfo = useCallback(async () => {
        if (!bookId) return;

        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`http://localhost:8000/books/${bookId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();
                setBookInfo(data);
            } else if (response.status === 403 || response.status === 404) {
                navigate('/dashboard');
            }
        } catch (error) {
            console.error('Error fetching book info:', error);
        }
    }, [bookId, navigate]);

    useEffect(() => {
        fetchBookInfo();
    }, [fetchBookInfo]);

    // Format file size
    const formatFileSize = (bytes: number): string => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    };

    // Validate file
    const validateFile = (file: File, type: 'transcript' | 'pdf'): string | null => {
        const allowedTypes = type === 'transcript' ? ALLOWED_TRANSCRIPT_TYPES : ALLOWED_PDF_TYPES;

        if (!allowedTypes.includes(file.type)) {
            if (type === 'transcript') {
                return 'Tipo de arquivo não suportado. Use TXT, DOCX ou PDF.';
            } else {
                return 'Tipo de arquivo não suportado. Use apenas PDF.';
            }
        }
        if (file.size > MAX_FILE_SIZE) {
            return 'Arquivo muito grande. Tamanho máximo: 50MB';
        }
        return null;
    };

    // Handle file selection
    const handleFiles = (fileList: FileList | null, type: 'transcript' | 'pdf') => {
        if (!fileList) return;

        const newFiles: UploadFile[] = [];

        for (const file of Array.from(fileList)) {
            const validationError = validateFile(file, type);
            if (validationError) {
                newFiles.push({
                    id: Math.random().toString(36).substring(7),
                    file,
                    type,
                    status: 'error',
                    progress: 0,
                    error: validationError
                });
            } else {
                newFiles.push({
                    id: Math.random().toString(36).substring(7),
                    file,
                    type,
                    status: 'pending',
                    progress: 0
                });
            }
        }

        setFiles(prev => [...prev, ...newFiles]);
    };

    // Drag and drop handlers for transcripts
    const handleTranscriptDragEnter = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDraggingTranscript(true);
    };

    const handleTranscriptDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDraggingTranscript(false);
    };

    const handleTranscriptDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleTranscriptDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDraggingTranscript(false);
        handleFiles(e.dataTransfer.files, 'transcript');
    };

    // Drag and drop handlers for PDFs
    const handlePdfDragEnter = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDraggingPdf(true);
    };

    const handlePdfDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDraggingPdf(false);
    };

    const handlePdfDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handlePdfDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDraggingPdf(false);
        handleFiles(e.dataTransfer.files, 'pdf');
    };

    // Remove file from list
    const removeFile = (id: string) => {
        setFiles(prev => prev.filter(f => f.id !== id));
    };

    // Clear completed/errored files
    const clearCompleted = () => {
        setFiles(prev => prev.filter(f => f.status === 'pending' || f.status === 'uploading'));
    };

    // Handle processing
    const handleProcessFiles = async () => {
        if (!bookId) return;

        const transcripts = files.filter(f => f.type === 'transcript' && f.status === 'pending');
        if (transcripts.length === 0) {
            alert('Adicione pelo menos uma transcrição antes de processar.');
            return;
        }

        try {
            setProcessing(true);

            const formData = new FormData();
            formData.append('book_id', bookId);

            // Add all files to FormData
            files.forEach(fileItem => {
                if (fileItem.status === 'pending') {
                    formData.append(fileItem.type === 'transcript' ? 'transcripts' : 'pdfs', fileItem.file);
                }
            });

            const token = localStorage.getItem('access_token');
            const response = await fetch(
                'http://localhost:8000/transcripts/upload',
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                }
            );

            if (response.ok) {
                // Now trigger processing
                const processResponse = await fetch(
                    `http://localhost:8000/books/${bookId}/process-transcripts`,
                    {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    }
                );

                if (processResponse.ok) {
                    const data = await processResponse.json();
                    alert(`Processamento iniciado com sucesso! Você pode sair da página.\n\nTask ID: ${data.task_id}`);
                    navigate('/dashboard');
                } else {
                    const error = await processResponse.json();
                    alert(`Erro ao iniciar processamento: ${error.detail}`);
                }
            } else {
                const error = await response.json();
                alert(`Erro ao fazer upload: ${error.detail}`);
            }
        } catch (error) {
            console.error('Erro ao processar arquivos:', error);
            alert('Erro ao processar arquivos. Verifique sua conexão.');
        } finally {
            setProcessing(false);
        }
    };

    const transcriptCount = files.filter(f => f.type === 'transcript' && f.status !== 'error').length;
    const pdfCount = files.filter(f => f.type === 'pdf' && f.status !== 'error').length;
    const hasTranscripts = transcriptCount > 0;

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
            {/* Background decorations */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
                <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse delay-1000"></div>
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10"></div>
            </div>

            <div className="relative max-w-5xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="p-2 bg-white/10 hover:bg-white/20 border border-white/20 text-white rounded-lg transition-all"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <BookOpen className="w-5 h-5 text-purple-400" />
                                <h1 className="text-3xl font-bold text-white">{bookInfo?.title || 'Carregando...'}</h1>
                            </div>
                            <p className="text-slate-400">Adicione transcrições e slides ao seu livro</p>
                        </div>
                    </div>
                </div>

                {/* Upload Areas */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    {/* Transcript Upload Area */}
                    <div
                        onDragEnter={handleTranscriptDragEnter}
                        onDragLeave={handleTranscriptDragLeave}
                        onDragOver={handleTranscriptDragOver}
                        onDrop={handleTranscriptDrop}
                        onClick={() => transcriptInputRef.current?.click()}
                        className={`bg-white/10 backdrop-blur-xl rounded-3xl border-2 border-dashed transition-all cursor-pointer ${isDraggingTranscript
                            ? 'border-purple-400 bg-purple-500/10 scale-[1.02]'
                            : 'border-white/20 hover:border-purple-400/50 hover:bg-white/[0.15]'
                            }`}
                    >
                        <div className="p-8 text-center">
                            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-2xl shadow-lg shadow-purple-500/25 mb-4">
                                <FileText className="w-8 h-8 text-white" />
                            </div>
                            <h3 className="text-lg font-semibold text-white mb-2">
                                Transcrições *
                            </h3>
                            <p className="text-slate-400 text-sm mb-2">
                                Arraste arquivos aqui ou clique
                            </p>
                            <p className="text-slate-500 text-xs">
                                TXT, DOCX, PDF • Máx: 50MB
                            </p>
                            {transcriptCount > 0 && (
                                <p className="text-purple-400 text-sm mt-3 font-medium">
                                    {transcriptCount} {transcriptCount === 1 ? 'transcrição adicionada' : 'transcrições adicionadas'}
                                </p>
                            )}
                        </div>
                    </div>

                    {/* PDF Upload Area */}
                    <div
                        onDragEnter={handlePdfDragEnter}
                        onDragLeave={handlePdfDragLeave}
                        onDragOver={handlePdfDragOver}
                        onDrop={handlePdfDrop}
                        onClick={() => pdfInputRef.current?.click()}
                        className={`bg-white/10 backdrop-blur-xl rounded-3xl border-2 border-dashed transition-all cursor-pointer ${isDraggingPdf
                            ? 'border-indigo-400 bg-indigo-500/10 scale-[1.02]'
                            : 'border-white/20 hover:border-indigo-400/50 hover:bg-white/[0.15]'
                            }`}
                    >
                        <div className="p-8 text-center">
                            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-indigo-500 to-blue-600 rounded-2xl shadow-lg shadow-indigo-500/25 mb-4">
                                <FilePlus className="w-8 h-8 text-white" />
                            </div>
                            <h3 className="text-lg font-semibold text-white mb-2">
                                PDFs / Slides
                            </h3>
                            <p className="text-slate-400 text-sm mb-2">
                                Arraste arquivos aqui ou clique
                            </p>
                            <p className="text-slate-500 text-xs">
                                Apenas PDF • Máx: 50MB
                            </p>
                            {pdfCount > 0 && (
                                <p className="text-indigo-400 text-sm mt-3 font-medium">
                                    {pdfCount} {pdfCount === 1 ? 'PDF adicionado' : 'PDFs adicionados'}
                                </p>
                            )}
                        </div>
                    </div>
                </div>

                <input
                    ref={transcriptInputRef}
                    type="file"
                    multiple
                    accept=".txt,.pdf,.docx"
                    onChange={(e) => handleFiles(e.target.files, 'transcript')}
                    className="hidden"
                />

                <input
                    ref={pdfInputRef}
                    type="file"
                    multiple
                    accept=".pdf"
                    onChange={(e) => handleFiles(e.target.files, 'pdf')}
                    className="hidden"
                />

                {/* Files List */}
                {files.length > 0 && (
                    <div className="bg-white/10 backdrop-blur-xl rounded-3xl border border-white/20 overflow-hidden mb-6">
                        <div className="p-6 border-b border-white/10 flex items-center justify-between">
                            <h2 className="text-xl font-semibold text-white">
                                Arquivos Adicionados ({files.length})
                            </h2>
                            {files.some(f => f.status === 'success' || f.status === 'error') && (
                                <button
                                    onClick={clearCompleted}
                                    className="px-4 py-2 text-sm bg-white/5 hover:bg-white/10 text-slate-300 rounded-lg transition-all"
                                >
                                    Limpar finalizados
                                </button>
                            )}
                        </div>

                        <div className="divide-y divide-white/10">
                            {files.map((fileItem) => (
                                <div key={fileItem.id} className="p-6 hover:bg-white/5 transition-all">
                                    <div className="flex items-start gap-4">
                                        {/* Icon */}
                                        <div className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center ${fileItem.status === 'success' ? 'bg-green-500/20' :
                                            fileItem.status === 'error' ? 'bg-red-500/20' :
                                                fileItem.type === 'transcript' ? 'bg-purple-500/20' : 'bg-indigo-500/20'
                                            }`}>
                                            {fileItem.status === 'success' && <CheckCircle className="w-6 h-6 text-green-400" />}
                                            {fileItem.status === 'error' && <XCircle className="w-6 h-6 text-red-400" />}
                                            {fileItem.status === 'pending' && fileItem.type === 'transcript' && <FileText className="w-6 h-6 text-purple-400" />}
                                            {fileItem.status === 'pending' && fileItem.type === 'pdf' && <File className="w-6 h-6 text-indigo-400" />}
                                        </div>

                                        {/* Info */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between mb-2">
                                                <div>
                                                    <h3 className="text-white font-medium truncate">
                                                        {fileItem.file.name}
                                                    </h3>
                                                    <span className={`text-xs px-2 py-1 rounded-full ${fileItem.type === 'transcript'
                                                        ? 'bg-purple-500/20 text-purple-300'
                                                        : 'bg-indigo-500/20 text-indigo-300'
                                                        }`}>
                                                        {fileItem.type === 'transcript' ? 'Transcrição' : 'PDF'}
                                                    </span>
                                                </div>
                                                <button
                                                    onClick={() => removeFile(fileItem.id)}
                                                    className="text-slate-400 hover:text-red-400 transition-colors ml-2"
                                                    title="Remover arquivo"
                                                >
                                                    <X className="w-5 h-5" />
                                                </button>
                                            </div>

                                            <p className="text-sm text-slate-400 mb-3">
                                                {formatFileSize(fileItem.file.size)}
                                                {fileItem.status === 'success' && ' • Upload concluído'}
                                                {fileItem.status === 'error' && ` • ${fileItem.error}`}
                                                {fileItem.status === 'pending' && ' • Pronto para processar'}
                                            </p>

                                            {fileItem.status === 'error' && (
                                                <div className="w-full bg-red-500/20 rounded-full h-2" />
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Info Message */}
                {files.length === 0 && (
                    <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 mb-6">
                        <p className="text-slate-300 text-center">
                            <span className="text-purple-400 font-medium">Transcrições</span> são obrigatórias.
                            <span className="text-indigo-400 font-medium"> PDFs</span> são opcionais.
                        </p>
                    </div>
                )}

                {/* Process Button */}
                {files.length > 0 && (
                    <div className="mt-6">
                        <button
                            onClick={handleProcessFiles}
                            disabled={processing || !hasTranscripts}
                            className="w-full py-4 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-slate-600 disabled:to-slate-700 disabled:cursor-not-allowed text-white rounded-xl transition-all flex items-center justify-center gap-2 font-semibold shadow-lg shadow-green-500/25 hover:shadow-green-500/40"
                        >
                            {processing ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Processando...
                                </>
                            ) : (
                                <>
                                    <Play className="w-5 h-5" />
                                    Processar Transcrições
                                </>
                            )}
                        </button>
                        <p className="text-center text-slate-400 text-sm mt-3">
                            {!hasTranscripts
                                ? 'Adicione pelo menos uma transcrição para continuar'
                                : 'Inicia a análise com IA. Você pode sair da página após clicar.'
                            }
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default TranscriptUploadDashboard;
