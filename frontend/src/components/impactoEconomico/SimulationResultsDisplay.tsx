import type { ImpactSimulationResponse, ImpactSimulationProjection } from '../../types/api';
import { ProjectionCard } from './ProjectionCard';

type ConfidenceLevel = 'forte' | 'moderada' | 'fraca';

function formatDate(value: string): string {
  try {
    return new Date(value).toLocaleDateString('pt-BR');
  } catch {
    return value;
  }
}

function buildManagerSummary(result: ImpactSimulationResponse): string {
  const significant = result.projected_outcomes.filter(
    (p) => p.confidence === 'forte' && p.projected_delta_pct !== null,
  );
  const mode = result.shock_mode === 'investment' ? 'investimento' : 'movimentação';
  const shockPct = result.shock_intensity_pct;
  const direction = shockPct >= 0 ? 'aumento' : 'redução';
  const absShock = Math.abs(shockPct);

  if (significant.length === 0) {
    return `Com ${direction} de ${absShock}% na ${mode}, a análise causal não encontrou evidência estatística suficiente para projetar impactos com confiança. Os resultados devem ser interpretados com cautela.`;
  }

  const topOutcome = significant.reduce((best, cur) =>
    Math.abs(cur.projected_delta_pct ?? 0) > Math.abs(best.projected_delta_pct ?? 0) ? cur : best,
  );

  const topDelta = topOutcome.projected_delta_pct ?? 0;
  const topDir = topDelta >= 0 ? 'crescimento' : 'queda';

  return `Com ${direction} de ${absShock}% na ${mode}, o maior impacto estimado é ${topDir} de ${Math.abs(topDelta).toFixed(2)}% em ${topOutcome.outcome_label}. ${significant.length} de ${result.projected_outcomes.length} indicadores apresentam evidência estatística forte (p < 5%).`;
}

function RiskPanel({ projections }: { projections: ImpactSimulationProjection[] }) {
  const counts: Record<ConfidenceLevel, number> = { forte: 0, moderada: 0, fraca: 0 };
  for (const p of projections) {
    const c = p.confidence as ConfidenceLevel;
    if (c in counts) counts[c]++;
  }
  const total = projections.length;
  if (total === 0) return null;

  const levels: { key: ConfidenceLevel; label: string; color: string; bg: string; border: string; description: string }[] = [
    {
      key: 'forte',
      label: 'Evidência forte',
      color: 'text-emerald-700',
      bg: 'bg-emerald-50',
      border: 'border-emerald-200',
      description: 'p < 5% e amostra robusta',
    },
    {
      key: 'moderada',
      label: 'Evidência moderada',
      color: 'text-amber-700',
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      description: 'p < 10% ou amostra limitada',
    },
    {
      key: 'fraca',
      label: 'Evidência fraca',
      color: 'text-red-700',
      bg: 'bg-red-50',
      border: 'border-red-200',
      description: 'Sem significância convencional',
    },
  ];

  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
      <p className="text-sm font-semibold text-gray-800 mb-3">Painel de Confiança</p>
      <div className="grid grid-cols-3 gap-3">
        {levels.map(({ key, label, color, bg, border, description }) => (
          <div key={key} className={`rounded-lg border ${border} ${bg} p-3 text-center`}>
            <p className={`text-2xl font-bold ${color}`}>{counts[key]}</p>
            <p className={`text-xs font-medium ${color} mt-0.5`}>{label}</p>
            <p className="text-xs text-gray-500 mt-1">{description}</p>
          </div>
        ))}
      </div>
      {counts.fraca > 0 && (
        <p className="text-xs text-gray-500 mt-3">
          ⚠ {counts.fraca} indicador{counts.fraca > 1 ? 'es' : ''} sem significância estatística — use esses resultados apenas como referência de ordem de grandeza.
        </p>
      )}
    </div>
  );
}

interface SimulationResultsDisplayProps {
  result: ImpactSimulationResponse;
}

export function SimulationResultsDisplay({ result }: SimulationResultsDisplayProps) {
  const managerSummary = buildManagerSummary(result);

  return (
    <div className="space-y-4 mt-4">
      {/* Card Resumo para Gestor */}
      <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-4">
        <p className="text-xs font-semibold text-indigo-600 uppercase tracking-wide mb-1">Resumo para o Gestor</p>
        <p className="text-sm text-indigo-900 leading-relaxed">{managerSummary}</p>
      </div>

      {/* Painel de Risco / Confiança */}
      <RiskPanel projections={result.projected_outcomes} />

      {/* Assumptions */}
      {result.assumptions.length > 0 && (
        <div className="rounded-md border border-emerald-100 bg-emerald-50 p-3 text-xs text-emerald-700">
          {result.assumptions.map((item) => (
            <p key={item} className="leading-6">• {item}</p>
          ))}
        </div>
      )}

      {/* Projection cards */}
      {result.projected_outcomes.length > 0 && (
        <div className="grid gap-3 md:grid-cols-2">
          {result.projected_outcomes.map((projection) => (
            <ProjectionCard
              key={projection.outcome}
              projection={projection}
              appliedShockPct={result.applied_shock_intensity_pct}
            />
          ))}
        </div>
      )}

      {/* Executive summary */}
      {result.executive_summary.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-sm font-medium text-gray-800">Resumo técnico detalhado</p>
          <ul className="list-disc pl-5 text-xs text-gray-600 space-y-1">
            {result.executive_summary.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Technical metadata (collapsed) */}
      <details className="text-xs text-gray-500">
        <summary className="cursor-pointer font-medium text-gray-600 hover:text-gray-800">
          Parâmetros técnicos
        </summary>
        <div className="mt-2 space-y-1 rounded-md border border-gray-100 bg-gray-50 p-3">
          <p>
            Modelo: {result.simulation_metadata.model_version}
            {' '}| gerado em {formatDate(result.simulation_metadata.as_of)}
            {' '}| origem: {result.simulation_metadata.generated_by}
          </p>
          {result.simulation_metadata.notes.length > 0 && (
            <ul className="list-disc pl-4 space-y-1 mt-1">
              {result.simulation_metadata.notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          )}
        </div>
      </details>
    </div>
  );
}
