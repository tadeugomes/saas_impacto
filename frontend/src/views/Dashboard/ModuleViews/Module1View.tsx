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
import type { TempoMedioEsperaData, DistribuicaoTipoNavioData } from '../../../types/indicators';

const INDICATORS_INFO = [
  { code: 'IND-1.01', name: 'Tempo Médio de Espera', unit: 'Horas', desc: 'Tempo entre chegada e atracação' },
  { code: 'IND-1.02', name: 'Tempo Médio em Porto', unit: 'Horas', desc: 'Tempo total no porto' },
  { code: 'IND-1.03', name: 'Tempo Bruto de Atracação', unit: 'Horas', desc: 'Tempo de atracação até desatracação' },
  { code: 'IND-1.04', name: 'Tempo Líquido de Operação', unit: 'Horas', desc: 'Tempo efetivo de operação' },
  { code: 'IND-1.05', name: 'Taxa de Ocupação de Berços', unit: '%', desc: 'Ocupação média dos berços' },
  { code: 'IND-1.06', name: 'Tempo Ocioso Médio', unit: 'Horas', desc: 'Tempo de paralisação' },
  { code: 'IND-1.07', name: 'Arqueação Bruta Média', unit: 'GT', desc: 'Tamanho médio dos navios' },
  { code: 'IND-1.08', name: 'Comprimento Médio', unit: 'Metros', desc: 'Comprimento médio dos navios' },
  { code: 'IND-1.09', name: 'Calado Máximo', unit: 'Metros', desc: 'Maior calado operacional' },
  { code: 'IND-1.10', name: 'Distribuição por Tipo', unit: '%', desc: 'Por tipo de navegação' },
  { code: 'IND-1.11', name: 'Número de Atracações', unit: 'Contagem', desc: 'Total de atracações' },
  { code: 'IND-1.12', name: 'Índice de Paralisação', unit: '%', desc: 'Tempo ocioso / tempo atracado' },
];

export function Module1View() {
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
          })
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
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Módulo 1 - Operações de Navios</h1>
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Módulo 1 - Operações de Navios</h1>
          <p className="text-gray-500 mt-1">
            12 indicadores de operações de navios seguindo padrão UNCTAD
          </p>
        </div>
        <ExportButton moduleCode="1" />
      </div>

      <FilterBar />

      {error && <ErrorAlert message={error} className="mb-6" />}

      {/* Indicators Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* IND-1.01: Tempo Médio de Espera */}
        <ChartCard
          title={INDICATORS_INFO[0].name}
          description={INDICATORS_INFO[0].desc}
          unit={INDICATORS_INFO[0].unit}
          isLoading={isLoading}
          error={indicators['IND-1.01'] ? null : 'Carregando...'}
        >
          {indicators['IND-1.01']?.data && (
            <BarChart
              labels={indicators['IND-1.01'].data.slice(0, 10).map((d: TempoMedioEsperaData) => d.id_instalacao)}
              datasets={[{
                label: 'Horas',
                data: indicators['IND-1.01'].data.slice(0, 10).map((d: TempoMedioEsperaData) => d.tempo_medio_espera_horas),
              }]}
              yAxisLabel="Horas"
              horizontal
            />
          )}
        </ChartCard>

        {/* IND-1.02: Tempo Médio em Porto */}
        <ChartCard
          title={INDICATORS_INFO[1].name}
          description={INDICATORS_INFO[1].desc}
          unit={INDICATORS_INFO[1].unit}
          isLoading={isLoading}
        >
          {indicators['IND-1.02']?.data && (
            <BarChart
              labels={indicators['IND-1.02'].data.slice(0, 10).map((d: any) => d.id_instalacao)}
              datasets={[{
                label: 'Horas',
                data: indicators['IND-1.02'].data.slice(0, 10).map((d: any) => d.tempo_medio_porto_horas),
              }]}
              yAxisLabel="Horas"
              horizontal
            />
          )}
        </ChartCard>

        {/* IND-1.03: Tempo Bruto de Atracação */}
        <ChartCard
          title={INDICATORS_INFO[2].name}
          description={INDICATORS_INFO[2].desc}
          unit={INDICATORS_INFO[2].unit}
                    isLoading={isLoading}
        >
          {indicators['IND-1.03']?.data && (
            <BarChart
              labels={indicators['IND-1.03'].data.slice(0, 10).map((d: any) => d.id_instalacao)}
              datasets={[{
                label: 'Horas',
                data: indicators['IND-1.03'].data.slice(0, 10).map((d: any) => d.tempo_bruto_atracacao_horas),
              }]}
              yAxisLabel="Horas"
              horizontal
            />
          )}
        </ChartCard>

        {/* IND-1.04: Tempo Líquido de Operação */}
        <ChartCard
          title={INDICATORS_INFO[3].name}
          description={INDICATORS_INFO[3].desc}
          unit={INDICATORS_INFO[3].unit}
                    isLoading={isLoading}
        >
          {indicators['IND-1.04']?.data && (
            <BarChart
              labels={indicators['IND-1.04'].data.slice(0, 10).map((d: any) => d.id_instalacao)}
              datasets={[{
                label: 'Horas',
                data: indicators['IND-1.04'].data.slice(0, 10).map((d: any) => d.tempo_liquido_operacao_horas),
              }]}
              yAxisLabel="Horas"
              horizontal
            />
          )}
        </ChartCard>

        {/* IND-1.05: Taxa de Ocupação de Berços */}
        <ChartCard
          title={INDICATORS_INFO[4].name}
          description={INDICATORS_INFO[4].desc}
          unit={INDICATORS_INFO[4].unit}
                    isLoading={isLoading}
        >
          {indicators['IND-1.05']?.data && (
            <BarChart
              labels={indicators['IND-1.05'].data.slice(0, 10).map((d: any) => d.id_instalacao)}
              datasets={[{
                label: 'Taxa (%)',
                data: indicators['IND-1.05'].data.slice(0, 10).map((d: any) => d.taxa_ocupacao_percentual),
              }]}
              yAxisLabel="%"
              horizontal
            />
          )}
        </ChartCard>

        {/* IND-1.06: Tempo Ocioso Médio */}
        <ChartCard
          title={INDICATORS_INFO[5].name}
          description={INDICATORS_INFO[5].desc}
          unit={INDICATORS_INFO[5].unit}
                    isLoading={isLoading}
        >
          {indicators['IND-1.06']?.data && (
            <BarChart
              labels={indicators['IND-1.06'].data.slice(0, 10).map((d: any) => d.id_instalacao)}
              datasets={[{
                label: 'Horas',
                data: indicators['IND-1.06'].data.slice(0, 10).map((d: any) => d.tempo_ocioso_medio_horas),
              }]}
              yAxisLabel="Horas"
              horizontal
            />
          )}
        </ChartCard>

        {/* IND-1.07: Arqueação Bruta Média */}
        <ChartCard
          title={INDICATORS_INFO[6].name}
          description={INDICATORS_INFO[6].desc}
          unit={INDICATORS_INFO[6].unit}
                    isLoading={isLoading}
        >
          {indicators['IND-1.07']?.data && (
            <BarChart
              labels={indicators['IND-1.07'].data.slice(0, 10).map((d: any) => d.id_instalacao)}
              datasets={[{
                label: 'GT',
                data: indicators['IND-1.07'].data.slice(0, 10).map((d: any) => d.arqueacao_bruta_media),
              }]}
              yAxisLabel="GT"
              horizontal
            />
          )}
        </ChartCard>

        {/* IND-1.08: Comprimento Médio */}
        <ChartCard
          title={INDICATORS_INFO[7].name}
          description={INDICATORS_INFO[7].desc}
          unit={INDICATORS_INFO[7].unit}
                    isLoading={isLoading}
        >
          {indicators['IND-1.08']?.data && (
            <BarChart
              labels={indicators['IND-1.08'].data.slice(0, 10).map((d: any) => d.id_instalacao)}
              datasets={[{
                label: 'Metros',
                data: indicators['IND-1.08'].data.slice(0, 10).map((d: any) => d.comprimento_medio_metros),
              }]}
              yAxisLabel="Metros"
              horizontal
            />
          )}
        </ChartCard>

        {/* IND-1.09: Calado Máximo */}
        <ChartCard
          title={INDICATORS_INFO[8].name}
          description={INDICATORS_INFO[8].desc}
          unit={INDICATORS_INFO[8].unit}
                    isLoading={isLoading}
        >
          {indicators['IND-1.09']?.data && indicators['IND-1.09'].data.length > 0 ? (
            <div className="h-64 flex items-center justify-center">
              <div className="text-center">
                <p className="text-4xl font-bold text-primary">
                  {indicators['IND-1.09'].data[0].calado_maximo_metros}m
                </p>
                <p className="text-gray-500 mt-2">Calado Máximo Operacional</p>
              </div>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              Dados não disponíveis
            </div>
          )}
        </ChartCard>

        {/* IND-1.10: Distribuição por Tipo (Pie Chart) */}
        <ChartCard
          title={INDICATORS_INFO[9].name}
          description={INDICATORS_INFO[9].desc}
          unit={INDICATORS_INFO[9].unit}
                    isLoading={isLoading}
        >
          {indicators['IND-1.10']?.data && (
            <PieChart
              labels={[...new Set(indicators['IND-1.10'].data.map((d: DistribuicaoTipoNavioData) => d.tipo_navegacao))] as string[]}
              data={[...new Set(indicators['IND-1.10'].data.map((d: DistribuicaoTipoNavioData) => d.qtd_atracacoes))] as number[]}
              variant="doughnut"
            />
          )}
        </ChartCard>

        {/* IND-1.11: Número de Atracações */}
        <ChartCard
          title={INDICATORS_INFO[10].name}
          description={INDICATORS_INFO[10].desc}
          unit={INDICATORS_INFO[10].unit}
                    isLoading={isLoading}
        >
          {indicators['IND-1.11']?.data && (
            <BarChart
              labels={indicators['IND-1.11'].data.slice(0, 10).map((d: any) => d.id_instalacao)}
              datasets={[{
                label: 'Atracações',
                data: indicators['IND-1.11'].data.slice(0, 10).map((d: any) => d.total_atracacoes),
              }]}
              yAxisLabel="Contagem"
              horizontal
            />
          )}
        </ChartCard>

        {/* IND-1.12: Índice de Paralisação */}
        <ChartCard
          title={INDICATORS_INFO[11].name}
          description={INDICATORS_INFO[11].desc}
          unit={INDICATORS_INFO[11].unit}
                    isLoading={isLoading}
        >
          {indicators['IND-1.12']?.data && (
            <BarChart
              labels={indicators['IND-1.12'].data.slice(0, 10).map((d: any) => d.id_instalacao)}
              datasets={[{
                label: '%',
                data: indicators['IND-1.12'].data.slice(0, 10).map((d: any) => d.indice_paralisacao_percentual),
              }]}
              yAxisLabel="%"
              horizontal
            />
          )}
        </ChartCard>
      </div>
    </div>
  );
}
