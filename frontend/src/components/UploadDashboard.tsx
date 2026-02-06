import React, { useState, useRef, useCallback } from 'react';
import { Upload, Video, CheckCircle, XCircle, Loader2, X, FileVideo } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

// ============================================
// UploadDashboard Component - Video Upload
// ============================================

interface VideoFile {
    id: string;
    file: File;
    status: 'pending' | 'uploading' | 'success' | 'error';
    progress: number;
    error?: string;
}

const UploadDashboard: React.FC = () => {
    const navigate = useNavigate();
    const [videos, setVideos] = useState<VideoFile[]>([]);
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // TEMPORARY: UUID fake apenas para VISUALIZAR o dashboard
    // Para fazer uploads REAIS, você precisa criar um livro no banco e colocar o UUID verdadeiro aqui
    const BOOK_ID = '00000000-0000-0000-0000-000000000000'; // ⚠️ UUID FAKE - uploads vão falhar

    const MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024; // 2GB
    const ALLOWED_VIDEO_TYPES = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm', 'video/quicktime'];
    const MAX_PARALLEL_UPLOADS = 3;

    // Format file size
    const formatFileSize = (bytes: number): string => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
        if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
        return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
    };

    // Validate video file
    const validateFile = (file: File): string | null => {
        if (!ALLOWED_VIDEO_TYPES.includes(file.type)) {
            return 'Tipo de arquivo não suportado. Use MP4, AVI, MOV, MKV ou WebM.';
        }
        if (file.size > MAX_FILE_SIZE) {
            return 'Arquivo muito grande. Tamanho máximo: 2GB';
        }
        return null;
    };

    // Upload single video
    const uploadVideo = async (videoFile: VideoFile) => {
        const formData = new FormData();
        formData.append('file', videoFile.file);
        formData.append('book_id', BOOK_ID);

        const token = localStorage.getItem('access_token');
        if (!token) {
            throw new Error('Token de autenticação não encontrado');
        }

        return new Promise<void>((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const progress = Math.round((e.loaded / e.total) * 100);
                    setVideos(prev => prev.map(v =>
                        v.id === videoFile.id ? { ...v, progress } : v
                    ));
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    setVideos(prev => prev.map(v =>
                        v.id === videoFile.id ? { ...v, status: 'success', progress: 100 } : v
                    ));
                    resolve();
                } else {
                    const errorData = JSON.parse(xhr.responseText);
                    const errorMessage = errorData.detail || 'Erro ao fazer upload';
                    setVideos(prev => prev.map(v =>
                        v.id === videoFile.id ? { ...v, status: 'error', error: errorMessage } : v
                    ));
                    reject(new Error(errorMessage));
                }
            });

            xhr.addEventListener('error', () => {
                setVideos(prev => prev.map(v =>
                    v.id === videoFile.id ? { ...v, status: 'error', error: 'Erro de conexão' } : v
                ));
                reject(new Error('Erro de conexão'));
            });

            xhr.open('POST', 'http://localhost:8000/videos/upload');
            xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            xhr.send(formData);
        });
    };

    // Process upload queue
    const processQueue = useCallback(async () => {
        const pendingVideos = videos.filter(v => v.status === 'pending');
        const uploadingCount = videos.filter(v => v.status === 'uploading').length;

        const canUpload = Math.min(
            MAX_PARALLEL_UPLOADS - uploadingCount,
            pendingVideos.length
        );

        for (let i = 0; i < canUpload; i++) {
            const video = pendingVideos[i];
            setVideos(prev => prev.map(v =>
                v.id === video.id ? { ...v, status: 'uploading' } : v
            ));

            uploadVideo(video).catch(console.error);
        }
    }, [videos]);

    // Auto-process queue when videos change
    React.useEffect(() => {
        processQueue();
    }, [videos, processQueue]);

    // Handle file selection
    const handleFiles = (files: FileList | null) => {
        if (!files) return;

        const newVideos: VideoFile[] = [];

        Array.from(files).forEach(file => {
            const validationError = validateFile(file);
            if (validationError) {
                // Add as error immediately
                newVideos.push({
                    id: Math.random().toString(36).substring(7),
                    file,
                    status: 'error',
                    progress: 0,
                    error: validationError
                });
            } else {
                newVideos.push({
                    id: Math.random().toString(36).substring(7),
                    file,
                    status: 'pending',
                    progress: 0
                });
            }
        });

        setVideos(prev => [...prev, ...newVideos]);
    };

    // Drag and drop handlers
    const handleDragEnter = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        handleFiles(e.dataTransfer.files);
    };

    // Remove video from queue
    const removeVideo = (id: string) => {
        setVideos(prev => prev.filter(v => v.id !== id));
    };

    // Clear completed/errored videos
    const clearCompleted = () => {
        setVideos(prev => prev.filter(v => v.status === 'pending' || v.status === 'uploading'));
    };

    // Logout handler
    const handleLogout = () => {
        localStorage.removeItem('access_token');
        navigate('/login');
    };

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
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">Dashboard de Upload</h1>
                        <p className="text-slate-400">Envie seus vídeos para transformar em conhecimento</p>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/20 text-white rounded-lg transition-all"
                    >
                        Sair
                    </button>
                </div>

                {/* Upload Area */}
                <div
                    onDragEnter={handleDragEnter}
                    onDragLeave={handleDragLeave}
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`bg-white/10 backdrop-blur-xl rounded-3xl border-2 border-dashed transition-all cursor-pointer mb-8 ${isDragging
                        ? 'border-purple-400 bg-purple-500/10 scale-[1.02]'
                        : 'border-white/20 hover:border-purple-400/50 hover:bg-white/[0.15]'
                        }`}
                >
                    <div className="p-12 text-center">
                        <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-2xl shadow-lg shadow-purple-500/25 mb-6">
                            <Upload className="w-10 h-10 text-white" />
                        </div>
                        <h3 className="text-xl font-semibold text-white mb-2">
                            Arraste vídeos aqui ou clique para selecionar
                        </h3>
                        <p className="text-slate-400 text-sm">
                            Formatos aceitos: MP4, AVI, MOV, MKV, WebM • Tamanho máximo: 2GB
                        </p>
                    </div>
                </div>

                <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept="video/*"
                    onChange={(e) => handleFiles(e.target.files)}
                    className="hidden"
                />

                {/* Video Queue */}
                {videos.length > 0 && (
                    <div className="bg-white/10 backdrop-blur-xl rounded-3xl border border-white/20 overflow-hidden">
                        <div className="p-6 border-b border-white/10 flex items-center justify-between">
                            <h2 className="text-xl font-semibold text-white">
                                Fila de Upload ({videos.length})
                            </h2>
                            {videos.some(v => v.status === 'success' || v.status === 'error') && (
                                <button
                                    onClick={clearCompleted}
                                    className="px-4 py-2 text-sm bg-white/5 hover:bg-white/10 text-slate-300 rounded-lg transition-all"
                                >
                                    Limpar finalizados
                                </button>
                            )}
                        </div>

                        <div className="divide-y divide-white/10">
                            {videos.map((video) => (
                                <div key={video.id} className="p-6 hover:bg-white/5 transition-all">
                                    <div className="flex items-start gap-4">
                                        {/* Icon */}
                                        <div className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center ${video.status === 'success' ? 'bg-green-500/20' :
                                            video.status === 'error' ? 'bg-red-500/20' :
                                                video.status === 'uploading' ? 'bg-blue-500/20' :
                                                    'bg-gray-500/20'
                                            }`}>
                                            {video.status === 'success' && <CheckCircle className="w-6 h-6 text-green-400" />}
                                            {video.status === 'error' && <XCircle className="w-6 h-6 text-red-400" />}
                                            {video.status === 'uploading' && <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />}
                                            {video.status === 'pending' && <FileVideo className="w-6 h-6 text-gray-400" />}
                                        </div>

                                        {/* Info */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between mb-2">
                                                <h3 className="text-white font-medium truncate">
                                                    {video.file.name}
                                                </h3>
                                                <button
                                                    onClick={() => removeVideo(video.id)}
                                                    className="text-slate-400 hover:text-red-400 transition-colors ml-2"
                                                    disabled={video.status === 'uploading'}
                                                >
                                                    <X className="w-5 h-5" />
                                                </button>
                                            </div>

                                            <p className="text-sm text-slate-400 mb-3">
                                                {formatFileSize(video.file.size)}
                                                {video.status === 'success' && ' • Upload concluído'}
                                                {video.status === 'error' && ` • ${video.error}`}
                                                {video.status === 'uploading' && ` • ${video.progress}%`}
                                                {video.status === 'pending' && ' • Aguardando...'}
                                            </p>

                                            {/* Progress Bar */}
                                            {(video.status === 'uploading' || video.status === 'success') && (
                                                <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                                                    <div
                                                        className={`h-full transition-all duration-300 ${video.status === 'success' ? 'bg-green-500' : 'bg-blue-500'
                                                            }`}
                                                        style={{ width: `${video.progress}%` }}
                                                    />
                                                </div>
                                            )}

                                            {video.status === 'error' && (
                                                <div className="w-full bg-red-500/20 rounded-full h-2" />
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {videos.length === 0 && (
                    <div className="text-center py-12">
                        <Video className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                        <p className="text-slate-400">Nenhum vídeo na fila. Adicione vídeos para começar!</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default UploadDashboard;
