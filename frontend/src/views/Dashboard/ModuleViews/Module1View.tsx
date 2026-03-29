import { useEffect, useMemo, useState } from 'react';
import { FilterBar } from '../../../components/filters/FilterBar';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { ExportButton } from '../../../components/common/ExportButton';
import { useFilterStore } from '../../../store/filterStore';
import { indicatorsService } from '../../../api/indicators';
import { IndicatorDashboardCard } from '../../../components/dashboard/IndicatorDashboardCard';
import type { IndicatorResponse } from '../../../types/api';
import { apiClient } from '../../../api/client';
import { useI18n } from '../../../i18n/I18nContext';

interface IndicatorConfig {
  code: string;
  name: string;
  unit: string;
  desc: string;
  chartType: 'bar' | 'pie' | 'metric';
  valueField: string;
  labelField?: string;
}

const INDICATORS_INFO: IndicatorConfig[] = [
  { code: 'IND-1.01', name: 'Tempo Médio de Espera', unit: 'Horas', desc: 'Tempo entre chegada e atracação', chartType: 'bar', valueField: 'tempo_medio_espera_horas', labelField: 'id_instalacao' },
  { code: 'IND-1.02', name: 'Tempo Médio em Porto', unit: 'Horas', desc: 'Tempo total no porto', chartType: 'bar', valueField: 'tempo_medio_porto_horas', labelField: 'id_instalacao' },
  { code: 'IND-1.03', name: 'Tempo Bruto de Atracação', unit: 'Horas', desc: 'Tempo de atracação até desatracação', chartType: 'bar', valueField: 'tempo_bruto_atracacao_horas', labelField: 'id_instalacao' },
  { code: 'IND-1.04', name: 'Tempo Líquido de Operação', unit: 'Horas', desc: 'Tempo efetivo de operação', chartType: 'bar', valueField: 'tempo_liquido_operacao_horas', labelField: 'id_instalacao' },
  { code: 'IND-1.05', name: 'Taxa de Ocupação de Berços', unit: '%', desc: 'Ocupação média dos berços', chartType: 'bar', valueField: 'taxa_ocupacao_percentual', labelField: 'id_instalacao' },
  { code: 'IND-1.06', name: 'Tempo Ocioso Médio', unit: 'Horas', desc: 'Tempo de paralisação', chartType: 'bar', valueField: 'tempo_ocioso_medio_horas', labelField: 'id_instalacao' },
  { code: 'IND-1.07', name: 'Arqueação Bruta Média', unit: 'GT', desc: 'Tamanho médio dos navios', chartType: 'bar', valueField: 'arqueacao_bruta_media', labelField: 'id_instalacao' },
  { code: 'IND-1.08', name: 'Comprimento Médio', unit: 'Metros', desc: 'Comprimento médio dos navios', chartType: 'bar', valueField: 'comprimento_medio_metros', labelField: 'id_instalacao' },
  { code: 'IND-1.09', name: 'Calado Máximo', unit: 'Metros', desc: 'Maior calado operacional', chartType: 'metric', valueField: 'calado_maximo_metros', labelField: 'id_instalacao' },
  { code: 'IND-1.10', name: 'Distribuição por Tipo', unit: '%', desc: 'Por tipo de navegação', chartType: 'pie', valueField: 'qtd_atracacoes', labelField: 'tipo_navegacao' },
  { code: 'IND-1.11', name: 'Número de Atracações', unit: 'Contagem', desc: 'Total de atracações', chartType: 'bar', valueField: 'total_atracacoes', labelField: 'id_instalacao' },
  { code: 'IND-1.12', name: 'Índice de Paralisação', unit: '%', desc: 'Tempo ocioso / tempo atracado', chartType: 'bar', valueField: 'indice_paralisacao_percentual', labelField: 'id_instalacao' },
];

type RawIndicatorRow = Record<string, unknown>;
type ModuleIndicatorResponse = IndicatorResponse<RawIndicatorRow>;
type IndicatorMap = Record<string, ModuleIndicatorResponse>;

const createEmptyIndicatorResponse = (codigoIndicador: string): ModuleIndicatorResponse => ({
  codigo_indicador: codigoIndicador,
  nome: codigoIndicador,
  unidade: '',
  unctad: false,
  data: [],
});

// --- Tipos analíticos ---

interface TendenciaItem {
  indicador_codigo: string;
  indicador_nome: string;
  unidade: string;
  valor_atual: number | null;
  valor_anterior: number | null;
  variacao_yoy_pct: number | null;
  cagr_3y_pct: number | null;
  classificacao: 'IMPROVING' | 'STABLE' | 'DETERIORATING' | 'SEM_DADOS';
  polaridade_inversa: boolean;
}

interface TendenciaResponse {
  id_instalacao: string;
  ano: number;
  indicadores: TendenciaItem[];
}

interface ScoreComponente {
  indicador_codigo: string;
  indicador_nome: string;
  valor_bruto: number | null;
  valor_normalizado: number | null;
  peso: number;
  contribuicao: number | null;
}

interface ScoreResponse {
  id_instalacao: string;
  ano: number;
  score_total: number;
  ranking_posicao: number;
  total_portos: number;
  componentes: ScoreComponente[];
  nota_metodologica: string;
}

// --- Helpers de UI ---

function trendIcon(cls: string): string {
  if (cls === 'IMPROVING') return '\u2193'; // ↓
  if (cls === 'DETERIORATING') return '\u2191'; // ↑
  if (cls === 'STABLE') return '\u2192'; // →
  return '\u2014'; // —
}

function trendColor(cls: string): string {
  if (cls === 'IMPROVING') return 'text-green-700 bg-green-50';
  if (cls === 'DETERIORATING') return 'text-red-700 bg-red-50';
  if (cls === 'STABLE') return 'text-yellow-700 bg-yellow-50';
  return 'text-gray-500 bg-gray-50';
}

function trendLabel(cls: string): string {
  if (cls === 'IMPROVING') return 'Melhorando';
  if (cls === 'DETERIORATING') return 'Piorando';
  if (cls === 'STABLE') return 'Estável';
  return 'Sem dados';
}

function scoreBarColor(score: number): string {
  if (score >= 70) return 'bg-green-500';
  if (score >= 40) return 'bg-yellow-500';
  return 'bg-red-500';
}

export function Module1View() {
  const { t } = useI18n();
  const { selectedYear, selectedInstallation } = useFilterStore();
  const [indicators, setIndicators] = useState<IndicatorMap>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tableSearch, setTableSearch] = useState('');
  const [selectedIndicator, setSelectedIndicator] = useState('all');

  // Analíticos
  const [tendencia, setTendencia] = useState<TendenciaResponse | null>(null);
  const [score, setScore] = useState<ScoreResponse | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'indicadores' | 'tendencia' | 'score'>('indicadores');

  useEffect(() => {
    const fetchIndicators = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const promises = INDICATORS_INFO.map((ind) =>
          indicatorsService
            .queryIndicator<RawIndicatorRow>({
              codigo_indicador: ind.code,
              params: {
                ano: selectedYear,
                id_instalacao: selectedInstallation || undefined,
              },
            })
            .catch(() => createEmptyIndicatorResponse(ind.code))
        );

        const results = await Promise.all(promises);
        const mapped: IndicatorMap = {};
        results.forEach((result, i) => {
          mapped[INDICATORS_INFO[i].code] = result;
        });
        setIndicators(mapped);
      } catch (err: unknown) {
        const errorResponse = err as { response?: { data?: { detail?: unknown } } };
        const errorMessage = errorResponse?.response?.data?.detail || t('common.errorLoading');
        setError(typeof errorMessage === 'string' ? errorMessage : t('common.errorLoading'));
      } finally {
        setIsLoading(false);
      }
    };

    fetchIndicators();
  }, [selectedYear, selectedInstallation]);

  // Fetch analíticos quando a instalação está selecionada
  useEffect(() => {
    if (!selectedInstallation || !selectedYear) {
      setTendencia(null);
      setScore(null);
      return;
    }

    const fetchAnalytics = async () => {
      setAnalyticsLoading(true);
      try {
        const [tendRes, scoreRes] = await Promise.allSettled([
          apiClient.get<TendenciaResponse[]>('/api/v1/indicators/module1/analise-tendencia', {
            params: { id_instalacao: selectedInstallation, ano_fim: selectedYear },
          }),
          apiClient.get<ScoreResponse[]>('/api/v1/indicators/module1/score-eficiencia', {
            params: { id_instalacao: selectedInstallation, ano: selectedYear },
          }),
        ]);

        if (tendRes.status === 'fulfilled' && tendRes.value.data?.length > 0) {
          setTendencia(tendRes.value.data[0]);
        } else {
          setTendencia(null);
        }

        if (scoreRes.status === 'fulfilled' && scoreRes.value.data?.length > 0) {
          setScore(scoreRes.value.data[0]);
        } else {
          setScore(null);
        }
      } catch {
        // Silencioso: analíticos são complementares
      } finally {
        setAnalyticsLoading(false);
      }
    };

    fetchAnalytics();
  }, [selectedYear, selectedInstallation]);

  const visibleIndicators = useMemo(() => {
    if (selectedIndicator === 'all') {
      return INDICATORS_INFO;
    }
    return INDICATORS_INFO.filter((item) => item.code === selectedIndicator);
  }, [selectedIndicator]);

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">{t('module1.title')}</h1>
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('module1.title')}</h1>
          <p className="text-gray-500 mt-1">{t('module1.subtitle')}</p>
        </div>
        <ExportButton moduleCode="1" />
      </div>

      <FilterBar />

      {/* Tabs: Indicadores / Tendência / Score */}
      <div className="mt-4 mb-4 border-b border-gray-200">
        <nav className="-mb-px flex space-x-6">
          <button
            className={`py-2 px-1 border-b-2 text-sm font-medium ${
              activeTab === 'indicadores'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('indicadores')}
          >
            Indicadores Descritivos
          </button>
          <button
            className={`py-2 px-1 border-b-2 text-sm font-medium ${
              activeTab === 'tendencia'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('tendencia')}
          >
            Tendência Operacional
          </button>
          <button
            className={`py-2 px-1 border-b-2 text-sm font-medium ${
              activeTab === 'score'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('score')}
          >
            Score de Eficiência
          </button>
        </nav>
      </div>

      {error && <ErrorAlert message={error} className="mb-6" />}

      {/* Tab: Indicadores Descritivos */}
      {activeTab === 'indicadores' && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
            <div>
              <label className="text-xs text-gray-500">Buscar na série</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 mt-1"
                placeholder="Filtrar nome no ranking"
                value={tableSearch}
                onChange={(event) => setTableSearch(event.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-gray-500">Indicador</label>
              <select
                className="w-full border border-gray-300 rounded-lg px-3 py-2 mt-1"
                value={selectedIndicator}
                onChange={(event) => setSelectedIndicator(event.target.value)}
              >
                <option value="all">Todos</option>
                {INDICATORS_INFO.map((indicator) => (
                  <option key={indicator.code} value={indicator.code}>
                    {indicator.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {visibleIndicators.map((ind) => (
              <IndicatorDashboardCard
                key={ind.code}
                title={ind.name}
                description={ind.desc}
                unit={ind.unit}
                isLoading={isLoading}
                data={indicators[ind.code]}
                chartType={ind.chartType}
                valueField={ind.valueField}
                labelField={ind.labelField}
                filterText={tableSearch}
                indicatorCode={ind.code}
              />
            ))}
          </div>
        </>
      )}

      {/* Tab: Tendência Operacional */}
      {activeTab === 'tendencia' && (
        <div className="mt-2">
          {!selectedInstallation ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
              Selecione uma instalação no filtro acima para ver a análise de tendência.
            </div>
          ) : analyticsLoading ? (
            <LoadingSpinner />
          ) : !tendencia ? (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-600">
              Sem dados de tendência para esta instalação/período.
            </div>
          ) : (
            <>
              <h2 className="text-lg font-semibold text-gray-800 mb-3">
                Tendência Operacional — {tendencia.id_instalacao} ({tendencia.ano})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {tendencia.indicadores.map((item) => (
                  <div key={item.indicador_codigo} className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-gray-500">{item.indicador_codigo}</span>
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${trendColor(item.classificacao)}`}>
                        {trendIcon(item.classificacao)} {trendLabel(item.classificacao)}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-gray-800">{item.indicador_nome}</p>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-gray-600">
                      <div>
                        <span className="block text-gray-400">Atual</span>
                        <span className="font-semibold">{item.valor_atual?.toFixed(1) ?? '—'} {item.unidade}</span>
                      </div>
                      <div>
                        <span className="block text-gray-400">Anterior</span>
                        <span className="font-semibold">{item.valor_anterior?.toFixed(1) ?? '—'} {item.unidade}</span>
                      </div>
                      <div>
                        <span className="block text-gray-400">Var. Anual</span>
                        <span className={`font-semibold ${
                          item.variacao_yoy_pct != null
                            ? (item.polaridade_inversa
                                ? (item.variacao_yoy_pct < 0 ? 'text-green-600' : 'text-red-600')
                                : (item.variacao_yoy_pct > 0 ? 'text-green-600' : 'text-red-600'))
                            : 'text-gray-400'
                        }`}>
                          {item.variacao_yoy_pct != null ? `${item.variacao_yoy_pct > 0 ? '+' : ''}${item.variacao_yoy_pct.toFixed(1)}%` : '—'}
                        </span>
                      </div>
                      <div>
                        <span className="block text-gray-400">Cresc. 3 anos</span>
                        <span className="font-semibold">
                          {item.cagr_3y_pct != null ? `${item.cagr_3y_pct > 0 ? '+' : ''}${item.cagr_3y_pct.toFixed(1)}%` : '—'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-xs text-blue-800">
                  <span className="font-semibold">Nota:</span>{' '}
                  Para indicadores de tempo, queda = melhoria operacional. Para atracações, crescimento = melhoria.
                  Classificação: variação {'>'} 5% = Em Melhora / Em Deterioração, conforme a direção do indicador.
                </p>
              </div>
            </>
          )}
        </div>
      )}

      {/* Tab: Score de Eficiência */}
      {activeTab === 'score' && (
        <div className="mt-2">
          {!selectedInstallation ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
              Selecione uma instalação no filtro acima para ver o score de eficiência.
            </div>
          ) : analyticsLoading ? (
            <LoadingSpinner />
          ) : !score ? (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-600">
              Sem dados de eficiência para esta instalação/período.
            </div>
          ) : (
            <>
              <h2 className="text-lg font-semibold text-gray-800 mb-3">
                Score de Eficiência — {score.id_instalacao} ({score.ano})
              </h2>

              {/* Score card principal */}
              <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm mb-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-4xl font-bold text-gray-900">{score.score_total.toFixed(1)}</p>
                    <p className="text-sm text-gray-500 mt-1">de 100 pontos</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-semibold text-gray-700">#{score.ranking_posicao}</p>
                    <p className="text-sm text-gray-500">de {score.total_portos} portos</p>
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${scoreBarColor(score.score_total)}`}
                    style={{ width: `${Math.min(score.score_total, 100)}%` }}
                  />
                </div>
              </div>

              {/* Decomposição por componente */}
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Decomposição por componente</h3>
              <div className="space-y-3">
                {score.componentes.map((comp) => (
                  <div key={comp.indicador_codigo} className="bg-white border border-gray-200 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-400">{comp.indicador_codigo}</span>
                        <span className="text-sm font-medium text-gray-700">{comp.indicador_nome}</span>
                      </div>
                      <div className="text-right text-xs text-gray-500">
                        Peso: {(comp.peso * 100).toFixed(0)}% | Contribuição: {comp.contribuicao?.toFixed(1) ?? '—'}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex-1 bg-gray-100 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${scoreBarColor(comp.valor_normalizado ?? 0)}`}
                          style={{ width: `${Math.min(comp.valor_normalizado ?? 0, 100)}%` }}
                        />
                      </div>
                      <span className="text-xs font-semibold text-gray-600 w-12 text-right">
                        {comp.valor_normalizado?.toFixed(0) ?? '—'}/100
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      Valor bruto: {comp.valor_bruto?.toFixed(1) ?? '—'}
                    </p>
                  </div>
                ))}
              </div>

              <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-xs text-blue-800">
                  <span className="font-semibold">Nota metodológica:</span>{' '}
                  {score.nota_metodologica}
                </p>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
