import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BookOpen, ChevronRight, Loader2, Save, X, ArrowLeft, FileText, Play, Download } from 'lucide-react';

// ============================================
// Types
// ============================================

interface Section {
    id: string;
    chapter_id: string;
    video_id: string;
    title: string;
    order: number;
    start_time: number;
    end_time: number;
    content_markdown: string | null;
    status: string;
    video_filename: string | null;
}

interface Chapter {
    id: string;
    book_id: string;
    title: string;
    order: number;
    created_at: string;
    sections: Section[];
}

type SelectedItem =
    | { type: 'chapter'; data: Chapter }
    | { type: 'section'; data: Section }
    | null;

// ============================================
// BookStructure Component
// ============================================

const BookStructure: React.FC = () => {
    const { bookId } = useParams<{ bookId: string }>();
    const navigate = useNavigate();

    const [chapters, setChapters] = useState<Chapter[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedItem, setSelectedItem] = useState<SelectedItem>(null);
    const [editTitle, setEditTitle] = useState('');
    const [editContent, setEditContent] = useState('');
    const [saving, setSaving] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [generatingSectionId, setGeneratingSectionId] = useState<string | null>(null);
    const [bookStatus, setBookStatus] = useState<string>('');

    const fetchBookDetails = useCallback(async () => {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`http://localhost:8000/books/${bookId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setBookStatus(data.status);
            }
        } catch (error) {
            console.error('Error fetching book details:', error);
        }
    }, [bookId]);

    // Fetch chapters and sections
    const fetchChapters = useCallback(async () => {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                navigate('/login');
                return;
            }

            const response = await fetch(`http://localhost:8000/books/${bookId}/chapters`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 401) {
                localStorage.removeItem('access_token');
                navigate('/login');
                return;
            }

            if (response.ok) {
                const data = await response.json();
                setChapters(data);

                // If chapters exist, get book status from the first one's parent or fetch book
                if (data.length > 0) {
                    fetchBookDetails();
                }
            }
        } catch (error) {
            console.error('Error fetching chapters:', error);
        } finally {
            setLoading(false);
        }
    }, [bookId, navigate, fetchBookDetails]);

    useEffect(() => {
        fetchChapters();
    }, [fetchChapters]);

    // Adaptive polling during content generation
    useEffect(() => {
        // Check if any section is processing
        const hasProcessingSections = chapters.some(ch =>
            ch.sections.some(sec => sec.status === 'PROCESSANDO')
        );

        // Check if book is generating content
        const isGeneratingContent = bookStatus === 'PROCESSANDO';

        if (hasProcessingSections || isGeneratingContent) {
            // Poll every 2 seconds during active generation
            const intervalId = setInterval(() => {
                fetchChapters();
                fetchBookDetails();
            }, 2000);

            return () => clearInterval(intervalId);
        }
    }, [chapters, bookStatus, fetchChapters, fetchBookDetails]);


    // Handle item selection
    const handleSelectChapter = (chapter: Chapter) => {
        setSelectedItem({ type: 'chapter', data: chapter });
        setEditTitle(chapter.title);
        setEditContent('');
    };

    const handleSelectSection = (section: Section) => {
        setSelectedItem({ type: 'section', data: section });
        setEditTitle(section.title);
        setEditContent(section.content_markdown || '');
    };

    // Handle save
    const handleSave = async () => {
        if (!selectedItem) return;

        setSaving(true);
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                navigate('/login');
                return;
            }

            if (selectedItem.type === 'chapter') {
                // Update chapter
                const response = await fetch(`http://localhost:8000/books/chapters/${selectedItem.data.id}`, {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ title: editTitle })
                });

                if (response.ok) {
                    const updatedChapter = await response.json();
                    setChapters(prev => prev.map(ch =>
                        ch.id === updatedChapter.id ? updatedChapter : ch
                    ));
                    setSelectedItem({ type: 'chapter', data: updatedChapter });
                }
            } else {
                // Update section
                const response = await fetch(`http://localhost:8000/books/sections/${selectedItem.data.id}`, {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        title: editTitle,
                        content_markdown: editContent
                    })
                });

                if (response.ok) {
                    const updatedSection = await response.json();
                    setChapters(prev => prev.map(ch => ({
                        ...ch,
                        sections: ch.sections.map(sec =>
                            sec.id === updatedSection.id ? updatedSection : sec
                        )
                    })));
                    setSelectedItem({ type: 'section', data: updatedSection });
                }
            }
        } catch (error) {
            console.error('Error saving:', error);
        } finally {
            setSaving(false);
        }
    };

    // Format time
    const formatTime = (seconds: number): string => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // Get status color
    const getStatusColor = (status: string): string => {
        switch (status) {
            case 'SUCCESS':
            case 'SUCESSO':
            case 'CONCLUIDO':
            case 'COMPLETED':
                return 'bg-green-500/20 text-green-400 border-green-500/30';
            case 'PROCESSING':
            case 'PROCESSANDO':
                return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
            case 'ERROR':
            case 'ERRO':
                return 'bg-red-500/20 text-red-400 border-red-500/30';
            case 'ESTRUTURA_GERADA':
            case 'DISCOVERY_COMPLETE':
                return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
            default:
                return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
        }
    };

    // Handle Generate Content
    const handleGenerateContent = async () => {
        // Check if any section has a video_id (manual trigger check)
        const hasVideo = chapters.some(ch => ch.sections.some(sec => sec.video_id));
        if (hasVideo) {
            alert("Processamento de conteúdo via vídeo ainda não implementado. Por favor, use transcrições.");
            return;
        }

        setGenerating(true);
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`http://localhost:8000/books/${bookId}/generate-content`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                fetchChapters(); // Refresh to show processing status
                setBookStatus('PROCESSANDO');
            } else {
                const error = await response.json();
                alert(`Erro: ${error.detail || 'Falha ao iniciar geração'}`);
            }
        } catch (error) {
            console.error('Error triggering generation:', error);
            alert('Erro de conexão ao iniciar geração.');
        } finally {
            setGenerating(false);
        }
    };

    // Handle Download PDF
    const handleDownloadPDF = async () => {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`http://localhost:8000/books/${bookId}/export/pdf`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                // Get the filename from Content-Disposition header
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = 'ebook.pdf';
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                    if (filenameMatch) {
                        filename = filenameMatch[1];
                    }
                }

                // Create blob and download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                const error = await response.json();
                alert(`Erro ao baixar PDF: ${error.detail || 'Erro desconhecido'}`);
            }
        } catch (error) {
            console.error('Error downloading PDF:', error);
            alert('Erro ao baixar PDF. Tente novamente.');
        }
    };

    // Check if all sections are generated
    const allSectionsGenerated = chapters.length > 0 && chapters.every(ch =>
        ch.sections.every(sec => sec.status === 'SUCESSO')
    );


    // Handle Generate Individual Section Content
    const handleGenerateSectionContent = async (sectionId: string) => {
        setGeneratingSectionId(sectionId);
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`http://localhost:8000/sections/${sectionId}/generate-content`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                // Instantly update local state to processing
                setChapters(prev => prev.map(ch => ({
                    ...ch,
                    sections: ch.sections.map(sec =>
                        sec.id === sectionId ? { ...sec, status: 'PROCESSANDO' } : sec
                    )
                })));

                // If the selected item is this section, update it too
                if (selectedItem?.type === 'section' && selectedItem.data.id === sectionId) {
                    setSelectedItem({
                        type: 'section',
                        data: { ...selectedItem.data, status: 'PROCESSANDO' }
                    });
                }
            } else {
                const error = await response.json();
                alert(`Erro: ${error.detail || 'Falha ao iniciar geração da seção'}`);
            }
        } catch (error) {
            console.error('Error triggering section generation:', error);
            alert('Erro de conexão ao iniciar geração da seção.');
        } finally {
            setGeneratingSectionId(null);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
            {/* Background decorations */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
                <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse delay-1000"></div>
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10"></div>
            </div>

            <div className="relative max-w-7xl mx-auto">
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
                            <h1 className="text-3xl font-bold text-white mb-2">Estrutura do Livro</h1>
                            <p className="text-slate-400">Capítulos e Seções</p>
                        </div>
                    </div>

                    {/* Generate Content Button */}
                    {(bookStatus === 'ESTRUTURA_GERADA' || bookStatus === 'DISCOVERY_COMPLETE') && (
                        <button
                            onClick={handleGenerateContent}
                            disabled={generating}
                            className="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white rounded-xl transition-all shadow-lg shadow-green-500/20 flex items-center gap-2 font-semibold"
                        >
                            {generating ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <BookOpen className="w-5 h-5" />
                            )}
                            Gerar Conteúdo Completo
                        </button>
                    )}

                    {/* Download PDF Button - Only show when all sections are generated */}
                    {allSectionsGenerated && (
                        <button
                            onClick={handleDownloadPDF}
                            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl transition-all shadow-lg shadow-purple-500/20 flex items-center gap-2 font-semibold"
                        >
                            <Download className="w-5 h-5" />
                            Baixar PDF
                        </button>
                    )}

                    {bookStatus === 'PROCESSANDO' && (
                        <div className="flex items-center gap-2 px-6 py-3 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-xl">
                            <Loader2 className="w-5 h-5 animate-spin" />
                            <span className="font-semibold">Gerando Conteúdo...</span>
                        </div>
                    )}
                </div>

                {/* Loading State */}
                {loading && (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-12 h-12 text-purple-400 animate-spin" />
                    </div>
                )}

                {/* Empty State */}
                {!loading && chapters.length === 0 && (
                    <div className="bg-white/10 backdrop-blur-xl rounded-3xl border border-white/20 p-12 text-center">
                        <BookOpen className="w-20 h-20 text-slate-600 mx-auto mb-4" />
                        <h3 className="text-xl font-semibold text-white mb-2">Nenhum capítulo criado ainda</h3>
                        <p className="text-slate-400">Os capítulos e seções serão gerados automaticamente após o processamento dos vídeos.</p>
                    </div>
                )}

                {/* Main Content */}
                {!loading && chapters.length > 0 && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Left Panel - Chapter/Section List */}
                        <div className="lg:col-span-2 bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6 max-h-[calc(100vh-200px)] overflow-y-auto">
                            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                                <FileText className="w-5 h-5" />
                                Estrutura
                            </h2>

                            <div className="space-y-4">
                                {chapters.map((chapter) => (
                                    <div key={chapter.id} className="space-y-2">
                                        {/* Chapter */}
                                        <div
                                            onClick={() => handleSelectChapter(chapter)}
                                            className={`p-4 rounded-lg cursor-pointer transition-all ${selectedItem?.type === 'chapter' && selectedItem.data.id === chapter.id
                                                ? 'bg-purple-600/30 border-2 border-purple-500'
                                                : 'bg-white/5 hover:bg-white/10 border-2 border-transparent'
                                                }`}
                                        >
                                            <div className="flex items-center gap-2">
                                                <ChevronRight className="w-5 h-5 text-purple-400" />
                                                <span className="font-semibold text-white">
                                                    {chapter.order}. {chapter.title}
                                                </span>
                                            </div>
                                        </div>

                                        {/* Sections */}
                                        <div className="ml-8 space-y-2">
                                            {chapter.sections.map((section) => (
                                                <div
                                                    key={section.id}
                                                    onClick={() => handleSelectSection(section)}
                                                    className={`p-3 rounded-lg cursor-pointer transition-all ${selectedItem?.type === 'section' && selectedItem.data.id === section.id
                                                        ? 'bg-indigo-600/30 border-2 border-indigo-500'
                                                        : 'bg-white/5 hover:bg-white/10 border-2 border-transparent'
                                                        }`}
                                                >
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-sm text-slate-300">
                                                            {chapter.order}.{section.order} {section.title}
                                                        </span>
                                                        <div className="flex items-center gap-2">
                                                            <span className={`px-2 py-1 rounded text-xs border ${getStatusColor(section.status)}`}>
                                                                {section.status}
                                                            </span>
                                                            {(section.status === 'PENDENTE' || section.status === 'ERRO') && (
                                                                <button
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        handleGenerateSectionContent(section.id);
                                                                    }}
                                                                    disabled={generatingSectionId === section.id || generating}
                                                                    className="p-1 bg-green-600/20 hover:bg-green-600/40 border border-green-500/30 text-green-400 rounded transition-all flex items-center gap-1 text-[10px] font-bold"
                                                                    title="Gerar apenas esta seção"
                                                                >
                                                                    {generatingSectionId === section.id ? (
                                                                        <Loader2 className="w-3 h-3 animate-spin" />
                                                                    ) : (
                                                                        <Play className="w-3 h-3" />
                                                                    )}
                                                                    GERAR
                                                                </button>
                                                            )}
                                                        </div>
                                                    </div>

                                                    {/* Progress Bar */}
                                                    <div className="mt-2">
                                                        <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                                                            <div
                                                                className={`h-full transition-all duration-500 ${section.status === 'PROCESSANDO'
                                                                    ? 'bg-gradient-to-r from-blue-500 to-indigo-500 animate-pulse'
                                                                    : section.status === 'SUCESSO'
                                                                        ? 'bg-gradient-to-r from-green-500 to-emerald-500'
                                                                        : section.status === 'ERRO'
                                                                            ? 'bg-gradient-to-r from-red-500 to-rose-500'
                                                                            : 'bg-slate-600'
                                                                    }`}
                                                                style={{
                                                                    width: section.status === 'PROCESSANDO'
                                                                        ? '50%'
                                                                        : section.status === 'SUCESSO' || section.status === 'ERRO'
                                                                            ? '100%'
                                                                            : '0%'
                                                                }}
                                                            ></div>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Right Panel - Edit Sidebar */}
                        {selectedItem && (
                            <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6 max-h-[calc(100vh-200px)] overflow-y-auto">
                                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-xl font-semibold text-white">
                                        {selectedItem.type === 'chapter' ? 'Editar Capítulo' : 'Editar Seção'}
                                    </h2>
                                    <button
                                        onClick={() => setSelectedItem(null)}
                                        className="p-1 hover:bg-white/10 rounded transition-all"
                                    >
                                        <X className="w-5 h-5 text-slate-400" />
                                    </button>
                                </div>

                                {/* Title Field */}
                                <div className="mb-4">
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        Título
                                    </label>
                                    <input
                                        type="text"
                                        value={editTitle}
                                        onChange={(e) => setEditTitle(e.target.value)}
                                        className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    />
                                </div>

                                {/* Section-specific fields */}
                                {selectedItem.type === 'section' && (
                                    <>
                                        {/* Status */}
                                        <div className="mb-4">
                                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                                Status
                                            </label>
                                            <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(selectedItem.data.status)}`}>
                                                {selectedItem.data.status}
                                            </span>
                                        </div>

                                        {/* Content Markdown */}
                                        <div className="mb-4">
                                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                                Conteúdo (Markdown)
                                            </label>
                                            <textarea
                                                value={editContent}
                                                onChange={(e) => setEditContent(e.target.value)}
                                                rows={12}
                                                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono text-sm"
                                                placeholder="Conteúdo em Markdown será gerado automaticamente..."
                                            />
                                        </div>
                                    </>
                                )}

                                {/* Save Button */}
                                <button
                                    onClick={handleSave}
                                    disabled={saving}
                                    className="w-full py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:from-slate-600 disabled:to-slate-700 text-white rounded-lg transition-all flex items-center justify-center gap-2"
                                >
                                    {saving ? (
                                        <>
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                            Salvando...
                                        </>
                                    ) : (
                                        <>
                                            <Save className="w-5 h-5" />
                                            Salvar Alterações
                                        </>
                                    )}
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default BookStructure;
