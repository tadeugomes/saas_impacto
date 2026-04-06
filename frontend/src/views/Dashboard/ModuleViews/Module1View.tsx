import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, TrendingDown, TrendingUp, Minus, Award, Activity, Clock } from 'lucide-react';
import { FilterBar } from '../../../components/filters/FilterBar';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { ExportButton } from '../../../components/common/ExportButton';
import { useFilterStore } from '../../../store/filterStore';
import { indicatorsService } from '../../../api/indicators';
import { IndicatorDashboardCard } from '../../../components/dashboard/IndicatorDashboardCard';
import type { IndicatorResponse } from '../../../types/api';
import { apiClient } from '../../../api/client';
import { useI18n } from '../../../i18n/I18nContext';
import { useIndicatorLabel } from '../../../i18n/indicatorTranslations';
import { CHART_PALETTE } from '../../../styles/chartTheme';

interface IndicatorConfig {
  code: string;
  name: string;
  unit: string;
  desc: string;
  chartType: 'bar' | 'pie' | 'metric';
  valueField: string;
  labelField?: string;
}

const INDICATORS_INFO: IndicatorConfig[] = [
  { code: 'IND-1.01', name: 'Tempo Médio de Espera', unit: 'Horas', desc: 'Tempo entre chegada e atracação', chartType: 'bar', valueField: 'tempo_medio_espera_horas', labelField: 'id_instalacao' },
  { code: 'IND-1.02', name: 'Tempo Médio em Porto', unit: 'Horas', desc: 'Tempo total no porto', chartType: 'bar', valueField: 'tempo_medio_porto_horas', labelField: 'id_instalacao' },
  { code: 'IND-1.03', name: 'Tempo Bruto de Atracação', unit: 'Horas', desc: 'Tempo de atracação até desatracação', chartType: 'bar', valueField: 'tempo_bruto_atracacao_horas', labelField: 'id_instalacao' },
  { code: 'IND-1.04', name: 'Tempo Líquido de Operação', unit: 'Horas', desc: 'Tempo efetivo de operação', chartType: 'bar', valueField: 'tempo_liquido_operacao_horas', labelField: 'id_instalacao' },
  { code: 'IND-1.05', name: 'Taxa de Ocupação de Berços', unit: '%', desc: 'Ocupação média dos berços', chartType: 'bar', valueField: 'taxa_ocupacao_percentual', labelField: 'id_instalacao' },
  { code: 'IND-1.06', name: 'Tempo Ocioso Médio', unit: 'Horas', desc: 'Tempo de paralisação', chartType: 'bar', valueField: 'tempo_ocioso_medio_horas', labelField: 'id_instalacao' },
  { code: 'IND-1.07', name: 'Arqueação Bruta Média', unit: 'GT', desc: 'Tamanho médio dos navios', chartType: 'bar', valueField: 'arqueacao_bruta_media', labelField: 'id_instalacao' },
  { code: 'IND-1.08', name: 'Comprimento Médio', unit: 'Metros', desc: 'Comprimento médio dos navios', chartType: 'bar', valueField: 'comprimento_medio_metros', labelField: 'id_instalacao' },
  { code: 'IND-1.09', name: 'Calado Máximo', unit: 'Metros', desc: 'Maior calado operacional', chartType: 'metric', valueField: 'calado_maximo_metros', labelField: 'id_instalacao' },
  { code: 'IND-1.10', name: 'Distribuição por Tipo', unit: '%', desc: 'Por tipo de navegação', chartType: 'pie', valueField: 'qtd_atracacoes', labelField: 'tipo_navegacao' },
  { code: 'IND-1.11', name: 'Número de Atracações', unit: 'Contagem', desc: 'Total de atracações', chartType: 'bar', valueField: 'total_atracacoes', labelField: 'id_instalacao' },
  { code: 'IND-1.12', name: 'Índice de Paralisação', unit: '%', desc: 'Tempo ocioso / tempo atracado', chartType: 'bar', valueField: 'indice_paralisacao_percentual', labelField: 'id_instalacao' },
];

type RawIndicatorRow = Record<string, unknown>;
type ModuleIndicatorResponse = IndicatorResponse<RawIndicatorRow>;
type IndicatorMap = Record<string, ModuleIndicatorResponse>;

const createEmptyIndicatorResponse = (codigoIndicador: string): ModuleIndicatorResponse => ({
  codigo_indicador: codigoIndicador,
  nome: codigoIndicador,
  unidade: '',
  unctad: false,
  data: [],
});

interface TendenciaItem {
  indicador_codigo: string;
  indicador_nome: string;
  unidade: string;
  valor_atual: number | null;
  valor_anterior: number | null;
  variacao_yoy_pct: number | null;
  cagr_3y_pct: number | null;
  classificacao: 'IMPROVING' | 'STABLE' | 'DETERIORATING' | 'SEM_DADOS';
  polaridade_inversa: boolean;
}

interface TendenciaResponse {
  id_instalacao: string;
  ano: number;
  indicadores: TendenciaItem[];
}

interface ScoreComponente {
  indicador_codigo: string;
  indicador_nome: string;
  valor_bruto: number | null;
  valor_normalizado: number | null;
  peso: number;
  contribuicao: number | null;
}

interface ScoreResponse {
  id_instalacao: string;
  ano: number;
  score_total: number;
  ranking_posicao: number;
  total_portos: number;
  componentes: ScoreComponente[];
  nota_metodologica: string;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function trendIcon(cls: string) {
  if (cls === 'IMPROVING') return <TrendingDown className="w-3 h-3" />;
  if (cls === 'DETERIORATING') return <TrendingUp className="w-3 h-3" />;
  if (cls === 'STABLE') return <Minus className="w-3 h-3" />;
  return <Minus className="w-3 h-3" />;
}

function trendColor(cls: string): string {
  if (cls === 'IMPROVING') return 'text-emerald-700 bg-emerald-50 border-emerald-200';
  if (cls === 'DETERIORATING') return 'text-red-700 bg-red-50 border-red-200';
  if (cls === 'STABLE') return 'text-amber-700 bg-amber-50 border-amber-200';
  return 'text-gray-500 bg-gray-50 border-gray-200';
}

function trendLabel(cls: string): string {
  if (cls === 'IMPROVING') return 'Melhorando';
  if (cls === 'DETERIORATING') return 'Piorando';
  if (cls === 'STABLE') return 'Estável';
  return 'Sem dados';
}

function scoreColor(score: number): { bar: string; text: string; bg: string; label: string } {
  if (score >= 70) return { bar: 'bg-emerald-500', text: 'text-emerald-700', bg: 'bg-emerald-50', label: 'Bom' };
  if (score >= 40) return { bar: 'bg-amber-500',   text: 'text-amber-700',   bg: 'bg-amber-50',   label: 'Regular' };
  return               { bar: 'bg-red-500',         text: 'text-red-700',     bg: 'bg-red-50',     label: 'Fraco' };
}

function maxNumericField(data: RawIndicatorRow[], field: string): number | null {
  const vals = data.map(r => Number(r[field])).filter(Number.isFinite);
  return vals.length > 0 ? Math.max(...vals) : null;
}

function avgNumericField(data: RawIndicatorRow[], field: string): number | null {
  const vals = data.map(r => Number(r[field])).filter(Number.isFinite);
  if (!vals.length) return null;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}

// ── Componente ────────────────────────────────────────────────────────────────

export function Module1View() {
  const { t } = useI18n();
  const tInd = useIndicatorLabel();
  const { selectedYear, selectedInstallation } = useFilterStore();
  const [indicators, setIndicators] = useState<IndicatorMap>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tableSearch, setTableSearch] = useState('');
  const [selectedIndicator, setSelectedIndicator] = useState('all');

  const localizedIndicators = useMemo(
    () => INDICATORS_INFO.map(ind => {
      const { name, desc } = tInd(ind.code, ind.name, ind.desc);
      return { ...ind, name, desc };
    }),
    [tInd],
  );

  const [tendencia, setTendencia] = useState<TendenciaResponse | null>(null);
  const [score, setScore] = useState<ScoreResponse | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'risco' | 'competitivo' | 'dados'>('overview');

  useEffect(() => {
    const fetchIndicators = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const promises = INDICATORS_INFO.map((ind) =>
          indicatorsService
            .queryIndicator<RawIndicatorRow>({
              codigo_indicador: ind.code,
              params: { ano: selectedYear, id_instalacao: selectedInstallation || undefined },
            })
            .catch(() => createEmptyIndicatorResponse(ind.code))
        );
        const results = await Promise.all(promises);
        const mapped: IndicatorMap = {};
        results.forEach((result, i) => { mapped[INDICATORS_INFO[i].code] = result; });
        setIndicators(mapped);
      } catch (err: unknown) {
        const e = err as { response?: { data?: { detail?: unknown } } };
        const msg = e?.response?.data?.detail || t('common.errorLoading');
        setError(typeof msg === 'string' ? msg : t('common.errorLoading'));
      } finally {
        setIsLoading(false);
      }
    };
    fetchIndicators();
  }, [selectedYear, selectedInstallation]);

  useEffect(() => {
    if (!selectedInstallation || !selectedYear) {
      setTendencia(null);
      setScore(null);
      return;
    }
    const fetchAnalytics = async () => {
      setAnalyticsLoading(true);
      try {
        const [tendRes, scoreRes] = await Promise.allSettled([
          apiClient.get<TendenciaResponse[]>('/api/v1/indicators/module1/analise-tendencia', {
            params: { id_instalacao: selectedInstallation, ano_fim: selectedYear },
          }),
          apiClient.get<ScoreResponse[]>('/api/v1/indicators/module1/score-eficiencia', {
            params: { id_instalacao: selectedInstallation, ano: selectedYear },
          }),
        ]);
        setTendencia(tendRes.status === 'fulfilled' && tendRes.value.data?.length > 0 ? tendRes.value.data[0] : null);
        setScore(scoreRes.status === 'fulfilled' && scoreRes.value.data?.length > 0 ? scoreRes.value.data[0] : null);
      } catch { /* analíticos são complementares */ }
      finally { setAnalyticsLoading(false); }
    };
    fetchAnalytics();
  }, [selectedYear, selectedInstallation]);

  // ── KPIs executivos computados a partir dos indicadores ──────────────────

  const topOcupacao = useMemo(() =>
    maxNumericField(indicators['IND-1.05']?.data ?? [], 'taxa_ocupacao_percentual'),
  [indicators]);

  const avgParalisacao = useMemo(() =>
    avgNumericField(indicators['IND-1.12']?.data ?? [], 'indice_paralisacao_percentual'),
  [indicators]);

  const uptime = avgParalisacao !== null ? Math.max(0, 100 - avgParalisacao) : null;

  const maxEspera = useMemo(() =>
    maxNumericField(indicators['IND-1.01']?.data ?? [], 'tempo_medio_espera_horas'),
  [indicators]);

  // ── Alertas de risco ──────────────────────────────────────────────────────

  const alerts = useMemo(() => {
    const list: { level: 'red' | 'yellow' | 'green'; msg: string }[] = [];
    if (avgParalisacao !== null && avgParalisacao > 5)
      list.push({ level: 'red', msg: `Índice de paralisação médio de ${avgParalisacao.toFixed(1)}% — risco operacional elevado (referência: <5%)` });
    if (topOcupacao !== null && topOcupacao > 80)
      list.push({ level: 'yellow', msg: `Ocupação de berços acima de 80% (${topOcupacao.toFixed(0)}%) — risco de saturação de capacidade sem novo CAPEX` });
    if (maxEspera !== null && maxEspera > 24)
      list.push({ level: 'red', msg: `Tempo de espera máximo de ${maxEspera.toFixed(1)}h — demurrage elevado reduz atratividade para armadores` });
    if (list.length === 0 && (topOcupacao !== null || uptime !== null))
      list.push({ level: 'green', msg: 'Parâmetros operacionais dentro dos limites de referência.' });
    return list;
  }, [avgParalisacao, topOcupacao, maxEspera, uptime]);

  const visibleIndicators = useMemo(() => {
    if (selectedIndicator === 'all') return localizedIndicators;
    return localizedIndicators.filter((item) => item.code === selectedIndicator);
  }, [selectedIndicator, localizedIndicators]);

  // ── Número de indicadores em deterioração (para badge na aba) ─────────────
  const nDeteriorating = useMemo(() =>
    tendencia?.indicadores.filter(i => i.classificacao === 'DETERIORATING').length ?? 0,
  [tendencia]);

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">{t('module1.title')}</h1>
        <LoadingSpinner />
      </div>
    );
  }

  const ACCENT = CHART_PALETTE.navy;

  return (
    <div>
      {/* Cabeçalho */}
      <div className="mb-4 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('module1.title')}</h1>
          <p className="text-sm text-gray-500 mt-0.5">{t('module1.subtitle')}</p>
        </div>
        <ExportButton moduleCode="1" />
      </div>

      <FilterBar />

      {/* ── Alertas de Risco ─────────────────────────────────────────────── */}
      {alerts.length > 0 && !isLoading && (
        <div className="mt-4 space-y-2">
          {alerts.map((a, i) => (
            <div
              key={i}
              className={`flex items-start gap-2.5 rounded-lg border px-4 py-3 text-sm ${
                a.level === 'red'
                  ? 'bg-red-50 border-red-200 text-red-800'
                  : a.level === 'yellow'
                    ? 'bg-amber-50 border-amber-200 text-amber-800'
                    : 'bg-emerald-50 border-emerald-200 text-emerald-800'
              }`}
            >
              <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{a.msg}</span>
            </div>
          ))}
        </div>
      )}

      {/* ── 3 KPIs Executivos ────────────────────────────────────────────── */}
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Score de Eficiência */}
        <div
          className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 border-l-4 flex items-center gap-4"
          style={{ borderLeftColor: ACCENT }}
        >
          <Award className="w-8 h-8 flex-shrink-0" style={{ color: ACCENT }} />
          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Score de Eficiência</p>
            {score ? (
              <>
                <p className="text-3xl font-extrabold mt-0.5" style={{ color: ACCENT }}>
                  {score.score_total.toFixed(0)}
                  <span className="text-base font-normal text-gray-400">/100</span>
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Rank <strong>#{score.ranking_posicao}</strong> de {score.total_portos} portos · {scoreColor(score.score_total).label}
                </p>
              </>
            ) : analyticsLoading ? (
              <p className="text-sm text-gray-400 mt-1">Calculando…</p>
            ) : (
              <p className="text-2xl font-bold text-gray-300 mt-0.5">—</p>
            )}
            {!selectedInstallation && (
              <p className="text-xs text-gray-400 mt-0.5">Selecione uma instalação</p>
            )}
          </div>
        </div>

        {/* Ocupação de Berços */}
        <div
          className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 border-l-4 flex items-center gap-4"
          style={{ borderLeftColor: CHART_PALETTE.teal }}
        >
          <Activity className="w-8 h-8 flex-shrink-0" style={{ color: CHART_PALETTE.teal }} />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Ocupação de Berços</p>
            {topOcupacao !== null ? (
              <>
                <p className="text-3xl font-extrabold mt-0.5" style={{ color: topOcupacao > 80 ? CHART_PALETTE.crimson : CHART_PALETTE.teal }}>
                  {topOcupacao.toFixed(0)}%
                </p>
                <div className="w-full bg-gray-100 rounded-full h-1.5 mt-1.5">
                  <div
                    className="h-1.5 rounded-full transition-all"
                    style={{
                      width: `${Math.min(topOcupacao, 100)}%`,
                      backgroundColor: topOcupacao > 80 ? CHART_PALETTE.crimson : CHART_PALETTE.teal,
                    }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {topOcupacao > 80 ? '⚠ Próximo da saturação' : topOcupacao > 60 ? 'Utilização saudável' : 'Headroom disponível'}
                </p>
              </>
            ) : (
              <p className="text-2xl font-bold text-gray-300 mt-0.5">—</p>
            )}
          </div>
        </div>

        {/* Uptime Operacional */}
        <div
          className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 border-l-4 flex items-center gap-4"
          style={{ borderLeftColor: CHART_PALETTE.gold }}
        >
          <Clock className="w-8 h-8 flex-shrink-0" style={{ color: CHART_PALETTE.gold }} />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Uptime Operacional</p>
            {uptime !== null ? (
              <>
                <p className="text-3xl font-extrabold mt-0.5" style={{ color: uptime < 95 ? CHART_PALETTE.crimson : CHART_PALETTE.gold }}>
                  {uptime.toFixed(1)}%
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  Paralisação média: {avgParalisacao?.toFixed(1)}%
                  {avgParalisacao !== null && avgParalisacao > 5 ? ' ⚠ acima do referencial de 5%' : ''}
                </p>
              </>
            ) : (
              <p className="text-2xl font-bold text-gray-300 mt-0.5">—</p>
            )}
          </div>
        </div>
      </div>

      {/* ── Tabs ─────────────────────────────────────────────────────────── */}
      <div className="mt-6 border-b border-gray-200">
        <nav className="-mb-px flex gap-1">
          {([
            { key: 'overview',    label: 'Visão Geral' },
            { key: 'competitivo', label: 'Desempenho Competitivo', badge: score ? `#${score.ranking_posicao}` : undefined },
            { key: 'risco',       label: 'Análise de Risco', badge: nDeteriorating > 0 ? String(nDeteriorating) : undefined },
            { key: 'dados',       label: 'Dados Técnicos' },
          ] as { key: typeof activeTab; label: string; badge?: string }[]).map(({ key, label, badge }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`relative py-2.5 px-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === key
                  ? 'border-[#0f2d52] text-[#0f2d52]'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {label}
              {badge && (
                <span className="ml-1.5 inline-flex items-center justify-center px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-[#0f2d52] text-white">
                  {badge}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {error && <ErrorAlert message={error} className="mt-4" />}

      {/* ── Tab: Visão Geral ─────────────────────────────────────────────── */}
      {activeTab === 'overview' && (
        <div className="mt-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-2">
            <div>
              <label className="text-xs text-gray-500">{t('common.searchSeries')}</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 mt-1 text-sm"
                placeholder="Filtrar instalação no ranking…"
                value={tableSearch}
                onChange={(e) => setTableSearch(e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-gray-500">{t('common.indicator')}</label>
              <select
                className="w-full border border-gray-300 rounded-lg px-3 py-2 mt-1 text-sm"
                value={selectedIndicator}
                onChange={(e) => setSelectedIndicator(e.target.value)}
              >
                <option value="all">{t('common.all')}</option>
                {localizedIndicators.map((ind) => (
                  <option key={ind.code} value={ind.code}>{ind.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {visibleIndicators.map((ind) => (
              <IndicatorDashboardCard
                key={ind.code}
                title={ind.name}
                description={ind.desc}
                unit={ind.unit}
                isLoading={isLoading}
                data={indicators[ind.code]}
                chartType={ind.chartType}
                valueField={ind.valueField}
                labelField={ind.labelField}
                filterText={tableSearch}
                indicatorCode={ind.code}
              />
            ))}
          </div>
        </div>
      )}

      {/* ── Tab: Desempenho Competitivo ──────────────────────────────────── */}
      {activeTab === 'competitivo' && (
        <div className="mt-4">
          {!selectedInstallation ? (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
              {t('module1.score.selectHint')}
            </div>
          ) : analyticsLoading ? (
            <LoadingSpinner />
          ) : !score ? (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-600">
              {t('module1.score.noData')}
            </div>
          ) : (() => {
            const sc = scoreColor(score.score_total);
            return (
              <>
                {/* Score principal */}
                <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 mb-4 border-l-4" style={{ borderLeftColor: ACCENT }}>
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Score de Eficiência Operacional</p>
                      <div className="flex items-baseline gap-2">
                        <span className="text-5xl font-extrabold" style={{ color: ACCENT }}>
                          {score.score_total.toFixed(1)}
                        </span>
                        <span className="text-lg text-gray-400">/100</span>
                        <span className={`ml-2 text-sm font-bold px-2.5 py-0.5 rounded-full ${sc.bg} ${sc.text}`}>
                          {sc.label}
                        </span>
                      </div>
                      <div className="w-64 bg-gray-100 rounded-full h-2 mt-3">
                        <div className={`h-2 rounded-full ${sc.bar}`} style={{ width: `${Math.min(score.score_total, 100)}%` }} />
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Ranking Nacional</p>
                      <p className="text-4xl font-extrabold text-gray-700">#{score.ranking_posicao}</p>
                      <p className="text-sm text-gray-500 mt-0.5">de {score.total_portos} instalações</p>
                      <p className="text-xs text-gray-400 mt-1">
                        Percentil {Math.round((1 - (score.ranking_posicao - 1) / score.total_portos) * 100)}º
                      </p>
                    </div>
                  </div>
                </div>

                {/* Decomposição */}
                <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('module1.score.decomposition')}</h3>
                <div className="space-y-2.5">
                  {score.componentes.map((comp) => {
                    const c = scoreColor(comp.valor_normalizado ?? 0);
                    return (
                      <div key={comp.indicador_codigo} className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2 min-w-0">
                            <span className="text-xs font-mono text-gray-400 flex-shrink-0">{comp.indicador_codigo}</span>
                            <span className="text-sm font-medium text-gray-800 truncate">{comp.indicador_nome}</span>
                          </div>
                          <div className="flex items-center gap-3 flex-shrink-0 ml-2">
                            <span className="text-xs text-gray-400">Peso {(comp.peso * 100).toFixed(0)}%</span>
                            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${c.bg} ${c.text}`}>
                              {comp.valor_normalizado?.toFixed(0) ?? '—'}/100
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                            <div className={`h-1.5 rounded-full ${c.bar}`} style={{ width: `${Math.min(comp.valor_normalizado ?? 0, 100)}%` }} />
                          </div>
                          <span className="text-xs text-gray-400 flex-shrink-0">
                            Contribuição: {comp.contribuicao?.toFixed(1) ?? '—'} pts
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-500">
                  <span className="font-semibold">Nota metodológica: </span>{score.nota_metodologica}
                </div>
              </>
            );
          })()}
        </div>
      )}

      {/* ── Tab: Análise de Risco ────────────────────────────────────────── */}
      {activeTab === 'risco' && (
        <div className="mt-4">
          {!selectedInstallation ? (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
              {t('module1.trend.selectHint')}
            </div>
          ) : analyticsLoading ? (
            <LoadingSpinner />
          ) : !tendencia ? (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-600">
              {t('module1.trend.noData')}
            </div>
          ) : (
            <>
              {/* Resumo de risco */}
              {nDeteriorating > 0 && (
                <div className="mb-4 flex items-start gap-2.5 rounded-lg border bg-red-50 border-red-200 text-red-800 px-4 py-3 text-sm">
                  <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span>
                    <strong>{nDeteriorating} indicador{nDeteriorating > 1 ? 'es' : ''} em deterioração</strong> detectado{nDeteriorating > 1 ? 's' : ''} em {tendencia.id_instalacao} ({tendencia.ano}).
                    Avalie exposição antes de novas posições.
                  </span>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {tendencia.indicadores.map((item) => (
                  <div
                    key={item.indicador_codigo}
                    className={`bg-white rounded-lg border p-4 shadow-sm border-l-4 ${
                      item.classificacao === 'DETERIORATING' ? 'border-l-red-400' :
                      item.classificacao === 'IMPROVING' ? 'border-l-emerald-400' :
                      'border-l-amber-300'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2 gap-2">
                      <div className="min-w-0">
                        <span className="text-xs font-mono text-gray-400">{item.indicador_codigo}</span>
                        <p className="text-sm font-semibold text-gray-800 leading-tight mt-0.5">{item.indicador_nome}</p>
                      </div>
                      <span className={`flex-shrink-0 inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border ${trendColor(item.classificacao)}`}>
                        {trendIcon(item.classificacao)}
                        {trendLabel(item.classificacao)}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs mt-3">
                      <div className="bg-gray-50 rounded-lg p-2 text-center">
                        <span className="block text-gray-400 mb-0.5">Atual</span>
                        <span className="font-bold text-gray-800">{item.valor_atual?.toFixed(1) ?? '—'} {item.unidade}</span>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-2 text-center">
                        <span className="block text-gray-400 mb-0.5">Anterior</span>
                        <span className="font-bold text-gray-800">{item.valor_anterior?.toFixed(1) ?? '—'} {item.unidade}</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between mt-2 text-xs px-1">
                      <span className="text-gray-400">Var. anual</span>
                      <span className={`font-bold ${
                        item.variacao_yoy_pct == null ? 'text-gray-400' :
                        (item.polaridade_inversa
                          ? (item.variacao_yoy_pct < 0 ? 'text-emerald-600' : 'text-red-600')
                          : (item.variacao_yoy_pct > 0 ? 'text-emerald-600' : 'text-red-600'))
                      }`}>
                        {item.variacao_yoy_pct != null
                          ? `${item.variacao_yoy_pct > 0 ? '+' : ''}${item.variacao_yoy_pct.toFixed(1)}%`
                          : '—'}
                      </span>
                      <span className="text-gray-400 ml-3">CAGR 3a</span>
                      <span className="font-bold text-gray-600">
                        {item.cagr_3y_pct != null ? `${item.cagr_3y_pct > 0 ? '+' : ''}${item.cagr_3y_pct.toFixed(1)}%` : '—'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-4 p-3 bg-gray-50 border border-gray-100 rounded-lg text-xs text-gray-500">
                Para indicadores de tempo, queda = melhoria. Para atracações, crescimento = melhoria. Limiar de classificação: variação {'>'} 5%.
              </div>
            </>
          )}
        </div>
      )}

      {/* ── Tab: Dados Técnicos ──────────────────────────────────────────── */}
      {activeTab === 'dados' && (
        <div className="mt-4 space-y-4">
          <p className="text-xs text-gray-400">Séries brutas para due diligence e análise técnica detalhada.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-2">
            <div>
              <label className="text-xs text-gray-500">{t('common.searchSeries')}</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 mt-1 text-sm"
                placeholder="Filtrar instalação…"
                value={tableSearch}
                onChange={(e) => setTableSearch(e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-gray-500">{t('common.indicator')}</label>
              <select
                className="w-full border border-gray-300 rounded-lg px-3 py-2 mt-1 text-sm"
                value={selectedIndicator}
                onChange={(e) => setSelectedIndicator(e.target.value)}
              >
                <option value="all">{t('common.all')}</option>
                {localizedIndicators.map((ind) => (
                  <option key={ind.code} value={ind.code}>{ind.name}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {visibleIndicators.map((ind) => (
              <IndicatorDashboardCard
                key={ind.code}
                title={ind.name}
                description={ind.desc}
                unit={ind.unit}
                isLoading={isLoading}
                data={indicators[ind.code]}
                chartType={ind.chartType}
                valueField={ind.valueField}
                labelField={ind.labelField}
                filterText={tableSearch}
                indicatorCode={ind.code}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
