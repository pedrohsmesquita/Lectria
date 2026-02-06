import React from 'react';
import { AlertCircle, Upload, X } from 'lucide-react';

interface ResumePendingUploadsModalProps {
    pendingCount: number;
    onResume: () => void;
    onDiscard: () => void;
}

const ResumePendingUploadsModal: React.FC<ResumePendingUploadsModalProps> = ({
    pendingCount,
    onResume,
    onDiscard
}) => {
    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-900 rounded-2xl border border-white/20 max-w-md w-full shadow-2xl">
                <div className="p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="w-12 h-12 bg-yellow-500/20 rounded-full flex items-center justify-center">
                            <AlertCircle className="w-6 h-6 text-yellow-400" />
                        </div>
                        <h2 className="text-xl font-semibold text-white">Uploads Pendentes</h2>
                    </div>

                    <p className="text-slate-300 mb-6">
                        Você tem <span className="font-semibold text-white">{pendingCount}</span> {pendingCount === 1 ? 'vídeo pendente' : 'vídeos pendentes'} de upload. Deseja continuar de onde parou?
                    </p>

                    <div className="flex gap-3">
                        <button
                            onClick={onDiscard}
                            className="flex-1 px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg transition-all flex items-center justify-center gap-2"
                        >
                            <X className="w-5 h-5" />
                            Descartar
                        </button>
                        <button
                            onClick={onResume}
                            className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg transition-all flex items-center justify-center gap-2"
                        >
                            <Upload className="w-5 h-5" />
                            Continuar
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ResumePendingUploadsModal;
