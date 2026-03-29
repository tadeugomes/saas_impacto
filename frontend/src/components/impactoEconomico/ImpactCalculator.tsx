import { useState, useMemo } from 'react';
import { ErrorAlert } from '../common/ErrorAlert';
import { SimulationInputForm } from './SimulationInputForm';
import { SimulationResultsDisplay } from './SimulationResultsDisplay';
import { impactoEconomicoService } from '../../api/impactoEconomico';
import type {
  AnalysisDetail,
  SimulationShockMode,
  ImpactSimulationRequest,
  ImpactSimulationResponse,
} from '../../types/api';

const REFERENCE_OUTCOME = 'toneladas_antaq_log';

function resolveOutcomes(detail: AnalysisDetail | null): string[] {
  if (!detail?.result_full || typeof detail.result_full !== 'object') return [];
  const full = detail.result_full as Record<string, unknown>;

  // Single-method: main_result.outcome
  const main = full.main_result as Record<string, unknown> | undefined;
  if (main?.outcome && typeof main.outcome === 'string') return [main.outcome];

  // Multi-outcome: outcomes dict
  const outcomes = full.outcomes as Record<string, unknown> | undefined;
  if (outcomes) return Object.keys(outcomes);

  // Comparison: comparison dict → each entry has outcomes
  const comparison = full.comparison as Record<string, unknown> | undefined;
  if (comparison) return Object.keys(comparison);

  return [];
}

interface ImpactCalculatorProps {
  analysis: AnalysisDetail;
}

export function ImpactCalculator({ analysis }: ImpactCalculatorProps) {
  const [shockMode, setShockMode] = useState<SimulationShockMode>('movement');
  const [shockPct, setShockPct] = useState(10);
  const [elasticity, setElasticity] = useState(0.8);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImpactSimulationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const targetOutcomes = useMemo(() => resolveOutcomes(analysis), [analysis]);
  const isDisabled = analysis.status !== 'success' || analysis.method === 'compare';

  const handleSubmit = async () => {
    if (analysis.status !== 'success') {
      setError('A análise precisa estar concluída para executar a simulação.');
      return;
    }

    if (!Number.isFinite(shockPct)) {
      setError('Informe uma variação válida.');
      return;
    }

    if (shockMode === 'investment' && (!Number.isFinite(elasticity) || elasticity <= 0)) {
      setError('Informe uma elasticidade maior que zero no modo investimento.');
      return;
    }

    if (targetOutcomes.length === 0) {
      setError('Não há indicadores disponíveis para simulação nesta análise.');
      return;
    }

    const request: ImpactSimulationRequest = {
      shock_mode: shockMode,
      shock_intensity_pct: shockPct,
      investment_to_movement_elasticity: shockMode === 'investment' ? elasticity : undefined,
      reference_outcome: REFERENCE_OUTCOME,
      target_outcomes: targetOutcomes,
    };

    setLoading(true);
    setError(null);
    try {
      const response = await impactoEconomicoService.simulateImpact(analysis.id, request);
      setResult(response);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: unknown } } };
      const msg = e?.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'Erro ao calcular simulação.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setResult(null);
    setError(null);
  };

  return (
    <div className="card">
      <SimulationInputForm
        shockMode={shockMode}
        shockPct={shockPct}
        investmentElasticity={elasticity}
        loading={loading}
        disabled={isDisabled}
        onShockModeChange={setShockMode}
        onShockPctChange={setShockPct}
        onElasticityChange={setElasticity}
        onSubmit={handleSubmit}
        onClear={handleClear}
        hasResult={result !== null}
      />

      {error && <ErrorAlert message={error} />}

      {result ? (
        <SimulationResultsDisplay result={result} />
      ) : (
        !loading && !error && (
          <p className="text-xs text-gray-400 mt-3">
            Execute o cálculo para visualizar a projeção de impacto com base na análise ativa.
          </p>
        )
      )}
    </div>
  );
}
