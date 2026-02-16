import React, { useState, useEffect, useCallback } from 'react';
import { BookOpen, Plus, Loader2, Trash2, FileText } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import CreateBookModal from './CreateBookModal';
import { translateStatus } from '../utils/statusTranslations';

// ============================================
// BooksDashboard Component - List all books
// ============================================

interface Book {
    id: string;
    title: string;
    author: string;
    status: string;
    status_display?: string;  // Status traduzido do backend
    processing_progress?: number;  // 0-100
    current_step?: string;  // Etapa atual
    created_at: string;
    video_count: number;
}

const BooksDashboard: React.FC = () => {
    const navigate = useNavigate();
    const [books, setBooks] = useState<Book[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [deleteConfirmBook, setDeleteConfirmBook] = useState<Book | null>(null);
    const [deleting, setDeleting] = useState(false);

    // Fetch books from API
    const fetchBooks = useCallback(async () => {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                navigate('/login');
                return;
            }

            const response = await fetch('http://localhost:8000/books', {
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
                setBooks(data);
            }
        } catch (error) {
            console.error('Error fetching books:', error);
        } finally {
            setLoading(false);
        }
    }, [navigate]);

    useEffect(() => {
        fetchBooks();

        // Determine polling interval based on current book states
        const hasActiveProcessing = books.some(book =>
            ['PROCESSANDO', 'ANALISANDO_CONTEUDO', 'GERANDO_SUMARIO', 'GERANDO_CONTEUDO'].includes(book.status)
        );

        const hasStructureReady = books.some(book =>
            ['ESTRUTURA_GERADA', 'DISCOVERY_COMPLETE'].includes(book.status)
        );

        let pollingInterval = 10000; // Default: 10 seconds for stable states

        if (hasActiveProcessing) {
            pollingInterval = 2000; // 2 seconds during active processing
        } else if (hasStructureReady) {
            pollingInterval = 5000; // 5 seconds when structure is ready
        }

        // Set up interval with current polling rate
        const intervalId = setInterval(fetchBooks, pollingInterval);

        // Cleanup interval on unmount or when dependencies change
        return () => clearInterval(intervalId);
    }, [fetchBooks, books]); // Re-run when books change to adjust polling rate



    // Handle logout
    const handleLogout = () => {
        localStorage.removeItem('access_token');
        navigate('/login');
    };

    // Handle book creation success
    const handleBookCreated = (newBook: any) => {
        // Ensure created_at is a string
        const bookToAdd: Book = {
            ...newBook,
            created_at: typeof newBook.created_at === 'string'
                ? newBook.created_at
                : new Date(newBook.created_at).toISOString()
        };
        setBooks(prev => [bookToAdd, ...prev]);
        setShowCreateModal(false);
    };

    // Format date
    const formatDate = (dateString: string | Date): string => {
        try {
            const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
            if (isNaN(date.getTime())) {
                return 'Data inválida';
            }
            return date.toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: 'short',
                year: 'numeric'
            });
        } catch (error) {
            console.error('Error formatting date:', error, dateString);
            return 'Data inválida';
        }
    };

    // Handle book deletion
    const handleDeleteBook = async (book: Book) => {
        setDeleting(true);
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                navigate('/login');
                return;
            }

            const response = await fetch(`http://localhost:8000/books/${book.id}`, {
                method: 'DELETE',
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
                // Remove book from local state
                setBooks(prev => prev.filter(b => b.id !== book.id));
                setDeleteConfirmBook(null);
            } else {
                const error = await response.json();
                alert(`Erro ao excluir livro: ${error.detail || 'Erro desconhecido'}`);
            }
        } catch (error) {
            console.error('Error deleting book:', error);
            alert('Erro ao excluir livro. Tente novamente.');
        } finally {
            setDeleting(false);
        }
    };

    // Get status badge color
    const getStatusColor = (status: string): string => {
        if (['COMPLETED', 'SUCCESS'].includes(status)) {
            return 'bg-green-500/20 text-green-400 border-green-500/30';
        } else if (['PROCESSING', 'EXTRACTING_AUDIO', 'UPLOADING_TO_GEMINI', 'ANALYZING_CONTENT', 'GENERATING_STRUCTURE'].includes(status)) {
            return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
        } else if (status === 'ERROR') {
            return 'bg-red-500/20 text-red-400 border-red-500/30';
        } else {
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
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">Meus Livros</h1>
                        <p className="text-slate-400">Gerencie seus livros e transcrições educacionais</p>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/20 text-white rounded-lg transition-all"
                    >
                        Sair
                    </button>
                </div>

                {/* Create New Book Button */}
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="w-full mb-8 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-2xl p-6 transition-all shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 hover:scale-[1.02]"
                >
                    <div className="flex items-center justify-center gap-3">
                        <Plus className="w-6 h-6" />
                        <span className="text-lg font-semibold">Criar Novo Livro</span>
                    </div>
                </button>

                {/* Loading State */}
                {loading && (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-12 h-12 text-purple-400 animate-spin" />
                    </div>
                )}

                {/* Empty State */}
                {!loading && books.length === 0 && (
                    <div className="bg-white/10 backdrop-blur-xl rounded-3xl border border-white/20 p-12 text-center">
                        <BookOpen className="w-20 h-20 text-slate-600 mx-auto mb-4" />
                        <h3 className="text-xl font-semibold text-white mb-2">Nenhum livro criado ainda</h3>
                        <p className="text-slate-400 mb-6">Crie seu primeiro livro para começar a adicionar transcrições</p>
                        <button
                            onClick={() => setShowCreateModal(true)}
                            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-all inline-flex items-center gap-2"
                        >
                            <Plus className="w-5 h-5" />
                            Criar Primeiro Livro
                        </button>
                    </div>
                )}

                {/* Books Grid */}
                {!loading && books.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {books.map((book) => (
                            <div
                                key={book.id}
                                className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 overflow-hidden hover:bg-white/[0.15] transition-all hover:scale-[1.02] group relative"
                            >
                                {/* Delete Button - Top Right Corner */}
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setDeleteConfirmBook(book);
                                    }}
                                    className="absolute top-4 right-4 p-2 bg-white/5 hover:bg-red-600 border border-white/10 hover:border-red-500 text-slate-400 hover:text-white rounded-lg transition-all z-10"
                                    title="Excluir livro"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>

                                {/* Clickable Card Content */}
                                <div
                                    onClick={() => navigate(`/books/${book.id}/structure`)}
                                    className="p-6 cursor-pointer"
                                >
                                    {/* Book Icon */}
                                    <div className="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl shadow-lg shadow-purple-500/25 mb-4">
                                        <BookOpen className="w-7 h-7 text-white" />
                                    </div>

                                    {/* Book Title */}
                                    <h3 className="text-xl font-semibold text-white mb-2 truncate">
                                        {book.title}
                                    </h3>

                                    {/* Author */}
                                    <p className="text-sm text-slate-400 mb-4">
                                        por {book.author}
                                    </p>

                                    {/* Status Badge */}
                                    <div className="mb-4">
                                        {book.video_count > 0 || ['PROCESSANDO', 'ANALISANDO_CONTEUDO', 'GERANDO_SUMARIO', 'GERANDO_CONTEUDO', 'ESTRUTURA_GERADA', 'CONCLUIDO', 'ERRO'].includes(book.status) ? (
                                            <>
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(book.status)} ${['PROCESSANDO', 'ANALISANDO_CONTEUDO', 'GERANDO_SUMARIO', 'GERANDO_CONTEUDO'].includes(book.status)
                                                        ? 'animate-pulse'
                                                        : ''
                                                        }`}>
                                                        {book.status_display || translateStatus(book.status)}
                                                    </span>
                                                </div>

                                                {/* Progress Bar */}
                                                {book.processing_progress != null && book.processing_progress < 100 && (
                                                    <div className="space-y-1">
                                                        <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                                                            <div
                                                                className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 transition-all duration-500"
                                                                style={{ width: `${book.processing_progress}%` }}
                                                            ></div>
                                                        </div>
                                                        {book.current_step && (
                                                            <p className="text-xs text-slate-400">{book.current_step}</p>
                                                        )}
                                                    </div>
                                                )}
                                            </>
                                        ) : (
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className="px-3 py-1 rounded-full text-xs font-medium border border-slate-600 bg-slate-800/50 text-slate-400">
                                                    Aguardando conteúdo
                                                </span>
                                            </div>
                                        )}
                                    </div>



                                    {/* Date */}
                                    <p className="text-xs text-slate-500 mb-4">
                                        Criado em {formatDate(book.created_at)}
                                    </p>

                                    {/* Action Button */}
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            navigate(`/upload-transcript/${book.id}`);
                                        }}
                                        className="w-full py-3 bg-white/5 hover:bg-purple-600 border border-white/10 hover:border-purple-500 text-white rounded-lg transition-all flex items-center justify-center gap-2"
                                    >
                                        <FileText className="w-4 h-4" />
                                        Enviar transcrição
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Create Book Modal */}
            {showCreateModal && (
                <CreateBookModal
                    onClose={() => setShowCreateModal(false)}
                    onBookCreated={handleBookCreated}
                />
            )}

            {/* Delete Confirmation Modal */}
            {deleteConfirmBook && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-slate-800 rounded-2xl border border-white/20 p-6 max-w-md w-full shadow-2xl">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center">
                                <Trash2 className="w-6 h-6 text-red-400" />
                            </div>
                            <h3 className="text-xl font-semibold text-white">Excluir Livro</h3>
                        </div>

                        <p className="text-slate-300 mb-2">
                            Tem certeza que deseja excluir o livro <strong className="text-white">"{deleteConfirmBook.title}"</strong>?
                        </p>
                        <p className="text-slate-400 text-sm mb-6">
                            Esta ação não pode ser desfeita. Todas as transcrições e dados relacionados serão permanentemente removidos.
                        </p>

                        <div className="flex gap-3">
                            <button
                                onClick={() => setDeleteConfirmBook(null)}
                                disabled={deleting}
                                className="flex-1 py-3 bg-white/10 hover:bg-white/20 border border-white/20 text-white rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={() => handleDeleteBook(deleteConfirmBook)}
                                disabled={deleting}
                                className="flex-1 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {deleting ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        Excluindo...
                                    </>
                                ) : (
                                    <>
                                        <Trash2 className="w-4 h-4" />
                                        Excluir
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default BooksDashboard;
