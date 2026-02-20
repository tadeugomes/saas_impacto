import { useState } from 'react';
import { Navigate, Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

type RegisterStep = 0 | 1 | 2;

const STEPS: RegisterStep[] = [0, 1, 2];

interface RegisterFormState {
  empresa: string;
  cnpj: string;
  plano: 'basic' | 'pro' | 'enterprise';
  nome_admin: string;
  email_admin: string;
  senha_admin: string;
  confirmar_senha: string;
}

export function RegisterView() {
  const { isAuthenticated, registerCompany, isLoading } = useAuth();
  const [step, setStep] = useState<RegisterStep>(0);
  const [formState, setFormState] = useState<RegisterFormState>({
    empresa: '',
    cnpj: '',
    plano: 'basic',
    nome_admin: '',
    email_admin: '',
    senha_admin: '',
    confirmar_senha: '',
  });
  const [error, setError] = useState('');

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const updateField = (field: keyof RegisterFormState, value: string) => {
    setFormState((previous) => ({ ...previous, [field]: value }));
  };

  const validateStep = (): string | null => {
    if (step === 0) {
      if (!formState.empresa.trim() || formState.empresa.trim().length < 2) {
        return 'Informe o nome da empresa (mínimo 2 caracteres).';
      }
      if (!formState.plano) {
        return 'Selecione um plano.';
      }
      return null;
    }

    if (step === 1) {
      if (!formState.nome_admin.trim()) {
        return 'Informe o nome do administrador.';
      }
      if (!formState.email_admin.trim() || !formState.email_admin.includes('@')) {
        return 'Informe um e-mail válido.';
      }
      if (formState.senha_admin.length < 8) {
        return 'A senha deve ter ao menos 8 caracteres.';
      }
      if (formState.senha_admin !== formState.confirmar_senha) {
        return 'As senhas não coincidem.';
      }
      return null;
    }

    return null;
  };

  const handleNext = async () => {
    const validationError = validateStep();
    if (validationError) {
      setError(validationError);
      return;
    }

    setError('');
    const currentIndex = STEPS.indexOf(step);
    const nextStep = STEPS[currentIndex + 1] as RegisterStep | undefined;
    if (nextStep !== undefined) {
      setStep(nextStep);
      return;
    }

    try {
      const { confirmar_senha, ...payload } = formState;
      await registerCompany(payload);
    } catch (err: unknown) {
      const errorResponse = err as { response?: { data?: { detail?: unknown } } };
      const detail = errorResponse?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Não foi possível concluir o cadastro.');
      return;
    }
  };

  const handleBack = () => {
    const currentIndex = STEPS.indexOf(step);
    const previousStep = STEPS[currentIndex - 1];
    if (previousStep !== undefined) {
      setError('');
      setStep(previousStep as RegisterStep);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-8">
        <h1 className="text-2xl font-bold text-gray-900">Cadastro inicial</h1>
        <p className="text-gray-500 mt-1 mb-6">Crie sua conta e comece a usar o SaaS Impacto Portuário.</p>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm mb-5">
            {error}
          </div>
        )}

        {step === 0 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="empresa">
                Nome da empresa
              </label>
              <input
                id="empresa"
                value={formState.empresa}
                onChange={(event) => updateField('empresa', event.target.value)}
                className="input"
                placeholder="Porto Exemplo S.A."
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="cnpj">
                CNPJ (opcional)
              </label>
              <input
                id="cnpj"
                value={formState.cnpj}
                onChange={(event) => updateField('cnpj', event.target.value)}
                className="input"
                placeholder="12.345.678/0001-90"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="plano">
                Plano
              </label>
              <select
                id="plano"
                value={formState.plano}
                onChange={(event) => updateField('plano', event.target.value)}
                className="input"
              >
                <option value="basic">Basic</option>
                <option value="pro">Pro</option>
                <option value="enterprise">Enterprise</option>
              </select>
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="nome_admin">
                Nome do administrador
              </label>
              <input
                id="nome_admin"
                value={formState.nome_admin}
                onChange={(event) => updateField('nome_admin', event.target.value)}
                className="input"
                placeholder="Seu nome"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="email_admin">
                E-mail do administrador
              </label>
              <input
                id="email_admin"
                type="email"
                value={formState.email_admin}
                onChange={(event) => updateField('email_admin', event.target.value)}
                className="input"
                placeholder="admin@empresa.com"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="senha_admin">
                Senha
              </label>
              <input
                id="senha_admin"
                type="password"
                value={formState.senha_admin}
                onChange={(event) => updateField('senha_admin', event.target.value)}
                className="input"
                placeholder="••••••••"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="confirmar_senha">
                Confirmar senha
              </label>
              <input
                id="confirmar_senha"
                type="password"
                value={formState.confirmar_senha}
                onChange={(event) => updateField('confirmar_senha', event.target.value)}
                className="input"
                placeholder="••••••••"
                required
              />
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-3 text-sm">
            <p className="text-gray-700">
              <span className="font-semibold">Empresa:</span> {formState.empresa}
            </p>
            <p className="text-gray-700">
              <span className="font-semibold">CNPJ:</span> {formState.cnpj || 'não informado'}
            </p>
            <p className="text-gray-700">
              <span className="font-semibold">Plano:</span> {formState.plano}
            </p>
            <p className="text-gray-700">
              <span className="font-semibold">Administrador:</span> {formState.nome_admin} ({formState.email_admin})
            </p>
          </div>
        )}

        <div className="flex gap-3 justify-end mt-6">
          <button
            type="button"
            onClick={handleBack}
            disabled={step === 0 || isLoading}
            className="px-4 py-2 rounded-lg border border-gray-300 disabled:opacity-50"
          >
            Voltar
          </button>
          <button
            type="button"
            onClick={handleNext}
            disabled={isLoading}
            className="btn btn-primary disabled:opacity-50"
          >
            {isLoading ? 'Processando...' : step === 2 ? 'Concluir cadastro' : 'Próximo'}
          </button>
        </div>

        <p className="mt-6 text-center text-sm text-gray-500">
          Já tem conta? <Link to="/login" className="text-primary font-medium">Entrar</Link>
        </p>
      </div>
    </div>
  );
}
