import { useState } from 'react';
// import { useNavigate, Navigate } from 'react-router-dom';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Anchor } from 'lucide-react';

export function LoginView() {
  // const navigate = useNavigate();
  const { login, isAuthenticated, isLoading } = useAuth();
  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState<string>('');

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await login({ email, password });
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail;
      setError(
        typeof errorMessage === 'string'
          ? errorMessage
          : 'Credenciais inválidas. Tente novamente.'
      );
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-primary rounded-xl flex items-center justify-center mb-4">
            <Anchor className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">SaaS Impacto Portuário</h1>
          <p className="text-gray-500 mt-1">Sistema de Análise do Setor Portuário</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              E-mail
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              placeholder="seu@email.com"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Senha
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full btn btn-primary py-3 text-lg disabled:opacity-50"
          >
            {isLoading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-500">
          <p>Credenciais de teste:</p>
          <p className="font-mono text-xs mt-1">admin@example.com / admin123</p>
        </div>
      </div>
    </div>
  );
}
