import type { ImpactSimulationResponse } from '../../types/api';
import { ProjectionCard } from './ProjectionCard';

function formatDate(value: string): string {
  try {
    return new Date(value).toLocaleDateString('pt-BR');
  } catch {
    return value;
  }
}

interface SimulationResultsDisplayProps {
  result: ImpactSimulationResponse;
}

export function SimulationResultsDisplay({ result }: SimulationResultsDisplayProps) {
  return (
    <div className="space-y-4 mt-4">
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
          <p className="text-sm font-medium text-gray-800">Resumo executivo</p>
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
