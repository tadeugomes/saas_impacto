import { useCallback, useEffect, useMemo, useState } from 'react';
import { ChevronDown, ChevronUp, Users, TrendingUp, Building2, BookOpen } from 'lucide-react';
import { FilterBar } from '../../../components/filters/FilterBar';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { ExportButton } from '../../../components/common/ExportButton';
import { useFilterStore } from '../../../store/filterStore';
import {
  type MunicipioLabelMap,
  isLikelyIdNameMismatch,
  normalizeMunicipioId,
  toMunicipioLabel,
} from '../../../utils/municipioLabels';
import { indicatorsService } from '../../../api/indicators';
import { IndicatorDashboardCard } from '../../../components/dashboard/IndicatorDashboardCard';
import type { IndicatorResponse } from '../../../types/api';
import {
  employmentMultiplierService,
  type EmploymentMultiplierResponse,
  type ConfidenceLevel,
} from '../../../api/employmentMultiplier';

// ── Types ────────────────────────────────────────────────────────────────────

interface IndicatorConfig {
  code: string;
  name: string;
  unit: string;
  desc: string;
  chartType: 'bar' | 'pie' | 'metric';
  valueField: string;
  labelField?: string;
  interpretation?: string;
}

type IndicatorBlock = 'A' | 'C';

type RawIndicatorRow = Record<string, unknown>;
type ModuleIndicatorResponse = IndicatorResponse<RawIndicatorRow>;
type IndicatorMap = Record<string, ModuleIndicatorResponse>;

// ── Constants: Bloco A — Empregos Diretos ────────────────────────────────────

const BLOCK_A_INDICATORS: (IndicatorConfig & { block: IndicatorBlock })[] = [
  {
    block: 'A', code: 'IND-3.01',
    name: 'Empregos Diretos Portuários', unit: 'Empregos',
    desc: 'Total de empregos formais no setor portuário (RAIS, vínculos ativos em 31/12)',
    chartType: 'bar', valueField: 'empregos_portuarios', labelField: 'id_municipio',
    interpretation: 'Quanto maior, maior a capacidade de geração de emprego formal do porto no município.',
  },
  {
    block: 'A', code: 'IND-3.05',
    name: 'Salário Médio Portuário', unit: 'R$',
    desc: 'Remuneração média mensal dos trabalhadores portuários',
    chartType: 'bar', valueField: 'salario_medio', labelField: 'id_municipio',
    interpretation: 'Compara a remuneração do setor portuário com a média municipal. Valores altos indicam emprego qualificado.',
  },
  {
    block: 'A', code: 'IND-3.06',
    name: 'Massa Salarial Anual', unit: 'R$',
    desc: 'Total de remuneração paga ao setor portuário no ano',
    chartType: 'bar', valueField: 'massa_salarial_anual', labelField: 'id_municipio',
    interpretation: 'Mede a injeção direta de renda do porto na economia local. Quanto maior, maior o efeito multiplicador sobre consumo.',
  },
  {
    block: 'A', code: 'IND-3.12',
    name: 'Participação no Emprego Local', unit: '%',
    desc: 'Peso do emprego portuário no total de empregos formais do município',
    chartType: 'bar', valueField: 'participacao_emprego_local', labelField: 'id_municipio',
    interpretation: 'Quanto maior, mais o município depende economicamente da atividade portuária para gerar empregos.',
  },
  {
    block: 'A', code: 'IND-3.11',
    name: 'Variação Anual de Empregos', unit: '%',
    desc: 'Variação percentual do emprego portuário em relação ao ano anterior',
    chartType: 'bar', valueField: 'variacao_anual', labelField: 'id_municipio',
    interpretation: 'Valores positivos indicam expansão do mercado de trabalho portuário; negativos indicam retração.',
  },
  {
    block: 'A', code: 'IND-3.07',
    name: 'Produtividade — Toneladas/Empregado', unit: 'ton/emp',
    desc: 'Volume de carga movimentado por trabalhador portuário',
    chartType: 'bar', valueField: 'ton_por_empregado', labelField: 'id_municipio',
    interpretation: 'Mede a eficiência operacional. Valores altos podem indicar alta mecanização ou operação de granéis.',
  },
];

// ── Constants: Bloco C — Perfil do Trabalhador ───────────────────────────────

const BLOCK_C_INDICATORS: (IndicatorConfig & { block: IndicatorBlock })[] = [
  {
    block: 'C', code: 'IND-3.02',
    name: 'Participação de Mulheres', unit: '%',
    desc: 'Percentual de mulheres no emprego portuário formal',
    chartType: 'bar', valueField: 'percentual_feminino', labelField: 'id_municipio',
    interpretation: 'Valores baixos indicam possível barreira de entrada. A média nacional do setor gira em torno de 15-20%.',
  },
  {
    block: 'C', code: 'IND-3.09',
    name: 'Distribuição por Escolaridade', unit: '%',
    desc: 'Distribuição dos trabalhadores portuários por nível de escolaridade',
    chartType: 'bar', valueField: 'distribuicao_escolaridade', labelField: 'id_municipio',
    interpretation: 'Mostra o perfil educacional da força de trabalho portuária e a demanda por qualificação.',
  },
  {
    block: 'C', code: 'IND-3.10',
    name: 'Idade Média do Trabalhador', unit: 'Anos',
    desc: 'Idade média dos trabalhadores formais do setor portuário',
    chartType: 'bar', valueField: 'idade_media', labelField: 'id_municipio',
    interpretation: 'Idades médias altas podem sinalizar dificuldade de renovação da força de trabalho.',
  },
];

const ALL_INDICATORS = [...BLOCK_A_INDICATORS, ...BLOCK_C_INDICATORS];

// ── Confidence semaphore ─────────────────────────────────────────────────────

const CONFIDENCE_CONFIG: Record<ConfidenceLevel, { color: string; bg: string; border: string; label: string; desc: string }> = {
  strong:   { color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200', label: 'Evidência forte', desc: 'Multiplicador amplamente validado na literatura internacional' },
  moderate: { color: 'text-amber-700',   bg: 'bg-amber-50',   border: 'border-amber-200',   label: 'Evidência moderada', desc: 'Baseado em estudos com amostra limitada ou contexto regional' },
  weak:     { color: 'text-red-700',     bg: 'bg-red-50',     border: 'border-red-200',     label: 'Evidência fraca', desc: 'Estimativa com alta incerteza ou amostra insuficiente' },
};

// ── Helpers ──────────────────────────────────────────────────────────────────

const createEmptyIndicatorResponse = (codigoIndicador: string): ModuleIndicatorResponse => ({
  codigo_indicador: codigoIndicador,
  nome: codigoIndicador,
  unidade: '',
  unctad: false,
  data: [],
});

function toIndicatorRows(response: ModuleIndicatorResponse): RawIndicatorRow[] {
  return response.data.filter((item): item is RawIndicatorRow => item !== null && typeof item === 'object');
}

function formatNumber(value: number, type: 'integer' | 'currency' | 'percent' | 'decimal' = 'integer'): string {
  if (type === 'currency') {
    if (value >= 1_000_000_000) return `R$ ${(value / 1_000_000_000).toFixed(1).replace('.', ',')} bi`;
    if (value >= 1_000_000) return `R$ ${(value / 1_000_000).toFixed(1).replace('.', ',')} mi`;
    if (value >= 1_000) return `R$ ${(value / 1_000).toFixed(1).replace('.', ',')} mil`;
    return `R$ ${value.toFixed(0)}`;
  }
  if (type === 'percent') return `${value.toFixed(1).replace('.', ',')}%`;
  if (type === 'decimal') return value.toFixed(1).replace('.', ',');
  return value.toLocaleString('pt-BR', { maximumFractionDigits: 0 });
}

function getTopMunicipio(indicatorsMap: IndicatorMap, code: string, valueField: string): { value: number; name: string } | null {
  const indicator = indicatorsMap[code];
  if (!indicator) return null;
  const rows = toIndicatorRows(indicator);
  if (!rows.length) return null;
  let best: { value: number; name: string } | null = null;
  for (const row of rows) {
    const val = Number(row[valueField]);
    if (!Number.isFinite(val)) continue;
    if (!best || val > best.value) {
      best = { value: val, name: typeof row.nome_municipio === 'string' ? row.nome_municipio : String(row.id_municipio ?? '') };
    }
  }
  return best;
}

// ── Component ────────────────────────────────────────────────────────────────

export function Module3View() {
  const { selectedYear, selectedInstallation } = useFilterStore();
  const [indicators, setIndicators] = useState<IndicatorMap>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tableSearch, setTableSearch] = useState('');
  const [municipioLabelIndex, setMunicipioLabelIndex] = useState<MunicipioLabelMap>({});
  const [profileOpen, setProfileOpen] = useState(false);

  // Bloco B — multiplicador
  const [multiplierData, setMultiplierData] = useState<EmploymentMultiplierResponse | null>(null);
  const [multiplierLoading, setMultiplierLoading] = useState(false);
  const [_multiplierError, setMultiplierError] = useState<string | null>(null);
  const [showCausalEstimate, setShowCausalEstimate] = useState(false);

  // ── Municipality labels ──────────────────────────────────────────────

  const resolveMunicipioLabels = useCallback(
    async (rawIds: string[]) => {
      const ids = Array.from(
        new Set(
          rawIds
            .map((id) => normalizeMunicipioId(id))
            .filter((id) => id && id.length >= 2 && !municipioLabelIndex[id]),
        ),
      );
      if (!ids.length) return;
      try {
        const response = await indicatorsService.getMunicipioLookup(ids);
        const nextLabels: MunicipioLabelMap = {};
        response.municipios.forEach((item) => {
          const municipioId = normalizeMunicipioId(item.id_municipio);
          const nomeMunicipio = item.nome_municipio?.trim();
          if (municipioId && nomeMunicipio) nextLabels[municipioId] = nomeMunicipio;
        });
        if (Object.keys(nextLabels).length > 0) {
          setMunicipioLabelIndex((current) => ({ ...current, ...nextLabels }));
        }
      } catch {
        // Falha de lookup é não-bloqueante
      }
    },
    [municipioLabelIndex],
  );

  const municipioLabelsFromIndicators = useMemo(() => {
    const lookup: MunicipioLabelMap = {};
    Object.values(indicators).forEach((indicator) => {
      toIndicatorRows(indicator).forEach((item) => {
        const id = normalizeMunicipioId(item.id_municipio);
        const nome = item.nome_municipio;
        if (id && typeof nome === 'string' && nome.trim() && !isLikelyIdNameMismatch(id, nome) && !normalizeMunicipioId(nome)) {
          lookup[id] = nome.trim();
        }
      });
    });
    return lookup;
  }, [indicators]);

  const municipioLabels = useMemo(
    () => ({ ...municipioLabelIndex, ...municipioLabelsFromIndicators }),
    [municipioLabelIndex, municipioLabelsFromIndicators],
  );

  const municipioCatalogIds = useMemo(() => {
    const ids = new Set<string>(Object.keys(municipioLabels));
    Object.values(indicators).forEach((indicator) => {
      toIndicatorRows(indicator).forEach((item) => {
        const id = normalizeMunicipioId(item.id_municipio);
        if (id) ids.add(id);
      });
    });
    return Array.from(ids);
  }, [indicators, municipioLabels]);

  useEffect(() => {
    void resolveMunicipioLabels(municipioCatalogIds);
  }, [municipioCatalogIds, resolveMunicipioLabels]);

  const getMunicipioLabel = useCallback(
    (item: RawIndicatorRow) => {
      const idMunicipio = normalizeMunicipioId(item.id_municipio);
      if (idMunicipio) return toMunicipioLabel(idMunicipio, municipioLabels);
      return typeof item.nome_municipio === 'string' && item.nome_municipio.trim()
        ? item.nome_municipio.trim() : 'N/A';
    },
    [municipioLabels],
  );

  // ── Fetch indicadores + multiplicador ──────────────────────────────────

  useEffect(() => {
    const fetchAll = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const promises = ALL_INDICATORS.map((ind) =>
          indicatorsService
            .queryIndicator<RawIndicatorRow>({
              codigo_indicador: ind.code,
              params: { ano: selectedYear, id_instalacao: selectedInstallation || undefined },
            })
            .catch(() => createEmptyIndicatorResponse(ind.code)),
        );
        const results = await Promise.all(promises);
        const mapped: IndicatorMap = {};
        results.forEach((result, i) => {
          mapped[ALL_INDICATORS[i].code] = result;
        });
        setIndicators(mapped);

        // Tentar buscar multiplicador para o município com mais empregos
        const empRows = toIndicatorRows(mapped['IND-3.01'] ?? createEmptyIndicatorResponse('IND-3.01'));
        if (empRows.length > 0) {
          const topRow = empRows.reduce((best, curr) => {
            const bestVal = Number(best.empregos_portuarios ?? 0);
            const currVal = Number(curr.empregos_portuarios ?? 0);
            return currVal > bestVal ? curr : best;
          }, empRows[0]);
          const munId = normalizeMunicipioId(topRow.id_municipio);
          if (munId) {
            setMultiplierLoading(true);
            try {
              const multResp = await employmentMultiplierService.getMultiplierEstimate(
                munId, selectedYear ?? undefined, false,
              );
              setMultiplierData(multResp);
            } catch {
              setMultiplierError('Multiplicador indisponível');
            } finally {
              setMultiplierLoading(false);
            }
          }
        }
      } catch (err: unknown) {
        const errorResponse = err as { response?: { data?: { detail?: unknown } } };
        const errorMessage = errorResponse?.response?.data?.detail || 'Erro ao carregar indicadores';
        setError(typeof errorMessage === 'string' ? errorMessage : 'Erro ao carregar indicadores');
      } finally {
        setIsLoading(false);
      }
    };
    fetchAll();
  }, [selectedYear, selectedInstallation]);

  // ── Derived data ───────────────────────────────────────────────────────

  const topDirectJobs = useMemo(() => getTopMunicipio(indicators, 'IND-3.01', 'empregos_portuarios'), [indicators]);
  const topSalary = useMemo(() => getTopMunicipio(indicators, 'IND-3.05', 'salario_medio'), [indicators]);
  const topPayroll = useMemo(() => getTopMunicipio(indicators, 'IND-3.06', 'massa_salarial_anual'), [indicators]);
  const topShare = useMemo(() => getTopMunicipio(indicators, 'IND-3.12', 'participacao_emprego_local'), [indicators]);

  const activeEstimate = useMemo(() => {
    if (!multiplierData) return null;
    if (showCausalEstimate && multiplierData.causal_estimate) return multiplierData.causal_estimate;
    return multiplierData.estimate;
  }, [multiplierData, showCausalEstimate]);

  // ── Loading state ──────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Emprego e Renda Portuária</h1>
        <LoadingSpinner />
      </div>
    );
  }

  // ── Render ─────────────────────────────────────────────────────────────

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Users className="h-8 w-8 text-amber-600" />
            Emprego e Renda Portuária
          </h1>
          <p className="text-gray-500 mt-1">
            Analise como a atividade portuária gera empregos diretos, indiretos e renda para os trabalhadores
          </p>
        </div>
        <ExportButton moduleCode="3" />
      </div>

      <FilterBar />

      {error && <ErrorAlert message={error} className="mb-4" />}

      {/* ═══════════════════════════════════════════════════════════════════
          BLOCO A — Empregos Diretos (RAIS)
          ═══════════════════════════════════════════════════════════════════ */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Building2 className="h-5 w-5 text-amber-600" />
          <h2 className="text-xl font-semibold text-gray-900">Empregos Diretos no Setor Portuário</h2>
        </div>

        <p className="text-sm text-gray-500 mb-4">
          Dados da RAIS (Relação Anual de Informações Sociais) filtrados pelos 24 CNAEs do setor portuário e aquaviário.
        </p>

        {/* Mini-cards resumo */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs text-gray-500 mb-1">Maior empregador</p>
            <p className="text-2xl font-bold text-amber-700">{topDirectJobs ? formatNumber(topDirectJobs.value) : '—'}</p>
            <p className="text-xs text-gray-400 mt-1 truncate">{topDirectJobs?.name ?? '—'}</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs text-gray-500 mb-1">Maior salário médio</p>
            <p className="text-2xl font-bold text-amber-700">{topSalary ? formatNumber(topSalary.value, 'currency') : '—'}</p>
            <p className="text-xs text-gray-400 mt-1 truncate">{topSalary?.name ?? '—'}</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs text-gray-500 mb-1">Maior massa salarial</p>
            <p className="text-2xl font-bold text-amber-700">{topPayroll ? formatNumber(topPayroll.value, 'currency') : '—'}</p>
            <p className="text-xs text-gray-400 mt-1 truncate">{topPayroll?.name ?? '—'}</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs text-gray-500 mb-1">Maior participação local</p>
            <p className="text-2xl font-bold text-amber-700">{topShare ? formatNumber(topShare.value, 'percent') : '—'}</p>
            <p className="text-xs text-gray-400 mt-1 truncate">{topShare?.name ?? '—'}</p>
          </div>
        </div>

        {/* Filtro de busca */}
        <div className="mb-4">
          <input
            className="w-full max-w-sm border border-gray-300 rounded-lg px-3 py-2 text-sm"
            placeholder="Filtrar município no ranking..."
            value={tableSearch}
            onChange={(e) => setTableSearch(e.target.value)}
          />
        </div>

        {/* Gráficos do Bloco A */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {BLOCK_A_INDICATORS.map((ind) => (
            <div key={ind.code}>
              <IndicatorDashboardCard
                title={ind.name}
                description={ind.desc}
                unit={ind.unit}
                isLoading={isLoading}
                data={indicators[ind.code]}
                chartType={ind.chartType}
                valueField={ind.valueField}
                labelAccessor={(item) => getMunicipioLabel(item)}
                filterText={tableSearch}
                indicatorCode={ind.code}
              />
              {ind.interpretation && (
                <p className="mt-1 px-3 text-xs text-gray-400 italic">{ind.interpretation}</p>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          BLOCO B — Empregos Indiretos e Induzidos (Multiplicadores)
          ═══════════════════════════════════════════════════════════════════ */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="h-5 w-5 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">Impacto Indireto no Emprego Local</h2>
        </div>

        <p className="text-sm text-gray-500 mb-4">
          Estimativa de quantos empregos indiretos (cadeia de fornecedores) e induzidos (consumo dos trabalhadores)
          são gerados pela atividade portuária, além dos empregos diretos registrados na RAIS.
        </p>

        {multiplierLoading && <LoadingSpinner />}

        {multiplierData && activeEstimate && (
          <div className="space-y-4">
            {/* Card principal de multiplicador */}
            <div className={`rounded-xl border p-6 ${CONFIDENCE_CONFIG[activeEstimate.confidence].bg} ${CONFIDENCE_CONFIG[activeEstimate.confidence].border}`}>
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {activeEstimate.municipality_name
                      ? `Impacto do Porto em ${activeEstimate.municipality_name}`
                      : 'Impacto Estimado no Emprego'}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {activeEstimate.multiplier_type === 'literature'
                      ? `Multiplicador: ${activeEstimate.multiplier_used}× (${multiplierData.literature.source})`
                      : `Estimativa causal — ${multiplierData.causal?.method === 'iv_2sls' ? 'Variáveis Instrumentais' : 'Painel IV'}`}
                  </p>
                </div>
                <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${CONFIDENCE_CONFIG[activeEstimate.confidence].bg} ${CONFIDENCE_CONFIG[activeEstimate.confidence].color}`}>
                  {activeEstimate.confidence === 'strong' ? '🟢' : activeEstimate.confidence === 'moderate' ? '🟡' : '🔴'}
                  {' '}{CONFIDENCE_CONFIG[activeEstimate.confidence].label}
                </span>
              </div>

              {/* Números grandes */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="text-center">
                  <p className="text-3xl font-bold text-gray-900">{formatNumber(activeEstimate.direct_jobs)}</p>
                  <p className="text-xs text-gray-500 mt-1">Empregos diretos</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-blue-700">{formatNumber(activeEstimate.indirect_estimated)}</p>
                  <p className="text-xs text-gray-500 mt-1">Indiretos estimados</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-indigo-700">{formatNumber(activeEstimate.induced_estimated)}</p>
                  <p className="text-xs text-gray-500 mt-1">Induzidos estimados</p>
                </div>
                <div className="text-center bg-white rounded-lg p-2 border border-gray-200">
                  <p className="text-3xl font-bold text-amber-700">{formatNumber(activeEstimate.total_impact)}</p>
                  <p className="text-xs text-gray-500 mt-1">Impacto total</p>
                </div>
              </div>

              {/* Frase executiva */}
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <p className="text-sm text-gray-700">
                  {activeEstimate.municipality_name ? (
                    <>
                      O setor portuário de <strong>{activeEstimate.municipality_name}</strong> sustenta
                      diretamente <strong>{formatNumber(activeEstimate.direct_jobs)} empregos formais</strong>.
                      Com base no multiplicador de <strong>{activeEstimate.multiplier_used}×</strong>,
                      estima-se que a atividade portuária gere adicionalmente
                      cerca de <strong>{formatNumber(activeEstimate.indirect_estimated)} empregos indiretos</strong> (na cadeia de fornecedores)
                      e <strong>{formatNumber(activeEstimate.induced_estimated)} empregos induzidos</strong> (pelo consumo dos trabalhadores),
                      totalizando aproximadamente <strong>{formatNumber(activeEstimate.total_impact)} empregos</strong> vinculados
                      ao porto.
                    </>
                  ) : (
                    <>
                      Com base no multiplicador de <strong>{activeEstimate.multiplier_used}×</strong>,
                      cada emprego direto no porto gera aproximadamente {(activeEstimate.multiplier_used - 1).toFixed(1)} empregos
                      adicionais na economia local.
                    </>
                  )}
                </p>
              </div>

              {/* Fonte e confiança */}
              <p className="text-xs text-gray-400 mt-3">
                {CONFIDENCE_CONFIG[activeEstimate.confidence].desc}. Fonte: {activeEstimate.source}.
              </p>
            </div>

            {/* Intervalo de multiplicadores da literatura */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Intervalo de multiplicadores (literatura internacional)</h4>
              <div className="flex items-center gap-2 mb-2">
                <div className="flex-1 bg-gray-100 rounded-full h-3 relative">
                  <div
                    className="bg-amber-400 h-3 rounded-full absolute"
                    style={{
                      left: `${((multiplierData.literature.range_low - 1) / 5) * 100}%`,
                      width: `${((multiplierData.literature.range_high - multiplierData.literature.range_low) / 5) * 100}%`,
                    }}
                  />
                  <div
                    className="bg-amber-700 h-5 w-1 rounded absolute -top-1"
                    style={{ left: `${((multiplierData.literature.coefficient - 1) / 5) * 100}%` }}
                  />
                </div>
              </div>
              <div className="flex justify-between text-xs text-gray-400">
                <span>1× (sem efeito)</span>
                <span>{multiplierData.literature.range_low}× — {multiplierData.literature.range_high}×</span>
                <span>6× (alto impacto)</span>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                A literatura indica que o setor portuário tem multiplicador entre {multiplierData.literature.range_low}× e {multiplierData.literature.range_high}×,
                com estimativa central de {multiplierData.literature.coefficient}×.
                Isso significa que cada emprego direto gera entre {(multiplierData.literature.range_low - 1).toFixed(1)} e {(multiplierData.literature.range_high - 1).toFixed(1)} empregos adicionais.
              </p>
            </div>

            {/* Toggle causal */}
            {multiplierData.causal && multiplierData.causal_estimate && (
              <button
                onClick={() => setShowCausalEstimate(!showCausalEstimate)}
                className="text-sm text-blue-600 hover:text-blue-800 underline"
              >
                {showCausalEstimate ? 'Ver estimativa da literatura' : 'Ver estimativa causal (baseada em dados do município)'}
              </button>
            )}
          </div>
        )}

        {!multiplierLoading && !multiplierData && (
          <div className="bg-gray-50 rounded-xl border border-gray-200 p-6 text-center">
            <p className="text-gray-500">
              Selecione um ano e uma instalação nos filtros acima para calcular o multiplicador de emprego.
            </p>
          </div>
        )}
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          BLOCO C — Perfil do Trabalhador Portuário (colapsável)
          ═══════════════════════════════════════════════════════════════════ */}
      <section>
        <button
          onClick={() => setProfileOpen(!profileOpen)}
          className="flex items-center gap-2 w-full text-left"
        >
          <BookOpen className="h-5 w-5 text-gray-500" />
          <h2 className="text-xl font-semibold text-gray-900">Perfil do Trabalhador Portuário</h2>
          {profileOpen
            ? <ChevronUp className="h-5 w-5 text-gray-400 ml-auto" />
            : <ChevronDown className="h-5 w-5 text-gray-400 ml-auto" />}
        </button>

        <p className="text-sm text-gray-500 mt-1 mb-4">
          Gênero, escolaridade e idade dos trabalhadores do setor portuário.
        </p>

        {profileOpen && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {BLOCK_C_INDICATORS.map((ind) => (
              <div key={ind.code}>
                <IndicatorDashboardCard
                  title={ind.name}
                  description={ind.desc}
                  unit={ind.unit}
                  isLoading={isLoading}
                  data={indicators[ind.code]}
                  chartType={ind.chartType}
                  valueField={ind.valueField}
                  labelAccessor={(item) => getMunicipioLabel(item)}
                  filterText={tableSearch}
                  indicatorCode={ind.code}
                />
                {ind.interpretation && (
                  <p className="mt-1 px-3 text-xs text-gray-400 italic">{ind.interpretation}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
