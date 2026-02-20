import { useEffect, useState } from 'react';
import { FilterBar } from '../../../components/filters/FilterBar';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { ChartCard } from '../../../components/charts/ChartCard';
import { BarChart } from '../../../components/charts/BarChart';
import { ExportButton } from '../../../components/common/ExportButton';
import { useFilterStore } from '../../../store/filterStore';
import { indicatorsService } from '../../../api/indicators';
import { getIndicatorFormat } from '../../../utils/chartFormats';
import type { IndicatorResponse } from '../../../types/api';

const INDICATORS_INFO = [
  { code: 'IND-6.01', name: 'Arrecadação ICMS', unit: 'R$', desc: 'Total arrecadado de ICMS no município', valueField: 'arrecadacao_icms' },
  { code: 'IND-6.02', name: 'Arrecadação ISS', unit: 'R$', desc: 'Total arrecadado de ISS no município', valueField: 'arrecadacao_iss' },
  { code: 'IND-6.03', name: 'Receita Total', unit: 'R$', desc: 'Receita total municipal (FINBRA)', valueField: 'receita_total' },
  { code: 'IND-6.04', name: 'Receita per Capita', unit: 'R$/hab', desc: 'Receita municipal por habitante', valueField: 'receita_per_capita' },
  { code: 'IND-6.06', name: 'ICMS por Tonelada', unit: 'R$/t', desc: 'ICMS arrecadado por tonelada movimentada', valueField: 'icms_por_tonelada' },
];

type IndicatorRow = Record<string, unknown>;
type ModuleIndicatorResponse = IndicatorResponse<IndicatorRow>;
type IndicatorMap = Record<string, ModuleIndicatorResponse>;

const createEmptyIndicatorResponse = (codigoIndicador: string): ModuleIndicatorResponse => ({
  codigo_indicador: codigoIndicador,
  nome: codigoIndicador,
  unidade: '',
  unctad: false,
  data: [],
});

function getValueFromData(item: IndicatorRow, valueField: string): number {
  const fieldValue = item[valueField];
  if (typeof fieldValue === 'number') {
    return fieldValue;
  }
  const fallbackValue = item.valor ?? item.total;
  if (typeof fallbackValue === 'number') {
    return fallbackValue;
  }
  return 0;
}

function getLabelFromData(item: IndicatorRow): string {
  return (
    (typeof item.nome_municipio === 'string' && item.nome_municipio) ||
    (typeof item.id_municipio === 'string' && item.id_municipio) ||
    (typeof item.porto === 'string' && item.porto) ||
    (typeof item.id_instalacao === 'string' && item.id_instalacao) ||
    'N/A'
  );
}

export function Module6View() {
  const { selectedYear, selectedInstallation } = useFilterStore();
  const [indicators, setIndicators] = useState<IndicatorMap>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchIndicators = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const promises = INDICATORS_INFO.map((ind) =>
          indicatorsService.queryIndicator<IndicatorRow>({
            codigo_indicador: ind.code,
            params: {
              ano: selectedYear,
              id_instalacao: selectedInstallation || undefined
            },
          }).catch(() => createEmptyIndicatorResponse(ind.code))
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

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Módulo 6 - Finanças Públicas</h1>
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Módulo 6 - Finanças Públicas</h1>
          <p className="text-gray-500 mt-1">
            5 indicadores de finanças públicas
          </p>
        </div>
        <ExportButton moduleCode="6" />
      </div>

      <FilterBar />

      {error && <ErrorAlert message={error} className="mb-6" />}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {INDICATORS_INFO.map((ind) => (
          <ChartCard
            key={ind.code}
            title={ind.name}
            description={ind.desc}
            unit={ind.unit}
            isLoading={isLoading}
          >
            {indicators[ind.code]?.data && indicators[ind.code].data.length > 0 ? (
              <BarChart
                labels={indicators[ind.code].data.slice(0, 10).map((d: IndicatorRow) => getLabelFromData(d))}
                datasets={[{
                  label: ind.unit,
                  data: indicators[ind.code].data.slice(0, 10).map((d: IndicatorRow) => getValueFromData(d, ind.valueField || '')),
                }]}
                yAxisLabel={ind.unit}
                horizontal
                valueFormat={getIndicatorFormat(ind.code)}
              />
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-400">
                Dados não disponíveis
              </div>
            )}
          </ChartCard>
        ))}
      </div>
    </div>
  );
}
