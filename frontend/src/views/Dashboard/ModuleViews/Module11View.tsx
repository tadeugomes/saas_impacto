import { useEffect, useState } from 'react';
import { FilterBar } from '../../../components/filters/FilterBar';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { ExportButton } from '../../../components/common/ExportButton';
import { useFilterStore } from '../../../store/filterStore';
import { PORTO_OPTIONS } from '../../../components/filters/InstallationSelector';
import { indicatorsService } from '../../../api/indicators';
import { useI18n } from '../../../i18n/I18nContext';
import { ChartCard } from '../../../components/charts/ChartCard';
import { LineChart } from '../../../components/charts/LineChart';
import type { IndicatorResponse } from '../../../types/api';
import {
  TrendingUp, BarChart3, PieChart, Target,
  ArrowUp, ArrowDown, Minus, Info,
} from 'lucide-react';

type RawRow = Record<string, unknown>;
type ModuleResponse = IndicatorResponse<RawRow>;
type IndicatorMap = Record<string, ModuleResponse>;

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
  const { t } = useI18n();
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
              results[code] = await indicatorsService.queryIndicator<RawRow>({
                codigo_indicador: code,
                params: {
                  id_instalacao: selectedInstallation || undefined,
                },
              });
            } catch {
              results[code] = { codigo_indicador: code, nome: code, unidade: '', unctad: false, data: [] };
            }
          })
        );
        setIndicators(results);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : t('common.errorLoading'));
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, [selectedInstallation]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;

  if (!selectedInstallation) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('module11.title')}</h1>
          <p className="text-gray-600 mt-1">{t('module11.subtitle')}</p>
        </div>
        <FilterBar showYear={false} />
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-center">
          <Info className="mx-auto mb-2 text-amber-500" size={32} />
          <p className="text-amber-800 font-medium">{t('module11.selectPort')}</p>
          <p className="text-amber-600 text-sm mt-1">{t('module11.selectPortHint')}</p>
        </div>
      </div>
    );
  }

  const forecastData = indicators['IND-11.01']?.data?.[0] as RawRow | undefined;
  const scenarioData = indicators['IND-11.02']?.data?.[0] as RawRow | undefined;
  const driversData = indicators['IND-11.03']?.data?.[0] as RawRow | undefined;
  const backtestData = indicators['IND-11.04']?.data?.[0] as RawRow | undefined;

  const forecastObj = forecastData?.forecast as RawRow | undefined;
  const previsoes_anuais = (forecastObj?.previsoes_anuais as Array<Record<string, number>>) || [];
  const cenarios = (scenarioData?.cenarios as Cenario[]) || [];
  const blocos = (driversData?.blocos as Bloco[]) || [];
  const horizontes = (backtestData?.horizontes as Record<string, Record<string, unknown>>) || {};
  const bt12 = horizontes['12m'] as Record<string, unknown> | undefined;
  const mape = bt12?.mape_pct as number | undefined;

  // Label legível da instalação (ex: "Itaqui (MA)")
  const instalacaoLabel = PORTO_OPTIONS.find(o => o.value === selectedInstallation)?.label ?? selectedInstallation ?? '';

  // Interpretações em linguagem de negócio
  const interp11 = forecastData?.interpretacao as RawRow | undefined;
  const interp12 = scenarioData?.interpretacao as RawRow | undefined;
  const resumoExecutivo = (interp11?.resumo_executivo ?? interp12?.resumo_executivo) as string | undefined;
  const interpMape = interp11?.mape as RawRow | undefined;
  const interpDrivers = (interp11?.drivers ?? interp12?.drivers) as RawRow | undefined;
  const interpCenarios = interp12?.cenarios as RawRow | undefined;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('module11.title')}</h1>
          <p className="text-gray-600 mt-1">
            {t('module11.subtitle')}
          </p>
        </div>
        <ExportButton moduleCode="11" />
      </div>

      <FilterBar showYear={false} />

      {/* Model Info + Backtest */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className={`rounded-xl border p-5 shadow-sm ${
          mape !== undefined && mape > 15
            ? 'bg-red-50 border-red-300'
            : 'bg-white border-gray-200'
        }`}>
          <div className="flex items-center gap-2 mb-2">
            <Target className={`w-5 h-5 ${mape !== undefined && mape > 15 ? 'text-red-500' : 'text-blue-500'}`} />
            <p className="text-sm font-medium text-gray-600">{t('module11.accuracy')}</p>
          </div>
          <p className={`text-3xl font-bold ${
            mape !== undefined && mape > 15 ? 'text-red-600' : 'text-gray-900'
          }`}>
            {mape !== undefined ? `${mape}%` : '—'}
          </p>
          <p className="text-xs text-gray-500 mt-1">{t('module11.validationPeriod')}</p>
          {mape !== undefined && mape > 15 && (
            <div className="mt-2 bg-red-100 border border-red-200 rounded-lg px-3 py-2">
              <p className="text-xs font-semibold text-red-700">Taxa de Erro Elevada</p>
              <p className="text-xs text-red-600 mt-0.5">Acionar equipe técnica para mais detalhes sobre a precisão deste porto.</p>
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 className="w-5 h-5 text-emerald-500" />
            <p className="text-sm font-medium text-gray-600">{t('module11.variables')}</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {(forecastData?.modelo as RawRow)?.n_features !== undefined ? String((forecastData?.modelo as RawRow).n_features) : '—'}
          </p>
          <p className="text-xs text-gray-500 mt-1">{t('module11.categories')}</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-amber-500" />
            <p className="text-sm font-medium text-gray-600">{t('module11.horizon')}</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">5 anos</p>
          <p className="text-xs text-gray-500 mt-1">{t('module11.horizonDesc')}</p>
        </div>
      </div>

      {/* Annual Forecast Summary (5 years) */}
      {previsoes_anuais.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-gray-500" />
            {t('module11.forecast.title')}
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-3 text-gray-500">Ano</th>
                  <th className="text-right py-2 px-3 text-gray-500">Tonelagem Anual</th>
                  <th className="text-right py-2 px-3 text-gray-500">Média Mensal</th>
                  <th className="text-right py-2 px-3 text-gray-500">IC 95%</th>
                  <th className="text-right py-2 px-3 text-gray-500">Confiança</th>
                </tr>
              </thead>
              <tbody>
                {previsoes_anuais.map((p, i) => {
                  const confianca = i === 0 ? 'Alta' : i <= 2 ? 'Média' : 'Baixa';
                  const confColor = i === 0 ? 'text-green-600' : i <= 2 ? 'text-amber-600' : 'text-red-500';
                  return (
                    <tr key={i} className="border-b border-gray-50">
                      <td className="py-2 px-3 font-medium text-gray-700">{p.ano}</td>
                      <td className="py-2 px-3 text-right font-bold text-gray-900">
                        {formatTon(p.tonelagem_anual)}
                      </td>
                      <td className="py-2 px-3 text-right text-gray-600">
                        {formatTon(p.tonelagem_media_mensal)}/mês
                      </td>
                      <td className="py-2 px-3 text-right text-gray-400">
                        {p.ic_95_inferior && p.ic_95_superior
                          ? `${formatTon(p.ic_95_inferior)} – ${formatTon(p.ic_95_superior)}`
                          : '—'}
                      </td>
                      <td className={`py-2 px-3 text-right text-xs font-medium ${confColor}`}>
                        {confianca}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-gray-400 mt-3">
            {t('module11.confidence.note')}
          </p>
        </div>
      )}

      {/* Scenarios (5 years) */}
      {cenarios.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('module11.scenarios.title')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {(cenarios as unknown as Record<string, unknown>[]).map((c: Record<string, unknown>, i: number) => {
              const variacao = c.variacao_acumulada_pct as number | null;
              const cagr = c.cagr_pct as number | null;
              const isPositive = (variacao ?? 0) > 0;
              const Icon = isPositive ? ArrowUp : (variacao ?? 0) < 0 ? ArrowDown : Minus;
              const color = (c.cenario as string) === 'otimista' ? 'text-green-600' : (c.cenario as string) === 'pessimista' ? 'text-red-600' : 'text-blue-600';
              type AnoPrevisao = Record<string, number> & { parcial?: boolean };
              const anuais = (c.previsoes_anuais as AnoPrevisao[]) || [];
              const anuaisCompletos = anuais.filter(a => !a.parcial);
              const ultimoAno = anuaisCompletos[anuaisCompletos.length - 1] ?? anuais[anuais.length - 1];

              return (
                <div key={i} className="border border-gray-100 rounded-lg p-4">
                  <p className={`text-sm font-semibold ${color} uppercase mb-1`}>{c.cenario as string}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {ultimoAno ? formatTon(ultimoAno.tonelagem_anual) : '—'}
                    <span className="text-xs font-normal text-gray-400 ml-1">
                      /ano em {ultimoAno?.ano}
                    </span>
                  </p>
                  <div className="flex items-center gap-1 mt-1">
                    <Icon className={`w-4 h-4 ${color}`} />
                    <span className={`text-sm font-medium ${color}`}>
                      {variacao !== null ? `${Math.abs(variacao)}% acum.` : '—'}
                    </span>
                  </div>
                  {cagr !== null && (
                    <p className="text-xs text-gray-500 mt-1">Crescimento anual: {cagr > 0 ? '+' : ''}{cagr}%/ano</p>
                  )}
                  {/* Mini table per year */}
                  <div className="mt-3 space-y-1">
                    {anuaisCompletos.map((a, j) => (
                      <div key={j} className="grid grid-cols-2 text-xs">
                        <span className="text-gray-500">{a.ano}</span>
                        <span className="font-medium text-gray-700 text-right">{formatTon(a.tonelagem_anual)}</span>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-gray-400 mt-2">{c.descricao as string}</p>
                </div>
              );
            })}
          </div>
          <p className="text-xs text-gray-400 mt-3">
            Os desvios dos cenários convergem 20% ao ano para a tendência base. Ref: {(scenarioData as RawRow)?.ano_referencia !== undefined ? String((scenarioData as RawRow).ano_referencia) : '—'}.
          </p>
          {!!(interpCenarios?.texto || interpCenarios?.texto_decisao) && (
            <div className="mt-4 space-y-3">
              {!!interpCenarios?.texto && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-700">{String(interpCenarios.texto)}</p>
                </div>
              )}
              {!!interpCenarios?.texto_decisao && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
                  <Info className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                  <p className="text-sm text-amber-800">{String(interpCenarios.texto_decisao)}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Scenario Comparison Chart */}
      {cenarios.length > 1 && (() => {
        const SCENARIO_COLORS: Record<string, string> = {
          base: '#3b82f6',
          otimista: '#10b981',
          pessimista: '#ef4444',
        };
        const baseScenario = (cenarios as unknown as Record<string, unknown>[]).find(
          (c) => (c.cenario as string) === 'base',
        );
        type AnoData = Record<string, number> & { parcial?: boolean };
        const baseAnuais = ((baseScenario?.previsoes_anuais as AnoData[]) || []).filter(a => !a.parcial);
        const chartLabels = baseAnuais.map(a => String(a.ano));

        const chartDatasets = (cenarios as unknown as Record<string, unknown>[]).map((c) => {
          const nome = c.cenario as string;
          const anuais = ((c.previsoes_anuais as AnoData[]) || []).filter(a => !a.parcial);
          return {
            label: nome.charAt(0).toUpperCase() + nome.slice(1),
            data: anuais.map(a => a.tonelagem_anual),
            borderColor: SCENARIO_COLORS[nome] || '#6b7280',
            backgroundColor: (SCENARIO_COLORS[nome] || '#6b7280') + '20',
            fill: nome === 'base',
            tension: 0.3,
          };
        });

        return chartLabels.length > 0 ? (
          <ChartCard title={t('module11.scenarios.chart')} description={instalacaoLabel}>
            <LineChart
              labels={chartLabels}
              datasets={chartDatasets}
              yAxisLabel="Tonelagem (ton)"
              yAxisBeginAtZero={false}
            />
          </ChartCard>
        ) : null;
      })()}

      {/* Driver Decomposition by Block */}
      {blocos.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <PieChart className="w-5 h-5 text-gray-500" />
            {t('module11.drivers.title')}
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
                <span className="text-xs text-gray-400 w-20">({b.n_features} variáveis)</span>
              </div>
            ))}
          </div>
          {!!interpDrivers?.texto && (
            <div className="mt-3 bg-emerald-50 rounded-lg p-4">
              <p className="text-sm text-emerald-800">{String(interpDrivers.texto)}</p>
            </div>
          )}
          <div className="mt-3 bg-blue-50 rounded-lg p-3 flex items-start gap-2">
            <Info className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />
            <p className="text-xs text-blue-700">
              {t('module11.drivers.description')}
            </p>
          </div>
        </div>
      )}

      {/* Multi-Horizon Backtest */}
      {Object.keys(horizontes).length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-gray-500" />
            {t('module11.validation.title')}
          </h2>

          {/* Summary table */}
          <div className="overflow-x-auto mb-4">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-3 text-gray-500">Período</th>
                  <th className="text-right py-2 px-3 text-gray-500">Erro (%)</th>
                  <th className="text-right py-2 px-3 text-gray-500">Erro Médio (ton)</th>
                  <th className="text-right py-2 px-3 text-gray-500">Desvio (ton)</th>
                  <th className="text-right py-2 px-3 text-gray-500">Avaliação</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(horizontes).map(([key, val]) => {
                  const h = val as Record<string, unknown>;
                  const hMape = h.mape_pct as number | undefined;
                  const label = hMape !== undefined
                    ? (hMape < 5 ? 'Excelente' : hMape < 10 ? 'Bom' : hMape < 15 ? 'Aceitável' : 'Fraco')
                    : '—';
                  const color = hMape !== undefined
                    ? (hMape < 5 ? 'text-green-600' : hMape < 10 ? 'text-blue-600' : hMape < 15 ? 'text-amber-600' : 'text-red-600')
                    : 'text-gray-400';

                  return (
                    <tr key={key} className="border-b border-gray-50">
                      <td className="py-2 px-3 font-medium text-gray-700">{key}</td>
                      <td className="py-2 px-3 text-right font-bold">{hMape !== undefined ? `${hMape}%` : '—'}</td>
                      <td className="py-2 px-3 text-right text-gray-600">
                        {h.mae ? formatTon(h.mae as number) : '—'}
                      </td>
                      <td className="py-2 px-3 text-right text-gray-500">
                        {h.rmse ? formatTon(h.rmse as number) : '—'}
                      </td>
                      <td className={`py-2 px-3 text-right text-xs font-medium ${color}`}>{label}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <p className="text-xs text-gray-400">
            Erro (%): desvio médio percentual medido em dados não usados no treinamento, com janela deslizante de 12 meses.
            Avaliação: Excelente (&lt;5%), Bom (5-10%), Aceitável (10-15%), Fraco (&gt;15%).
          </p>
          {!!(interpMape?.texto || interpMape?.impacto_operacional) && (
            <div className="mt-4 bg-gray-50 rounded-lg p-4 space-y-2">
              {!!interpMape?.texto && (
                <p className="text-sm text-gray-700">{String(interpMape.texto)}</p>
              )}
              {!!interpMape?.impacto_operacional && (
                <p className="text-sm text-gray-600 italic">{String(interpMape.impacto_operacional)}</p>
              )}
            </div>
          )}
        </div>
      )}
      {/* Resumo executivo — leitura de negócio para investidores */}
      {resumoExecutivo && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <div className="flex items-start justify-between mb-3">
            <div>
              <p className="text-xs font-semibold text-blue-500 uppercase tracking-wide">{t('module11.executive.title')}</p>
              <p className="text-base font-semibold text-blue-900 mt-0.5">
                Porto de {instalacaoLabel}
              </p>
            </div>
            <Info className="w-5 h-5 text-blue-400 shrink-0 mt-1" />
          </div>
          <p className="text-sm text-blue-900 leading-relaxed">{resumoExecutivo}</p>
          <p className="text-xs text-blue-500 mt-3">
            {t('module11.executive.note')}
          </p>
        </div>
      )}
    </div>
  );
}
