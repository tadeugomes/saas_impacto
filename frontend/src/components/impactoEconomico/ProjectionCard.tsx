import type { ImpactSimulationResponse } from '../../types/api';

type Projection = ImpactSimulationResponse['projected_outcomes'][number];

function confidenceTag(confidence: Projection['confidence']): string {
  switch (confidence) {
    case 'forte': return 'Confiança Alta';
    case 'moderada': return 'Confiança Moderada';
    case 'fraca': return 'Confiança Baixa';
    default: return String(confidence);
  }
}

function formatValue(v: number | null): string {
  if (v === null || v === undefined) return '—';
  return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
}

interface ProjectionCardProps {
  projection: Projection;
  appliedShockPct: number;
}

export function ProjectionCard({ projection, appliedShockPct }: ProjectionCardProps) {
  const delta = formatValue(projection.projected_delta_pct);
  const isPositive = (projection.projected_delta_pct ?? 0) > 0;
  const isNegative = (projection.projected_delta_pct ?? 0) < 0;

  const conservativeText =
    projection.projected_delta_pct_conservative !== null && projection.projected_delta_pct_optimistic !== null
      ? `${formatValue(projection.projected_delta_pct_conservative)} a ${formatValue(projection.projected_delta_pct_optimistic)}`
      : '—';

  const ci100Text =
    projection.treatment_effect_100pct_ci_lower !== null && projection.treatment_effect_100pct_ci_upper !== null
      ? `${formatValue(projection.treatment_effect_100pct_ci_lower)} a ${formatValue(projection.treatment_effect_100pct_ci_upper)}`
      : '—';

  const confColor = projection.confidence === 'forte'
    ? 'text-green-700 bg-green-50 border-green-200'
    : projection.confidence === 'moderada'
      ? 'text-amber-700 bg-amber-50 border-amber-200'
      : 'text-red-700 bg-red-50 border-red-200';

  return (
    <div className="rounded-lg border border-gray-200 p-4 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-medium text-gray-800">{projection.outcome_label}</p>
        <span className={`text-[11px] px-2 py-1 rounded-full border ${confColor}`}>
          {confidenceTag(projection.confidence)}
        </span>
      </div>

      <p className={`text-3xl font-bold tabular-nums ${
        isPositive ? 'text-emerald-700' : isNegative ? 'text-red-600' : 'text-gray-700'
      }`}>
        {delta}
      </p>

      <p className="text-xs text-gray-500">
        Projeção para cenário de {appliedShockPct.toFixed(1)}% de variação
      </p>

      <div className="text-xs text-gray-500 space-y-0.5">
        <p>Faixa conservador/otimista: {conservativeText}</p>
        <p>IC 95% (efeito base): {ci100Text}</p>
      </div>

      {projection.warning && (
        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded p-1.5">
          {projection.warning}
        </p>
      )}

      {projection.notes.length > 0 && (
        <ul className="list-disc pl-4 text-xs text-gray-400 space-y-0.5">
          {projection.notes.map((note) => (
            <li key={`${projection.outcome}-${note}`}>{note}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
