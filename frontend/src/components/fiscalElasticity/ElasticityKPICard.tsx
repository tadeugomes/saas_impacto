import { Building2, Globe } from 'lucide-react';
import { CHART_PALETTE } from '../../styles/chartTheme';
import type { ElasticidadeResult } from '../../types/api';

interface ElasticityKPICardProps {
  type: 'municipal' | 'federal';
  elasticidade: ElasticidadeResult | null;
  loading?: boolean;
}

export function ElasticityKPICard({ type, elasticidade, loading }: ElasticityKPICardProps) {
  const isMunicipal = type === 'municipal';
  const accent = isMunicipal ? CHART_PALETTE.navy : CHART_PALETTE.teal;
  const label = isMunicipal ? 'ISS Municipal' : 'Tributos Federais';
  const Icon = isMunicipal ? Building2 : Globe;

  // Interpretação: "cada +10% em tonelagem → +X% em ISS"
  const interpretation = elasticidade
    ? `Cada +10% em tonelagem → +${((Math.pow(1.1, elasticidade.beta) - 1) * 100).toFixed(1)}% em ${isMunicipal ? 'ISS' : 'tributos federais'}`
    : null;

  const significance = elasticidade
    ? elasticidade.p_value < 0.01
      ? 'p < 0,01 (altamente significativo)'
      : elasticidade.p_value < 0.05
        ? 'p < 0,05 (significativo)'
        : elasticidade.p_value < 0.10
          ? `p = ${elasticidade.p_value.toFixed(3)} (marginalmente significativo)`
          : `p = ${elasticidade.p_value.toFixed(3)} (não significativo)`
    : null;

  return (
    <div
      className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 border-l-4"
      style={{ borderLeftColor: accent }}
    >
      <div className="flex items-start gap-3">
        <Icon className="w-6 h-6 flex-shrink-0 mt-0.5" style={{ color: accent }} />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">{label}</p>

          {loading ? (
            <p className="text-sm text-gray-400 mt-2">Calculando…</p>
          ) : elasticidade ? (
            <>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-4xl font-extrabold" style={{ color: accent }}>
                  {elasticidade.beta.toFixed(2)}
                </span>
                <span className="text-sm text-gray-400">elasticidade</span>
              </div>

              <p className="text-xs text-gray-500 mt-1">
                IC 95%: [{elasticidade.ci_lower.toFixed(2)}, {elasticidade.ci_upper.toFixed(2)}]
              </p>

              {interpretation && (
                <p className="text-xs font-medium mt-2 leading-relaxed" style={{ color: accent }}>
                  {interpretation}
                </p>
              )}

              <div className="flex items-center gap-3 mt-3 text-xs text-gray-400">
                <span>R² = {(elasticidade.r2 * 100).toFixed(0)}%</span>
                <span>·</span>
                <span>n = {elasticidade.n_obs} obs</span>
                <span>·</span>
                <span>{elasticidade.n_portos} portos</span>
              </div>

              {significance && (
                <p className={`text-xs mt-1 ${elasticidade.p_value < 0.05 ? 'text-emerald-600' : 'text-amber-600'}`}>
                  {significance}
                </p>
              )}
            </>
          ) : (
            <div className="mt-2">
              <p className="text-2xl font-bold text-gray-300">—</p>
              <p className="text-xs text-gray-400 mt-1">
                Dados insuficientes para estimar elasticidade
                {!isMunicipal ? ' (ISS ausente em muitos portos)' : ''}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
