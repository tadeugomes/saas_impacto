import { useMemo } from 'react';
import { ChartCard } from '../charts/ChartCard';
import { BarChart } from '../charts/BarChart';
import { PieChart } from '../charts/PieChart';
import { formatByType } from '../../utils/numberFormat';

import { getIndicatorFormat } from '../../utils/chartFormats';

type ChartType = 'bar' | 'pie' | 'metric';

interface IndicatorRow {
  label: string;
  value: number;
}

type RawIndicatorRecord = Record<string, unknown>;
type RawIndicatorResponse = { data?: RawIndicatorRecord[] };

interface IndicatorDashboardCardProps {
  title: string;
  description?: string;
  unit?: string;
  isLoading: boolean;
  data?: RawIndicatorResponse | null;
  chartType: ChartType;
  valueField: string;
  labelField?: string;
  fallbackLabel?: string;
  filterText?: string;
  valueAccessor?: (item: RawIndicatorRecord) => unknown;
  labelAccessor?: (item: RawIndicatorRecord) => unknown;
  indicatorCode: string;
  topN?: number;
  tableRows?: number;
}

function parseNumber(value: unknown): number | null {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatDisplayValue(value: number, indicatorCode: string): string {
  const format = getIndicatorFormat(indicatorCode);
  return formatByType(value, format);
}

function dedupeRowsByLabel(rows: IndicatorRow[]): IndicatorRow[] {
  const grouped = new Map<string, number>();
  rows.forEach((row) => {
    const current = grouped.get(row.label) ?? 0;
    grouped.set(row.label, current + row.value);
  });
  return Array.from(grouped.entries()).map(([label, value]) => ({ label, value }));
}

export function IndicatorDashboardCard({
  title,
  description,
  unit,
  isLoading,
  data,
  chartType,
  valueField,
  labelField,
  fallbackLabel = 'N/A',
  filterText = '',
  valueAccessor,
  labelAccessor,
  indicatorCode,
  topN = 10,
  tableRows = 5,
}: IndicatorDashboardCardProps) {
  const rows = useMemo<IndicatorRow[]>(() => {
    const source: RawIndicatorRecord[] = data?.data ?? [];
    const resolvedRows: IndicatorRow[] = [];

    for (const item of source) {
      const rawValue = valueAccessor ? valueAccessor(item) : item?.[valueField];
      const value = parseNumber(rawValue);
      if (value === null) {
        continue;
      }

      const rawLabel = labelAccessor
        ? labelAccessor(item)
        : labelField
          ? item?.[labelField]
          : item?.id_municipio || item?.nome_municipio || item?.id_instalacao;

      const label = rawLabel === undefined || rawLabel === null || rawLabel === ''
        ? fallbackLabel
        : String(rawLabel);
      resolvedRows.push({ label, value });
    }

    const filtered = filterText
      ? resolvedRows.filter((item) => item.label.toLowerCase().includes(filterText.toLowerCase()))
      : resolvedRows;

    const aggregated = dedupeRowsByLabel(filtered);
    return aggregated.sort((a, b) => b.value - a.value);
  }, [data, valueField, labelField, filterText, valueAccessor, labelAccessor, fallbackLabel]);

  const topChartRows = rows.slice(0, topN);
  const topTableRows = rows.slice(0, tableRows);

  const chartValueFormat = getIndicatorFormat(indicatorCode);
  const noData = topChartRows.length === 0;

  return (
    <ChartCard
      title={title}
      description={description}
      unit={unit}
      isLoading={isLoading}
      error={noData ? 'Sem dados para o filtro selecionado.' : undefined}
    >
      {chartType === 'metric' ? (
        <div className="h-64 flex items-center justify-center">
          {topChartRows.length > 0 ? (
            <div className="text-center">
              <p className="text-4xl font-bold text-primary">{formatDisplayValue(topChartRows[0].value, indicatorCode)}</p>
              <p className="text-gray-500 mt-2">Maior valor observado</p>
            </div>
          ) : (
            <div className="text-gray-400">Sem dados disponíveis</div>
          )}
        </div>
      ) : chartType === 'pie' ? (
        <PieChart
          labels={topChartRows.map((row) => row.label)}
          data={topChartRows.map((row) => row.value)}
          variant="doughnut"
        />
      ) : (
        <BarChart
          labels={topChartRows.map((row) => row.label)}
          datasets={[
            {
              label: unit ?? title,
              data: topChartRows.map((row) => row.value),
            },
          ]}
          yAxisLabel={unit || title}
          valueFormat={chartValueFormat}
          horizontal
        />
      )}

      {topTableRows.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs font-semibold text-gray-600 mb-1">Top {topTableRows.length} em ranking</p>
          <div className="overflow-auto">
            <table className="w-full text-xs text-left">
              <thead className="text-gray-500 border-b border-gray-100">
                <tr>
                  <th className="py-2 pr-3 font-medium">Label</th>
                  <th className="py-2 pr-3 font-medium text-right">Valor</th>
                </tr>
              </thead>
              <tbody>
                {topTableRows.map((row) => (
                  <tr key={`${indicatorCode}-${row.label}`} className="border-b border-gray-50 last:border-b-0">
                    <td className="py-2 pr-3">{row.label}</td>
                    <td className="py-2 pr-3 text-right font-mono">{formatDisplayValue(row.value, indicatorCode)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <p className="mt-4 text-xs text-gray-400">Sem dados para renderizar ranking.</p>
      )}
    </ChartCard>
  );
}
