import { useEffect, useState } from 'react';
import { Info } from 'lucide-react';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ElasticityKPICard } from './ElasticityKPICard';
import { FiscalCompositionChart } from './FiscalCompositionChart';
import { FiscalCalculator } from './FiscalCalculator';
import { ParticipacaoISSChart } from './ParticipacaoISSChart';
import { ScatterChart } from '../charts/ScatterChart';
import { ChartCard } from '../charts/ChartCard';
import { indicatorsService } from '../../api/indicators';
import { CHART_PALETTE } from '../../styles/chartTheme';
import type { FiscalElasticidadeResponse } from '../../types/api';

export function ContribuicaoFiscalSection() {
  const [data, setData] = useState<FiscalElasticidadeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    indicatorsService
      .getFiscalElasticidade()
      .then(setData)
      .catch((err: unknown) => {
        const e = err as { response?: { data?: { detail?: unknown } } };
        const msg = e?.response?.data?.detail;
        setError(typeof msg === 'string' ? msg : 'Erro ao carregar dados de elasticidade fiscal.');
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {error}
      </div>
    );
  }

  const elMun = data?.elasticidade_municipal ?? null;
  const elFed = data?.elasticidade_federal ?? null;
  const hasElasticidade = !!(elMun || elFed);

  // Preparar dados para scatter
  const scatterPoints = (data?.scatter_points ?? []).map((p) => ({
    x: p.tonelagem_m_ton,
    y: p.iss_r_mi,
    label: `${p.porto} (${p.ano})`,
    uf: p.uf,
    ano: p.ano,
  }));

  // Calcular linha de regressão para scatter (ISS vs tonelagem)
  // ln(y) = intercept + slope * ln(x) → precisa do intercept
  // O intercepto inclui a média dos efeitos fixos de porto.
  // Calculamos numericamente a partir dos pontos médios.
  let regressionLine: { slope: number; intercept: number } | undefined;
  if (elMun && scatterPoints.length > 0) {
    const logXs = scatterPoints.map((p) => Math.log(p.x));
    const logYs = scatterPoints.map((p) => Math.log(p.y));
    const meanLogX = logXs.reduce((a, b) => a + b, 0) / logXs.length;
    const meanLogY = logYs.reduce((a, b) => a + b, 0) / logYs.length;
    const intercept = meanLogY - elMun.beta * meanLogX;
    regressionLine = { slope: elMun.beta, intercept };
  }

  return (
    <div className="space-y-6">
      {/* Disclaimer metodológico */}
      <div className="flex items-start gap-2.5 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-xs text-blue-800">
        <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <span>
          <strong>Análise associativa, não causal.</strong>{' '}
          Regressão OLS log-log com efeitos fixos de porto (HC3). Dados de Demonstrações Financeiras de 22 operadores portuários, 2018–2024.
          Outliers filtrados (tributos {'>'} R$ 500M). Tonelagem via ANTAQ (disponível em produção).
        </span>
      </div>

      {/* KPI cards de elasticidade */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Elasticidades Estimadas — Painel 22 Portos</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <ElasticityKPICard type="municipal" elasticidade={elMun} loading={loading} />
          <ElasticityKPICard type="federal" elasticidade={elFed} loading={loading} />
        </div>
      </div>

      {/* Scatter + Composição */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scatter */}
        <ChartCard
          title="Tonelagem × ISS por Porto-Ano"
          description="Cada ponto = 1 porto em 1 ano. Linha = ajuste OLS log-log (β médio do setor)"
          accentColor={CHART_PALETTE.navy}
          source="DFs dos operadores + ANTAQ"
        >
          {scatterPoints.length > 0 ? (
            <ScatterChart
              points={scatterPoints}
              regressionLine={regressionLine}
              xLabel="Tonelagem (M ton)"
              yLabel="ISS (R$ mi)"
              height="h-72"
            />
          ) : (
            <div className="h-72 flex items-center justify-center text-gray-400 text-sm">
              Dados de tonelagem disponíveis em produção (requer BigQuery).
            </div>
          )}
        </ChartCard>

        {/* Composição */}
        <FiscalCompositionChart
          composition={data?.composition ?? []}
          loading={loading}
        />
      </div>

      {/* Participação do Porto no ISS Municipal */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Dependência Fiscal do Município — Participação do Porto no ISS
        </h3>
        <p className="text-xs text-gray-500 mb-3">
          Fração do ISS arrecadado pelo município que provém diretamente do operador portuário.
          Clique em um card para ver a série histórica.
        </p>
        <ParticipacaoISSChart />
      </div>

      {/* Calculadora */}
      <FiscalCalculator
        portosDisponiveis={data?.portos_disponiveis ?? []}
        hasElasticidade={hasElasticidade}
      />

      {/* Nota metodológica completa */}
      {data?.nota_metodologica && (
        <details className="text-xs text-gray-500">
          <summary className="cursor-pointer font-medium text-gray-600 hover:text-gray-800">
            Nota metodológica completa
          </summary>
          <p className="mt-2 leading-relaxed">{data.nota_metodologica}</p>
        </details>
      )}
    </div>
  );
}
