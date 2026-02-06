import React, { useState } from 'react';
import { X, BookOpen, Loader2 } from 'lucide-react';

// ============================================
// CreateBookModal Component
// ============================================

interface CreateBookModalProps {
    onClose: () => void;
    onBookCreated: (book: any) => void;
}

const CreateBookModal: React.FC<CreateBookModalProps> = ({ onClose, onBookCreated }) => {
    const [title, setTitle] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!title.trim()) {
            setError('O título não pode estar vazio');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const token = localStorage.getItem('access_token');

            const response = await fetch('http://localhost:8000/books', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ title: title.trim() })
            });

            if (response.ok) {
                const newBook = await response.json();
                onBookCreated(newBook);
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Erro ao criar livro');
            }
        } catch (err) {
            setError('Erro de conexão. Tente novamente.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-900 rounded-2xl border border-white/20 max-w-md w-full shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-white/10">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg flex items-center justify-center">
                            <BookOpen className="w-5 h-5 text-white" />
                        </div>
                        <h2 className="text-xl font-semibold text-white">Criar Novo Livro</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-white transition-colors"
                        disabled={loading}
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-6">
                    <div className="mb-6">
                        <label htmlFor="book-title" className="block text-sm font-medium text-slate-300 mb-2">
                            Título do Livro
                        </label>
                        <input
                            id="book-title"
                            type="text"
                            value={title}
                            onChange={(e) => {
                                setTitle(e.target.value);
                                setError('');
                            }}
                            placeholder="Ex: Fundamentos de Python"
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition-all"
                            disabled={loading}
                            autoFocus
                        />
                        {error && (
                            <p className="mt-2 text-sm text-red-400">{error}</p>
                        )}
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg transition-all"
                            disabled={loading}
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            disabled={loading || !title.trim()}
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Criando...
                                </>
                            ) : (
                                'Criar Livro'
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CreateBookModal;
