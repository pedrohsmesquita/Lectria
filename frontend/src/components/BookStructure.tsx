import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BookOpen, ChevronRight, Loader2, Save, X, ArrowLeft, FileText, Video, Clock } from 'lucide-react';

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
            }
        } catch (error) {
            console.error('Error fetching chapters:', error);
        } finally {
            setLoading(false);
        }
    }, [bookId, navigate]);

    useEffect(() => {
        fetchChapters();
    }, [fetchChapters]);

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
                return 'bg-green-500/20 text-green-400 border-green-500/30';
            case 'PROCESSING':
                return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
            case 'ERROR':
                return 'bg-red-500/20 text-red-400 border-red-500/30';
            default:
                return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
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
                                                        <span className={`px-2 py-1 rounded text-xs border ${getStatusColor(section.status)}`}>
                                                            {section.status}
                                                        </span>
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
                                        {/* Video Info */}
                                        <div className="mb-4 p-3 bg-white/5 rounded-lg">
                                            <div className="flex items-center gap-2 text-sm text-slate-300 mb-2">
                                                <Video className="w-4 h-4" />
                                                <span className="font-medium">Vídeo:</span>
                                            </div>
                                            <p className="text-sm text-slate-400 mb-2">
                                                {selectedItem.data.video_filename || 'N/A'}
                                            </p>
                                            <div className="flex items-center gap-2 text-sm text-slate-400">
                                                <Clock className="w-4 h-4" />
                                                <span>
                                                    {formatTime(selectedItem.data.start_time)} - {formatTime(selectedItem.data.end_time)}
                                                </span>
                                            </div>
                                        </div>

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
