import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Minus, AlertTriangle, Info } from 'lucide-react';
import { indicatorsService } from '../../api/indicators';
import { CHART_PALETTE } from '../../styles/chartTheme';
import type { ParticipacaoISSPorto, ParticipacaoISSResponse } from '../../types/api';
import { LoadingSpinner } from '../common/LoadingSpinner';

function riskLevel(pct: number): { label: string; color: string; bg: string; border: string } {
  if (pct >= 10) return { label: 'Alta dependência', color: 'text-red-700',     bg: 'bg-red-50',     border: 'border-red-200' };
  if (pct >= 2)  return { label: 'Dependência média', color: 'text-amber-700',  bg: 'bg-amber-50',   border: 'border-amber-200' };
  return              { label: 'Baixa dependência', color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200' };
}

function TendenciaIcon({ tendencia }: { tendencia: string }) {
  if (tendencia === 'crescente')    return <TrendingUp  className="w-3.5 h-3.5 text-red-500" />;
  if (tendencia === 'decrescente')  return <TrendingDown className="w-3.5 h-3.5 text-emerald-600" />;
  return <Minus className="w-3.5 h-3.5 text-gray-400" />;
}

function PortoCard({ porto }: { porto: ParticipacaoISSPorto }) {
  const [expanded, setExpanded] = useState(false);
  const risk = riskLevel(porto.participacao_atual_pct);
  const barWidth = Math.min(porto.participacao_atual_pct * 5, 100); // escala: 20% = largura total

  return (
    <div
      className={`rounded-xl border ${risk.border} ${risk.bg} p-4 cursor-pointer transition-all`}
      onClick={() => setExpanded((v) => !v)}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-semibold text-gray-800 leading-tight">
              {porto.porto.replace('Porto do ', '').replace('Porto de ', '').replace('Portos do ', 'Portos ').replace('PortosRio', 'PortosRio')}
            </p>
            <span className="text-xs text-gray-400">{porto.nome_municipio} ({porto.uf})</span>
          </div>

          {/* Barra de progresso */}
          <div className="mt-2 w-full bg-white/60 rounded-full h-2">
            <div
              className="h-2 rounded-full transition-all"
              style={{
                width: `${barWidth}%`,
                backgroundColor: porto.participacao_atual_pct >= 10
                  ? CHART_PALETTE.crimson
                  : porto.participacao_atual_pct >= 2
                    ? CHART_PALETTE.gold
                    : CHART_PALETTE.teal,
              }}
            />
          </div>
        </div>

        <div className="text-right flex-shrink-0">
          <p className={`text-2xl font-extrabold ${risk.color}`}>
            {porto.participacao_atual_pct.toFixed(1)}%
          </p>
          <div className="flex items-center justify-end gap-1 mt-0.5">
            <TendenciaIcon tendencia={porto.tendencia} />
            <span className={`text-xs ${risk.color}`}>{risk.label}</span>
          </div>
          <p className="text-xs text-gray-400 mt-0.5">{porto.ano_referencia}</p>
        </div>
      </div>

      {/* Valores absolutos */}
      <div className="flex gap-4 mt-2 text-xs text-gray-500">
        <span>ISS do porto: R$ {porto.iss_df_r_mi.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}M</span>
        <span>·</span>
        <span>ISS total município: R$ {porto.iss_finbra_r_mi.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}M</span>
      </div>

      {/* Série histórica (expandida) */}
      {expanded && porto.serie.length > 1 && (
        <div className="mt-3 pt-3 border-t border-white/40">
          <p className="text-xs font-semibold text-gray-600 mb-2">Série histórica</p>
          <div className="flex gap-2 flex-wrap">
            {porto.serie.map((item) => (
              <div key={item.ano} className="text-center px-2 py-1 bg-white/60 rounded text-xs">
                <p className="font-bold text-gray-700">{item.participacao_pct.toFixed(1)}%</p>
                <p className="text-gray-400">{item.ano}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function ParticipacaoISSChart() {
  const [data, setData] = useState<ParticipacaoISSResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    indicatorsService
      .getParticipacaoISS()
      .then(setData)
      .catch((err: unknown) => {
        const e = err as { response?: { data?: { detail?: unknown } } };
        const msg = e?.response?.data?.detail;
        setError(typeof msg === 'string' ? msg : 'Erro ao carregar dados de participação.');
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  if (error) {
    return (
      <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
        <span>{error}</span>
      </div>
    );
  }

  if (!data || data.portos.length === 0) {
    return <p className="text-sm text-gray-400 py-4 text-center">Sem dados disponíveis.</p>;
  }

  const highDependency = data.portos.filter((p) => p.participacao_atual_pct >= 10);

  return (
    <div className="space-y-4">
      {/* Alerta de alta dependência */}
      {highDependency.length > 0 && (
        <div className="flex items-start gap-2.5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>
            <strong>{highDependency.map((p) => p.porto.replace('Porto do ', '').replace('Porto de ', '')).join(', ')}</strong>
            {' '}representa{highDependency.length > 1 ? 'm' : ''} mais de 10% do ISS do município — alta dependência fiscal em relação à atividade portuária.
          </span>
        </div>
      )}

      {/* Cards por porto */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {data.portos.map((porto) => (
          <PortoCard key={porto.porto} porto={porto} />
        ))}
      </div>

      {/* Nota */}
      <div className="flex items-start gap-1.5 text-xs text-gray-400">
        <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
        <span>{data.nota_metodologica}</span>
      </div>
    </div>
  );
}
