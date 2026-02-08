import React, { useState, useEffect } from 'react';
import { BookOpen, Plus, Upload, Video, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import CreateBookModal from './CreateBookModal';

// ============================================
// BooksDashboard Component - List all books
// ============================================

interface Book {
    id: string;
    title: string;
    author: string;
    status: string;
    created_at: string;
    video_count: number;
}

const BooksDashboard: React.FC = () => {
    const navigate = useNavigate();
    const [books, setBooks] = useState<Book[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);

    // Fetch books from API
    const fetchBooks = async () => {
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
    };

    useEffect(() => {
        fetchBooks();
    }, []);

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

    // Get status badge color
    const getStatusColor = (status: string): string => {
        switch (status) {
            case 'COMPLETED':
                return 'bg-green-500/20 text-green-400 border-green-500/30';
            case 'PROCESSING':
                return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
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
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">Meus Livros</h1>
                        <p className="text-slate-400">Gerencie seus livros e vídeos educacionais</p>
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
                        <p className="text-slate-400 mb-6">Crie seu primeiro livro para começar a adicionar vídeos</p>
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
                                onClick={() => navigate(`/books/${book.id}/structure`)}
                                className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 overflow-hidden hover:bg-white/[0.15] transition-all hover:scale-[1.02] cursor-pointer group"
                            >
                                <div className="p-6">
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
                                    <div className="flex items-center gap-2 mb-4">
                                        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(book.status)}`}>
                                            {book.status}
                                        </span>
                                    </div>

                                    {/* Video Count */}
                                    <div className="flex items-center gap-2 text-slate-300 mb-4">
                                        <Video className="w-4 h-4" />
                                        <span className="text-sm">
                                            {book.video_count} {book.video_count === 1 ? 'vídeo' : 'vídeos'}
                                        </span>
                                    </div>

                                    {/* Date */}
                                    <p className="text-xs text-slate-500 mb-4">
                                        Criado em {formatDate(book.created_at)}
                                    </p>

                                    {/* Action Button */}
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            navigate(`/upload/${book.id}`);
                                        }}
                                        className="w-full py-3 bg-white/5 hover:bg-purple-600 border border-white/10 hover:border-purple-500 text-white rounded-lg transition-all flex items-center justify-center gap-2 group-hover:bg-purple-600"
                                    >
                                        <Upload className="w-4 h-4" />
                                        Adicionar Vídeos
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
        </div>
    );
};

export default BooksDashboard;
