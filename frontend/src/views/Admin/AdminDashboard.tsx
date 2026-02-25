import { useEffect, useState } from 'react';
import { adminService } from '../../api/admin';
import type { TenantUsageResponse } from '../../types/api';

export function AdminDashboard() {
  const [usage, setUsage] = useState<TenantUsageResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        const payload = await adminService.getDashboardUsage();
        setUsage(payload);
      } catch (err: unknown) {
        const errorResponse = err as { response?: { data?: { detail?: unknown } } };
        const detail = errorResponse?.response?.data?.detail;
        setError(typeof detail === 'string' ? detail : 'Erro ao carregar dashboard administrativo.');
      } finally {
        setIsLoading(false);
      }
    };

    load();
  }, []);

  const formatBytes = (value: number): string => {
    if (!Number.isFinite(value)) {
      return '0 B';
    }
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = value;
    let unit = 0;
    while (size >= 1024 && unit < units.length - 1) {
      size /= 1024;
      unit += 1;
    }
    return `${size.toFixed(1)} ${units[unit]}`;
  };

  if (isLoading) {
    return <div className="card">Carregando uso do tenant...</div>;
  }

  if (error || !usage) {
    return (
      <div className="card">
        <p className="text-red-700">{error || 'Sem dados disponíveis no momento.'}</p>
      </div>
    );
  }

  const rateLimitPercent = usage.taxa_rate_limit ? `${Math.min(usage.taxa_rate_limit * 100, 100).toFixed(1)}%` : 'N/A';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard Administrativo</h1>
        <p className="text-sm text-gray-500 mt-1">Uso e atividade do tenant nos últimos 30 dias.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <div className="card">
          <p className="text-sm text-gray-500">Total de análises</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{usage.total_analises}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Análises concluídas</p>
          <p className="text-3xl font-bold text-green-600 mt-1">{usage.analises_sucesso}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Análises com falha</p>
          <p className="text-3xl font-bold text-red-600 mt-1">{usage.analises_falha}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Usuários ativos (7d)</p>
          <p className="text-3xl font-bold text-indigo-600 mt-1">{usage.usuarios_ativos_7d}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Usuários ativos (30d)</p>
          <p className="text-3xl font-bold text-indigo-600 mt-1">{usage.usuarios_ativos_30d}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <h2 className="font-semibold text-gray-900 mb-3">Indicadores mais consultados</h2>
          {usage.top_indicadores.length === 0 ? (
            <p className="text-gray-500 text-sm">Sem consultas recentes para exibir.</p>
          ) : (
            <ul className="divide-y">
              {usage.top_indicadores.map((item) => (
                <li key={item.codigo} className="py-2 flex justify-between text-sm">
                  <span className="font-medium text-gray-800">{item.codigo}</span>
                  <span className="text-gray-500">{item.acessos} acessos</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <h2 className="font-semibold text-gray-900 mb-3">Consumo BigQuery</h2>
          <p className="text-sm text-gray-500">Últimos 30 dias</p>
          <p className="text-3xl font-bold text-blue-700 mt-2">{formatBytes(usage.bq_bytes_last_30d)}</p>
          <p className="mt-4 text-xs text-gray-500">Utilização de rate limit (estimada): {rateLimitPercent}</p>
        </div>
      </div>
    </div>
  );
}
