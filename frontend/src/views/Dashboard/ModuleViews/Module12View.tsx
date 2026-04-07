import { useEffect, useMemo, useState } from 'react';
import { FilterBar } from '../../../components/filters/FilterBar';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { ExportButton } from '../../../components/common/ExportButton';
import { useFilterStore } from '../../../store/filterStore';
import { indicatorsService } from '../../../api/indicators';
import { IndicatorDashboardCard } from '../../../components/dashboard/IndicatorDashboardCard';
import type { IndicatorResponse } from '../../../types/api';
import { useI18n } from '../../../i18n/I18nContext';
import { useIndicatorLabel } from '../../../i18n/indicatorTranslations';

interface IndicatorConfig {
  code: string;
  name: string;
  unit: string;
  desc: string;
  chartType: 'bar' | 'pie' | 'metric';
  valueField: string;
  labelField?: string;
  tooltipContext?: string;
}

const INDICATORS_INFO: IndicatorConfig[] = [
  {
    code: 'IND-12.01',
    name: 'Capacidade Máxima de Movimentação',
    unit: 't/ano ou TEU/ano',
    desc: 'Quanto o porto consegue movimentar por ano em cada berço, considerando padrões internacionais de ocupação (UNCTAD)',
    chartType: 'bar',
    valueField: 'c_cais_bruta',
    labelField: 'perfil_carga',
    tooltipContext: 'da capacidade do maior berço',
  },
  {
    code: 'IND-12.02',
    name: 'Nível de Ocupação dos Berços',
    unit: '%',
    desc: 'Quanto do tempo disponível dos berços já está sendo utilizado — valores acima do limite indicam risco de congestionamento e filas',
    chartType: 'bar',
    valueField: 'bor_obs_pct',
    labelField: 'perfil_carga',
    tooltipContext: 'do berço mais ocupado',
  },
  {
    code: 'IND-12.03',
    name: 'Aproveitamento da Capacidade Instalada',
    unit: '%',
    desc: 'Percentual da capacidade total que está efetivamente sendo utilizado — indica potencial de crescimento ou necessidade de expansão',
    chartType: 'bar',
    valueField: 'bur_obs_pct',
    labelField: 'perfil_carga',
    tooltipContext: 'do berço mais utilizado',
  },
  {
    code: 'IND-12.04',
    name: 'Volume Médio por Navio',
    unit: 't ou TEU',
    desc: 'Carga média movimentada por atracação — valores maiores indicam operações de maior escala e eficiência logística',
    chartType: 'bar',
    valueField: 'mean_lm',
    labelField: 'perfil_carga',
    tooltipContext: 'do maior volume médio',
  },
  {
    code: 'IND-12.05',
    name: 'Tempo Médio de Permanência no Berço',
    unit: 'Horas',
    desc: 'Quanto tempo cada navio ocupa o berço em média — tempos menores significam maior rotatividade e produtividade',
    chartType: 'bar',
    valueField: 'mean_ta_h',
    labelField: 'perfil_carga',
    tooltipContext: 'do maior tempo de permanência',
  },
  {
    code: 'IND-12.06',
    name: 'Distribuição da Capacidade por Tipo de Carga',
    unit: 't/ano ou TEU/ano',
    desc: 'Como a capacidade do porto se divide entre granéis, contêineres e carga geral — revela o perfil logístico e oportunidades de diversificação',
    chartType: 'pie',
    valueField: 'c_alocada',
    labelField: 'perfil_carga',
  },
  {
    code: 'IND-12.08',
    name: 'Capacidade Disponível para Crescimento',
    unit: 't ou TEU',
    desc: 'Diferença entre o que o porto pode movimentar e o que efetivamente movimenta — indica espaço para novos contratos ou necessidade de investimento',
    chartType: 'bar',
    valueField: 'folga_operacional',
    labelField: 'perfil_carga',
    tooltipContext: 'da maior folga disponível',
  },
];

interface CapacityAnalysis {
  nao_conteiner: CapacityResult[];
  conteiner: CapacityResult[];
  consolidacao: {
    c_cais_total: number;
    c_armazenagem: number | null;
    c_hinterland: number | null;
    c_sistema: number;
    gargalo: string;
    n_perfis: number;
    n_atracacoes_total: number;
    n_bercos_distintos: number;
  };
  parametros: Record<string, unknown>;
  config_terminal?: {
    fonte: string;
    nome_terminal: string | null;
  };
  h_ef_breakdown?: {
    h_cal: number;
    h_cli: number;
    h_mnt: number;
    h_nav: number;
    h_out: number;
    h_ef_medio: number;
    n_bercos: number;
    fonte: string;
  } | null;
}

interface CapacityResult {
  ano: number;
  id_instalacao: string;
  berco: string;
  perfil_carga: string;
  sentido: string | null;
  is_container: boolean;
  n_bercos: number;
  h_ef: number;
  bor_adm: number;
  c_cais_bruta: number;
  c_alocada?: number;
  fracao_tempo?: number;
  bor_obs_pct: number | null;
  bur_obs_pct: number | null;
  mov_realizada: number;
  saturado: boolean;
  folga_operacional: number | null;
  mean_ta_h: number | null;
  mean_lm: number | null;
  ta_plus_a: number | null;
  n_atracacoes: number;
  unidade_capacidade: string;
}

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

const buildTooltipAfterLabel = (contextLabel: string) => {
  return (context: import('chart.js').TooltipItem<'bar'>) => {
    const allData = (context.dataset.data as (number | null)[])
      .map(Number)
      .filter((v): v is number => Number.isFinite(v));
    if (allData.length === 0) return '';
    const max = Math.max(...allData);
    if (max === 0) return '';
    const pct = Math.round((Number(context.raw) / max) * 100);
    return `${pct}% ${contextLabel}`;
  };
};

const formatNumber = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '-';
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toFixed(1);
};

export function Module12View() {
  const { t } = useI18n();
  const tInd = useIndicatorLabel();
  const { selectedYear, selectedInstallation } = useFilterStore();
  const [analysis, setAnalysis] = useState<CapacityAnalysis | null>(null);
  const [indicators, setIndicators] = useState<IndicatorMap>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndicator, setSelectedIndicator] = useState('all');

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      // Fetch capacity analysis from dedicated endpoint
      try {
        const params = new URLSearchParams();
        if (selectedInstallation) params.set('id_instalacao', selectedInstallation);
        if (selectedYear) params.set('ano', String(selectedYear));

        const resp = await fetch(
          `/api/v1/indicators/module12/capacidade-cais?${params.toString()}`,
          {
            headers: {
              'X-Tenant-ID': localStorage.getItem('tenant_id') || '',
              Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
            },
          },
        );

        if (resp.ok) {
          const data: CapacityAnalysis = await resp.json();
          setAnalysis(data);

          // Convert capacity results to indicator format for dashboard cards
          const allResults = [...(data.nao_conteiner || []), ...(data.conteiner || [])];
          const mapped: IndicatorMap = {};
          for (const ind of INDICATORS_INFO) {
            mapped[ind.code] = {
              codigo_indicador: ind.code,
              nome: ind.name,
              unidade: ind.unit,
              unctad: false,
              data: allResults.map((r) => ({
                ...r,
                id_instalacao: r.id_instalacao,
                ano: r.ano,
              })),
            };
          }
          setIndicators(mapped);
        } else {
          const errBody = await resp.json().catch(() => ({ detail: 'Erro ao carregar dados' }));
          setError(typeof errBody.detail === 'string' ? errBody.detail : 'Erro ao carregar dados');
        }
      } catch {
        // Fallback: try individual indicators via generic endpoint
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
              .catch(() => createEmptyIndicatorResponse(ind.code)),
          );
          const results = await Promise.all(promises);
          const mapped: IndicatorMap = {};
          results.forEach((result, i) => {
            mapped[INDICATORS_INFO[i].code] = result;
          });
          setIndicators(mapped);
        } catch (err: unknown) {
          setError('Não foi possível carregar os dados de capacidade. Verifique sua conexão e tente novamente.');
        }
      } finally {
        setIsLoading(false);
      }
    };

    if (selectedInstallation) {
      fetchData();
    } else {
      setIsLoading(false);
      setAnalysis(null);
    }
  }, [selectedYear, selectedInstallation]);

  const localizedIndicators = useMemo(
    () =>
      INDICATORS_INFO.map((ind) => {
        const { name, desc } = tInd(ind.code, ind.name, ind.desc);
        return { ...ind, name, desc };
      }),
    [tInd],
  );

  const visibleIndicators = useMemo(() => {
    if (selectedIndicator === 'all') return localizedIndicators;
    return localizedIndicators.filter((item) => item.code === selectedIndicator);
  }, [selectedIndicator, localizedIndicators]);

  const consolidacao = analysis?.consolidacao;

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          {t('module12.title')}
        </h1>
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('module12.title')}</h1>
          <p className="text-gray-500 mt-1">{t('module12.subtitle')}</p>
        </div>
        <ExportButton moduleCode="12" />
      </div>

      <FilterBar />

      {!selectedInstallation && (
        <div className="mt-6 p-4 bg-blue-50 text-blue-700 rounded-lg">
          Selecione um porto ou terminal para visualizar a análise de capacidade e oportunidades de investimento.
        </div>
      )}

      {error && <ErrorAlert message={error} className="mt-4 mb-6" />}

      {/* Summary Cards */}
      {consolidacao && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-sm border p-4">
            <div className="text-sm text-gray-500">Capacidade Total do Porto</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">
              {formatNumber(consolidacao.c_cais_total)}
            </div>
            <div className="text-xs text-gray-400 mt-1">toneladas/ano (todos os tipos de carga)</div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border p-4">
            <div className="text-sm text-gray-500">Capacidade Efetiva do Sistema</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">
              {formatNumber(consolidacao.c_sistema)}
            </div>
            <div className="text-xs text-gray-400 mt-1">
              Limitada pelo {consolidacao.c_sistema === consolidacao.c_cais_total ? 'cais' : consolidacao.gargalo === 'armazenagem' ? 'armazenamento' : consolidacao.gargalo === 'hinterland' ? 'acesso terrestre' : consolidacao.gargalo}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border p-4">
            <div className="text-sm text-gray-500">Principal Restrição</div>
            <div className={`text-2xl font-bold mt-1 ${
              consolidacao.gargalo === 'cais' ? 'text-amber-600' : 'text-red-600'
            }`}>
              {consolidacao.gargalo === 'cais' ? 'Berços de Atracação' :
               consolidacao.gargalo === 'armazenagem' ? 'Armazenamento' :
               consolidacao.gargalo === 'hinterland' ? 'Acesso Terrestre' : '-'}
            </div>
            <div className="text-xs text-gray-400 mt-1">
              Fator que mais limita o crescimento
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border p-4">
            <div className="text-sm text-gray-500">Base de Análise</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">
              {consolidacao.n_atracacoes_total.toLocaleString('pt-BR')} <span className="text-base font-normal text-gray-500">atracações</span>
            </div>
            <div className="text-xs text-gray-400 mt-1">
              {consolidacao.n_bercos_distintos} berços em {consolidacao.n_perfis} combinações de carga
            </div>
          </div>
        </div>
      )}

      {/* H_ef Breakdown */}
      {analysis?.h_ef_breakdown && (
        <div className="bg-white rounded-xl shadow-sm border p-5 mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Disponibilidade Operacional Real (H_ef)
          </h3>
          <p className="text-xs text-gray-500 mb-4">
            Das {analysis.h_ef_breakdown.h_cal.toLocaleString('pt-BR')}h do ano, quantas horas o porto efetivamente opera — baseado em registros reais de paralisação (ANTAQ)
          </p>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <div className="text-center">
              <div className="text-xs text-gray-400">Horas/Ano</div>
              <div className="text-lg font-bold text-gray-900">{analysis.h_ef_breakdown.h_cal.toLocaleString('pt-BR')}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-red-400">Clima</div>
              <div className="text-lg font-bold text-red-600">−{Math.round(analysis.h_ef_breakdown.h_cli).toLocaleString('pt-BR')}h</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-orange-400">Manutenção</div>
              <div className="text-lg font-bold text-orange-600">−{Math.round(analysis.h_ef_breakdown.h_mnt).toLocaleString('pt-BR')}h</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-blue-400">Maré/Navegação</div>
              <div className="text-lg font-bold text-blue-600">−{Math.round(analysis.h_ef_breakdown.h_nav).toLocaleString('pt-BR')}h</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-400">Outras Paradas</div>
              <div className="text-lg font-bold text-gray-600">−{Math.round(analysis.h_ef_breakdown.h_out).toLocaleString('pt-BR')}h</div>
            </div>
            <div className="text-center bg-green-50 rounded-lg p-2">
              <div className="text-xs text-green-600 font-medium">H_ef Efetivo</div>
              <div className="text-lg font-bold text-green-700">{Math.round(analysis.h_ef_breakdown.h_ef_medio).toLocaleString('pt-BR')}h</div>
              <div className="text-[10px] text-green-500">média de {analysis.h_ef_breakdown.n_bercos} berços</div>
            </div>
          </div>
        </div>
      )}

      {/* Saturation Alerts */}
      {analysis && (() => {
        const saturados = [...(analysis.nao_conteiner || []), ...(analysis.conteiner || [])].filter((r) => r.saturado);
        if (saturados.length === 0) return null;
        return (
          <div className="mb-6">
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg mb-3">
              <span className="text-red-700 font-semibold text-sm">
                Alerta: {saturados.length} {saturados.length === 1 ? 'berço opera' : 'berços operam'} acima da capacidade recomendada
              </span>
              <p className="text-red-600 text-xs mt-1">
                Berços saturados geram filas de navios, aumento de custos de demurrage e perda de competitividade.
              </p>
            </div>
            {saturados.map((r, idx) => (
              <div
                key={idx}
                className="p-3 bg-red-50 border border-red-200 rounded-lg mb-2 flex items-center gap-2"
              >
                <span className="text-red-500 font-semibold text-sm">CONGESTIONADO</span>
                <span className="text-red-700 text-sm">
                  {r.perfil_carga} no berço {r.berco} — ocupação de {r.bor_obs_pct?.toFixed(1)}% (limite recomendado: {(r.bor_adm * 100).toFixed(0)}%)
                </span>
              </div>
            ))}
          </div>
        );
      })()}

      {/* Indicator filter */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <div>
          <label className="text-xs text-gray-500">Indicador</label>
          <select
            className="w-full border border-gray-300 rounded-lg px-3 py-2 mt-1"
            value={selectedIndicator}
            onChange={(event) => setSelectedIndicator(event.target.value)}
          >
            <option value="all">Todos</option>
            {localizedIndicators.map((indicator) => (
              <option key={indicator.code} value={indicator.code}>
                {indicator.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Indicator Cards */}
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
            indicatorCode={ind.code}
            tooltipAfterLabel={ind.tooltipContext ? buildTooltipAfterLabel(ind.tooltipContext) : undefined}
          />
        ))}
      </div>

      {/* Operational Parameters Table */}
      {analysis && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Detalhamento por Berço e Tipo de Carga
          </h2>
          <p className="text-sm text-gray-500 mb-4">
            Visão operacional de cada berço — identifique gargalos específicos e oportunidades de melhoria
          </p>
          <div className="overflow-x-auto bg-white rounded-xl shadow-sm border">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Tipo de Carga</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Berço</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Permanência (h)</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Vol. Médio/Navio</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Capacidade</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Ocupação</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Limite Recom.</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Utilização</th>
                  <th className="px-4 py-3 text-center font-medium text-gray-600">Situação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {[...(analysis.nao_conteiner || []), ...(analysis.conteiner || [])].map(
                  (r, idx) => (
                    <tr key={idx} className={r.saturado ? 'bg-red-50' : ''}>
                      <td className="px-4 py-2 text-gray-900">{r.perfil_carga}</td>
                      <td className="px-4 py-2 text-gray-600">{r.berco}</td>
                      <td className="px-4 py-2 text-right">{r.mean_ta_h?.toFixed(1) ?? '-'}</td>
                      <td className="px-4 py-2 text-right">{formatNumber(r.mean_lm)}</td>
                      <td className="px-4 py-2 text-right font-medium">
                        {formatNumber(r.c_cais_bruta)}
                      </td>
                      <td className="px-4 py-2 text-right">{r.bor_obs_pct?.toFixed(1) ? `${r.bor_obs_pct?.toFixed(1)}%` : '-'}</td>
                      <td className="px-4 py-2 text-right">{(r.bor_adm * 100).toFixed(0)}%</td>
                      <td className="px-4 py-2 text-right">{r.bur_obs_pct?.toFixed(1) ? `${r.bur_obs_pct?.toFixed(1)}%` : '-'}</td>
                      <td className="px-4 py-2 text-center">
                        {r.saturado ? (
                          <span className="px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium">
                            Congestionado
                          </span>
                        ) : (
                          <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                            Operacional
                          </span>
                        )}
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
