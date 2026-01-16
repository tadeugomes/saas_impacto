import { useEffect, useState } from 'react';
import { FilterBar } from '../../../components/filters/FilterBar';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { ChartCard } from '../../../components/charts/ChartCard';
import { BarChart } from '../../../components/charts/BarChart';
import { PieChart } from '../../../components/charts/PieChart';
import { ExportButton } from '../../../components/common/ExportButton';
import { useFilterStore } from '../../../store/filterStore';
import { indicatorsService } from '../../../api/indicators';

const INDICATORS_INFO = [
  { code: 'IND-2.01', name: 'Carga Total Movimentada', unit: 'Toneladas', desc: 'Soma de carga embarcada e desembarcada', valueField: 'tonelagem_total' },
  { code: 'IND-2.05', name: 'Carga Média por Atracação', unit: 'Toneladas', desc: 'Carga média por atracação', valueField: 'carga_media_atracacao' },
  { code: 'IND-2.06', name: 'Produtividade de Berço', unit: 'Ton/hora', desc: 'Toneladas por hora de operação', valueField: 'produtividade_ton_hora' },
  { code: 'IND-2.10', name: 'Tonelagem Total (Ranking)', unit: 'Toneladas', desc: 'Ranking por tonelagem', valueField: 'tonelagem_total' },
  { code: 'IND-2.11', name: 'Concentração de Carga', unit: 'Toneladas', desc: 'Índice de concentração', valueField: 'tonelagem_total' },
  { code: 'IND-2.12', name: 'Mix de Carga', unit: '%', desc: 'Distribuição por tipo de carga', valueField: 'percentual', isPieChart: true },
  { code: 'IND-2.13', name: 'Sazonalidade', unit: 'Índice', desc: 'Variação mensal da carga', valueField: 'indice_sazonalidade' },
];

function getValueFromData(item: any, valueField: string): number {
  return item[valueField] || 0;
}

function getLabelFromData(item: any): string {
  return item.id_instalacao || item.tipo_carga || item.mes?.toString() || 'N/A';
}

export function Module2View() {
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
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Módulo 2 - Operações de Carga</h1>
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Módulo 2 - Operações de Carga</h1>
          <p className="text-gray-500 mt-1">
            7 indicadores de operações de carga
          </p>
        </div>
        <ExportButton moduleCode="2" />
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
                (ind as any).isPieChart ? (
                  <PieChart
                    labels={indData.data.slice(0, 10).map((d: any) => getLabelFromData(d))}
                    data={indData.data.slice(0, 10).map((d: any) => getValueFromData(d, ind.valueField))}
                    variant="doughnut"
                  />
                ) : (
                  <BarChart
                    labels={indData.data.slice(0, 10).map((d: any) => getLabelFromData(d))}
                    datasets={[{
                      label: ind.unit,
                      data: indData.data.slice(0, 10).map((d: any) => getValueFromData(d, ind.valueField)),
                    }]}
                    yAxisLabel={ind.unit}
                    horizontal
                  />
                )
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
