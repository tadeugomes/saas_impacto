import { useEffect, useState } from 'react';
import { FilterBar } from '../../../components/filters/FilterBar';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { useFilterStore } from '../../../store/filterStore';
import { indicatorsService } from '../../../api/indicators';
import { IndicatorDashboardCard } from '../../../components/dashboard/IndicatorDashboardCard';
import type { IndicatorResponse } from '../../../types/api';
import { TrendingUp, TrendingDown, DollarSign, BarChart3, Users, Building } from 'lucide-react';

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
  { code: 'IND-8.01', name: 'Taxa Selic Meta', unit: '% a.a.', desc: 'Custo de oportunidade do investidor', chartType: 'metric', valueField: 'selic_meta_aa', labelField: 'data' },
  { code: 'IND-8.02', name: 'IPCA Acumulado 12m', unit: '%', desc: 'Erosão do retorno real', chartType: 'bar', valueField: 'ipca_acumulado_12m', labelField: 'data' },
  { code: 'IND-8.03', name: 'Câmbio PTAX', unit: 'BRL/USD', desc: 'Competitividade exportadora', chartType: 'bar', valueField: 'cambio_ptax_venda', labelField: 'data' },
  { code: 'IND-8.04', name: 'IBC-Br', unit: 'Índice', desc: 'Proxy mensal do PIB', chartType: 'bar', valueField: 'ibc_br', labelField: 'data' },
  { code: 'IND-8.05', name: 'População Municipal', unit: 'Hab.', desc: 'População do município portuário', chartType: 'metric', valueField: 'populacao' },
  { code: 'IND-8.06', name: 'PIB per Capita', unit: 'R$', desc: 'Tamanho da economia local', chartType: 'metric', valueField: 'pib_per_capita_reais' },
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

const MACRO_ICONS: Record<string, typeof TrendingUp> = {
  'IND-8.01': TrendingUp,
  'IND-8.02': TrendingDown,
  'IND-8.03': DollarSign,
  'IND-8.04': BarChart3,
  'IND-8.05': Users,
  'IND-8.06': Building,
};

export function Module8View() {
  const { selectedYear, selectedInstallation } = useFilterStore();
  const [indicators, setIndicators] = useState<IndicatorMap>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      setError(null);

      try {
        const results: IndicatorMap = {};

        await Promise.allSettled(
          INDICATORS_INFO.map(async (ind) => {
            try {
              const resp = await indicatorsService.queryIndicator({
                codigo_indicador: ind.code,
                ano: selectedYear || undefined,
                id_instalacao: selectedInstallation || undefined,
              });
              results[ind.code] = resp;
            } catch {
              results[ind.code] = createEmptyIndicatorResponse(ind.code);
            }
          })
        );

        setIndicators(results);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Erro ao carregar indicadores');
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, [selectedYear, selectedInstallation]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;

  // Extract latest values for the macro summary cards
  const getLatestValue = (code: string, field: string): string => {
    const data = indicators[code]?.data;
    if (!data || data.length === 0) return '—';
    const last = data[data.length - 1];
    const val = last[field];
    if (val === null || val === undefined) return '—';
    if (typeof val === 'number') {
      if (field.includes('populacao')) return val.toLocaleString('pt-BR');
      if (field.includes('pib_per_capita')) return `R$ ${val.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
      return val.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    return String(val);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Contexto Macroeconômico</h1>
          <p className="text-gray-600 mt-1">
            Indicadores BACEN e IBGE para contexto de investimento no setor portuário
          </p>
        </div>
      </div>

      <FilterBar />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {INDICATORS_INFO.slice(0, 4).map((ind) => {
          const Icon = MACRO_ICONS[ind.code] || TrendingUp;
          return (
            <div key={ind.code} className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 bg-emerald-50 rounded-lg flex items-center justify-center">
                  <Icon className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">{ind.name}</p>
                  <p className="text-xs text-gray-400">{ind.desc}</p>
                </div>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {getLatestValue(ind.code, ind.valueField)}
              </p>
              <p className="text-xs text-gray-500 mt-1">{ind.unit}</p>
              <p className="text-xs text-gray-400 mt-1">
                Fonte: {ind.code.startsWith('IND-8.0') && Number(ind.code.slice(-1)) <= 4 ? 'BACEN SGS' : 'IBGE'}
              </p>
            </div>
          );
        })}
      </div>

      {/* Detailed Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {INDICATORS_INFO.map((ind) => (
          <IndicatorDashboardCard
            key={ind.code}
            indicator={indicators[ind.code] || createEmptyIndicatorResponse(ind.code)}
            config={ind}
          />
        ))}
      </div>
    </div>
  );
}
