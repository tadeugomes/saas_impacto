import { LineChart } from '../charts/LineChart';
import { formatDecimal } from '../../utils/numberFormat';

interface EventStudyPoint {
  rel_time: number;
  coef: number;
  se?: number | null;
  ci_lower?: number | null;
  ci_upper?: number | null;
  pvalue?: number | null;
  p_value?: number | null;
  period?: string;
}

interface EventStudyChartProps {
  outcome: string;
  outcomeLabel?: string;
  coefficients: EventStudyPoint[];
}

interface ParsedEventStudyPoint {
  relTime: number;
  coef: number;
  se: number | null;
  ciLower: number | null;
  ciUpper: number | null;
  pValue: number | null;
  significant: boolean | null;
  isReference: boolean;
}

function parseNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === 'string') {
    const sanitized = value.trim().replace(/[^0-9eE.+\-_,]/g, '').replace(/_/g, '');
    if (!sanitized) {
      return null;
    }

    const hasComma = sanitized.includes(',');
    const hasDot = sanitized.includes('.');
    let normalized: string;
    if (hasComma && hasDot) {
      const lastComma = sanitized.lastIndexOf(',');
      const lastDot = sanitized.lastIndexOf('.');
      normalized =
        lastComma > lastDot ? sanitized.replace(/\./g, '').replace(',', '.') : sanitized.replace(/,/g, '');
    } else if (hasComma) {
      normalized = sanitized.replace(',', '.');
    } else {
      normalized = sanitized;
    }

    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

function formatRelTime(relTime: number): string {
  return relTime >= 0 ? `+${relTime}` : String(relTime);
}

function isSignificant(pValue: number | null): boolean | null {
  if (pValue === null) {
    return null;
  }

  return pValue < 0.05;
}

export function EventStudyChart({ outcome, outcomeLabel, coefficients }: EventStudyChartProps) {
  const points = coefficients
    .map((point) => {
      const relTime = parseNumber(point.rel_time);
      const coef = parseNumber(point.coef);
      if (relTime === null || coef === null) {
        return null;
      }

      return {
        relTime,
        coef,
        se: parseNumber(point.se),
        ciLower: parseNumber(point.ci_lower),
        ciUpper: parseNumber(point.ci_upper),
        pValue: parseNumber(point.pvalue ?? point.p_value),
        significant: isSignificant(parseNumber(point.pvalue ?? point.p_value)),
        isReference: point.period === 'reference',
      } as ParsedEventStudyPoint;
    })
    .filter((point): point is ParsedEventStudyPoint => point !== null)
    .sort((a, b) => a.relTime - b.relTime);

  if (!points.length) {
    return <div className="text-sm text-gray-500">Não há pontos válidos para Event Study.</div>;
  }

  const labels = points.map((point) => `t=${formatRelTime(point.relTime)}`);
  const lowerBand = points.map((point) => point.ciLower);
  const upperBand = points.map((point) => point.ciUpper);
  const significantData = points.map((point) => (point.significant ? point.coef : null));
  const nonSignificantData = points.map((point) =>
    point.significant === false ? point.coef : null,
  );
  const zeroLine = points.map(() => 0);
  const significantCount = points.filter((point) => point.significant).length;
  const significantCount10 = points.filter(
    (point) => (point.pValue !== null ? point.pValue < 0.10 : false),
  ).length;
  const postReference = points.filter((point) => point.relTime >= 0 && !point.isReference);
  const referenceCount = postReference.length;
  const postAverage = referenceCount
    ? postReference.reduce((sum, point) => sum + point.coef, 0) / referenceCount
    : null;

  const prePeriods = points.filter((point) => point.relTime < 0).length;
  const postPeriods = points.filter((point) => point.relTime >= 0).length;
  const referenceLabel = points.find((point) => point.isReference) ? 'incluindo referência t=-1' : '';
  const eventSummary = [
    `Períodos pré: ${prePeriods}`,
    `Pós: ${postPeriods}${referenceLabel}`,
    `signif. (5%): ${significantCount}/${points.length}`,
    `signif. (10%): ${significantCount10}/${points.length}`,
  ].join(' | ');
  const postSummary =
    referenceCount > 0 && postAverage !== null
      ? `Média pós-tratamento (sem referência): ${formatDecimal(postAverage, 6)}`
      : 'Sem períodos pós-tratamento disponíveis na janela informada.';

  return (
    <div className="space-y-2">
      <p className="text-xs text-gray-500">Evento: {outcomeLabel || outcome}</p>
      <p className="text-xs text-gray-600">{eventSummary}</p>
      <p className="text-xs text-gray-700">{postSummary}</p>
      <div className="h-64">
        <LineChart
          labels={labels}
          datasets={[
            {
              label: 'Referência (0)',
              data: zeroLine,
              borderColor: '#6b7280',
              backgroundColor: '#6b728022',
              fill: false,
              borderDash: [6, 4],
              pointRadius: 0,
            },
            {
              label: 'CI superior',
              data: upperBand,
              borderColor: '#d97706',
              backgroundColor: '#d9770618',
              borderDash: [4, 4],
              pointRadius: 0,
              fill: false,
            },
            {
              label: 'CI inferior',
              data: lowerBand,
              borderColor: '#d97706',
              backgroundColor: '#d9770618',
              borderDash: [4, 4],
              pointRadius: 0,
              fill: false,
            },
              {
                label: 'Coeficiente (p < 0,05)',
                data: significantData,
                borderColor: '#10b981',
                backgroundColor: '#10b98133',
                fill: false,
                pointRadius: 5,
              },
            {
              label: 'Coeficiente (p ≥ 0,05)',
              data: nonSignificantData,
              borderColor: '#3b82f6',
              backgroundColor: '#3b82f633',
                fill: false,
                pointRadius: 3,
                pointStyle: 'rectRot',
              },
              ...(points.some((point) => point.isReference)
                ? [
                    {
                      label: 'Período referência',
                      data: points.map((point) => (point.isReference ? point.coef : null)),
                      borderColor: '#7c3aed',
                      backgroundColor: '#7c3aed33',
                      fill: false,
                      pointRadius: 5,
                      pointStyle: 'triangle',
                    },
                  ]
                : []),
            ]}
            yAxisLabel="Coeficiente"
            yAxisFormat="decimal6"
            yAxisBeginAtZero={false}
            title={`Event study (${outcomeLabel || outcome})`}
        />
      </div>

      <details className="text-sm">
        <summary className="text-gray-600 cursor-pointer">Ver pontos e IC95%</summary>
        <div className="mt-2 max-h-44 overflow-auto text-xs">
          <table className="min-w-full text-left">
            <thead className="text-gray-500 border-b border-gray-100">
              <tr>
                <th className="py-1 pr-4">Rel. time</th>
                <th className="py-1 pr-4">Coef</th>
                <th className="py-1 pr-4">SE</th>
                <th className="py-1 pr-4">CI inf.</th>
                <th className="py-1 pr-4">CI sup.</th>
                <th className="py-1 pr-4">Significância (10%)</th>
                <th className="py-1 pr-4">P-valor</th>
              </tr>
            </thead>
            <tbody>
              {points.map((point) => (
                <tr key={`${point.relTime}-${point.coef}`} className="border-b border-gray-50">
                  <td className="py-1 pr-4 font-mono">{point.relTime}</td>
                  <td className="py-1 pr-4 font-mono">{formatDecimal(point.coef, 6)}</td>
                  <td className="py-1 pr-4 font-mono">
                    {point.se === null ? '—' : formatDecimal(point.se, 6)}
                  </td>
                  <td className="py-1 pr-4 font-mono">
                    {point.ciLower === null ? '—' : formatDecimal(point.ciLower, 6)}
                  </td>
                  <td className="py-1 pr-4 font-mono">
                    {point.ciUpper === null ? '—' : formatDecimal(point.ciUpper, 6)}
                  </td>
                  <td className="py-1 pr-4 font-mono">
                    {point.significant === null ? '—' : point.significant ? 'Sim' : 'Não'}
                  </td>
                  <td className="py-1 pr-4 font-mono">
                    {point.pValue === null ? '—' : formatDecimal(point.pValue, 6)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
