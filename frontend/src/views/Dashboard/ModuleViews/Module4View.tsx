import { useEffect, useMemo, useState } from 'react';
import { FilterBar } from '../../../components/filters/FilterBar';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { ExportButton } from '../../../components/common/ExportButton';
import { useFilterStore } from '../../../store/filterStore';
import { indicatorsService } from '../../../api/indicators';
import { IndicatorDashboardCard } from '../../../components/dashboard/IndicatorDashboardCard';
import type { IndicatorResponse } from '../../../types/api';

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
  { code: 'IND-4.01', name: 'Exportações', unit: 'US$ FOB', desc: 'Valor total das exportações', chartType: 'bar', valueField: 'valor_exportacoes_usd', labelField: 'id_municipio' },
  { code: 'IND-4.02', name: 'Importações', unit: 'US$ FOB', desc: 'Valor total das importações', chartType: 'bar', valueField: 'valor_importacoes_usd', labelField: 'id_municipio' },
  { code: 'IND-4.03', name: 'Balança Comercial', unit: 'US$', desc: 'Saldo comercial (Exp - Imp)', chartType: 'bar', valueField: 'balanca_comercial_usd', labelField: 'id_municipio' },
  { code: 'IND-4.04', name: 'Peso Exportado', unit: 'kg', desc: 'Peso líquido das exportações', chartType: 'bar', valueField: 'peso_liquido_exportacoes_kg', labelField: 'id_municipio' },
  { code: 'IND-4.05', name: 'Peso Importado', unit: 'kg', desc: 'Peso líquido das importações', chartType: 'bar', valueField: 'peso_liquido_importacoes_kg', labelField: 'id_municipio' },
  { code: 'IND-4.10', name: 'Market Share', unit: '%', desc: 'Participação no mercado nacional', chartType: 'bar', valueField: 'market_share_pct', labelField: 'id_municipio' },
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

export function Module4View() {
  const { selectedYear, selectedInstallation } = useFilterStore();
  const [indicators, setIndicators] = useState<IndicatorMap>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tableSearch, setTableSearch] = useState('');
  const [selectedIndicator, setSelectedIndicator] = useState('all');

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
        const errorMessage = errorResponse?.response?.data?.detail || 'Erro ao carregar indicadores';
        setError(typeof errorMessage === 'string' ? errorMessage : 'Erro ao carregar indicadores');
      } finally {
        setIsLoading(false);
      }
    };

    fetchIndicators();
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
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Módulo 4 - Comércio Exterior</h1>
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Módulo 4 - Comércio Exterior</h1>
          <p className="text-gray-500 mt-1">6 indicadores de comércio exterior</p>
        </div>
        <ExportButton moduleCode="4" />
      </div>

      <FilterBar />

      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
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

      {error && <ErrorAlert message={error} className="mb-6" />}

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
    </div>
  );
}
