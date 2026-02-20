interface ComparisonRow {
  Method: string;
  Estimate: number | null;
  SE: number | null;
  CI_Lower: number | null;
  CI_Upper: number | null;
  P_Value: number | null;
  Significant: string;
  Notes?: string | null;
  [key: string]: unknown;
}

interface ComparisonPayload {
  outcome: string;
  recommendation?: string;
  consistency_assessment?: unknown;
  comparison_table?: ComparisonRow[];
}

function toDisplay(value: unknown): string {
  if (value === null || value === undefined || Number.isNaN(value as number)) {
    return '—';
  }
  if (typeof value === 'number') {
    return value.toFixed(4);
  }
  return String(value);
}

export function MethodComparisonTable({
  items,
}: {
  items: ComparisonPayload[];
}) {
  if (!items.length) {
    return null;
  }

  return (
    <div className="space-y-4">
      {items.map((item) => {
        const rows = item.comparison_table || [];
        return (
          <div key={item.outcome} className="rounded-lg border border-gray-200 p-4">
            <h4 className="font-medium text-sm text-gray-800 mb-3">
              Comparação de métodos: {item.outcome}
            </h4>

            {rows.length > 0 ? (
              <div className="overflow-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-gray-500 border-b">
                    <tr>
                      <th className="py-2 pr-3">Método</th>
                      <th className="py-2 pr-3">Estimate</th>
                      <th className="py-2 pr-3">SE</th>
                      <th className="py-2 pr-3">CI_inf</th>
                      <th className="py-2 pr-3">CI_sup</th>
                      <th className="py-2 pr-3">P-Value</th>
                      <th className="py-2 pr-3">Signif.</th>
                      <th className="py-2 pr-3">Notas</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr key={`${item.outcome}-${row.Method}`} className="border-b last:border-b-0 border-gray-100">
                        <td className="py-2 pr-3 font-medium">{row.Method}</td>
                        <td className="py-2 pr-3 font-mono">{toDisplay(row.Estimate)}</td>
                        <td className="py-2 pr-3 font-mono">{toDisplay(row.SE)}</td>
                        <td className="py-2 pr-3 font-mono">{toDisplay(row.CI_Lower)}</td>
                        <td className="py-2 pr-3 font-mono">{toDisplay(row.CI_Upper)}</td>
                        <td className="py-2 pr-3 font-mono">{toDisplay(row.P_Value)}</td>
                        <td className="py-2 pr-3">{row.Significant}</td>
                        <td className="py-2 pr-3">{row.Notes || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-gray-500">Sem tabela de comparação para este outcome.</p>
            )}

            <div className="mt-3 text-xs text-gray-500">
              <p>Recomendação: {item.recommendation || '—'}</p>
              <p className="mt-1">Consistência: {item.consistency_assessment ? String(item.consistency_assessment) : '—'}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
