import { useCallback, useEffect, useMemo, useState } from 'react';
import { ChevronDown, ChevronUp, Users, TrendingUp, Building2, BookOpen } from 'lucide-react';
import { FilterBar } from '../../../components/filters/FilterBar';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { ExportButton } from '../../../components/common/ExportButton';
import { ChartCard } from '../../../components/charts/ChartCard';
import { LineChart } from '../../../components/charts/LineChart';
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
import { getIndicatorFormat } from '../../../utils/chartFormats';
import {
  employmentMultiplierService,
  type EmploymentMultiplierResponse,
  type EmploymentMultiplierConfidenceEstimate,
  type EmploymentMultiplierImpactRow,
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

interface TrendIndicatorConfig {
  code: string;
  name: string;
  unit: string;
  valueField: string;
  valueAlias?: string;
  description: string;
}

type IndicatorBlock = 'A' | 'C';

type RawIndicatorRow = Record<string, unknown>;
type ModuleIndicatorResponse = IndicatorResponse<RawIndicatorRow>;
type IndicatorMap = Record<string, ModuleIndicatorResponse>;
type IndicatorErrorMap = Record<string, string | null>;
type IndicatorWarningMap = Record<string, string[]>;

const TREND_YEARS = 5;
const SIMULATION_MIN_DELTA = -50;
const SIMULATION_MAX_DELTA = 100;
const QUICK_SIMULATION_DELTAS = [-50, -25, -10, 0, 10, 25, 50, 100] as const;

// IND-3.09 usa grau_instrucao como dimensão; IND-3.03 foi removido
const DIMENSION_LABEL_FIELDS: Record<string, string> = {
  'IND-3.09': 'grau_instrucao',
};

const TREND_INDICATORS: TrendIndicatorConfig[] = [
  {
    code: 'IND-3.01',
    name: 'Evolução de Empregos Diretos',
    unit: 'Empregos',
    valueField: 'empregos_portuarios',
    description: 'Série anual para o município selecionado.',
  },
  {
    code: 'IND-3.05',
    name: 'Evolução do Salário Médio',
    unit: 'R$',
    valueField: 'salario_medio',
    description: 'Série anual da remuneração média.',
  },
  {
    code: 'IND-3.06',
    name: 'Evolução da Massa Salarial',
    unit: 'R$',
    valueField: 'massa_salarial_anual',
    description: 'Série anual da massa salarial do trabalho portuário.',
  },
  {
    code: 'IND-3.11',
    name: 'Evolução da Variação de Empregos',
    unit: '%',
    valueField: 'variacao_percentual',
    description: 'Série anual da variação percentual de empregos.',
  },
];

// ── Constants: Bloco A — Empregos Diretos ────────────────────────────────────
// IND-3.03 removido: paridade por categoria não identificável na RAIS com filtro CNAE portuário

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
    block: 'A', code: 'IND-3.08',
    name: 'Receita por Empregado (proxy PIB)', unit: 'R$/emp',
    desc: 'PIB municipal por empregado portuário — proxy de produtividade econômica (dados indisponíveis diretamente na RAIS)',
    chartType: 'bar', valueField: 'pib_por_empregado_portuario', labelField: 'id_municipio',
    interpretation: 'Proxy de valor gerado por trabalhador portuário. Requer cruzamento com dados de PIB; pode estar indisponível para alguns municípios.',
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
    chartType: 'bar', valueField: 'variacao_percentual', labelField: 'id_municipio',
    interpretation: 'Valores positivos indicam expansão do mercado de trabalho portuário; negativos indicam retração.',
  },
  {
    block: 'A', code: 'IND-3.07',
    name: 'Produtividade — Toneladas/Empregado', unit: 'ton/emp',
    desc: 'Volume de carga movimentado por trabalhador portuário (RAIS + ANTAQ)',
    chartType: 'bar', valueField: 'ton_por_empregado', labelField: 'id_municipio',
    interpretation: 'Mede a eficiência operacional. Valores altos podem indicar alta mecanização ou operação de granéis. Requer cruzamento RAIS+ANTAQ; pode estar indisponível para alguns municípios.',
  },
];

// ── Constants: Bloco C — Perfil do Trabalhador ───────────────────────────────
// IND-3.03 removido: paridade por categoria não identificável na RAIS com filtro CNAE portuário

const BLOCK_C_INDICATORS: (IndicatorConfig & { block: IndicatorBlock })[] = [
  {
    block: 'C', code: 'IND-3.02',
    name: 'Participação de Mulheres', unit: '%',
    desc: 'Percentual de mulheres no emprego portuário formal',
    chartType: 'bar', valueField: 'percentual_feminino', labelField: 'id_municipio',
    interpretation: 'Valores baixos indicam possível barreira de entrada. A média nacional do setor gira em torno de 15-20%.',
  },
  {
    block: 'C', code: 'IND-3.04',
    name: 'Taxa de Emprego Temporário', unit: '%',
    desc: 'Percentual de contratos temporários no setor portuário (dados podem ser escassos na RAIS formal)',
    chartType: 'bar', valueField: 'taxa_temporario', labelField: 'id_municipio',
    interpretation: 'Valores elevados podem indicar sazonalidade operacional ou precarização do vínculo empregatício.',
  },
  {
    block: 'C', code: 'IND-3.09',
    name: 'Distribuição por Escolaridade', unit: '%',
    desc: 'Distribuição dos trabalhadores portuários por nível de escolaridade (selecione um município para ver o detalhamento por grau)',
    chartType: 'bar', valueField: 'percentual', labelField: 'id_municipio',
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

type ConfidenceLevel = 'strong' | 'moderate' | 'weak';

const CONFIDENCE_CONFIG: Record<ConfidenceLevel, { color: string; bg: string; border: string; label: string; desc: string }> = {
  strong:   { color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200', label: 'Evidência forte', desc: 'Multiplicador amplamente validado na literatura internacional' },
  moderate: { color: 'text-amber-700',   bg: 'bg-amber-50',   border: 'border-amber-200',   label: 'Evidência moderada', desc: 'Baseado em estudos com amostra limitada ou contexto regional' },
  weak:     { color: 'text-red-700',     bg: 'bg-red-50',     border: 'border-red-200',     label: 'Evidência fraca', desc: 'Estimativa com alta incerteza ou amostra insuficiente' },
};

interface EmploymentSimulation {
  deltaTonelagem: number;
  baselineTonelagemMilhoes: number | null;
  targetTonelagemMilhoes: number | null;
  diretos: number;
  diretosDelta: number;
  indiretos: number;
  indiretosDelta: number;
  induzidos: number;
  induzidosDelta: number;
  total: number;
  totalDelta: number;
}

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

function parseNumber(value: unknown): number | null {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null;
  }

  if (typeof value === 'string') {
    const normalized = value
      .trim()
      .replace(/\s/g, '')
      .replace(/\./g, '')
      .replace(',', '.');
    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

function parseYear(value: unknown): number | null {
  if (typeof value === 'number') {
    const year = Number.isFinite(value) ? Math.trunc(value) : null;
    return year;
  }

  if (typeof value === 'string') {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

function getValueFromRow(row: RawIndicatorRow, field: string): number | null {
  return parseNumber(row[field]);
}

type TrendSeries = {
  labels: string[];
  values: number[];
};

function buildTrendSeries(rows: Array<{ row: RawIndicatorRow; value: number }>): TrendSeries | null {
  const byYear: Array<{ year: number; value: number }> = rows
    .map((entry) => ({ year: parseYear(entry.row.ano), value: entry.value }))
    .filter((entry): entry is { year: number; value: number } => entry.year !== null);

  if (!byYear.length) {
    return null;
  }

  const dedup = new Map<number, number>();
  for (const item of byYear) {
    dedup.set(item.year, item.value);
  }

  const ordered = Array.from(dedup.entries()).sort((a, b) => a[0] - b[0]);

  if (ordered.length < 2) {
    return null;
  }

  return {
    labels: ordered.map(([year]) => String(year)),
    values: ordered.map(([, value]) => value),
  };
}

function computeGrowth(values: number[]): number | null {
  if (values.length < 2) {
    return null;
  }

  const first = values[0];
  const last = values[values.length - 1];
  if (!Number.isFinite(first) || !Number.isFinite(last) || first === undefined || last === undefined || first === 0) {
    return null;
  }

  return ((last - first) / first) * 100;
}

function formatTonelagem(value: number): string {
  return `${value.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 2 })} mi t`;
}

function parseSimulationBaseline(row: EmploymentMultiplierImpactRow | undefined): number | null {
  return parseNumber(row?.tonelagem_antaq_milhoes);
}

function buildSimulation(
  estimate: EmploymentMultiplierConfidenceEstimate | null,
  baseTonelagemMilhoes: number | null,
  deltaTonelagemPercent: number,
  scenarioRow?: EmploymentMultiplierImpactRow | null,
): EmploymentSimulation | null {
  if (!estimate) return null;
  const factor = 1 + (Number(deltaTonelagemPercent) || 0) / 100;
  const safeFactor = Math.max(0, factor);
  const clampNonNegative = (value: number): number => Number(Math.max(0, value).toFixed(2));
  const scenario = scenarioRow?.scenario;
  const hasScenario = scenario !== null
    && scenario !== undefined
    && Math.abs(scenario.delta_tonelagem_pct - deltaTonelagemPercent) < 0.0001;

  if (baseTonelagemMilhoes === null) {
    return {
      deltaTonelagem: deltaTonelagemPercent,
      baselineTonelagemMilhoes: null,
      targetTonelagemMilhoes: null,
      diretos: hasScenario
        ? clampNonNegative(estimate.direct_jobs + scenario.delta_empregos_diretos)
        : Math.max(0, Math.round(estimate.direct_jobs * safeFactor)),
      diretosDelta: hasScenario
        ? Number(scenario.delta_empregos_diretos.toFixed(2))
        : Number((Math.max(0, Math.round(estimate.direct_jobs * safeFactor)) - estimate.direct_jobs).toFixed(2)),
      indiretos: hasScenario
        ? clampNonNegative(estimate.indirect_estimated + scenario.delta_empregos_indiretos)
        : Number((estimate.indirect_estimated * safeFactor).toFixed(2)),
      indiretosDelta: hasScenario
        ? Number(scenario.delta_empregos_indiretos.toFixed(2))
        : Number((Number((estimate.indirect_estimated * safeFactor).toFixed(2)) - estimate.indirect_estimated).toFixed(2)),
      induzidos: hasScenario
        ? clampNonNegative(estimate.induced_estimated + scenario.delta_empregos_induzidos)
        : Number((estimate.induced_estimated * safeFactor).toFixed(2)),
      induzidosDelta: hasScenario
        ? Number(scenario.delta_empregos_induzidos.toFixed(2))
        : Number((Number((estimate.induced_estimated * safeFactor).toFixed(2)) - estimate.induced_estimated).toFixed(2)),
      total: hasScenario
        ? clampNonNegative(estimate.total_impact + scenario.delta_emprego_total)
        : Number((estimate.direct_jobs * safeFactor + estimate.indirect_estimated * safeFactor + estimate.induced_estimated * safeFactor).toFixed(2)),
      totalDelta: hasScenario
        ? Number(scenario.delta_emprego_total.toFixed(2))
        : Number((Number((estimate.direct_jobs * safeFactor + estimate.indirect_estimated * safeFactor + estimate.induced_estimated * safeFactor).toFixed(2)) - estimate.total_impact).toFixed(2)),
    };
  }

  const projectedTonelagem = Number((baseTonelagemMilhoes * safeFactor).toFixed(3));

  const diretos = hasScenario
    ? clampNonNegative(estimate.direct_jobs + scenario.delta_empregos_diretos)
    : Math.max(0, Math.round(estimate.direct_jobs * safeFactor));
  const indiretos = hasScenario
    ? clampNonNegative(estimate.indirect_estimated + scenario.delta_empregos_indiretos)
    : Math.max(0, Number((estimate.indirect_estimated * safeFactor).toFixed(2)));
  const induzidos = hasScenario
    ? clampNonNegative(estimate.induced_estimated + scenario.delta_empregos_induzidos)
    : Math.max(0, Number((estimate.induced_estimated * safeFactor).toFixed(2)));
  const total = hasScenario
    ? clampNonNegative(estimate.total_impact + scenario.delta_emprego_total)
    : Math.max(0, Number((estimate.direct_jobs * safeFactor + estimate.indirect_estimated * safeFactor + estimate.induced_estimated * safeFactor).toFixed(2)));

  const diretosDelta = hasScenario
    ? Number(scenario.delta_empregos_diretos.toFixed(2))
    : Number((diretos - estimate.direct_jobs).toFixed(2));
  const indiretosDelta = hasScenario
    ? Number(scenario.delta_empregos_indiretos.toFixed(2))
    : Number((indiretos - estimate.indirect_estimated).toFixed(2));
  const induzidosDelta = hasScenario
    ? Number(scenario.delta_empregos_induzidos.toFixed(2))
    : Number((induzidos - estimate.induced_estimated).toFixed(2));
  const totalDelta = hasScenario
    ? Number(scenario.delta_emprego_total.toFixed(2))
    : Number((total - estimate.total_impact).toFixed(2));

  return {
    deltaTonelagem: deltaTonelagemPercent,
    baselineTonelagemMilhoes: baseTonelagemMilhoes,
    targetTonelagemMilhoes: projectedTonelagem,
    diretos,
    diretosDelta,
    indiretos,
    indiretosDelta,
    induzidos,
    induzidosDelta,
    total,
    totalDelta,
  };
}

function formatDelta(value: number): string {
  const prefix = value > 0 ? '+' : value < 0 ? '−' : '';
  return `${prefix}${value.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 2 })}`;
}

function formatDeltaBadgeClass(value: number): string {
  if (value > 0) return 'text-emerald-700 bg-emerald-50 border-emerald-200';
  if (value < 0) return 'text-red-700 bg-red-50 border-red-200';
  return 'text-gray-700 bg-gray-50 border-gray-200';
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
    const val = parseNumber(row[valueField]);
    if (val === null) continue;
    if (!best || val > best.value) {
      best = { value: val, name: typeof row.nome_municipio === 'string' ? row.nome_municipio : String(row.id_municipio ?? '') };
    }
  }
  return best;
}

// ── Component ────────────────────────────────────────────────────────────────

export function Module3View() {
  const { selectedYear } = useFilterStore();
  const [indicators, setIndicators] = useState<IndicatorMap>({});
  const [trendIndicators, setTrendIndicators] = useState<IndicatorMap>({});
  const [indicatorErrors, setIndicatorErrors] = useState<IndicatorErrorMap>({});
  const [indicatorWarnings, setIndicatorWarnings] = useState<IndicatorWarningMap>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trendLoading, setTrendLoading] = useState(false);
  const [trendError, setTrendError] = useState<string | null>(null);
  const [tableSearch, setTableSearch] = useState('');
  const [municipioLabelIndex, setMunicipioLabelIndex] = useState<MunicipioLabelMap>({});
  const [profileOpen, setProfileOpen] = useState(false);
  const [selectedMunicipio, setSelectedMunicipio] = useState('');
  const [salaryQueryInput, setSalaryQueryInput] = useState('');
  const [salaryComparisonText, setSalaryComparisonText] = useState('');
  const [simulationDelta, setSimulationDelta] = useState<number>(0);

  // Bloco B — multiplicador
  const [multiplierData, setMultiplierData] = useState<EmploymentMultiplierResponse | null>(null);
  const [multiplierLoading, setMultiplierLoading] = useState(false);
  const [_multiplierError, setMultiplierError] = useState<string | null>(null);
  const [simulationMultiplierData, setSimulationMultiplierData] = useState<EmploymentMultiplierResponse | null>(null);
  const [simulationMultiplierLoading, setSimulationMultiplierLoading] = useState(false);
  const [_simulationMultiplierError, setSimulationMultiplierError] = useState<string | null>(null);
  const [showCausalEstimate, setShowCausalEstimate] = useState(false);

  // Detecta hint de ano RAIS a partir dos warnings retornados
  // Quando RAIS 2023 não está disponível, a API retorna warning indicando o último ano disponível
  const [raisYearHint, setRaisYearHint] = useState<number | null>(null);

  const formatIndicatorError = (err: unknown): string | null => {
    const errorLike = err as {
      response?: { data?: { detail?: string | Array<string> | Record<string, string> } };
      message?: string;
    };

    const detail = errorLike?.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) {
      const detailText = detail.trim();
      if (detailText.includes('Quota exceeded')) {
        return 'Consulta indisponível temporariamente: limite de cota de processamento do BigQuery atingido.';
      }
      return detailText;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      return detail.join('; ');
    }
    if (typeof detail === 'object' && detail !== null) {
      const detailText = JSON.stringify(detail);
      return detailText.length ? detailText : 'Erro desconhecido ao carregar indicador';
    }
    if (typeof errorLike.message === 'string' && errorLike.message.trim()) {
      return errorLike.message;
    }
    return 'Erro ao carregar indicador';
  };

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

  const municipioOptions = useMemo(
    () => {
      const options = Array.from(new Set(municipioCatalogIds))
        .map((id) => ({
          value: id,
          label: toMunicipioLabel(id, municipioLabels, { showCode: false }),
        }))
        .sort((a, b) => a.label.localeCompare(b.label));
      return [{ value: '', label: 'Todos os municípios' }, ...options];
    },
    [municipioCatalogIds, municipioLabels],
  );

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

  const getLabelAccessor = useCallback(
    (code: string) => {
      const dimensionField = DIMENSION_LABEL_FIELDS[code];
      if (dimensionField) {
        // Usa a dimensão própria do indicador (ex.: grau_instrucao para IND-3.09)
        // quando um município está selecionado, ou quando os dados são de dimensão múltipla
        // (IND-3.09 retorna linhas por grau_instrucao, não por município)
        if (selectedMunicipio) {
          return (item: RawIndicatorRow) => {
            const dimensionValue = item[dimensionField];
            if (typeof dimensionValue === 'string' && dimensionValue.trim()) {
              return dimensionValue.trim();
            }
            return getMunicipioLabel(item);
          };
        }
        // Sem município selecionado: IND-3.09 retorna linhas por município+grau_instrucao.
        // Mostra "Município — Grau" para distinguir linhas com mesmo município.
        return (item: RawIndicatorRow) => {
          const dimensionValue = item[dimensionField];
          const municipio = getMunicipioLabel(item);
          if (typeof dimensionValue === 'string' && dimensionValue.trim()) {
            return `${municipio} — ${dimensionValue.trim()}`;
          }
          return municipio;
        };
      }
      return getMunicipioLabel;
    },
    [selectedMunicipio, getMunicipioLabel],
  );

  const getSingleIndicatorValue = useCallback(
    (code: string, field: string): number | null => {
      const response = indicators[code];
      if (!response) return null;
      const rows = toIndicatorRows(response);
      if (!rows.length) return null;

      if (!selectedMunicipio) {
        return getValueFromRow(rows[0], field);
      }

      for (const row of rows) {
        const rowMunicipio = normalizeMunicipioId(row.id_municipio);
        if (rowMunicipio === selectedMunicipio) {
          const value = getValueFromRow(row, field);
          if (value !== null) return value;
        }
      }

      return getValueFromRow(rows[0], field);
    },
    [indicators, selectedMunicipio],
  );

  // ── Fetch indicadores + multiplicador ──────────────────────────────────

  useEffect(() => {
    const fetchAll = async () => {
      setIsLoading(true);
      setError(null);
      setIndicatorErrors({});
      setIndicatorWarnings({});
      setMultiplierData(null);
      setSimulationMultiplierData(null);
      try {
        const promises = ALL_INDICATORS.map((ind) => (
          indicatorsService
            .queryIndicator<RawIndicatorRow>({
              codigo_indicador: ind.code,
              params: {
                ano: selectedYear,
                ...(selectedMunicipio ? { id_municipio: selectedMunicipio } : {}),
              },
            })
            .then((response) => ({ code: ind.code, response, error: null as string | null }))
            .catch((err: unknown) => ({
              code: ind.code,
              response: createEmptyIndicatorResponse(ind.code),
              error: formatIndicatorError(err),
            }))
        ));
        const results = await Promise.all(promises);
        const mapped: IndicatorMap = {};
        const errors: IndicatorErrorMap = {};
        const warnings: IndicatorWarningMap = {};
        results.forEach((result) => {
          mapped[result.code] = result.response;
          if (result.error) {
            errors[result.code] = result.error;
          }
          const responseWarnings = result.response.warnings?.map((item) => item.mensagem).filter(
            (message): message is string => typeof message === 'string' && message.trim().length > 0,
          ) ?? [];
          if (responseWarnings.length) {
            warnings[result.code] = responseWarnings;
          }
        });
        setIndicators(mapped);
        setIndicatorErrors(errors);
        setIndicatorWarnings(warnings);
        if (Object.keys(errors).length > 0) {
          setError('Alguns indicadores não puderam ser carregados. Verifique os detalhes por card.');
        }

        // Detecta se a RAIS não tem dados para o ano selecionado
        // A API retorna warning "ano_apos_cobertura" com o último ano disponível
        const allEmpty = results.every((r) => r.response.data.length === 0);
        if (allEmpty) {
          // Tenta extrair o ano máximo disponível dos warnings
          let detectedMaxYear: number | null = null;
          for (const result of results) {
            const warn = result.response.warnings ?? [];
            for (const w of warn) {
              if (typeof w.mensagem === 'string') {
                const match = w.mensagem.match(/[Úú]ltimo ano com dados[:\s]+(\d{4})/);
                if (match) {
                  const yr = Number(match[1]);
                  if (!detectedMaxYear || yr > detectedMaxYear) detectedMaxYear = yr;
                }
              }
            }
          }
          setRaisYearHint(detectedMaxYear);
        } else {
          setRaisYearHint(null);
        }

        // Tentar buscar multiplicador para o município selecionado, ou no agregado geral.
        const allEmploymentRows = toIndicatorRows(mapped['IND-3.01'] ?? createEmptyIndicatorResponse('IND-3.01'));
        const selectedEmploymentRows = selectedMunicipio
          ? allEmploymentRows.filter((row) => normalizeMunicipioId(row.id_municipio) === selectedMunicipio)
          : allEmploymentRows;
        const employmentRows = selectedEmploymentRows.length > 0 ? selectedEmploymentRows : allEmploymentRows;

        if (employmentRows.length > 0) {
          const topRow = employmentRows.reduce((best, curr) => {
            const bestVal = Number(best.empregos_portuarios ?? 0);
            const currVal = Number(curr.empregos_portuarios ?? 0);
            return currVal > bestVal ? curr : best;
          }, employmentRows[0]);
          const munId = normalizeMunicipioId(topRow.id_municipio);
          if (munId) {
            setMultiplierLoading(true);
            try {
              const multResp = await employmentMultiplierService.getMultiplierEstimate(
                munId, selectedYear ?? undefined, false,
              );
              setMultiplierData(multResp);
              setSimulationMultiplierData(multResp);
            } catch {
              setMultiplierError('Multiplicador indisponível');
              setSimulationMultiplierData(null);
            } finally {
              setMultiplierLoading(false);
            }
          }
        }
      } catch (err: unknown) {
        const errorResponse = err as { response?: { data?: { detail?: unknown } } };
        const errorMessage = errorResponse?.response?.data?.detail || 'Erro ao carregar indicadores';
        setError(typeof errorMessage === 'string' ? errorMessage : 'Erro ao carregar indicadores');
        setIndicatorWarnings({});
      } finally {
        setIsLoading(false);
      }
    };
    fetchAll();
  }, [selectedYear, selectedMunicipio]);

  useEffect(() => {
    const fetchTrendIndicators = async () => {
      if (!selectedMunicipio) {
        setTrendIndicators({});
        setTrendLoading(false);
        setTrendError(null);
        return;
      }

      setTrendLoading(true);
      setTrendError(null);
      try {
        const startYear = selectedYear - TREND_YEARS;
        const trendParams = {
          id_municipio: selectedMunicipio,
          ano_inicio: startYear,
          ano_fim: selectedYear,
        };
        const promises = TREND_INDICATORS.map((indicator) =>
          indicatorsService
            .queryIndicator<RawIndicatorRow>({
              codigo_indicador: indicator.code,
              params: trendParams,
            })
            .then((response) => ({ code: indicator.code, response, error: null as string | null }))
            .catch((err: unknown) => ({
              code: indicator.code,
              response: createEmptyIndicatorResponse(indicator.code),
              error: formatIndicatorError(err),
            })),
        );

        const results = await Promise.all(promises);
        const nextIndicators: IndicatorMap = {};
        const nextWarnings: IndicatorWarningMap = {};
        const nextErrors: IndicatorErrorMap = {};

        results.forEach((result) => {
          nextIndicators[result.code] = result.response;
          if (result.error) {
            nextErrors[result.code] = result.error;
          }
          const responseWarnings = result.response.warnings?.map((item) => item.mensagem).filter(
            (message): message is string => typeof message === 'string' && message.trim().length > 0,
          ) ?? [];
          if (responseWarnings.length) {
            nextWarnings[result.code] = responseWarnings;
          }
        });

        setTrendIndicators(nextIndicators);
        if (Object.keys(nextErrors).length > 0) {
          setTrendError('Alguns indicadores de tendência não puderam ser carregados.');
        }
      } catch (err: unknown) {
        const errorResponse = err as { response?: { data?: { detail?: unknown } } };
        const msg = errorResponse?.response?.data?.detail || 'Erro ao carregar séries temporais.';
        setTrendError(typeof msg === 'string' ? msg : 'Erro ao carregar séries temporais.');
      } finally {
        setTrendLoading(false);
      }
    };

    void fetchTrendIndicators();
  }, [selectedMunicipio, selectedYear]);

  // ── Derived data ───────────────────────────────────────────────────────

  const topDirectJobs = useMemo(() => getTopMunicipio(indicators, 'IND-3.01', 'empregos_portuarios'), [indicators]);
  const topSalary = useMemo(() => getTopMunicipio(indicators, 'IND-3.05', 'salario_medio'), [indicators]);
  const topPayroll = useMemo(() => getTopMunicipio(indicators, 'IND-3.06', 'massa_salarial_anual'), [indicators]);
  const topShare = useMemo(() => getTopMunicipio(indicators, 'IND-3.12', 'participacao_emprego_local'), [indicators]);
  const municipalitySummary = useMemo(() => ({
    jobs: getSingleIndicatorValue('IND-3.01', 'empregos_portuarios'),
    salary: getSingleIndicatorValue('IND-3.05', 'salario_medio'),
    payroll: getSingleIndicatorValue('IND-3.06', 'massa_salarial_anual'),
    participation: getSingleIndicatorValue('IND-3.12', 'participacao_emprego_local'),
  }), [getSingleIndicatorValue]);

  const trendSeries = useMemo(() => {
    const result: Record<string, TrendSeries | null> = {};

    TREND_INDICATORS.forEach((indicator) => {
      const response = trendIndicators[indicator.code];
      const rows = toIndicatorRows(response ?? createEmptyIndicatorResponse(indicator.code));
      const entries = rows
        .map((row) => ({ row, value: getValueFromRow(row, indicator.valueField) }))
        .filter((entry): entry is { row: RawIndicatorRow; value: number } => entry.value !== null);
      result[indicator.code] = buildTrendSeries(entries);
    });

    return result;
  }, [trendIndicators]);

  const trendGrowth = useMemo(() => {
    const result: Record<string, number | null> = {};
    TREND_INDICATORS.forEach((indicator) => {
      const series = trendSeries[indicator.code];
      result[indicator.code] = series ? computeGrowth(series.values) : null;
    });
    return result;
  }, [trendSeries]);

  const activeEstimate = useMemo((): EmploymentMultiplierConfidenceEstimate | null => {
    if (!multiplierData) return null;
    if (showCausalEstimate && multiplierData.causal_estimate) return multiplierData.causal_estimate;
    return multiplierData.estimate;
  }, [multiplierData, showCausalEstimate]);

  const multiplierImpactRow = useMemo<EmploymentMultiplierImpactRow | null>(() => {
    const data = multiplierData?.data?.[0];
    return data ?? null;
  }, [multiplierData]);

  const baselineTonelagemMilhoes = useMemo(
    () => parseSimulationBaseline(multiplierImpactRow),
    [multiplierImpactRow],
  );

  const simulationData = useMemo(
    () => simulationMultiplierData ?? multiplierData,
    [simulationMultiplierData, multiplierData],
  );
  const simulationImpactRow = useMemo<EmploymentMultiplierImpactRow | null>(() => {
    const data = simulationData?.data?.[0];
    return data ?? null;
  }, [simulationData]);

  useEffect(() => {
    setSimulationDelta(0);
    setSimulationMultiplierData(multiplierData);
    setSimulationMultiplierError(null);
    setSimulationMultiplierLoading(false);
  }, [activeEstimate?.municipality_id, selectedYear]);

  useEffect(() => {
    const municipalityId = multiplierData?.municipality_id;
    if (!municipalityId) {
      setSimulationMultiplierData(null);
      setSimulationMultiplierError(null);
      setSimulationMultiplierLoading(false);
      return;
    }

    if (simulationDelta === 0) {
      setSimulationMultiplierData(multiplierData);
      setSimulationMultiplierError(null);
      setSimulationMultiplierLoading(false);
      return;
    }

    let cancelled = false;
    const timer = window.setTimeout(() => {
      void (async () => {
        setSimulationMultiplierLoading(true);
        setSimulationMultiplierError(null);
        try {
          const scenarioResponse = await employmentMultiplierService.getMultiplierEstimate(
            municipalityId,
            selectedYear ?? undefined,
            false,
            simulationDelta,
          );
          if (!cancelled) {
            setSimulationMultiplierData(scenarioResponse);
          }
        } catch {
          if (!cancelled) {
            setSimulationMultiplierError('Não foi possível atualizar o cenário agora. Exibindo projeção local.');
            setSimulationMultiplierData(multiplierData);
          }
        } finally {
          if (!cancelled) {
            setSimulationMultiplierLoading(false);
          }
        }
      })();
    }, 260);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [multiplierData, selectedYear, simulationDelta]);

  const simulation = useMemo(
    () => {
      const effectiveEstimate = simulationData?.estimate;
      return buildSimulation(
        effectiveEstimate ?? activeEstimate,
        baselineTonelagemMilhoes,
        simulationDelta,
        simulationImpactRow,
      );
    },
    [activeEstimate, baselineTonelagemMilhoes, simulationDelta, simulationData, simulationImpactRow],
  );
  const simulationBaseEstimate = useMemo(
    () => simulationData?.estimate ?? activeEstimate,
    [simulationData, activeEstimate],
  );

  const tonelagemDeltaPercent = useMemo<number | null>(() => {
    if (!simulation || simulation.baselineTonelagemMilhoes === null || simulation.targetTonelagemMilhoes === null) {
      return null;
    }
    if (simulation.baselineTonelagemMilhoes === 0) {
      return null;
    }
    return Number(
      (((simulation.targetTonelagemMilhoes - simulation.baselineTonelagemMilhoes) / simulation.baselineTonelagemMilhoes) * 100).toFixed(2),
    );
  }, [simulation]);

  const simulationCurve = useMemo(() => {
    const lines = QUICK_SIMULATION_DELTAS.map((delta) => {
      const simulated = buildSimulation(activeEstimate, baselineTonelagemMilhoes, delta);
      return {
        delta,
        total: simulated ? simulated.total : null,
      };
    });

    return {
      labels: lines.map((line) => `${line.delta > 0 ? '+' : ''}${line.delta}%`),
      values: lines.map((line) => line.total),
    };
  }, [activeEstimate, baselineTonelagemMilhoes]);

  const selectedMunicipioLabel = useMemo(
    () => (selectedMunicipio ? toMunicipioLabel(selectedMunicipio, municipioLabels, { showCode: false }) : null),
    [selectedMunicipio, municipioLabels],
  );

  const runSalaryComparison = useCallback(async () => {
    const salary = parseNumber(salaryQueryInput);
    if (!selectedMunicipio) {
      setSalaryComparisonText('Selecione um município para comparar seu salário.');
      return;
    }
    if (salary === null) {
      setSalaryComparisonText('Digite um valor numérico válido para salário.');
      return;
    }

    const municipalSalary = getSingleIndicatorValue('IND-3.05', 'salario_medio');
    if (municipalSalary === null) {
      setSalaryComparisonText('Sem série de salário médio disponível para o município selecionado.');
      return;
    }

    try {
      const baselineResponse = await indicatorsService.queryIndicator<RawIndicatorRow>({
        codigo_indicador: 'IND-3.05',
        params: { ano: selectedYear },
      });
      const baselineRows = toIndicatorRows(baselineResponse);
      const baselineValues = baselineRows
        .map((row) => getValueFromRow(row, 'salario_medio'))
        .filter((value): value is number => value !== null);
      const baseline = baselineValues.length
        ? baselineValues.reduce((acc, value) => acc + value, 0) / baselineValues.length
        : null;

      if (baseline === null || !Number.isFinite(baseline)) {
        setSalaryComparisonText('Não foi possível calcular a média nacional do setor para comparação.');
        return;
      }

      const municipalGap = ((salary - municipalSalary) / municipalSalary) * 100;
      const nationalGap = ((salary - baseline) / baseline) * 100;
      const comparison = [
        `Salário informado: ${formatNumber(salary, 'currency')}.`,
        `Média municipal em ${selectedMunicipioLabel ?? 'município selecionado'}: ${formatNumber(municipalSalary, 'currency')}.`,
        `Média do setor no ano (${selectedYear}): ${formatNumber(baseline, 'currency')}.`,
        `Diferença vs município: ${formatNumber(municipalGap, 'percent')} (${municipalGap >= 0 ? 'acima' : 'abaixo'}).`,
        `Diferença vs média do setor: ${formatNumber(nationalGap, 'percent')} (${nationalGap >= 0 ? 'acima' : 'abaixo'}).`,
      ];

      setSalaryComparisonText(comparison.join(' '));
    } catch {
      setSalaryComparisonText('Não foi possível carregar o benchmark nacional no momento.');
    }
  }, [selectedMunicipio, selectedMunicipioLabel, salaryQueryInput, selectedYear, getSingleIndicatorValue]);


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

      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <FilterBar showInstallation={false} />
        <div className="flex items-center gap-2">
          <label htmlFor="module3-municipio" className="text-sm font-medium text-gray-700">
            Município
          </label>
          <select
            id="module3-municipio"
            value={selectedMunicipio}
            onChange={(e) => setSelectedMunicipio(e.target.value)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg bg-white text-gray-700"
          >
            {municipioOptions.map((option) => (
              <option key={option.value || 'all'} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <ErrorAlert message={error} className="mb-4" />}

      {/* Banner: ano RAIS indisponível */}
      {raisYearHint !== null && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 flex items-start gap-3">
          <span className="text-amber-500 text-lg leading-none mt-0.5">⚠️</span>
          <div>
            <p className="text-sm font-medium text-amber-800">
              Dados da RAIS não disponíveis para {selectedYear}
            </p>
            <p className="text-sm text-amber-700 mt-0.5">
              {raisYearHint
                ? <>O último ano com dados da RAIS disponíveis é <strong>{raisYearHint}</strong>. Selecione esse ano no filtro acima para visualizar os indicadores.</>
                : <>Os dados da RAIS para o ano selecionado ainda não foram publicados. Tente um ano anterior (ex.: 2022).</>}
            </p>
          </div>
        </div>
      )}

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

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="bg-amber-50 rounded-xl border border-amber-100 p-4">
            <p className="text-xs text-amber-600 uppercase mb-1">Selecionado</p>
            <p className="text-lg font-semibold text-gray-900">
              {selectedMunicipioLabel ?? 'Nenhum município'}
            </p>
            {selectedMunicipio ? (
              <div className="mt-3 text-sm text-gray-700 space-y-1">
                <p><strong>Empregos:</strong> {municipalitySummary.jobs !== null ? formatNumber(municipalitySummary.jobs, 'integer') : '—'}</p>
                <p><strong>Salário médio:</strong> {municipalitySummary.salary !== null ? formatNumber(municipalitySummary.salary, 'currency') : '—'}</p>
                <p><strong>Massa salarial:</strong> {municipalitySummary.payroll !== null ? formatNumber(municipalitySummary.payroll, 'currency') : '—'}</p>
                <p><strong>Participação local:</strong> {municipalitySummary.participation !== null ? formatNumber(municipalitySummary.participation, 'percent') : '—'}</p>
              </div>
            ) : (
              <p className="text-sm text-gray-500 mt-2">Selecione um município no topo para ver a leitura individual.</p>
            )}
          </div>

          <div className="md:col-span-2 bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-sm text-gray-500 mb-2">Comparador de salário do usuário</p>
            <div className="flex flex-col gap-2 sm:flex-row">
              <input
                value={salaryQueryInput}
                onChange={(e) => setSalaryQueryInput(e.target.value)}
                inputMode="decimal"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                placeholder="Informe seu salário mensal (R$)"
              />
              <button
                type="button"
                onClick={() => void runSalaryComparison()}
                className="px-4 py-2 text-sm text-white bg-amber-600 rounded-lg hover:bg-amber-700 disabled:opacity-50"
                disabled={!selectedMunicipio}
              >
                Comparar
              </button>
            </div>
            {salaryComparisonText && (
              <p className="text-sm text-gray-700 mt-2">{salaryComparisonText}</p>
            )}
          </div>
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
                labelAccessor={getLabelAccessor(ind.code)}
                filterText={tableSearch}
                indicatorCode={ind.code}
                warnings={indicatorWarnings[ind.code]}
                error={indicatorErrors[ind.code] ?? null}
              />
              {ind.interpretation && (
                <p className="mt-1 px-3 text-xs text-gray-400 italic">{ind.interpretation}</p>
              )}
            </div>
          ))}
        </div>
      </section>

      <section>
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="h-5 w-5 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">Evolução recente do município selecionado</h2>
        </div>
        <p className="text-sm text-gray-500 mb-4">
          Série temporal dos últimos {TREND_YEARS} anos para leitura dinâmica (apenas se houver município selecionado).
        </p>

        {!selectedMunicipio ? (
          <div className="bg-gray-50 rounded-xl border border-gray-200 p-6 text-sm text-gray-500">
            Selecione um município para carregar a tendência anual dos principais indicadores.
          </div>
        ) : trendLoading ? (
          <LoadingSpinner />
        ) : trendError ? (
          <ErrorAlert message={trendError} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {TREND_INDICATORS.map((ind) => {
              const series = trendSeries[ind.code];
              const growth = trendGrowth[ind.code];
              const warnings = indicatorWarnings[ind.code];
              return (
                <ChartCard
                  key={ind.code}
                  title={ind.name}
                  description={ind.description}
                  unit={ind.unit}
                  error={series === null ? 'Sem dados para montar série temporal.' : undefined}
                  isLoading={false}
                  extraInfo={warnings && warnings.length > 0 ? warnings.join(' | ') : 'Média de tendência por período da seleção'}
                >
                  {series && (
                    <div className="space-y-4">
                      <LineChart
                        labels={series.labels}
                        datasets={[{ label: ind.unit, data: series.values }]}
                        yAxisLabel={ind.unit}
                        yAxisFormat={getIndicatorFormat(ind.code)}
                        yAxisBeginAtZero={ind.code === 'IND-3.01'}
                      />
                      <p className="text-xs text-gray-500">
                        Variação acumulada no período:
                        {' '}
                        {growth === null ? '—' : formatNumber(growth, 'percent')}
                      </p>
                    </div>
                  )}
                </ChartCard>
              );
            })}
          </div>
        )}
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

            {/* Simulador de impacto por tonelagem movimentada */}
            {simulation && (
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700">Simulador de impacto por tonelagem</h4>
                    <p className="text-xs text-gray-500 mt-1">
                      Ajuste a variação de toneladas movimentadas e veja, mantendo o multiplicador, a evolução dos empregos diretos,
                      indiretos, induzidos e o impacto total estimado.
                    </p>
                  </div>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${formatDeltaBadgeClass(simulation.totalDelta)}`}>
                    Δ total: {formatDelta(simulation.totalDelta)}
                  </span>
                </div>
                {simulationMultiplierLoading && (
                  <p className="text-xs text-gray-500 mb-2">Recalculando cenário com base no cenário remoto.</p>
                )}
                {_simulationMultiplierError && (
                  <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-2 py-1 mb-2">
                    {_simulationMultiplierError}
                  </p>
                )}

                <label htmlFor="simulation-delta" className="text-sm text-gray-700">
                  Variação da tonelagem movimentada
                </label>
                <div className="mt-2 flex items-center gap-3">
                  <input
                    id="simulation-delta"
                    type="range"
                    min={SIMULATION_MIN_DELTA}
                    max={SIMULATION_MAX_DELTA}
                    step={1}
                    value={simulationDelta}
                    onChange={(e) => setSimulationDelta(Number(e.target.value))}
                    className="w-full"
                  />
                  <span className="text-sm font-medium text-gray-800 w-16 text-right">
                    {formatDelta(simulation.deltaTonelagem)}%
                  </span>
                </div>

                <div className="flex flex-wrap gap-2 mt-2">
                  {QUICK_SIMULATION_DELTAS.map((quickDelta) => (
                    <button
                      key={quickDelta}
                      type="button"
                      onClick={() => setSimulationDelta(quickDelta)}
                      className={`text-xs px-3 py-1.5 rounded-full border ${
                        quickDelta === simulation.deltaTonelagem
                          ? 'bg-blue-50 border-blue-400 text-blue-700'
                          : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      {quickDelta > 0 ? `+${quickDelta}%` : `${quickDelta}%`}
                    </button>
                  ))}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mt-4">
                  <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                    <p className="text-xs text-gray-500">Tonelagem base</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {baselineTonelagemMilhoes === null ? '—' : formatTonelagem(baselineTonelagemMilhoes)}
                    </p>
                    <p className={`text-xs mt-1 ${tonelagemDeltaPercent === null ? 'text-gray-700 bg-gray-50 border-gray-200' : formatDeltaBadgeClass(tonelagemDeltaPercent)}`}>
                      {simulation.targetTonelagemMilhoes === null
                        ? 'Referência indisponível'
                        : `Alvo: ${formatTonelagem(simulation.targetTonelagemMilhoes)} (${tonelagemDeltaPercent === null ? '—' : `${formatDelta(tonelagemDeltaPercent)}%`})`
                      }
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                    <p className="text-xs text-gray-500">Empregos diretos</p>
                    <p className="text-lg font-semibold text-gray-900">{formatNumber(simulation.diretos)}</p>
                    <p className={`text-xs mt-1 ${formatDeltaBadgeClass(simulation.diretosDelta)}`}>
                      {formatDelta(simulation.diretosDelta)} (contra base)
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                    <p className="text-xs text-gray-500">Empregos indiretos e induzidos</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {formatNumber(simulation.indiretos + simulation.induzidos, 'decimal')}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Indiretos: {formatNumber(simulation.indiretos, 'decimal')} | Induzidos: {formatNumber(simulation.induzidos, 'decimal')}
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                    <p className="text-xs text-gray-500">Impacto total projetado</p>
                    <p className="text-lg font-semibold text-gray-900">{formatNumber(simulation.total)}</p>
                    <p className={`text-xs mt-1 ${formatDeltaBadgeClass(simulation.total - activeEstimate.total_impact)}`}>
                      {formatDelta(simulation.total - (simulationBaseEstimate?.total_impact ?? 0))} (em relação à base)
                    </p>
                  </div>
                </div>

                <div className="mt-5">
                  <p className="text-xs text-gray-500 mb-2">Sensibilidade do impacto total por cenário</p>
                  <LineChart
                    labels={simulationCurve.labels}
                    datasets={[{ label: 'Empregos totais', data: simulationCurve.values, borderColor: '#0ea5e9' }]}
                    yAxisLabel="Empregos"
                    yAxisFormat="quantity"
                  />
                </div>
              </div>
            )}

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
              {raisYearHint !== null
                ? `Sem dados de empregos diretos para ${selectedYear}. Selecione o ano ${raisYearHint ?? 'anterior'} para calcular o multiplicador.`
                : 'Sem dados de empregos diretos disponíveis. Verifique o ano selecionado e tente novamente.'}
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
                    labelAccessor={getLabelAccessor(ind.code)}
                    filterText={tableSearch}
                    indicatorCode={ind.code}
                    warnings={indicatorWarnings[ind.code]}
                    error={indicatorErrors[ind.code] ?? null}
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
