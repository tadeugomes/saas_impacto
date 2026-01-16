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

// Note: These indicators currently have NO DATA in the database
const INDICATORS_INFO = [
  { code: 'IND-5.01', name: 'PIB Municipal', unit: 'R$', desc: 'PIB Total do Município', valueField: 'pib_municipal' },
  { code: 'IND-5.02', name: 'PIB per Capita', unit: 'R$/hab', desc: 'PIB per capita do município', valueField: 'pib_per_capita' },
  { code: 'IND-5.03', name: 'População', unit: 'Hab', desc: 'População municipal estimada', valueField: 'populacao' },
  { code: 'IND-5.06', name: 'Intensidade Portuária', unit: 'ton/R$', desc: 'Razão Tonelada/PIB', valueField: 'intensidade_portuaria' },
  { code: 'IND-5.11', name: 'Crescimento Tonelagem', unit: '%', desc: 'Variação anual da tonelagem', valueField: 'crescimento_tonelagem_pct' },
];

function getValueFromData(item: any, valueField: string): number {
  return item[valueField] ?? item.valor ?? item.total ?? 0;
}

function getLabelFromData(item: any): string {
  return item.nome_municipio || item.id_municipio || item.id_instalacao || 'N/A';
}

export function Module5View() {
  const { selectedYear, selectedInstallation } = useFilterStore();
  const [indicators, setIndicators] = useState<Record<string, any>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchIndicators = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const promises = INDICATORS_INFO.map((ind) =>
          indicatorsService.queryIndicator({
            codigo_indicador: ind.code,
            params: {
              ano: selectedYear,
              id_instalacao: selectedInstallation || undefined
            },
          }).catch(() => ({ data: [] }))
        );
        const results = await Promise.all(promises);
        const mapped: Record<string, any> = {};
        results.forEach((result, i) => {
          mapped[INDICATORS_INFO[i].code] = result;
        });
        setIndicators(mapped);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Erro ao carregar indicadores');
      } finally {
        setIsLoading(false);
      }
    };

    fetchIndicators();
  }, [selectedYear, selectedInstallation]);

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Módulo 5 - Impacto Econômico</h1>
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Módulo 5 - Impacto Econômico Regional</h1>
          <p className="text-gray-500 mt-1">
            5 indicadores de impacto econômico regional
          </p>
        </div>
        <ExportButton moduleCode="5" />
      </div>

      <FilterBar />

      {error && <ErrorAlert message={error} className="mb-6" />}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {INDICATORS_INFO.map((ind) => {
          const indData = indicators[ind.code];
          const hasData = indData?.data && indData.data.length > 0;

          return (
            <ChartCard
              key={ind.code}
              title={ind.name}
              description={ind.desc}
              unit={ind.unit}
              isLoading={isLoading}
            >
              {hasData ? (
                <BarChart
                  labels={indData.data.slice(0, 10).map((d: any) => getLabelFromData(d))}
                  datasets={[{
                    label: ind.unit,
                    data: indData.data.slice(0, 10).map((d: any) => getValueFromData(d, ind.valueField)),
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
          );
        })}
      </div>
    </div>
  );
}
