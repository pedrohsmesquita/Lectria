import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    BookOpen, ChevronRight, Loader2, Save, X, ArrowLeft, FileText, Play, Download,
    Edit, Trash2, ChevronUp, MoveVertical, Image as ImageIcon, Plus, Upload, ChevronDown, CheckCircle2, Clock, AlertCircle, Settings, BookMarked
} from 'lucide-react';

// ============================================
// Types
// ============================================

interface SectionAsset {
    id: string;
    placeholder: string;
    caption: string | null;
    source_type: string;
    storage_path: string;
    slide_page: number | null;
    crop_info: any | null;
}

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
    assets: SectionAsset[];
}

interface Chapter {
    id: string;
    book_id: string;
    title: string;
    order: number;
    is_bibliography: boolean;
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
    const [savingBibliography, setSavingBibliography] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [generatingSectionId, setGeneratingSectionId] = useState<string | null>(null);
    const [bookStatus, setBookStatus] = useState<string>('');

    // Editing mode state
    const [isEditMode, setIsEditMode] = useState(false);
    const [tempChapters, setTempChapters] = useState<Chapter[]>([]);

    // Asset Management State
    const [isVisualMode, setIsVisualMode] = useState(true);
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [uploadCaption, setUploadCaption] = useState('');
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);

    // Unified Edit Asset Modal State
    const [isEditAssetModalOpen, setIsEditAssetModalOpen] = useState(false);
    const [editingAsset, setEditingAsset] = useState<SectionAsset | null>(null);
    const [editAssetCaption, setEditAssetCaption] = useState('');
    const [editAssetFile, setEditAssetFile] = useState<File | null>(null);
    const [isSavingAsset, setIsSavingAsset] = useState(false);

    // Manual Image Insertion Ref & State
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [lastCursorPosition, setLastCursorPosition] = useState<number | null>(null);

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
        const hasProcessingSections = chapters.some((ch: Chapter) =>
            ch.sections.some((sec: Section) => sec.status === 'PROCESSANDO')
        );

        // Check if book is generating content
        const isGeneratingContent = bookStatus === 'PROCESSANDO';

        // ONLY poll if not in edit mode
        if (!isEditMode && (hasProcessingSections || isGeneratingContent)) {
            // Poll every 2 seconds during active generation
            const intervalId = setInterval(() => {
                fetchChapters();
                fetchBookDetails();
            }, 2000);

            return () => clearInterval(intervalId);
        }
    }, [chapters, bookStatus, fetchChapters, fetchBookDetails, isEditMode]);


    // Handle item selection
    const handleSelectChapter = (chapter: Chapter) => {
        if (isEditMode) return; // Prevent selection in edit mode
        setSelectedItem({ type: 'chapter', data: chapter });
        setEditTitle(chapter.title);
        setEditContent('');
    };

    const handleSelectSection = (section: Section) => {
        if (isEditMode) return; // Prevent selection in edit mode
        setSelectedItem({ type: 'section', data: section });
        setEditTitle(section.title);
        setEditContent(section.content_markdown || '');
    };

    // Rearrangement Logic
    const toggleEditMode = () => {
        if (!isEditMode) {
            setTempChapters(JSON.parse(JSON.stringify(chapters)));
            setSelectedItem(null);
        }
        setIsEditMode(!isEditMode);
    };

    const handleUploadAsset = async () => {
        if (!selectedItem || selectedItem.type !== 'section' || !uploadFile) return;

        setIsUploading(true);
        const formData = new FormData();
        formData.append('file', uploadFile);
        formData.append('caption', uploadCaption);

        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`http://localhost:8000/assets/${selectedItem.data.id}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData,
            });

            if (!response.ok) throw new Error('Falha ao enviar imagem');

            const data = await response.json();

            // Update local state
            setChapters((prev: Chapter[]) => prev.map((ch: Chapter) => ({
                ...ch,
                sections: ch.sections.map((sec: Section) => {
                    if (sec.id === selectedItem.data.id) {
                        let newContent = sec.content_markdown || '';
                        const placeholder = `\n\n${data.asset.placeholder}\n\n`;

                        if (lastCursorPosition !== null) {
                            newContent =
                                newContent.slice(0, lastCursorPosition) +
                                placeholder +
                                newContent.slice(lastCursorPosition);
                        } else {
                            newContent += placeholder;
                        }

                        return {
                            ...sec,
                            assets: [...(sec.assets || []), data.asset],
                            content_markdown: newContent
                        };
                    }
                    return sec;
                })
            })));

            // Also update the current editContent if it's the active section
            if (selectedItem.data.id === selectedItem.data.id) {
                setEditContent(prev => {
                    const placeholder = `\n\n${data.asset.placeholder}\n\n`;
                    if (lastCursorPosition !== null) {
                        return prev.slice(0, lastCursorPosition) + placeholder + prev.slice(lastCursorPosition);
                    }
                    return prev + placeholder;
                });
            }

            // Reset modal state
            setIsUploadModalOpen(false);
            setUploadFile(null);
            setUploadCaption('');
            setLastCursorPosition(null);

        } catch (error) {
            console.error('Error uploading asset:', error);
            alert('Erro ao enviar imagem. Tente novamente.');
        } finally {
            setIsUploading(false);
        }
    };

    const handleDeleteAsset = async (assetId: string) => {
        if (!window.confirm('Tem certeza que deseja remover esta imagem?')) return;

        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`http://localhost:8000/assets/${assetId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) throw new Error('Falha ao deletar imagem');

            // Find the placeholder before updating state
            let deletedPlaceholder = '';
            chapters.forEach(ch => {
                ch.sections.forEach(sec => {
                    if (selectedItem?.type === 'section' && sec.id === selectedItem.data.id) {
                        const asset = sec.assets.find(a => a.id === assetId);
                        if (asset) deletedPlaceholder = asset.placeholder;
                    }
                });
            });

            // Update local state
            setChapters((prev: Chapter[]) => prev.map((ch: Chapter) => ({
                ...ch,
                sections: ch.sections.map((sec: Section) => {
                    if (selectedItem?.type === 'section' && sec.id === selectedItem.data.id) {
                        return {
                            ...sec,
                            assets: sec.assets.filter((a: SectionAsset) => a.id !== assetId),
                            content_markdown: deletedPlaceholder
                                ? sec.content_markdown?.replace(new RegExp(`\\n*\\s*${deletedPlaceholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\n*`, 'g'), '\n\n').trim() || ''
                                : sec.content_markdown
                        };
                    }
                    return sec;
                })
            })));

            // Also update the current editContent if it's the active section
            if (deletedPlaceholder && selectedItem?.type === 'section') {
                setEditContent(prev => {
                    const regex = new RegExp(`\\n*\\s*${deletedPlaceholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\n*`, 'g');
                    return prev.replace(regex, '\n\n').trim();
                });
            }

            // Refresh from server to ensure sync
            fetchChapters();
        } catch (error) {
            console.error('Error deleting asset:', error);
            alert('Erro ao remover imagem.');
        }
    };

    const handleUpdateAsset = async (assetId: string, options: { caption?: string, file?: File }) => {
        const formData = new FormData();
        if (options.caption !== undefined) formData.append('caption', options.caption);
        if (options.file) formData.append('file', options.file);

        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`http://localhost:8000/assets/${assetId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (!response.ok) throw new Error('Falha ao atualizar recurso');

            const data = await response.json();

            setChapters((prev: Chapter[]) => prev.map((ch: Chapter) => ({
                ...ch,
                sections: ch.sections.map((sec: Section) => {
                    if (selectedItem?.type === 'section' && sec.id === selectedItem.data.id) {
                        return {
                            ...sec,
                            assets: sec.assets.map((a: SectionAsset) =>
                                a.id === assetId
                                    ? {
                                        ...a,
                                        caption: data.caption ?? a.caption,
                                        storage_path: data.storage_path ?? a.storage_path
                                    }
                                    : a
                            )
                        };
                    }
                    return sec;
                })
            })));

            // Re-fetch to ensure UI is in sync with backend
            fetchChapters();
        } catch (error) {
            console.error('Error updating asset:', error);
            alert('Erro ao atualizar imagem.');
        }
    };

    const renderContent = (content: string | null, assets: SectionAsset[]) => {
        if (!content) return <p className="text-slate-500 italic">Sem conteúdo gerado.</p>;

        const parts = content.split(/(\[IMAGE_\d+\])/g);

        return (
            <div className="space-y-4">
                {parts.map((part, index) => {
                    const match = part.match(/\[IMAGE_(\d+)\]/);
                    if (match) {
                        const asset = assets.find(a => a.placeholder === part);
                        if (!asset) return <div key={index} className="p-4 bg-red-50 text-red-500 border border-red-200 rounded">Imagem {part} não encontrada ou inválida</div>;

                        const rawPath = asset.storage_path.replace(/\\/g, '/');
                        const pathAfterMedia = rawPath.includes('/media/')
                            ? rawPath.split('/media/')[1]
                            : rawPath.includes('media/')
                                ? rawPath.split('media/')[1]
                                : rawPath;

                        const imageUrl = `http://localhost:8000/media/${pathAfterMedia}`;

                        return (
                            <div key={index} className="group relative my-6 bg-slate-50 rounded-lg overflow-hidden border border-slate-200 shadow-sm transition-all hover:shadow-md">
                                <img
                                    src={imageUrl}
                                    alt={asset.caption || "Imagem da seção"}
                                    className="w-full h-auto object-contain bg-slate-100"
                                />
                                {asset.caption && (
                                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center p-6 text-center text-white text-sm font-medium">
                                        {asset.caption}
                                    </div>
                                )}
                                <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                        onClick={() => {
                                            setEditingAsset(asset);
                                            setEditAssetCaption(asset.caption || '');
                                            setEditAssetFile(null);
                                            setIsEditAssetModalOpen(true);
                                        }}
                                        className="p-1.5 bg-white/90 hover:bg-white rounded-full text-indigo-600 shadow-sm transition-all hover:scale-110"
                                        title="Editar imagem e legenda"
                                    >
                                        <Settings className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => handleDeleteAsset(asset.id)}
                                        className="p-1.5 bg-red-500 hover:bg-red-600 rounded-full text-white shadow-sm transition-all hover:scale-110"
                                        title="Remover imagem"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                                <div className="absolute bottom-2 left-2 px-2 py-0.5 bg-black/50 text-white text-[10px] font-bold rounded uppercase tracking-wider backdrop-blur-sm">
                                    {asset.placeholder}
                                </div>
                            </div>
                        );
                    }
                    return <div key={index} className="whitespace-pre-wrap leading-relaxed text-slate-800">{part}</div>;
                })}
            </div>
        );
    };

    const moveChapter = (index: number, direction: 'up' | 'down') => {
        const newChapters = [...tempChapters];
        const newIndex = direction === 'up' ? index - 1 : index + 1;
        if (newIndex < 0 || newIndex >= newChapters.length) return;

        const [movedChapter] = newChapters.splice(index, 1);
        newChapters.splice(newIndex, 0, movedChapter);

        // Update orders
        newChapters.forEach((ch, i) => {
            ch.order = i + 1;
        });

        setTempChapters(newChapters);
    };

    const moveSection = (chapterIndex: number, sectionIndex: number, direction: 'up' | 'down') => {
        const newChapters = [...tempChapters];
        const sections = [...newChapters[chapterIndex].sections];
        const newIndex = direction === 'up' ? sectionIndex - 1 : sectionIndex + 1;
        if (newIndex < 0 || newIndex >= sections.length) return;

        const [movedSection] = sections.splice(sectionIndex, 1);
        sections.splice(newIndex, 0, movedSection);

        // Update orders
        sections.forEach((sec, i) => {
            sec.order = i + 1;
        });

        newChapters[chapterIndex].sections = sections;
        setTempChapters(newChapters);
    };

    const moveSectionToChapter = (sourceChapterIndex: number, sectionIndex: number, targetChapterId: string) => {
        if (!targetChapterId) return;
        const newChapters = [...tempChapters];
        const targetChapterIndex = newChapters.findIndex(ch => ch.id === targetChapterId);
        if (targetChapterIndex === -1 || targetChapterIndex === sourceChapterIndex) return;

        // Remove from source
        const [movedSection] = newChapters[sourceChapterIndex].sections.splice(sectionIndex, 1);

        // Update source orders
        newChapters[sourceChapterIndex].sections.forEach((sec: Section, i: number) => {
            sec.order = i + 1;
        });

        // Add to target
        movedSection.chapter_id = targetChapterId;
        newChapters[targetChapterIndex].sections.push(movedSection);

        // Update target orders
        newChapters[targetChapterIndex].sections.forEach((sec: Section, i: number) => {
            sec.order = i + 1;
        });

        setTempChapters(newChapters);
    };

    const saveStructure = async () => {
        setSaving(true);
        try {
            const token = localStorage.getItem('access_token');
            const structureUpdate = {
                chapters: tempChapters.map((ch: Chapter) => ({
                    id: ch.id,
                    order: ch.order,
                    sections: ch.sections.map((sec: Section) => ({
                        id: sec.id,
                        order: sec.order,
                        chapter_id: sec.chapter_id
                    }))
                }))
            };

            const response = await fetch(`http://localhost:8000/books/${bookId}/structure`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(structureUpdate)
            });

            if (response.ok) {
                setChapters(tempChapters);
                setIsEditMode(false);
            } else {
                const error = await response.json();
                alert(`Erro ao salvar estrutura: ${error.detail || 'Erro desconhecido'}`);
            }
        } catch (error) {
            console.error('Error saving structure:', error);
            alert('Erro de conexão ao salvar estrutura.');
        } finally {
            setSaving(false);
        }
    };

    // Handle Save Bibliography
    const handleSaveBibliography = async () => {
        if (!selectedItem || selectedItem.type !== 'section') return;

        const confirmed = window.confirm(
            'Alterações na numeração das referências serão aplicadas automaticamente em todas as seções do livro. Deseja continuar?'
        );
        if (!confirmed) return;

        setSavingBibliography(true);
        try {
            const token = localStorage.getItem('access_token');
            if (!token) { navigate('/login'); return; }

            const response = await fetch(`http://localhost:8000/books/${bookId}/bibliography`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content_markdown: editContent })
            });

            if (response.ok) {
                const result = await response.json();
                alert(`✅ ${result.message}\n\n📚 ${result.references_updated} referência(s) atualizada(s)\n📄 ${result.sections_affected} seção(ões) com citações atualizadas`);
                // Refresh to reflect any changes in section contents
                fetchChapters();
            } else {
                const error = await response.json();
                alert(`Erro ao salvar bibliografia: ${error.detail || 'Erro desconhecido'}`);
            }
        } catch (error) {
            console.error('Error saving bibliography:', error);
            alert('Erro de conexão ao salvar bibliografia.');
        } finally {
            setSavingBibliography(false);
        }
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
                    setChapters((prev: Chapter[]) => prev.map((ch: Chapter) =>
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
                    setChapters((prev: Chapter[]) => prev.map((ch: Chapter) => ({
                        ...ch,
                        sections: ch.sections.map((sec: Section) =>
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
        const hasVideo = chapters.some((ch: Chapter) => ch.sections.some((sec: Section) => sec.video_id));
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
    const allSectionsGenerated = chapters.length > 0 && chapters.every((ch: Chapter) =>
        ch.sections.every((sec: Section) => sec.status === 'SUCESSO')
    );

    // Check if any section is NOT pending
    const canEditStructure = chapters.length > 0 && chapters.every((ch: Chapter) =>
        ch.sections.every((sec: Section) => sec.status === 'PENDENTE' || sec.status === 'ESTRUTURA_GERADA')
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
                setChapters((prev: Chapter[]) => prev.map((ch: Chapter) => ({
                    ...ch,
                    sections: ch.sections.map((sec: Section) =>
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

                    <div className="flex items-center gap-4">
                        {/* Edit Structure Button */}
                        {!generating && !loading && chapters.length > 0 && canEditStructure && bookStatus !== 'PROCESSANDO' && (
                            <button
                                onClick={toggleEditMode}
                                className={`px-4 py-2 rounded-xl transition-all border flex items-center gap-2 font-semibold ${isEditMode
                                    ? 'bg-red-500/20 border-red-500/50 text-red-400'
                                    : 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                                    }`}
                            >
                                {isEditMode ? <X className="w-5 h-5" /> : <Play className="w-4 h-4 rotate-90" />}
                                {isEditMode ? 'Cancelar Edição' : 'Editar Estrutura'}
                            </button>
                        )}

                        {/* Save Structure Button */}
                        {isEditMode && (
                            <button
                                onClick={saveStructure}
                                disabled={saving}
                                className="px-6 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl transition-all shadow-lg shadow-blue-500/20 flex items-center gap-2 font-semibold disabled:opacity-50"
                            >
                                {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />}
                                Salvar Estrutura
                            </button>
                        )}

                        {/* Generate Content Button */}
                        {!isEditMode && (bookStatus === 'ESTRUTURA_GERADA' || bookStatus === 'DISCOVERY_COMPLETE') && (
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
                        {!isEditMode && allSectionsGenerated && (
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
                </div>

                {/* Edit Mode Instructions */}
                {isEditMode && (
                    <div className="mb-6 p-4 bg-blue-500/20 border border-blue-500/40 rounded-2xl animate-in fade-in slide-in-from-top-4 duration-300">
                        <p className="text-blue-200 text-center font-medium">
                            Mova capítulos, seções no mesmo capítulo ou entre capítulos utilizando as setas e o menu de seleção.
                        </p>
                    </div>
                )}

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
                {!loading && (isEditMode ? tempChapters : chapters).length > 0 && (
                    <div className={`grid grid-cols-1 ${isEditMode ? 'lg:grid-cols-1' : 'lg:grid-cols-3'} gap-6`}>
                        {/* Left Panel - Chapter/Section List */}
                        <div className={`${isEditMode ? 'lg:col-span-1' : 'lg:col-span-2'} bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6 max-h-[calc(100vh-200px)] overflow-y-auto`}>
                            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                                <FileText className="w-5 h-5" />
                                Estrutura {isEditMode && <span className="text-blue-400 text-sm font-normal">(Modo de Edição)</span>}
                            </h2>

                            <div className="space-y-4">
                                {(isEditMode ? tempChapters : chapters).map((chapter: Chapter, chapterIndex: number) => (
                                    <div key={chapter.id} className="space-y-2">
                                        {/* Chapter */}
                                        <div
                                            onClick={() => handleSelectChapter(chapter)}
                                            className={`p-4 rounded-lg transition-all ${!isEditMode && selectedItem?.type === 'chapter' && selectedItem.data.id === chapter.id
                                                ? chapter.is_bibliography ? 'bg-amber-600/30 border-2 border-amber-500' : 'bg-purple-600/30 border-2 border-purple-500'
                                                : 'bg-white/5 hover:bg-white/10 border-2 border-transparent'
                                                } ${isEditMode ? 'cursor-default' : 'cursor-pointer'}`}
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-2">
                                                    {chapter.is_bibliography ? (
                                                        <BookMarked className="w-5 h-5 text-amber-400" />
                                                    ) : (
                                                        <ChevronRight className="w-5 h-5 text-purple-400" />
                                                    )}
                                                    <span className={`font-semibold ${chapter.is_bibliography ? 'text-amber-300' : 'text-white'}`}>
                                                        {chapter.is_bibliography ? '' : chapter.order + '.'} {chapter.title}
                                                    </span>
                                                    {chapter.is_bibliography && (
                                                        <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-full uppercase tracking-wider">
                                                            Referências
                                                        </span>
                                                    )}
                                                </div>

                                                {isEditMode && (
                                                    <div className="flex items-center gap-2">
                                                        <button
                                                            onClick={(e: React.MouseEvent) => { e.stopPropagation(); moveChapter(chapterIndex, 'up'); }}
                                                            disabled={chapterIndex === 0}
                                                            className="p-1 hover:bg-white/20 rounded disabled:opacity-30 transition-colors"
                                                            title="Mover capítulo para cima"
                                                        >
                                                            <ChevronRight className="w-5 h-5 -rotate-90" />
                                                        </button>
                                                        <button
                                                            onClick={(e: React.MouseEvent) => { e.stopPropagation(); moveChapter(chapterIndex, 'down'); }}
                                                            disabled={chapterIndex === tempChapters.length - 1}
                                                            className="p-1 hover:bg-white/20 rounded disabled:opacity-30 transition-colors"
                                                            title="Mover capítulo para baixo"
                                                        >
                                                            <ChevronRight className="w-5 h-5 rotate-90" />
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        {/* Sections */}
                                        <div className="ml-8 space-y-2">
                                            {chapter.sections.map((section: Section, sectionIndex: number) => (
                                                <div
                                                    key={section.id}
                                                    onClick={() => handleSelectSection(section)}
                                                    className={`p-3 rounded-lg transition-all ${!isEditMode && selectedItem?.type === 'section' && selectedItem.data.id === section.id
                                                        ? 'bg-indigo-600/30 border-2 border-indigo-500'
                                                        : 'bg-white/5 hover:bg-white/10 border-2 border-transparent'
                                                        } ${isEditMode ? 'cursor-default' : 'cursor-pointer'}`}
                                                >
                                                    <div className="flex items-center justify-between">
                                                        <div className="flex items-center gap-3">
                                                            <span className="text-sm text-slate-300">
                                                                {chapter.order}.{section.order} {section.title}
                                                            </span>
                                                        </div>

                                                        <div className="flex items-center gap-2">
                                                            {isEditMode ? (
                                                                <div className="flex items-center gap-3 bg-black/20 p-1 rounded-lg">
                                                                    {/* Move arrows */}
                                                                    <div className="flex items-center border-r border-white/10 pr-2 mr-2">
                                                                        <button
                                                                            onClick={(e: React.MouseEvent) => { e.stopPropagation(); moveSection(chapterIndex, sectionIndex, 'up'); }}
                                                                            disabled={sectionIndex === 0}
                                                                            className="p-1 hover:bg-white/20 rounded disabled:opacity-30 transition-colors"
                                                                            title="Mover seção para cima"
                                                                        >
                                                                            <ChevronRight className="w-4 h-4 -rotate-90" />
                                                                        </button>
                                                                        <button
                                                                            onClick={(e: React.MouseEvent) => { e.stopPropagation(); moveSection(chapterIndex, sectionIndex, 'down'); }}
                                                                            disabled={sectionIndex === chapter.sections.length - 1}
                                                                            className="p-1 hover:bg-white/20 rounded disabled:opacity-30 transition-colors"
                                                                            title="Mover seção para baixo"
                                                                        >
                                                                            <ChevronRight className="w-4 h-4 rotate-90" />
                                                                        </button>
                                                                    </div>

                                                                    {/* Chapter select */}
                                                                    <select
                                                                        value={chapter.id}
                                                                        onChange={(e: React.ChangeEvent<HTMLSelectElement>) => moveSectionToChapter(chapterIndex, sectionIndex, e.target.value)}
                                                                        className="bg-slate-800 text-xs text-white border border-white/10 rounded px-2 py-1 outline-none focus:ring-1 focus:ring-blue-500"
                                                                    >
                                                                        {tempChapters.map((ch: Chapter) => (
                                                                            <option key={ch.id} value={ch.id}>
                                                                                Mover p/ Cap {ch.order}
                                                                            </option>
                                                                        ))}
                                                                    </select>
                                                                </div>
                                                            ) : (
                                                                <>
                                                                    <span className={`px-2 py-1 rounded text-xs border ${getStatusColor(section.status)}`}>
                                                                        {section.status}
                                                                    </span>
                                                                    {(section.status === 'PENDENTE' || section.status === 'ERRO') && (
                                                                        <button
                                                                            onClick={(e: React.MouseEvent) => {
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
                                                                </>
                                                            )}
                                                        </div>
                                                    </div>

                                                    {/* Progress Bar (Hide in edit mode for cleaner UI) */}
                                                    {!isEditMode && (
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
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Right Panel - Interactive Sidebar */}
                        {!isEditMode && selectedItem && (
                            <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6 max-h-[calc(100vh-200px)] overflow-y-auto">
                                <div className="flex items-center justify-between mb-6">
                                    <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                                        {selectedItem.type === 'chapter'
                                            ? ((selectedItem.data as Chapter).is_bibliography ? <><BookMarked className="w-5 h-5 text-amber-400" /> Referências Bibliográficas</> : 'Capítulo')
                                            : (() => {
                                                // Check if parent chapter is bibliography
                                                const parentChapter = chapters.find(ch => ch.id === (selectedItem.data as Section).chapter_id);
                                                return parentChapter?.is_bibliography ? <><BookMarked className="w-5 h-5 text-amber-400" /> Editar Bibliografia</> : 'Seção';
                                            })()
                                        }
                                    </h2>
                                    <button
                                        onClick={() => setSelectedItem(null)}
                                        className="p-1 hover:bg-white/10 rounded transition-all"
                                    >
                                        <X className="w-5 h-5 text-slate-400" />
                                    </button>
                                </div>

                                <div className="space-y-6">
                                    {/* Title Field */}
                                    <div>
                                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                                            Título
                                        </label>
                                        <input
                                            type="text"
                                            value={editTitle}
                                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditTitle(e.target.value)}
                                            className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                                        />
                                    </div>

                                    {/* Save Reminder — hidden for bibliography sections */}
                                    {(() => {
                                        const parentChapter = selectedItem.type === 'section'
                                            ? chapters.find(ch => ch.id === (selectedItem.data as Section).chapter_id)
                                            : null;
                                        if (parentChapter?.is_bibliography) return null;
                                        return (
                                            <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 flex items-start gap-3">
                                                <AlertCircle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                                                <p className="text-xs text-amber-200/80 leading-relaxed font-medium">
                                                    Lembre-se de clicar em <span className="text-white font-bold underline decoration-amber-500/30 underline-offset-2">Salvar Alterações</span> ao final da página para atualizar o conteúdo.
                                                </p>
                                            </div>
                                        );
                                    })()}

                                    {selectedItem.type === 'section' && (
                                        <>
                                            {/* Content Area */}
                                            <div>
                                                <div className="flex items-center justify-between mb-3">
                                                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider">
                                                        Conteúdo
                                                    </label>
                                                    <div className="flex bg-black/30 p-1 rounded-lg">
                                                        <button
                                                            onClick={() => setIsVisualMode(true)}
                                                            className={`px-3 py-1 text-[10px] font-bold rounded-md uppercase tracking-wider transition-colors ${isVisualMode ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'}`}
                                                        >
                                                            Visual
                                                        </button>
                                                        <button
                                                            onClick={() => setIsVisualMode(false)}
                                                            className={`px-3 py-1 text-[10px] font-bold rounded-md uppercase tracking-wider transition-colors ${!isVisualMode ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'}`}
                                                        >
                                                            EDITOR
                                                        </button>
                                                    </div>
                                                </div>

                                                {!isVisualMode && (
                                                    <div className="flex items-center gap-2 mb-4">
                                                        <button
                                                            onClick={() => {
                                                                if (textareaRef.current) {
                                                                    setLastCursorPosition(textareaRef.current.selectionStart);
                                                                }
                                                                setIsUploadModalOpen(true);
                                                            }}
                                                            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 text-xs font-bold rounded-xl border border-indigo-500/20 transition-all active:scale-[0.98] group"
                                                        >
                                                            <ImageIcon className="w-4 h-4 group-hover:scale-110 transition-transform" />
                                                            INSERIR IMAGEM NO CURSOR
                                                        </button>
                                                    </div>
                                                )}

                                                {isVisualMode ? (
                                                    <div className="bg-white border border-slate-200 rounded-xl p-6 min-h-[400px] overflow-hidden shadow-inner">
                                                        {renderContent(editContent, (selectedItem.data as Section).assets || [])}
                                                    </div>
                                                ) : (
                                                    <textarea
                                                        ref={textareaRef}
                                                        value={editContent}
                                                        onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setEditContent(e.target.value)}
                                                        rows={20}
                                                        className="w-full px-4 py-4 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-[13px] leading-relaxed custom-scrollbar shadow-inner"
                                                        placeholder="Conteúdo em Markdown..."
                                                    />
                                                )}
                                            </div>
                                        </>
                                    )}

                                    {/* Action Buttons */}
                                    <div className="pt-4 space-y-3">
                                        {(() => {
                                            // Check if the selected section belongs to a bibliography chapter
                                            const parentChapter = selectedItem.type === 'section'
                                                ? chapters.find(ch => ch.id === (selectedItem.data as Section).chapter_id)
                                                : null;
                                            const isBibSection = parentChapter?.is_bibliography === true;

                                            if (isBibSection) {
                                                return (
                                                    <>
                                                        {/* Bibliography warning */}
                                                        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 flex items-start gap-3">
                                                            <AlertCircle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                                                            <p className="text-xs text-amber-200/80 leading-relaxed font-medium">
                                                                Alterações na numeração serão aplicadas em <span className="text-white font-bold">todas as seções do livro</span>.
                                                            </p>
                                                        </div>
                                                        <button
                                                            onClick={handleSaveBibliography}
                                                            disabled={savingBibliography}
                                                            className="w-full py-3.5 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700 disabled:opacity-50 text-white rounded-xl shadow-lg shadow-amber-500/20 transition-all flex items-center justify-center gap-2 font-bold text-sm tracking-wide active:scale-[0.98]"
                                                        >
                                                            {savingBibliography ? (
                                                                <><Loader2 className="w-5 h-5 animate-spin" />SALVANDO BIBLIOGRAFIA...</>
                                                            ) : (
                                                                <><BookMarked className="w-5 h-5" />SALVAR BIBLIOGRAFIA</>
                                                            )}
                                                        </button>
                                                    </>
                                                );
                                            }

                                            return (
                                                <button
                                                    onClick={handleSave}
                                                    disabled={saving}
                                                    className="w-full py-3.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 text-white rounded-xl shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center gap-2 font-bold text-sm tracking-wide active:scale-[0.98]"
                                                >
                                                    {saving ? (
                                                        <><Loader2 className="w-5 h-5 animate-spin" />SALVANDO...</>
                                                    ) : (
                                                        <><Save className="w-5 h-5" />SALVAR ALTERAÇÕES</>
                                                    )}
                                                </button>
                                            );
                                        })()
                                        }
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Manual Image Upload Modal */}
            {isUploadModalOpen && (
                <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
                    <div className="bg-slate-900 rounded-3xl shadow-2xl w-full max-w-md overflow-hidden border border-white/10 animate-in fade-in zoom-in duration-200">
                        <div className="px-8 py-6 border-b border-white/10 flex items-center justify-between bg-white/5">
                            <h3 className="text-xl font-bold text-white flex items-center gap-3">
                                <div className="p-2 bg-indigo-500/20 rounded-lg">
                                    <ImageIcon className="w-5 h-5 text-indigo-400" />
                                </div>
                                Inserir Imagem
                            </h3>
                            <button
                                onClick={() => setIsUploadModalOpen(false)}
                                className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-white/10 transition-all"
                            >
                                <X className="w-6 h-6" />
                            </button>
                        </div>

                        <div className="p-8 space-y-6">
                            <div>
                                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3">
                                    Arquivo de Imagem local
                                </label>
                                <div className={`relative border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center transition-all ${uploadFile ? 'border-indigo-500/50 bg-indigo-500/5' : 'border-white/10 hover:border-indigo-500/30 bg-white/5 hover:bg-white/10'}`}>
                                    <input
                                        type="file"
                                        accept="image/*"
                                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUploadFile(e.target.files?.[0] || null)}
                                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                    />
                                    {uploadFile ? (
                                        <>
                                            <div className="p-3 bg-indigo-500/20 rounded-2xl mb-4">
                                                <CheckCircle2 className="w-8 h-8 text-indigo-400" />
                                            </div>
                                            <span className="text-sm font-semibold text-white truncate max-w-full px-4">{uploadFile.name}</span>
                                            <span className="text-xs text-indigo-400/70 mt-2 font-medium">Clique para selecionar outro</span>
                                        </>
                                    ) : (
                                        <>
                                            <div className="p-3 bg-white/5 rounded-2xl mb-4">
                                                <Upload className="w-8 h-8 text-slate-500" />
                                            </div>
                                            <span className="text-sm text-slate-300 font-semibold mb-1">Selecionar Imagem</span>
                                            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">PNG, JPG, WebP</span>
                                        </>
                                    )}
                                </div>
                            </div>

                            <div>
                                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3">
                                    Legenda explicativa
                                </label>
                                <textarea
                                    value={uploadCaption}
                                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setUploadCaption(e.target.value)}
                                    placeholder="Ex: Diagrama mostrando o ciclo da água..."
                                    className="w-full px-4 py-3 text-sm bg-white/5 border border-white/10 rounded-2xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 min-h-[100px] resize-none"
                                />
                            </div>
                        </div>

                        <div className="px-8 py-6 bg-white/5 border-t border-white/10 flex gap-4">
                            <button
                                onClick={() => setIsUploadModalOpen(false)}
                                className="flex-1 px-6 py-3.5 text-sm font-bold text-slate-400 hover:text-white hover:bg-white/5 rounded-2xl transition-all uppercase tracking-wider"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleUploadAsset}
                                disabled={!uploadFile || !uploadCaption || isUploading}
                                className="flex-1 px-6 py-3.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:opacity-30 text-white text-sm font-bold rounded-2xl shadow-xl shadow-indigo-500/20 transition-all active:scale-[0.98] flex items-center justify-center gap-3 uppercase tracking-wider"
                            >
                                {isUploading ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Enviando
                                    </>
                                ) : (
                                    <>
                                        <Plus className="w-5 h-5" />
                                        Adicionar
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
            {/* Modal de Adição de Recurso */}
            {/* Modal de Edição de Recurso (Imagem/Legenda) */}
            {isEditAssetModalOpen && editingAsset && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                    <div
                        className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"
                        onClick={() => !isSavingAsset && setIsEditAssetModalOpen(false)}
                    />
                    <div className="relative w-full max-w-2xl bg-slate-900 border border-white/10 rounded-[32px] shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-300">
                        <div className="px-8 py-6 bg-white/5 border-b border-white/10 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-indigo-500/20 rounded-2xl group">
                                    <Settings className="w-6 h-6 text-indigo-400 group-hover:rotate-90 transition-all duration-500" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-white tracking-tight">Editar Recurso</h3>
                                    <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">{editingAsset.placeholder}</p>
                                </div>
                            </div>
                            <button
                                onClick={() => setIsEditAssetModalOpen(false)}
                                className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-white/10 transition-all"
                            >
                                <X className="w-6 h-6" />
                            </button>
                        </div>

                        <div className="p-8 space-y-8 max-h-[70vh] overflow-y-auto custom-scrollbar">
                            {/* Visualização Atual */}
                            <div className="grid grid-cols-2 gap-8">
                                <div>
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-4">
                                        Imagem Atual
                                    </label>
                                    <div className="aspect-video bg-slate-800 rounded-2xl overflow-hidden border border-white/5 shadow-inner flex items-center justify-center group/preview relative">
                                        <img
                                            src={`http://localhost:8000/media/${editingAsset.storage_path.replace(/\\/g, '/').split('media/')[1] || editingAsset.storage_path.replace(/\\/g, '/')}`}
                                            className="w-full h-full object-contain"
                                            alt="Preview"
                                        />
                                        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/preview:opacity-100 transition-opacity flex items-center justify-center pointer-events-none">
                                            <ImageIcon className="w-6 h-6 text-white/50" />
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-4">
                                        Substituir por nova
                                    </label>
                                    <div className={`relative h-full aspect-video border-2 border-dashed rounded-2xl flex flex-col items-center justify-center transition-all ${editAssetFile ? 'border-indigo-500/50 bg-indigo-500/10' : 'border-white/10 hover:border-indigo-500/30 bg-white/5 hover:bg-white/10'}`}>
                                        <input
                                            type="file"
                                            accept="image/*"
                                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditAssetFile(e.target.files?.[0] || null)}
                                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                        />
                                        {editAssetFile ? (
                                            <div className="flex flex-col items-center p-4">
                                                <div className="p-2 bg-indigo-500/20 rounded-lg mb-2">
                                                    <CheckCircle2 className="w-5 h-5 text-indigo-400" />
                                                </div>
                                                <span className="text-[10px] font-semibold text-white truncate max-w-[150px]">{editAssetFile.name}</span>
                                            </div>
                                        ) : (
                                            <div className="flex flex-col items-center pointer-events-none">
                                                <Upload className="w-6 h-6 text-slate-500 mb-2" />
                                                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Novo Arquivo</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Campo de Legenda */}
                            <div className="space-y-3">
                                <label className="flex items-center justify-between">
                                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">Legenda da Imagem</span>
                                    <span className="text-[10px] font-medium text-slate-600 italic">Opcional</span>
                                </label>
                                <div className="relative group/input">
                                    <div className="absolute top-4 left-4 text-indigo-400/50 group-focus-within/input:text-indigo-400 transition-colors">
                                        <FileText className="w-5 h-5" />
                                    </div>
                                    <textarea
                                        value={editAssetCaption}
                                        onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setEditAssetCaption(e.target.value)}
                                        placeholder="Descreva o que esta imagem representa..."
                                        className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all min-h-[120px] resize-none text-sm leading-relaxed"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="px-8 py-6 bg-white/5 border-t border-white/10 flex gap-4">
                            <button
                                onClick={() => setIsEditAssetModalOpen(false)}
                                className="flex-1 px-6 py-3.5 text-sm font-bold text-slate-400 hover:text-white hover:bg-white/5 rounded-2xl transition-all uppercase tracking-wider"
                                disabled={isSavingAsset}
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={async () => {
                                    if (!editingAsset) return;
                                    setIsSavingAsset(true);
                                    try {
                                        await handleUpdateAsset(editingAsset.id, {
                                            caption: editAssetCaption,
                                            file: editAssetFile || undefined
                                        });
                                        setIsEditAssetModalOpen(false);
                                    } catch (err) {
                                        console.error(err);
                                    } finally {
                                        setIsSavingAsset(false);
                                    }
                                }}
                                disabled={isSavingAsset}
                                className="flex-2 px-10 py-3.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:opacity-30 text-white text-sm font-bold rounded-2xl shadow-xl shadow-indigo-500/20 transition-all active:scale-[0.98] flex items-center justify-center gap-3 uppercase tracking-wider"
                            >
                                {isSavingAsset ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Salvando
                                    </>
                                ) : (
                                    <>
                                        <Save className="w-5 h-5" />
                                        Salvar Alterações
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

export default BookStructure;
