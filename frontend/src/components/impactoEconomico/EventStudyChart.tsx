import { LineChart } from '../charts/LineChart';

interface EventStudyPoint {
  rel_time: number;
  coef: number;
  se?: number | null;
  ci_lower?: number | null;
  ci_upper?: number | null;
}

interface EventStudyChartProps {
  outcome: string;
  coefficients: EventStudyPoint[];
}

export function EventStudyChart({ outcome, coefficients }: EventStudyChartProps) {
  const normalized = coefficients
    .map((point) => ({
      ...point,
      coef: typeof point.coef === 'number' && Number.isFinite(point.coef) ? point.coef : 0,
    }))
    .sort((a, b) => a.rel_time - b.rel_time);

  const labels = normalized.map((point) => `t=${point.rel_time >= 0 ? `+${point.rel_time}` : point.rel_time}`);
  const values = normalized.map((point) => point.coef);

  return (
    <div className="space-y-2">
      <p className="text-xs text-gray-500">Evento: {outcome}</p>
      <div className="h-64">
        <LineChart
          labels={labels}
          datasets={[
            {
              label: 'coef',
              data: values,
              borderColor: '#3b82f6',
              backgroundColor: '#3b82f620',
              fill: false,
            },
          ]}
          yAxisLabel="Coeficiente"
          title={`Event study (${outcome})`}
        />
      </div>

      {normalized.length > 0 && (
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
                </tr>
              </thead>
              <tbody>
                {normalized.map((point) => (
                  <tr key={`${point.rel_time}-${point.coef}`} className="border-b border-gray-50">
                    <td className="py-1 pr-4 font-mono">{point.rel_time}</td>
                    <td className="py-1 pr-4 font-mono">
                      {typeof point.coef === 'number' ? point.coef.toFixed(4) : '—'}
                    </td>
                    <td className="py-1 pr-4 font-mono">
                      {typeof point.se === 'number' ? point.se.toFixed(4) : '—'}
                    </td>
                    <td className="py-1 pr-4 font-mono">
                      {typeof point.ci_lower === 'number' ? point.ci_lower.toFixed(4) : '—'}
                    </td>
                    <td className="py-1 pr-4 font-mono">
                      {typeof point.ci_upper === 'number' ? point.ci_upper.toFixed(4) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </div>
  );
}
