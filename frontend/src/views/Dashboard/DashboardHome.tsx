import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FilterBar } from '../../components/filters/FilterBar';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../components/common/ErrorAlert';
import { indicatorsService } from '../../api/indicators';
import type { ModulesOverview } from '../../types/api';
import {
  Anchor,
  Package,
  Users,
  Globe,
  TrendingUp,
  Building,
  LineChart,
  ArrowRight,
} from 'lucide-react';

const MODULE_INFO = [
  { id: 1, name: 'Operações de Navios', icon: Anchor, color: 'module1', path: '/dashboard/module1', indicators: 12 },
  { id: 2, name: 'Operações de Carga', icon: Package, color: 'module2', path: '/dashboard/module2', indicators: 13 },
  { id: 3, name: 'Recursos Humanos', icon: Users, color: 'module3', path: '/dashboard/module3', indicators: 12 },
  { id: 4, name: 'Comércio Exterior', icon: Globe, color: 'module4', path: '/dashboard/module4', indicators: 10 },
  { id: 5, name: 'Impacto Econômico', icon: TrendingUp, color: 'module5', path: '/dashboard/module5', indicators: 21 },
  { id: 6, name: 'Finanças Públicas', icon: Building, color: 'module6', path: '/dashboard/module6', indicators: 6 },
  { id: 7, name: 'Índices Sintéticos', icon: LineChart, color: 'module7', path: '/dashboard/module7', indicators: 7 },
];

export function DashboardHome() {
  const [overview, setOverview] = useState<ModulesOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOverview = async () => {
      try {
        setIsLoading(true);
        const data = await indicatorsService.getModulesOverview();
        setOverview(data);
      } catch (err: unknown) {
        const errorResponse = err as { response?: { data?: { detail?: unknown } } };
        const detail = errorResponse?.response?.data?.detail;
        console.error('Erro ao carregar overview:', err);
        setError(typeof detail === 'string' ? detail : 'Erro ao carregar overview');
      } finally {
        setIsLoading(false);
      }
    };

    fetchOverview();
  }, []);

  if (isLoading) {
    return <LoadingSpinner />;
  }

  // Default values when API fails
  const totalIndicadores = overview?.total_indicadores ?? 0;
  const unctadCompliant = overview?.unctad_compliant ?? 0;
  const totalModulos = overview?.total_modulos ?? 7;
  const sistemaNome = overview?.sistema || 'SaaS Impacto Portuário';

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">
            {sistemaNome} - Visão geral dos {totalIndicadores} indicadores
          </p>
        </div>
      </div>

      <FilterBar />

      {/* Error alert */}
      {error && <ErrorAlert message={error} className="mb-6" />}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="card">
          <p className="text-sm text-gray-500">Total Indicadores</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{totalIndicadores}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Padrão UNCTAD</p>
          <p className="text-3xl font-bold text-blue-600 mt-1">{unctadCompliant}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Total Módulos</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{totalModulos}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Status</p>
          <p className="text-3xl font-bold text-green-600 mt-1">Ativo</p>
        </div>
      </div>

      {/* Module Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {MODULE_INFO.map((module) => {
          const Icon = module.icon;
          const moduleData = overview?.modulos.find((m) => m.modulo === module.id);

          // Map colors to explicit classes to avoid Tailwind purging issues
          const colorClasses: Record<string, { bg: string, text: string }> = {
            module1: { bg: 'bg-module1/10', text: 'text-module1' },
            module2: { bg: 'bg-module2/10', text: 'text-module2' },
            module3: { bg: 'bg-module3/10', text: 'text-module3' },
            module4: { bg: 'bg-module4/10', text: 'text-module4' },
            module5: { bg: 'bg-module5/10', text: 'text-module5' },
            module6: { bg: 'bg-module6/10', text: 'text-module6' },
            module7: { bg: 'bg-module7/10', text: 'text-module7' },
          };

          const styles = colorClasses[module.color] || { bg: 'bg-gray-100', text: 'text-gray-600' };

          return (
            <Link
              key={module.id}
              to={module.path}
              className="card hover:shadow-md transition-shadow group"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-lg ${styles.bg}`}>
                    <Icon className={`w-6 h-6 ${styles.text}`} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 group-hover:text-primary transition-colors">
                      Módulo {module.id}
                    </h3>
                    <p className="text-sm text-gray-500">{module.name}</p>
                  </div>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-primary transition-colors" />
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Indicadores</span>
                  <span className="font-medium text-gray-900">{moduleData?.total_indicadores ?? module.indicators}</span>
                </div>
                <div className="flex items-center justify-between text-sm mt-1">
                  <span className="text-gray-500">UNCTAD</span>
                  <span className="font-medium text-blue-600">{moduleData?.unctad_compliant ?? 0}</span>
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
