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
  { code: 'IND-3.01', name: 'Empregos Portuários', unit: 'Empregos', desc: 'Total de empregos no setor portuário (RAIS)', valueField: 'empregos_portuarios' },
  { code: 'IND-3.02', name: 'Paridade de Gênero', unit: '%', desc: 'Percentual de mulheres no setor portuário', valueField: 'percentual_feminino' },
  { code: 'IND-3.04', name: 'Taxa Emprego Temporário', unit: '%', desc: 'Percentual de contratos temporários', valueField: 'taxa_temporario' },
  { code: 'IND-3.05', name: 'Salário Médio', unit: 'R$', desc: 'Remuneração média mensal', valueField: 'salario_medio' },
  { code: 'IND-3.06', name: 'Massa Salarial', unit: 'R$', desc: 'Massa salarial anual estimada', valueField: 'massa_salarial_anual' },
  { code: 'IND-3.12', name: 'Participação Emprego Local', unit: '%', desc: 'Participação do setor portuário no emprego total do município', valueField: 'participacao_emprego_local' },
];

function getValueFromData(item: any, valueField: string): number {
  return item[valueField] ?? item.valor ?? item.total ?? 0;
}

function getLabelFromData(item: any): string {
  return item.nome_municipio || item.municipio || item.id_municipio || item.id_instalacao || 'N/A';
}

export function Module3View() {
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
          <p className="text-gray-500 mt-1">
            6 indicadores de recursos humanos
          </p>
        </div>
        <ExportButton moduleCode="3" />
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
