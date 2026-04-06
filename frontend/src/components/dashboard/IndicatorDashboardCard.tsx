import { useMemo } from 'react';
import { ChartCard } from '../charts/ChartCard';
import { BarChart } from '../charts/BarChart';
import { PieChart } from '../charts/PieChart';
import { formatByType } from '../../utils/numberFormat';
import { getIndicatorFormat } from '../../utils/chartFormats';
import { MODULE_ACCENT, moduleFromIndicatorCode } from '../../styles/chartTheme';

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
  warnings?: string[];
  topN?: number;
  tableRows?: number;
  error?: string | null;
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
  error,
  warnings,
}: IndicatorDashboardCardProps) {
  const rows = useMemo<IndicatorRow[]>(() => {
    const source: RawIndicatorRecord[] = data?.data ?? [];
    const resolvedRows: IndicatorRow[] = [];

    for (const item of source) {
      const rawValue = valueAccessor ? valueAccessor(item) : item?.[valueField];
      const value = parseNumber(rawValue);
      if (value === null) continue;

      const rawLabel = labelAccessor
        ? labelAccessor(item)
        : labelField
          ? item?.[labelField]
          : item?.id_municipio || item?.nome_municipio || item?.id_instalacao;

      const label =
        rawLabel === undefined || rawLabel === null || rawLabel === ''
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
  const moduleNum = moduleFromIndicatorCode(indicatorCode);
  const accentColor = MODULE_ACCENT[moduleNum] ?? MODULE_ACCENT[1];

  const hasData = topChartRows.length > 0;
  const warningText = warnings && warnings.length > 0 ? warnings.join(' | ') : null;

  const resolvedError: string | null = error
    ?? (!hasData ? (warningText ?? 'Sem dados para o filtro selecionado.') : null);

  const extraInfoText: string | undefined = hasData && warningText ? warningText : undefined;

  return (
    <ChartCard
      title={title}
      description={description}
      unit={unit}
      isLoading={isLoading}
      error={resolvedError ?? undefined}
      extraInfo={extraInfoText}
      accentColor={accentColor}
    >
      {chartType === 'metric' ? (
        <div className="h-64 flex items-center justify-center">
          {topChartRows.length > 0 ? (
            <div className="text-center">
              <p
                className="text-5xl font-extrabold"
                style={{ color: accentColor }}
              >
                {formatDisplayValue(topChartRows[0].value, indicatorCode)}
              </p>
              <p className="text-sm text-gray-500 mt-2 font-medium">{topChartRows[0].label}</p>
              <p className="text-xs text-gray-400 mt-0.5">Maior valor observado</p>
            </div>
          ) : (
            <div className="text-gray-400 text-sm">Sem dados disponíveis</div>
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
              backgroundColor: accentColor,
            },
          ]}
          yAxisLabel={unit || title}
          valueFormat={chartValueFormat}
          horizontal
        />
      )}

      {topChartRows.length > 0 && topTableRows.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">
            Top {topTableRows.length}
          </p>
          <div className="overflow-auto rounded-lg border border-gray-100">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100">
                  <th className="py-2 px-3 font-semibold text-gray-500">#</th>
                  <th className="py-2 px-3 font-semibold text-gray-500">Nome</th>
                  <th className="py-2 px-3 font-semibold text-gray-500 text-right">Valor</th>
                </tr>
              </thead>
              <tbody>
                {topTableRows.map((row, idx) => (
                  <tr
                    key={`${indicatorCode}-${row.label}`}
                    className={`border-b border-gray-50 last:border-b-0 ${
                      idx === 0 ? 'bg-blue-50/60' : idx % 2 === 0 ? 'bg-gray-50/40' : 'bg-white'
                    }`}
                  >
                    <td className="py-2 px-3">
                      {idx === 0 ? (
                        <span
                          className="inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold text-white"
                          style={{ backgroundColor: accentColor }}
                        >
                          1
                        </span>
                      ) : (
                        <span className="text-gray-400">{idx + 1}</span>
                      )}
                    </td>
                    <td className={`py-2 px-3 ${idx === 0 ? 'font-semibold text-gray-800' : 'text-gray-600'}`}>
                      {row.label}
                    </td>
                    <td className={`py-2 px-3 text-right font-mono ${idx === 0 ? 'font-bold' : 'text-gray-600'}`}>
                      {formatDisplayValue(row.value, indicatorCode)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </ChartCard>
  );
}
