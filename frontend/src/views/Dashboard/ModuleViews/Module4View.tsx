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

const INDICATORS_INFO = [
  { code: 'IND-4.01', name: 'Exportações', unit: 'US$ FOB', desc: 'Valor total das exportações', valueField: 'valor_exportacoes_usd', labelField: 'id_municipio' },
  { code: 'IND-4.02', name: 'Importações', unit: 'US$ FOB', desc: 'Valor total das importações', valueField: 'valor_importacoes_usd', labelField: 'id_municipio' },
  { code: 'IND-4.03', name: 'Balança Comercial', unit: 'US$', desc: 'Saldo comercial (Exp - Imp)', valueField: 'balanca_comercial_usd', labelField: 'id_municipio' },
  { code: 'IND-4.04', name: 'Peso Exportado', unit: 'kg', desc: 'Peso líquido das exportações', valueField: 'peso_liquido_exportacoes_kg', labelField: 'id_municipio' },
  { code: 'IND-4.05', name: 'Peso Importado', unit: 'kg', desc: 'Peso líquido das importações', valueField: 'peso_liquido_importacoes_kg', labelField: 'id_municipio' },
  { code: 'IND-4.10', name: 'Market Share', unit: '%', desc: 'Participação no mercado nacional', valueField: 'market_share_pct', labelField: 'id_municipio' },
];

function getValueFromData(item: any, valueField: string): number {
  return item[valueField] || 0;
}

function getLabelFromData(item: any, labelField: string): string {
  return item.nome_municipio || item[labelField] || item.id_instalacao || 'N/A';
}

export function Module4View() {
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
          <p className="text-gray-500 mt-1">
            6 indicadores de comércio exterior
          </p>
        </div>
        <ExportButton moduleCode="4" />
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
                  labels={indData.data.slice(0, 10).map((d: any) => getLabelFromData(d, ind.labelField))}
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
