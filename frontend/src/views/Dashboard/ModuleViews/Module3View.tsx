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
  { code: 'IND-3.01', name: 'Empregos Portuários', unit: 'Empregos', desc: 'Total de empregos no setor portuário (RAIS)', chartType: 'bar', valueField: 'empregos_portuarios', labelField: 'id_municipio' },
  { code: 'IND-3.02', name: 'Paridade de Gênero', unit: '%', desc: 'Percentual de mulheres no setor portuário', chartType: 'bar', valueField: 'percentual_feminino', labelField: 'id_municipio' },
  { code: 'IND-3.04', name: 'Taxa Emprego Temporário', unit: '%', desc: 'Percentual de contratos temporários', chartType: 'bar', valueField: 'taxa_temporario', labelField: 'id_municipio' },
  { code: 'IND-3.05', name: 'Salário Médio', unit: 'R$', desc: 'Remuneração média mensal', chartType: 'bar', valueField: 'salario_medio', labelField: 'id_municipio' },
  { code: 'IND-3.06', name: 'Massa Salarial', unit: 'R$', desc: 'Massa salarial anual estimada', chartType: 'bar', valueField: 'massa_salarial_anual', labelField: 'id_municipio' },
  { code: 'IND-3.12', name: 'Participação Emprego Local', unit: '%', desc: 'Participação do setor portuário no emprego total do município', chartType: 'bar', valueField: 'participacao_emprego_local', labelField: 'id_municipio' },
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

export function Module3View() {
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
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Módulo 3 - Recursos Humanos</h1>
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Módulo 3 - Recursos Humanos</h1>
          <p className="text-gray-500 mt-1">6 indicadores de recursos humanos</p>
        </div>
        <ExportButton moduleCode="3" />
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
