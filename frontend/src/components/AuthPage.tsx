import React, { useState } from 'react';
import { Mail, Lock, User, BookOpen, ArrowRight, Eye, EyeOff, Loader2 } from 'lucide-react';

// ============================================
// AuthPage Component - Lectria Authentication
// ============================================

type AuthMode = 'login' | 'register';

interface FormErrors {
    fullName?: string;
    email?: string;
    password?: string;
}

const AuthPage: React.FC = () => {
    const [mode, setMode] = useState<AuthMode>('login');
    const [isLoading, setIsLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    // Form fields
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    // Validation errors
    const [errors, setErrors] = useState<FormErrors>({});

    // Email validation regex
    const isValidEmail = (email: string): boolean => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    };

    // Form validation
    const validateForm = (): boolean => {
        const newErrors: FormErrors = {};

        if (mode === 'register' && fullName.trim().length < 3) {
            newErrors.fullName = 'Nome deve ter pelo menos 3 caracteres';
        }

        if (!isValidEmail(email)) {
            newErrors.email = 'E-mail inválido';
        }

        if (password.length < 6) {
            newErrors.password = 'Senha deve ter pelo menos 6 caracteres';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    // Handle form submission
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateForm()) return;

        setIsLoading(true);

        // ================================================
        // API INTEGRATION - Uncomment to connect to backend
        // ================================================


        try {
            const endpoint = mode === 'register'
                ? 'http://localhost:8000/auth/register'
                : 'http://localhost:8000/auth/login';

            const payload = mode === 'register'
                ? { full_name: fullName, email, password }
                : { email, password };

            // Using fetch
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Erro na autenticação');
            }

            const data = await response.json();

            // Store token in localStorage
            localStorage.setItem('access_token', data.access_token);

            // Redirect to dashboard
            window.location.href = '/dashboard';

        } catch (error) {
            console.error('Auth error:', error);
            setErrors({
                email: error instanceof Error ? error.message : 'Erro ao processar solicitação'
            });
        } finally {
            setIsLoading(false);
        }


        // ================================================
        // SIMULATED SUCCESS - Remove when API is connected
        // ================================================
        /*
        setTimeout(() => {
            setIsLoading(false);
            console.log('Auth successful (simulated):', { mode, email, fullName });
            // Simulate redirect
            // window.location.href = '/dashboard';
            alert(`${mode === 'login' ? 'Login' : 'Cadastro'} realizado com sucesso! Redirecionando para /dashboard...`);
        }, 1500);
        */
    };

    // Switch between login and register modes
    const switchMode = (newMode: AuthMode) => {
        setMode(newMode);
        setErrors({});
        setFullName('');
        setEmail('');
        setPassword('');
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
            {/* Background decorations */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
                <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse delay-1000"></div>
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10"></div>
            </div>

            {/* Auth Card */}
            <div className="relative w-full max-w-md">
                {/* Logo and Title */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-2xl shadow-lg shadow-purple-500/25 mb-4">
                        <BookOpen className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-3xl font-bold text-white mb-2">Lectria</h1>
                    <p className="text-slate-400">Transformando vídeos em conhecimento</p>
                </div>

                {/* Card Container */}
                <div className="bg-white/10 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 overflow-hidden">
                    {/* Tab Switcher */}
                    <div className="flex bg-white/5">
                        <button
                            onClick={() => switchMode('login')}
                            className={`flex-1 py-4 text-sm font-semibold transition-all duration-300 ${mode === 'login'
                                ? 'text-white bg-gradient-to-r from-purple-500/20 to-indigo-500/20 border-b-2 border-purple-400'
                                : 'text-slate-400 hover:text-slate-300'
                                }`}
                        >
                            Entrar
                        </button>
                        <button
                            onClick={() => switchMode('register')}
                            className={`flex-1 py-4 text-sm font-semibold transition-all duration-300 ${mode === 'register'
                                ? 'text-white bg-gradient-to-r from-purple-500/20 to-indigo-500/20 border-b-2 border-purple-400'
                                : 'text-slate-400 hover:text-slate-300'
                                }`}
                        >
                            Criar Conta
                        </button>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="p-8 space-y-5">
                        {/* Full Name - Only for Register */}
                        {mode === 'register' && (
                            <div className="space-y-2 animate-fadeIn">
                                <label className="text-sm font-medium text-slate-300">Nome Completo</label>
                                <div className="relative">
                                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                    <input
                                        type="text"
                                        value={fullName}
                                        onChange={(e) => setFullName(e.target.value)}
                                        placeholder="Seu nome completo"
                                        className={`w-full pl-12 pr-4 py-3.5 bg-white/5 border rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-400 transition-all ${errors.fullName ? 'border-red-400' : 'border-white/10'
                                            }`}
                                    />
                                </div>
                                {errors.fullName && (
                                    <p className="text-red-400 text-xs mt-1">{errors.fullName}</p>
                                )}
                            </div>
                        )}

                        {/* Email */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-300">E-mail</label>
                            <div className="relative">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="seu@email.com"
                                    className={`w-full pl-12 pr-4 py-3.5 bg-white/5 border rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-400 transition-all ${errors.email ? 'border-red-400' : 'border-white/10'
                                        }`}
                                />
                            </div>
                            {errors.email && (
                                <p className="text-red-400 text-xs mt-1">{errors.email}</p>
                            )}
                        </div>

                        {/* Password */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-300">Senha</label>
                            <div className="relative">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    className={`w-full pl-12 pr-12 py-3.5 bg-white/5 border rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-400 transition-all ${errors.password ? 'border-red-400' : 'border-white/10'
                                        }`}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300 transition-colors"
                                >
                                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                </button>
                            </div>
                            {errors.password && (
                                <p className="text-red-400 text-xs mt-1">{errors.password}</p>
                            )}
                        </div>

                        {/* Forgot Password - Login only */}
                        {mode === 'login' && (
                            <div className="text-right">
                                <a href="#" className="text-sm text-purple-400 hover:text-purple-300 transition-colors">
                                    Esqueceu a senha?
                                </a>
                            </div>
                        )}

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full py-4 bg-gradient-to-r from-purple-500 to-indigo-600 text-white font-semibold rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 disabled:opacity-70 disabled:cursor-not-allowed disabled:hover:scale-100"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Processando...
                                </>
                            ) : (
                                <>
                                    {mode === 'login' ? 'Entrar' : 'Criar Conta'}
                                    <ArrowRight className="w-5 h-5" />
                                </>
                            )}
                        </button>


                    </form>
                </div>

                {/* Footer */}
                <p className="text-center text-slate-500 text-sm mt-6">
                    Ao continuar, você concorda com nossos{' '}
                    <a href="#" className="text-purple-400 hover:text-purple-300 transition-colors">
                        Termos de Uso
                    </a>{' '}
                    e{' '}
                    <a href="#" className="text-purple-400 hover:text-purple-300 transition-colors">
                        Política de Privacidade
                    </a>
                </p>
            </div>
        </div>
    );
};

export default AuthPage;
