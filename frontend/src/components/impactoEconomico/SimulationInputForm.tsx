import type { SimulationShockMode } from '../../types/api';

const PRESETS = [
  { label: '-10%', value: -10 },
  { label: '+5%', value: 5 },
  { label: '+15%', value: 15 },
  { label: '+25%', value: 25 },
];

interface SimulationInputFormProps {
  shockMode: SimulationShockMode;
  shockPct: number;
  investmentElasticity: number;
  loading: boolean;
  disabled: boolean;
  onShockModeChange: (mode: SimulationShockMode) => void;
  onShockPctChange: (pct: number) => void;
  onElasticityChange: (val: number) => void;
  onSubmit: () => void;
  onClear: () => void;
  hasResult: boolean;
}

function parseNumeric(val: string): number {
  const n = parseFloat(val.replace(',', '.'));
  return Number.isFinite(n) ? n : 0;
}

export function SimulationInputForm({
  shockMode,
  shockPct,
  investmentElasticity,
  loading,
  disabled,
  onShockModeChange,
  onShockPctChange,
  onElasticityChange,
  onSubmit,
  onClear,
  hasResult,
}: SimulationInputFormProps) {
  return (
    <div className="space-y-3">
      {/* Header + actions */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold text-gray-900">Simulador de Cenários</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Projete o impacto econômico usando os coeficientes da análise ativa.
          </p>
        </div>
        <div className="flex gap-2">
          {hasResult && (
            <button
              type="button"
              onClick={onClear}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-gray-300 text-gray-600 text-xs font-medium hover:bg-gray-50"
            >
              Limpar
            </button>
          )}
          <button
            type="button"
            onClick={onSubmit}
            disabled={loading || disabled}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Calculando...' : 'Calcular cenário'}
          </button>
        </div>
      </div>

      {/* Presets */}
      <div className="flex flex-wrap gap-2">
        <span className="text-xs text-gray-500 self-center">Cenários rápidos:</span>
        {PRESETS.map((p) => (
          <button
            key={p.value}
            type="button"
            onClick={() => onShockPctChange(p.value)}
            className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
              shockPct === p.value
                ? 'bg-indigo-100 border-indigo-300 text-indigo-700'
                : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Shock mode */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-gray-700">Fonte do cenário:</p>
        <div className="flex flex-wrap gap-3">
          <label className="inline-flex items-center gap-2 text-xs text-gray-600">
            <input
              type="radio"
              name="simulationShockMode"
              value="movement"
              checked={shockMode === 'movement'}
              onChange={() => onShockModeChange('movement')}
              className="h-3.5 w-3.5 accent-indigo-600"
            />
            Variação de movimentação (%)
          </label>
          <label className="inline-flex items-center gap-2 text-xs text-gray-600">
            <input
              type="radio"
              name="simulationShockMode"
              value="investment"
              checked={shockMode === 'investment'}
              onChange={() => onShockModeChange('investment')}
              className="h-3.5 w-3.5 accent-indigo-600"
            />
            Variação de investimento (%)
          </label>
        </div>
      </div>

      {/* Shock intensity */}
      <div className="flex flex-wrap items-end gap-3">
        <label className="text-xs text-gray-600">
          {shockMode === 'investment' ? 'Variação de investimento (%)' : 'Variação de movimentação (%)'}
        </label>
        <input
          type="number"
          min={-100}
          max={500}
          step={1}
          value={shockPct}
          onChange={(e) => onShockPctChange(parseNumeric(e.target.value))}
          className="w-28 border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
        />
        <span className="text-xs text-gray-500">Comparado ao cenário base</span>
      </div>

      {/* Elasticity + limitation note (investment mode) */}
      {shockMode === 'investment' && (
        <>
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
            <p className="font-semibold">Base de dados de investimentos indisponível</p>
            <p className="mt-1">
              O modo investimento requer dados históricos de investimentos portuários por município
              (SEP/MT, PAC), ainda não integrados ao sistema. Use a elasticidade abaixo como
              aproximação manual. Os resultados têm incerteza substancialmente maior do que no
              modo movimentação.
            </p>
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <label className="text-xs text-gray-600">
              Elasticidade (resposta da movimentação ao investimento):
            </label>
            <input
              type="number"
              min={0.01}
              step={0.01}
              value={investmentElasticity}
              onChange={(e) => onElasticityChange(parseNumeric(e.target.value))}
              className="w-28 border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
            />
            <span className="text-xs text-gray-500">
              Ex.: 0,8 = 10% investimento gera ~8% movimentação
            </span>
          </div>
        </>
      )}
    </div>
  );
}
