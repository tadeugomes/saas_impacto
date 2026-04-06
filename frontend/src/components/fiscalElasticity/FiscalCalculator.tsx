import { useState } from 'react';
import { Calculator, TrendingUp, TrendingDown, Building2, Globe, Info } from 'lucide-react';
import { CHART_PALETTE } from '../../styles/chartTheme';
import { indicatorsService } from '../../api/indicators';
import type { SimulacaoFiscalResponse } from '../../types/api';

interface FiscalCalculatorProps {
  portosDisponiveis: string[];
  hasElasticidade: boolean;
}

function formatMi(val: number | null | undefined): string {
  if (val === null || val === undefined) return '—';
  const abs = Math.abs(val);
  if (abs >= 1000) return `R$ ${(val / 1000).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} bi`;
  return `R$ ${val.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} mi`;
}

function DeltaBlock({
  label,
  baseline,
  delta,
  ci,
  accent,
  Icon,
}: {
  label: string;
  baseline: number | null | undefined;
  delta: number | null | undefined;
  ci?: [number, number] | null;
  accent: string;
  Icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
}) {
  if (delta === null || delta === undefined) return null;
  const isPositive = delta >= 0;

  return (
    <div
      className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 border-l-4 flex-1 min-w-0"
      style={{ borderLeftColor: accent }}
    >
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4 flex-shrink-0" style={{ color: accent }} />
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{label}</p>
      </div>

      {baseline !== null && baseline !== undefined && (
        <p className="text-xs text-gray-400 mb-1">Baseline: {formatMi(baseline)}/ano</p>
      )}

      <div className="flex items-baseline gap-1">
        {isPositive ? (
          <TrendingUp className="w-4 h-4 text-emerald-600 flex-shrink-0" />
        ) : (
          <TrendingDown className="w-4 h-4 text-red-500 flex-shrink-0" />
        )}
        <span className={`text-2xl font-extrabold ${isPositive ? 'text-emerald-700' : 'text-red-600'}`}>
          {isPositive ? '+' : ''}{formatMi(delta)}
        </span>
        <span className="text-xs text-gray-400">/ano</span>
      </div>

      {ci && ci[0] !== null && ci[1] !== null && (
        <p className="text-xs text-gray-400 mt-1">
          IC 95%: {isPositive ? '+' : ''}{formatMi(ci[0])} a {isPositive ? '+' : ''}{formatMi(ci[1])}
        </p>
      )}
    </div>
  );
}

export function FiscalCalculator({ portosDisponiveis, hasElasticidade }: FiscalCalculatorProps) {
  const [selectedPorto, setSelectedPorto] = useState<string>('__media__');
  const [shockPct, setShockPct] = useState<number>(20);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimulacaoFiscalResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await indicatorsService.simulateFiscalImpact(
        selectedPorto === '__media__' ? null : selectedPorto,
        shockPct,
      );
      setResult(res);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: unknown } } };
      const msg = e?.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'Erro ao calcular simulação fiscal.');
    } finally {
      setLoading(false);
    }
  };

  const totalDelta =
    (result?.delta_municipal_r_mi ?? 0) + (result?.delta_federal_r_mi ?? 0);
  const totalBaseline =
    (result?.baseline_municipal_r_mi ?? 0) + (result?.baseline_federal_r_mi ?? 0);

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 border-l-4" style={{ borderLeftColor: CHART_PALETTE.gold }}>
      <div className="flex items-center gap-2 mb-4">
        <Calculator className="w-5 h-5" style={{ color: CHART_PALETTE.gold }} />
        <h3 className="font-semibold text-gray-900">Calculadora de Retorno Fiscal</h3>
        <span
          className="ml-auto text-xs px-2 py-0.5 rounded-full font-medium"
          style={{ backgroundColor: `${CHART_PALETTE.gold}20`, color: CHART_PALETTE.gold }}
        >
          elasticidade média do setor
        </span>
      </div>

      {!hasElasticidade && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 mb-4">
          <p>A regressão de elasticidade requer dados de tonelagem do BigQuery (disponível em produção). Em desenvolvimento local os coeficientes não estão disponíveis, mas a composição e os baselines são carregados normalmente.</p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="text-xs font-medium text-gray-600 block mb-1">
            Porto de referência
          </label>
          <select
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
            value={selectedPorto}
            onChange={(e) => { setSelectedPorto(e.target.value); setResult(null); }}
          >
            <option value="__media__">Média do setor (todos os portos)</option>
            {portosDisponiveis.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <p className="text-xs text-gray-400 mt-1">
            Quando específico: usa ISS real do ano mais recente como baseline.
          </p>
        </div>

        <div>
          <label className="text-xs font-medium text-gray-600 block mb-1">
            Variação de tonelagem: {shockPct > 0 ? '+' : ''}{shockPct}%
          </label>
          <input
            type="range"
            min={-50}
            max={100}
            step={5}
            value={shockPct}
            onChange={(e) => { setShockPct(Number(e.target.value)); setResult(null); }}
            className="w-full accent-[#0f2d52]"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-0.5">
            <span>-50%</span>
            <span>0%</span>
            <span>+100%</span>
          </div>

          <div className="flex gap-2 mt-2 flex-wrap">
            {[-20, -10, 10, 20, 30, 50].map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => { setShockPct(v); setResult(null); }}
                className={`px-2 py-0.5 rounded-full text-xs border transition-colors ${
                  shockPct === v
                    ? 'bg-[#0f2d52] text-white border-[#0f2d52]'
                    : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
                }`}
              >
                {v > 0 ? '+' : ''}{v}%
              </button>
            ))}
          </div>
        </div>
      </div>

      <button
        type="button"
        onClick={handleCalculate}
        disabled={loading || !hasElasticidade}
        className="w-full py-2.5 rounded-lg font-semibold text-sm text-white transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
        style={{ backgroundColor: CHART_PALETTE.navy }}
      >
        {loading ? 'Calculando…' : 'Calcular Retorno Fiscal'}
      </button>

      {error && (
        <p className="text-xs text-red-600 mt-2">{error}</p>
      )}

      {result && (
        <div className="mt-5 space-y-3">
          {/* Headline */}
          <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 text-center">
            <p className="text-xs text-gray-500 mb-0.5">Receita fiscal total ao setor público</p>
            <p className={`text-2xl font-extrabold ${totalDelta >= 0 ? 'text-emerald-700' : 'text-red-600'}`}>
              {totalDelta >= 0 ? '+' : ''}{formatMi(totalDelta)}/ano
            </p>
            {totalBaseline > 0 && (
              <p className="text-xs text-gray-400 mt-0.5">
                Sobre baseline de {formatMi(totalBaseline)}/ano
                ({shockPct > 0 ? '+' : ''}{(totalDelta / totalBaseline * 100).toFixed(1)}%)
              </p>
            )}
          </div>

          {/* Split */}
          <div className="flex gap-3 flex-wrap">
            <DeltaBlock
              label="ISS Municipal"
              baseline={result.baseline_municipal_r_mi}
              delta={result.delta_municipal_r_mi}
              ci={result.delta_municipal_ci as [number, number] | null}
              accent={CHART_PALETTE.navy}
              Icon={Building2}
            />
            <DeltaBlock
              label="Tributos Federais"
              baseline={result.baseline_federal_r_mi}
              delta={result.delta_federal_r_mi}
              ci={result.delta_federal_ci as [number, number] | null}
              accent={CHART_PALETTE.teal}
              Icon={Globe}
            />
          </div>

          {/* Nota */}
          <div className="flex items-start gap-1.5 text-xs text-gray-400 mt-2">
            <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
            <span>{result.nota}</span>
          </div>
        </div>
      )}
    </div>
  );
}
