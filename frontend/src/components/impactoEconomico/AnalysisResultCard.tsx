import { useMemo } from 'react';
import { Calendar, Clock, FileDown, Target } from 'lucide-react';

import type { AnalysisDetail } from '../../types/api';
import { formatDecimal, formatPercentPrecise } from '../../utils/numberFormat';
import { AnalysisStatusBadge } from './AnalysisStatusBadge';

function asNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function displayStatusText(detail: AnalysisDetail): string {
  return detail.status === 'success'
    ? 'Análise concluída com sucesso'
    : detail.status === 'failed'
      ? 'Falha na execução'
      : detail.status === 'running'
        ? 'Executando análise'
        : 'Aguardando processamento';
}

export function AnalysisResultCard({ detail }: { detail: AnalysisDetail }) {
  const summary = detail.result_summary || {};
  const pvalue = asNumber(summary.p_value);
  const coef = asNumber(summary.coef);
  const nObs = asNumber(summary.n_obs);
  const isSignificant = pvalue !== null ? pvalue < 0.05 : null;

  const outcomes = useMemo(() => {
    const values = summary.outcomes;
    return Array.isArray(values) ? values.filter((value): value is string => typeof value === 'string') : [];
  }, [summary.outcomes]);

  const outcomeLabel = typeof summary.outcome === 'string' && summary.outcome.length > 0
    ? summary.outcome
    : outcomes[0] ?? '—';

  const startedAt = detail.started_at ? new Date(detail.started_at).toLocaleString('pt-BR') : '—';
  const completedAt = detail.completed_at ? new Date(detail.completed_at).toLocaleString('pt-BR') : '—';

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h3 className="font-semibold text-gray-900">Resultado da análise</h3>
          <p className="text-sm text-gray-600 mt-1">
            {displayStatusText(detail)} • Método: <strong>{detail.method}</strong>
          </p>
        </div>
        <AnalysisStatusBadge status={detail.status} />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4 text-sm">
        <div className="rounded-lg border border-gray-200 p-3">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Outcome</p>
          <p className="mt-1 font-semibold text-gray-900">{outcomeLabel}</p>
        </div>
        <div className="rounded-lg border border-gray-200 p-3">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Coeficiente</p>
          <p className="mt-1 font-semibold text-gray-900">
            {coef === null ? '—' : formatDecimal(coef, 4)}
          </p>
        </div>
        <div className="rounded-lg border border-gray-200 p-3">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Significância (5%)</p>
          <p className="mt-1 font-semibold text-gray-900">
            {isSignificant === null ? '—' : isSignificant ? 'Significativo' : 'Não significativo'}
          </p>
        </div>
        <div className="rounded-lg border border-gray-200 p-3">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Nº observações</p>
          <p className="mt-1 font-semibold text-gray-900">{nObs ?? '—'}</p>
        </div>
      </div>

      <div className="rounded-lg border border-gray-100 bg-gray-50 p-3 space-y-1 text-sm text-gray-700">
        <div className="flex items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1">
            <Target className="h-4 w-4 text-gray-400" />
            P-value
          </span>
          <span className="font-semibold">
            {pvalue === null ? '—' : pvalue < 0.0001 ? '< 0,0001' : formatPercentPrecise(pvalue * 100)}
          </span>
        </div>

        <div className="flex items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1">
            <Clock className="h-4 w-4 text-gray-400" />
            Duração
          </span>
          <span>
            {detail.duration_seconds === undefined || detail.duration_seconds === null
              ? '—'
              : `${detail.duration_seconds.toFixed(1)}s`}
          </span>
        </div>

        <div className="flex items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1">
            <Calendar className="h-4 w-4 text-gray-400" />
            Início
          </span>
          <span>{startedAt}</span>
        </div>
      </div>

      <div className="flex items-center justify-between gap-2 mt-4 text-xs text-gray-500">
        <span>Término: {completedAt}</span>
      </div>

      {detail.error_message && (
        <div className="mt-4 p-3 rounded-lg border border-red-200 bg-red-50 text-red-700 text-sm">
          {detail.error_message}
        </div>
      )}

      {Object.keys(detail.request_params).length > 0 && (
        <details className="mt-4">
          <summary className="cursor-pointer text-sm text-gray-600">Parâmetros da análise</summary>
          <pre className="mt-2 max-h-64 overflow-auto text-xs bg-gray-50 p-3 border border-gray-100 rounded-lg">
            {JSON.stringify(detail.request_params, null, 2)}
          </pre>
        </details>
      )}

      {detail.result_summary?.warnings && detail.result_summary.warnings.length > 0 && (
        <div className="mt-4">
          <p className="text-sm font-medium text-amber-700 mb-1">Avisos</p>
          <ul className="list-disc pl-5 text-sm text-amber-700">
            {detail.result_summary.warnings.map((warning: string, index: number) => (
              <li key={`${warning}-${index}`}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      <button
        className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50"
        onClick={() => {
          const blob = new Blob([JSON.stringify(detail.result_full || {}, null, 2)], {
            type: 'application/json',
          });
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          const filename = `analise_${detail.id}.json`;
          link.href = url;
          link.download = filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
        }}
        title="Exportar JSON bruto"
      >
        <FileDown className="h-4 w-4" />
        Exportar JSON
      </button>
    </div>
  );
}
