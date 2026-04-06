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
}

const INDICATORS_INFO: IndicatorConfig[] = [
  {
    code: 'IND-12.01',
    name: 'Capacidade Bruta do Cais',
    unit: 't/ano ou TEU/ano',
    desc: 'Capacidade via Eq. 1b com BOR admissível UNCTAD',
    chartType: 'bar',
    valueField: 'c_cais_bruta',
    labelField: 'perfil_carga',
  },
  {
    code: 'IND-12.02',
    name: 'BOR Observado vs. Admissível',
    unit: '%',
    desc: 'Taxa de Ocupação de Berço (sinal de saturação)',
    chartType: 'bar',
    valueField: 'bor_obs_pct',
    labelField: 'perfil_carga',
  },
  {
    code: 'IND-12.03',
    name: 'BUR — Taxa de Utilização',
    unit: '%',
    desc: 'Movimentação realizada / Capacidade teórica',
    chartType: 'bar',
    valueField: 'bur_obs_pct',
    labelField: 'perfil_carga',
  },
  {
    code: 'IND-12.04',
    name: 'Lote Médio por Atracação (IQR)',
    unit: 't ou TEU',
    desc: 'Lm depurado por filtro IQR (parâmetro da Eq. 1b)',
    chartType: 'bar',
    valueField: 'mean_lm',
    labelField: 'perfil_carga',
  },
  {
    code: 'IND-12.05',
    name: 'Tempo Médio Atracado (IQR)',
    unit: 'Horas',
    desc: 'Ta depurado por IQR',
    chartType: 'bar',
    valueField: 'mean_ta_h',
    labelField: 'perfil_carga',
  },
  {
    code: 'IND-12.06',
    name: 'Capacidade Alocada por Perfil',
    unit: 't/ano ou TEU/ano',
    desc: 'Capacidade por mix de carga (fração de tempo)',
    chartType: 'pie',
    valueField: 'c_alocada',
    labelField: 'perfil_carga',
  },
  {
    code: 'IND-12.08',
    name: 'Folga Operacional',
    unit: 't ou TEU',
    desc: 'Diferença entre capacidade e demanda observada',
    chartType: 'bar',
    valueField: 'folga_operacional',
    labelField: 'perfil_carga',
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
  };
  parametros: Record<string, unknown>;
  config_terminal?: {
    fonte: string;
    nome_terminal: string | null;
  };
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
          setError('Erro ao carregar indicadores de capacidade');
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
          Selecione uma instalação para analisar a capacidade portuária.
        </div>
      )}

      {error && <ErrorAlert message={error} className="mt-4 mb-6" />}

      {/* Summary Cards */}
      {consolidacao && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-sm border p-4">
            <div className="text-sm text-gray-500">Capacidade Total (Cais)</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">
              {formatNumber(consolidacao.c_cais_total)}
            </div>
            <div className="text-xs text-gray-400 mt-1">t/ano (todos os perfis)</div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border p-4">
            <div className="text-sm text-gray-500">Capacidade Sistêmica</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">
              {formatNumber(consolidacao.c_sistema)}
            </div>
            <div className="text-xs text-gray-400 mt-1">
              min(cais, arm, hint) = {consolidacao.c_sistema === consolidacao.c_cais_total ? 'cais' : consolidacao.gargalo}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border p-4">
            <div className="text-sm text-gray-500">Gargalo</div>
            <div className={`text-2xl font-bold mt-1 ${
              consolidacao.gargalo === 'cais' ? 'text-amber-600' : 'text-red-600'
            }`}>
              {consolidacao.gargalo === 'cais' ? 'Cais' :
               consolidacao.gargalo === 'armazenagem' ? 'Armazenagem' :
               consolidacao.gargalo === 'hinterland' ? 'Hinterlândia' : '-'}
            </div>
            <div className="text-xs text-gray-400 mt-1">
              Subsistema mais restritivo
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border p-4">
            <div className="text-sm text-gray-500">Perfis Analisados</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">
              {consolidacao.n_perfis}
            </div>
            <div className="text-xs text-gray-400 mt-1">
              Fonte: {analysis?.config_terminal?.fonte === 'config' ? 'Config terminal' : 'Parâmetros default'}
            </div>
          </div>
        </div>
      )}

      {/* Saturation Alerts */}
      {analysis && (
        <div className="mb-6">
          {[...(analysis.nao_conteiner || []), ...(analysis.conteiner || [])]
            .filter((r) => r.saturado)
            .map((r, idx) => (
              <div
                key={idx}
                className="p-3 bg-red-50 border border-red-200 rounded-lg mb-2 flex items-center gap-2"
              >
                <span className="text-red-500 font-semibold text-sm">SATURADO</span>
                <span className="text-red-700 text-sm">
                  {r.perfil_carga} no berço {r.berco} — BOR obs {r.bor_obs_pct?.toFixed(1)}% &gt; BOR adm {(r.bor_adm * 100).toFixed(0)}%
                </span>
              </div>
            ))}
        </div>
      )}

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
          />
        ))}
      </div>

      {/* Operational Parameters Table */}
      {analysis && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Parâmetros Operacionais (IQR-filtrados)
          </h2>
          <div className="overflow-x-auto bg-white rounded-xl shadow-sm border">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Perfil</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Berço</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Ta (h)</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Lm</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">C_cais</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">BOR obs %</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">BOR adm %</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">BUR %</th>
                  <th className="px-4 py-3 text-center font-medium text-gray-600">Status</th>
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
                      <td className="px-4 py-2 text-right">{r.bor_obs_pct?.toFixed(1) ?? '-'}</td>
                      <td className="px-4 py-2 text-right">{(r.bor_adm * 100).toFixed(0)}</td>
                      <td className="px-4 py-2 text-right">{r.bur_obs_pct?.toFixed(1) ?? '-'}</td>
                      <td className="px-4 py-2 text-center">
                        {r.saturado ? (
                          <span className="px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium">
                            Saturado
                          </span>
                        ) : (
                          <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                            OK
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
