import { BarChart } from '../charts/BarChart';
import { ChartCard } from '../charts/ChartCard';
import { CHART_PALETTE } from '../../styles/chartTheme';
import type { CompositionItem } from '../../types/api';

interface FiscalCompositionChartProps {
  composition: CompositionItem[];
  loading?: boolean;
}

export function FiscalCompositionChart({ composition, loading }: FiscalCompositionChartProps) {
  const sorted = composition.slice(0, 12); // top 12

  const labels = sorted.map((c) => {
    const name = c.porto.replace('Portos do ', 'Portos ').replace('Porto de ', '').replace('Porto do ', '');
    return name.length > 20 ? name.substring(0, 18) + '…' : name;
  });

  const municipalData = sorted.map((c) => c.municipal_r_mi);
  const federalData = sorted.map((c) => c.federal_r_mi);

  const avgMunicipalPct = sorted.length > 0
    ? sorted.reduce((s, c) => s + c.pct_municipal, 0) / sorted.length
    : null;

  return (
    <ChartCard
      title="Split Municipal vs. Federal por Porto"
      description="Proporção média de tributos municipais (ISS+IPTU) vs. federais (PIS/COFINS/IRPJ/CSLL)"
      unit="R$ mi"
      accentColor={CHART_PALETTE.teal}
      isLoading={loading}
    >
      {sorted.length === 0 ? (
        <p className="text-sm text-gray-400 py-8 text-center">Sem dados de composição disponíveis.</p>
      ) : (
        <>
          <BarChart
            labels={labels}
            datasets={[
              {
                label: 'Municipal (ISS+IPTU)',
                data: municipalData,
                backgroundColor: CHART_PALETTE.navy,
              },
              {
                label: 'Federal (PIS/COFINS/IRPJ/CSLL)',
                data: federalData,
                backgroundColor: CHART_PALETTE.teal,
              },
            ]}
            horizontal
            height="h-80"
            yAxisLabel="R$ milhões"
          />
          {avgMunicipalPct !== null && (
            <p className="text-xs text-gray-400 mt-3 text-center">
              Média municipal nos portos com dados: <strong>{avgMunicipalPct.toFixed(1)}%</strong> do total.
              O restante vai para a União via tributos federais.
            </p>
          )}
        </>
      )}
    </ChartCard>
  );
}
