import { useEffect, useState } from 'react';
import { FilterBar } from '../../../components/filters/FilterBar';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { useFilterStore } from '../../../store/filterStore';
import { indicatorsService } from '../../../api/indicators';
import type { IndicatorResponse } from '../../../types/api';
import {
  TrendingUp, BarChart3, PieChart, Target, DollarSign,
  ArrowUp, ArrowDown, Minus, Info,
} from 'lucide-react';

type RawRow = Record<string, unknown>;
type ModuleResponse = IndicatorResponse<RawRow>;
type IndicatorMap = Record<string, ModuleResponse>;

interface ForecastPoint {
  periodo: string;
  tonelagem_prevista: number;
  ic_80_inferior?: number;
  ic_80_superior?: number;
  ic_95_inferior?: number;
  ic_95_superior?: number;
}

interface Driver {
  feature: string;
  importancia_pct: number;
}

interface Bloco {
  bloco: string;
  importancia_pct: number;
  n_features: number;
}

interface Cenario {
  cenario: string;
  descricao: string;
  tonelagem_anual_prevista: number;
  tonelagem_ano_anterior: number;
  variacao_pct: number | null;
}

interface BacktestPoint {
  periodo: string;
  real: number;
  previsto: number;
  erro_pct: number;
}

const BLOCK_COLORS: Record<string, string> = {
  'Histórico': 'bg-blue-100 text-blue-700',
  'Macroeconomia': 'bg-emerald-100 text-emerald-700',
  'Operação': 'bg-amber-100 text-amber-700',
  'Safra': 'bg-green-100 text-green-700',
  'Clima': 'bg-cyan-100 text-cyan-700',
};

function formatTon(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}k`;
  return value.toFixed(0);
}

export function Module11View() {
  const { selectedInstallation } = useFilterStore();
  const [indicators, setIndicators] = useState<IndicatorMap>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const codes = ['IND-11.01', 'IND-11.02', 'IND-11.03', 'IND-11.04'];

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      setError(null);
      try {
        const results: IndicatorMap = {};
        await Promise.allSettled(
          codes.map(async (code) => {
            try {
              results[code] = await indicatorsService.queryIndicator({
                codigo_indicador: code,
                id_instalacao: selectedInstallation || undefined,
              });
            } catch {
              results[code] = { codigo_indicador: code, nome: code, unidade: '', unctad: false, data: [] };
            }
          })
        );
        setIndicators(results);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Erro ao carregar forecast');
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, [selectedInstallation]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;

  const forecastData = indicators['IND-11.01']?.data?.[0] as RawRow | undefined;
  const scenarioData = indicators['IND-11.02']?.data?.[0] as RawRow | undefined;
  const driversData = indicators['IND-11.03']?.data?.[0] as RawRow | undefined;
  const backtestData = indicators['IND-11.04']?.data?.[0] as RawRow | undefined;

  const previsoes = ((forecastData?.forecast as RawRow)?.previsoes as ForecastPoint[]) || [];
  const cenarios = (scenarioData?.cenarios as Cenario[]) || [];
  const blocos = (driversData?.blocos as Bloco[]) || [];
  const backtestComparacao = (backtestData?.comparacao as BacktestPoint[]) || [];
  const mape = backtestData?.mape_pct as number | undefined;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Forecast de Throughput</h1>
        <p className="text-gray-600 mt-1">
          Previsão SARIMAX com variáveis macro, operacionais, safra e clima
        </p>
      </div>

      <FilterBar />

      {/* Model Info + Backtest */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-5 h-5 text-blue-500" />
            <p className="text-sm font-medium text-gray-600">Precisão (MAPE)</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {mape !== undefined ? `${mape}%` : '—'}
          </p>
          <p className="text-xs text-gray-500 mt-1">Walk-forward 12 meses</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 className="w-5 h-5 text-emerald-500" />
            <p className="text-sm font-medium text-gray-600">Features no Modelo</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {(forecastData?.modelo as RawRow)?.n_features ?? '—'}
          </p>
          <p className="text-xs text-gray-500 mt-1">5 blocos de variáveis</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-amber-500" />
            <p className="text-sm font-medium text-gray-600">Horizonte</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">12 meses</p>
          <p className="text-xs text-gray-500 mt-1">IC 80% e 95%</p>
        </div>
      </div>

      {/* Forecast Table */}
      {previsoes.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-gray-500" />
            Previsão de Tonelagem (12 meses)
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-3 text-gray-500">Período</th>
                  <th className="text-right py-2 px-3 text-gray-500">Previsão</th>
                  <th className="text-right py-2 px-3 text-gray-500">IC 80%</th>
                  <th className="text-right py-2 px-3 text-gray-500">IC 95%</th>
                </tr>
              </thead>
              <tbody>
                {previsoes.map((p, i) => (
                  <tr key={i} className="border-b border-gray-50">
                    <td className="py-2 px-3 font-medium text-gray-700">{p.periodo}</td>
                    <td className="py-2 px-3 text-right font-bold text-gray-900">{formatTon(p.tonelagem_prevista)}</td>
                    <td className="py-2 px-3 text-right text-gray-500">
                      {p.ic_80_inferior && p.ic_80_superior ? `${formatTon(p.ic_80_inferior)} – ${formatTon(p.ic_80_superior)}` : '—'}
                    </td>
                    <td className="py-2 px-3 text-right text-gray-400">
                      {p.ic_95_inferior && p.ic_95_superior ? `${formatTon(p.ic_95_inferior)} – ${formatTon(p.ic_95_superior)}` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Scenarios */}
      {cenarios.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Cenários</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {cenarios.map((c, i) => {
              const isPositive = (c.variacao_pct ?? 0) > 0;
              const Icon = isPositive ? ArrowUp : (c.variacao_pct ?? 0) < 0 ? ArrowDown : Minus;
              const color = c.cenario === 'otimista' ? 'text-green-600' : c.cenario === 'pessimista' ? 'text-red-600' : 'text-blue-600';

              return (
                <div key={i} className="border border-gray-100 rounded-lg p-4">
                  <p className={`text-sm font-semibold ${color} uppercase mb-1`}>{c.cenario}</p>
                  <p className="text-2xl font-bold text-gray-900">{formatTon(c.tonelagem_anual_prevista)}</p>
                  <div className="flex items-center gap-1 mt-1">
                    <Icon className={`w-4 h-4 ${color}`} />
                    <span className={`text-sm font-medium ${color}`}>
                      {c.variacao_pct !== null ? `${c.variacao_pct > 0 ? '+' : ''}${c.variacao_pct}%` : '—'}
                    </span>
                    <span className="text-xs text-gray-400">vs. ano anterior</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">{c.descricao}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Driver Decomposition by Block */}
      {blocos.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <PieChart className="w-5 h-5 text-gray-500" />
            Decomposição de Drivers
          </h2>
          <div className="space-y-3">
            {blocos.map((b, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className={`px-2 py-1 rounded text-xs font-medium ${BLOCK_COLORS[b.bloco] || 'bg-gray-100 text-gray-600'}`}>
                  {b.bloco}
                </span>
                <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full transition-all"
                    style={{ width: `${Math.min(b.importancia_pct, 100)}%` }}
                  />
                </div>
                <span className="text-sm font-bold text-gray-700 w-16 text-right">{b.importancia_pct}%</span>
                <span className="text-xs text-gray-400 w-20">({b.n_features} vars)</span>
              </div>
            ))}
          </div>
          <div className="mt-3 bg-blue-50 rounded-lg p-3 flex items-start gap-2">
            <Info className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />
            <p className="text-xs text-blue-700">
              Importância calculada pelo coeficiente absoluto de cada variável no modelo SARIMAX.
              Variáveis agrupadas em 5 blocos: Histórico, Macroeconomia, Operação, Safra e Clima.
            </p>
          </div>
        </div>
      )}

      {/* Backtest Comparison */}
      {backtestComparacao.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-gray-500" />
            Backtesting — Real vs. Previsto (últimos 12 meses)
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-3 text-gray-500">Período</th>
                  <th className="text-right py-2 px-3 text-gray-500">Real</th>
                  <th className="text-right py-2 px-3 text-gray-500">Previsto</th>
                  <th className="text-right py-2 px-3 text-gray-500">Erro</th>
                </tr>
              </thead>
              <tbody>
                {backtestComparacao.map((p, i) => (
                  <tr key={i} className="border-b border-gray-50">
                    <td className="py-2 px-3 text-gray-700">{p.periodo}</td>
                    <td className="py-2 px-3 text-right font-medium">{formatTon(p.real)}</td>
                    <td className="py-2 px-3 text-right">{formatTon(p.previsto)}</td>
                    <td className={`py-2 px-3 text-right font-medium ${p.erro_pct > 10 ? 'text-red-600' : p.erro_pct > 5 ? 'text-amber-600' : 'text-green-600'}`}>
                      {p.erro_pct}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
