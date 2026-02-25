import { useCallback, useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { ChevronDown, ChevronUp, Download, Play, RefreshCw, Search } from 'lucide-react';

import { useFilterStore } from '../../../store/filterStore';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { ChartCard } from '../../../components/charts/ChartCard';
import { BarChart } from '../../../components/charts/BarChart';
import { ExportButton } from '../../../components/common/ExportButton';
import { FilterBar } from '../../../components/filters/FilterBar';
import { AnalysisStatusBadge } from '../../../components/impactoEconomico/AnalysisStatusBadge';
import { AnalysisResultCard } from '../../../components/impactoEconomico/AnalysisResultCard';
import { EventStudyChart } from '../../../components/impactoEconomico/EventStudyChart';
import { MethodComparisonTable } from '../../../components/impactoEconomico/MethodComparisonTable';
import { useAnalysis } from '../../../hooks/useAnalysis';
import { getIndicatorFormat } from '../../../utils/chartFormats';
import { formatDecimal } from '../../../utils/numberFormat';
import {
  type MunicipioLabelMap,
  isLikelyIdNameMismatch,
  normalizeMunicipioId as normalizeMunicipioIdFromApi,
  formatMunicipioLabelList,
  resolveMunicipioLabel,
  toMunicipioLabel,
  toSafeMunicipioIdArray,
} from '../../../utils/municipioLabels';
import { impactoEconomicoService } from '../../../api/impactoEconomico';
import { indicatorsService } from '../../../api/indicators';
import type {
  AnalysisCreateRequest,
  AnalysisDetail,
  AnalysisMethod,
  AnalysisScope,
  AnalysisResponse,
  MatchingResponse,
  IndicatorMetadata,
  IndicatorResponse,
  PolicyMunicipioItem,
} from '../../../types/api';

type ImplementationStatus = 'implemented' | 'technical_debt';


interface CoeffPoint {
  rel_time: number;
  coef: number;
  se?: number | null;
  ci_lower?: number | null;
  ci_upper?: number | null;
}

interface CausalSummaryPoint {
  outcome: string;
  method: string;
  coef: number;
  se: number | null;
  pvalue: number | null;
  ciLower: number | null;
  ciUpper: number | null;
  nObs: number | null;
  significant: boolean | null;
}

interface EventStudyPayload {
  outcome: string;
  coefficients: CoeffPoint[];
}

type RawIndicatorRow = Record<string, unknown>;
type ModuleIndicatorResponse = IndicatorResponse<unknown>;
type ModuleIndicatorStore = Record<string, ModuleIndicatorResponse>;
type ApiErrorLike = { response?: { data?: { detail?: unknown } } };

interface ComparisonRow {
  Method: string;
  Estimate: number | null;
  SE: number | null;
  CI_Lower: number | null;
  CI_Upper: number | null;
  P_Value: number | null;
  Significant: string;
  Notes?: string | null;
  [key: string]: unknown;
}

interface ComparisonPayload {
  outcome: string;
  recommendation?: string;
  consistency_assessment?: string;
  comparison_table?: ComparisonRow[];
}

interface CausalNarrative {
  outcome: string;
  outcomeLabel: string;
  method: string;
  question: string;
  interpretation: string;
  implication: string;
  decision: string;
  significance: string;
  confidence: string;
}

interface OutcomeMetadata {
  label: string;
  isLog: boolean;
  kind:
    | 'log'
    | 'correlation'
    | 'elasticity'
    | 'ratio'
    | 'share'
    | 'index'
    | 'level'
    | 'difference'
    | 'unknown';
}

const ANALYSIS_METHOD_LABELS: Record<AnalysisMethod, string> = {
  did: 'Diferenças em Diferenças',
  iv: 'Variáveis Instrumentais',
  panel_iv: 'Painel com Instrumento',
  event_study: 'Estudo de Evento',
  compare: 'Comparação de Métodos',
  scm: 'Controle Sintético',
  augmented_scm: 'Controle Sintético Aumentado',
};

const ANALYSIS_METHOD_DESCRIPTIONS: Record<AnalysisMethod, string> = {
  did: 'Compara a evolução dos municípios portuários com municípios semelhantes antes e depois do evento',
  iv: 'Usa a movimentação de carga como instrumento para isolar o efeito causal do porto',
  panel_iv: 'Combina dados em painel com instrumento para controlar efeitos fixos de município e ano',
  event_study: 'Mostra a evolução do impacto ano a ano, validando se não havia diferença antes do evento',
  compare: 'Roda múltiplos métodos e verifica se chegam à mesma conclusão',
  scm: 'Constrói um "município fictício" para comparação contrafactual',
  augmented_scm: 'Controle sintético com correção de viés por regressão',
};

const OUTCOME_METADATA: Record<string, OutcomeMetadata> = {
  pib_log: { label: 'PIB Municipal', isLog: true, kind: 'log' },
  pib_per_capita_log: { label: 'Renda per Capita', isLog: true, kind: 'log' },
  n_vinculos_log: { label: 'Empregos no Setor Portuário', isLog: true, kind: 'log' },
  empregos_totais_log: { label: 'Empregos Totais do Município', isLog: true, kind: 'log' },
  toneladas_antaq_log: { label: 'Movimentação de Carga (toneladas)', isLog: true, kind: 'log' },
  comercio_dolar_log: { label: 'Comércio Exterior', isLog: true, kind: 'log' },
  exportacao_dolar_log: { label: 'Exportações', isLog: true, kind: 'log' },
  importacao_dolar_log: { label: 'Importações', isLog: true, kind: 'log' },
  massa_salarial_total_log: { label: 'Massa Salarial Total', isLog: true, kind: 'log' },
  massa_salarial_portuaria_log: { label: 'Massa Salarial do Setor Portuário', isLog: true, kind: 'log' },
  populacao_log: { label: 'População', isLog: true, kind: 'log' },
  receitas_total_log: { label: 'Receita Municipal', isLog: true, kind: 'log' },
  despesas_total_log: { label: 'Despesa Municipal', isLog: true, kind: 'log' },
  pib: { label: 'PIB Municipal', isLog: false, kind: 'level' },
  pib_per_capita: { label: 'Renda per Capita', isLog: false, kind: 'level' },
  n_vinculos: { label: 'Empregos no Setor Portuário', isLog: false, kind: 'level' },
  empregos_totais: { label: 'Empregos Totais', isLog: false, kind: 'level' },
  toneladas_antaq: { label: 'Movimentação de Carga', isLog: false, kind: 'level' },
  comercio_dolar: { label: 'Comércio Exterior', isLog: false, kind: 'level' },
  exportacao_dolar: { label: 'Exportações', isLog: false, kind: 'level' },
  importacao_dolar: { label: 'Importações', isLog: false, kind: 'level' },
  crescimento_pib_percentual: { label: 'Crescimento do PIB', isLog: false, kind: 'difference' },
  crescimento_tonelagem_pct: { label: 'Crescimento da Movimentação', isLog: false, kind: 'difference' },
  crescimento_empregos_pct: { label: 'Crescimento de Empregos', isLog: false, kind: 'difference' },
  crescimento_comercio_pct: { label: 'Crescimento do Comércio Exterior', isLog: false, kind: 'difference' },
  correlacao_tonelagem_pib: { label: 'Associação Carga × PIB', isLog: false, kind: 'correlation' },
  correlacao_tonelagem_empregos: { label: 'Associação Carga × Empregos', isLog: false, kind: 'correlation' },
  correlacao_comercio_pib: { label: 'Associação Comércio × PIB', isLog: false, kind: 'correlation' },
  elasticidade_tonelagem_pib: { label: 'Sensibilidade Carga/PIB', isLog: false, kind: 'elasticity' },
  participacao_pib_regional_pct: { label: 'Participação no PIB Regional', isLog: false, kind: 'share' },
  crescimento_relativo_uf_pp: { label: 'Crescimento Relativo ao Estado', isLog: false, kind: 'difference' },
  razao_emprego_total_portuario: { label: 'Proporção Emprego Total/Portuário', isLog: false, kind: 'ratio' },
  indice_concentracao_portuaria: { label: 'Concentração da Atividade Portuária', isLog: false, kind: 'index' },
};

type ConfidenceLevel = 'strong' | 'moderate' | 'weak';

function getConfidenceLevel(row: CausalSummaryPoint): ConfidenceLevel {
  const p = row.pvalue;
  const n = row.nObs;
  if (p !== null && p < 0.05 && (n === null || n >= 30)) return 'strong';
  if (p !== null && p < 0.10) return 'moderate';
  if (p !== null && p < 0.05 && n !== null && n < 30) return 'moderate';
  return 'weak';
}

const CONFIDENCE_CONFIG: Record<ConfidenceLevel, { color: string; bg: string; border: string; label: string; description: string }> = {
  strong:   { color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200', label: 'Evidência forte',   description: 'Resultado estatisticamente significativo com amostra robusta' },
  moderate: { color: 'text-amber-700',   bg: 'bg-amber-50',   border: 'border-amber-200',   label: 'Evidência moderada', description: 'Resultado com significância marginal ou amostra limitada' },
  weak:     { color: 'text-red-700',     bg: 'bg-red-50',     border: 'border-red-200',     label: 'Evidência fraca',    description: 'Sem significância estatística convencional neste recorte' },
};

/** Outcomes disponíveis para seleção pelo usuário, com rótulo amigável */
const OUTCOME_CHOICES: { value: string; label: string }[] = [
  { value: 'pib_log', label: 'PIB Municipal' },
  { value: 'pib_per_capita_log', label: 'Renda per Capita' },
  { value: 'n_vinculos_log', label: 'Empregos no Setor Portuário' },
  { value: 'empregos_totais_log', label: 'Empregos Totais' },
  { value: 'toneladas_antaq_log', label: 'Movimentação de Carga' },
  { value: 'comercio_dolar_log', label: 'Comércio Exterior' },
  { value: 'exportacao_dolar_log', label: 'Exportações' },
  { value: 'importacao_dolar_log', label: 'Importações' },
  { value: 'massa_salarial_total_log', label: 'Massa Salarial Total' },
  { value: 'massa_salarial_portuaria_log', label: 'Massa Salarial Portuária' },
  { value: 'populacao_log', label: 'População' },
];

const createEmptyIndicatorResponse = (codigoIndicador: string): ModuleIndicatorResponse => ({
  codigo_indicador: codigoIndicador,
  nome: codigoIndicador,
  unidade: '',
  unctad: false,
  data: [],
});

function toIndicatorRows(response: ModuleIndicatorResponse): RawIndicatorRow[] {
  return response.data.filter(
    (item): item is RawIndicatorRow => item !== null && typeof item === 'object',
  );
}

function parseComparisonRows(rawRows: unknown): ComparisonRow[] {
  if (!Array.isArray(rawRows)) {
    return [];
  }

  return rawRows
    .filter((entry): entry is Record<string, unknown> => entry !== null && typeof entry === 'object')
    .map((row) => {
      const method = row.Method;
      const estimate = row.Estimate;
      const se = row.SE;
      const ciLower = row.CI_Lower;
      const ciUpper = row.CI_Upper;
      const pValue = row.P_Value;
      const significant = row.Significant;
      const notes = row.Notes;

      return {
        Method: typeof method === 'string' ? method : '—',
        Estimate: toDisplayNumber(estimate),
        SE: toDisplayNumber(se),
        CI_Lower: toDisplayNumber(ciLower),
        CI_Upper: toDisplayNumber(ciUpper),
        P_Value: toDisplayNumber(pValue),
        Significant: typeof significant === 'string' ? significant : '—',
        Notes: typeof notes === 'string' ? notes : null,
        ...row,
      };
    });
}

function parseToNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === 'string') {
    const sanitized = value.replace(/[^0-9eE.+\-_,]/g, '').replace(/_/g, '').trim();
    if (!sanitized) {
      return null;
    }

    const hasComma = sanitized.includes(',');
    const hasDot = sanitized.includes('.');
    let normalized: string;
    if (hasComma && hasDot) {
      const lastComma = sanitized.lastIndexOf(',');
      const lastDot = sanitized.lastIndexOf('.');
      normalized = lastComma > lastDot
        ? sanitized.replace(/\./g, '').replace(',', '.')
        : sanitized.replace(/,/g, '');
    } else if (hasComma) {
      normalized = sanitized.replace(',', '.');
    } else {
      normalized = sanitized;
    }

    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

function parseNumericFinite(value: unknown): number | null {
  const parsed = parseToNumber(value);
  return parsed !== null && Number.isFinite(parsed) ? parsed : null;
}

function sortedNumericRows(
  rows: RawIndicatorRow[],
  valueField: string,
  maxRows = 10,
): Array<{ row: RawIndicatorRow; value: number }> {
  return rows
    .map((row) => {
      const parsed = toDisplayValue(row, valueField);
      if (!Number.isFinite(parsed)) {
        return null;
      }

      return { row, value: parsed };
    })
    .filter((entry): entry is { row: RawIndicatorRow; value: number } => entry !== null)
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, maxRows);
}

function extractEventStudyCoefficients(raw: unknown): CausalPoint[] {
  if (!Array.isArray(raw)) {
    return [];
  }

  return raw
    .map((item) => {
      if (!item || typeof item !== 'object') {
        return null;
      }

      const candidate = item as Record<string, unknown>;
      const relTime = parseNumericFinite(candidate.rel_time);
      const coef = parseNumericFinite(candidate.coef);
      if (relTime === null || coef === null) {
        return null;
      }

      return {
        rel_time: relTime,
        coef,
        se: parseNumericFinite(candidate.se),
        ci_lower: parseNumericFinite(candidate.ci_lower),
        ci_upper: parseNumericFinite(candidate.ci_upper),
        pvalue: parseNumericFinite(candidate.pvalue),
      };
    })
    .filter((item): item is CausalPoint => item !== null)
    .sort((a, b) => a.rel_time - b.rel_time);
}

interface CausalPoint {
  rel_time: number;
  coef: number;
  se: number | null;
  ci_lower: number | null;
  ci_upper: number | null;
  pvalue: number | null;
}

function pickRepresentativeEventStudyPoint(points: CausalPoint[]): CausalPoint | null {
  if (!points.length) {
    return null;
  }

  const atZero = points.find((point) => point.rel_time === 0);
  if (atZero) {
    return atZero;
  }

  return points.find((point) => point.rel_time > 0) ?? points[0];
}

function buildCausalSummary(detail: AnalysisDetail | null): CausalSummaryPoint[] {
  if (!detail?.result_full || detail.status !== 'success') {
    return [];
  }

  const result = detail.result_full as Record<string, unknown>;
  if (detail.method === 'compare') {
    return [];
  }

  const rows: CausalSummaryPoint[] = [];
  for (const [outcome, payloadUnknown] of Object.entries(result)) {
    if (!payloadUnknown || typeof payloadUnknown !== 'object') {
      continue;
    }

    if (detail.method === 'event_study') {
      const summaryPoint = pickRepresentativeEventStudyPoint(extractEventStudyCoefficients(
        (payloadUnknown as Record<string, unknown>).coefficients,
      ));

      if (!summaryPoint) {
        continue;
      }

      const pValue = summaryPoint.pvalue;
      rows.push({
        outcome,
        method: detail.method,
        coef: summaryPoint.coef,
        se: summaryPoint.se,
        pvalue: pValue,
        ciLower: summaryPoint.ci_lower,
        ciUpper: summaryPoint.ci_upper,
        nObs: parseNumericFinite((payloadUnknown as Record<string, unknown>).n_obs),
        significant: pValue !== null && pValue < 0.05,
      });
      continue;
    }

    const payloadRecord = payloadUnknown as Record<string, unknown>;
    const mainUnknown = payloadRecord.main_result ?? payloadRecord;
    if (!mainUnknown || typeof mainUnknown !== 'object') {
      continue;
    }

    const mainResult = mainUnknown as Record<string, unknown>;
    const coefRaw = mainResult.coef ?? mainResult.att;
    const coef = parseNumericFinite(coefRaw);
    if (coef === null) {
      continue;
    }

    const pValue = parseNumericFinite(mainResult.p_value ?? mainResult.pvalue);
    rows.push({
      outcome,
      method: detail.method,
      coef,
      se: parseNumericFinite(mainResult.std_err ?? mainResult.se),
      pvalue: pValue,
      ciLower: parseNumericFinite(mainResult.ci_lower),
      ciUpper: parseNumericFinite(mainResult.ci_upper),
      nObs: parseNumericFinite(mainResult.n_obs),
      significant: pValue !== null && pValue < 0.05,
    });
  }

  return rows;
}

function buildEventStudyPayloads(detail: AnalysisDetail | null): EventStudyPayload[] {
  if (!detail?.result_full) {
    return [];
  }

  const payload = detail.result_full as Record<string, unknown>;
  if (detail.method !== 'event_study' && detail.method !== 'did') {
    return [];
  }

  const outputs: EventStudyPayload[] = [];
  for (const [outcome, payloadUnknown] of Object.entries(payload)) {
    if (!payloadUnknown || typeof payloadUnknown !== 'object') {
      continue;
    }

    const payloadRecord = payloadUnknown as Record<string, unknown>;
    const rawCoefficients =
      detail.method === 'event_study'
        ? payloadRecord.coefficients
        : (payloadRecord.event_study as { coefficients?: unknown } | undefined)?.coefficients;

    if (!Array.isArray(rawCoefficients)) {
      continue;
    }

    const coefficients = extractEventStudyCoefficients(rawCoefficients);
    if (coefficients.length === 0) {
      continue;
    }

    outputs.push({
      outcome,
      coefficients,
    });
  }

  return outputs;
}

const ANALYSIS_METHODS: { value: AnalysisMethod; label: string }[] = [
  { value: 'did', label: 'DiD (Difference-in-Differences)' },
  { value: 'iv', label: 'IV (Variáveis Instrumentais)' },
  { value: 'panel_iv', label: 'Panel IV' },
  { value: 'event_study', label: 'Event Study' },
  { value: 'compare', label: 'Comparar métodos' },
];

type IndicatorGroup = 'economia' | 'porto' | 'comercio' | 'tendencias';

const INDICATORS_INFO: Array<{
  code: string; name: string; unit: string; desc: string; valueField: string;
  interpretation: string; group: IndicatorGroup;
}> = [
  { code: 'IND-5.01', name: 'PIB Municipal', unit: 'R$', desc: 'Valor total da economia do município', valueField: 'pib_municipal', interpretation: 'Quanto maior, maior é a escala econômica local. Compare com o ano anterior e municípios similares.', group: 'economia' },
  { code: 'IND-5.02', name: 'Renda per Capita', unit: 'R$/hab', desc: 'PIB dividido pela população', valueField: 'pib_per_capita', interpretation: 'Melhor proxy de renda média. Crescimento indica melhora no bem-estar econômico.', group: 'economia' },
  { code: 'IND-5.03', name: 'População', unit: 'Hab', desc: 'População residente estimada', valueField: 'populacao', interpretation: 'Base de contexto para indicadores per capita e de mercado de trabalho.', group: 'economia' },
  { code: 'IND-5.04', name: 'Participação de Serviços no PIB', unit: '%', desc: 'Quanto o setor de serviços representa na economia', valueField: 'pib_servicos_percentual', interpretation: 'Mudanças indicam reestruturação produtiva. Municípios portuários tendem a ter serviços logísticos relevantes.', group: 'economia' },
  { code: 'IND-5.05', name: 'Participação da Indústria no PIB', unit: '%', desc: 'Quanto a indústria representa na economia', valueField: 'pib_industria_percentual', interpretation: 'Alta participação industrial pode amplificar o impacto portuário via cadeias de suprimento.', group: 'economia' },
  { code: 'IND-5.06', name: 'Volume de Carga por R$ do PIB', unit: 'ton/R$', desc: 'Quanto o porto movimenta por unidade de PIB gerado', valueField: 'intensidade_portuaria', interpretation: 'Alto valor = maior dependência da atividade logística para gerar riqueza local.', group: 'porto' },
  { code: 'IND-5.07', name: 'Comércio Exterior por R$ do PIB', unit: 'US$/R$', desc: 'Abertura comercial relativa ao tamanho da economia', valueField: 'intensidade_comercial', interpretation: 'Mede exposição ao comércio internacional. Mais alto = economia mais aberta e sensível a câmbio e preços externos.', group: 'comercio' },
  { code: 'IND-5.08', name: 'Empregos Portuários no Total', unit: '%', desc: 'Parcela do mercado de trabalho ligada ao porto', valueField: 'concentracao_emprego_pct', interpretation: 'Quanto maior, maior a dependência do ciclo portuário para geração de emprego local.', group: 'porto' },
  { code: 'IND-5.09', name: 'Salários Portuários no Total', unit: '%', desc: 'Participação da massa salarial portuária', valueField: 'concentracao_salarial_pct', interpretation: 'Indica sensibilidade da renda familiar local ao desempenho do setor portuário.', group: 'porto' },
  { code: 'IND-5.10', name: 'Crescimento do PIB', unit: '%', desc: 'Variação anual da economia', valueField: 'crescimento_pib_percentual', interpretation: 'Taxa positiva significa expansão. Sem causalidade direta — use a análise causal para atribuição.', group: 'tendencias' },
  { code: 'IND-5.11', name: 'Crescimento da Movimentação', unit: '%', desc: 'Variação anual do volume de carga ANTAQ', valueField: 'crescimento_tonelagem_pct', interpretation: 'Mede dinamismo físico do porto. Crescimento sustentado pode anteceder expansão econômica.', group: 'porto' },
  { code: 'IND-5.12', name: 'Crescimento de Empregos Portuários', unit: '%', desc: 'Variação anual de vínculos no setor', valueField: 'crescimento_empregos_pct', interpretation: 'Pode ser sazonal. Quedas abruptas sugerem risco de mercado de trabalho local.', group: 'tendencias' },
  { code: 'IND-5.13', name: 'Crescimento do Comércio Exterior', unit: '%', desc: 'Variação anual de exp + imp', valueField: 'crescimento_comercio_pct', interpretation: 'Exportação e importação agregadas. Reflete competitividade e demanda externa.', group: 'comercio' },
  { code: 'IND-5.14', name: 'Associação Carga × PIB', unit: 'coef.', desc: 'Correlação entre volume de carga e crescimento do PIB', valueField: 'correlacao_tonelagem_pib', interpretation: 'Alta correlação sugere ligação, mas não prova causalidade. Use a análise causal para quantificar o efeito.', group: 'porto' },
  { code: 'IND-5.15', name: 'Associação Carga × Empregos', unit: 'coef.', desc: 'Correlação entre carga e empregos portuários', valueField: 'correlacao_tonelagem_empregos', interpretation: 'Indica se expansão de carga acompanha geração de empregos no setor.', group: 'porto' },
  { code: 'IND-5.16', name: 'Associação Comércio × PIB', unit: 'coef.', desc: 'Correlação entre comércio exterior e PIB', valueField: 'correlacao_comercio_pib', interpretation: 'Mede integração entre abertura comercial e desempenho econômico local.', group: 'comercio' },
  { code: 'IND-5.17', name: 'Sensibilidade Carga/PIB', unit: 'elastic.', desc: 'Resposta da tonelagem a variações no PIB', valueField: 'elasticidade_tonelagem_pib', interpretation: 'Elasticidade > 1 = movimentação cresce proporcionalmente mais que o PIB — porto pró-cíclico.', group: 'porto' },
  { code: 'IND-5.18', name: 'Peso no PIB Regional', unit: '%', desc: 'Participação no PIB da microrregião', valueField: 'participacao_pib_regional_pct', interpretation: 'Mede concentração territorial. Crescimento indica ganho de relevância regional.', group: 'economia' },
  { code: 'IND-5.19', name: 'Crescimento vs. Estado', unit: 'p.p.', desc: 'Diferença de crescimento do município em relação ao estado', valueField: 'crescimento_relativo_uf_pp', interpretation: 'Valor positivo = município cresce mais que a média estadual. Possível efeito porto.', group: 'tendencias' },
  { code: 'IND-5.20', name: 'Proporção Emprego Total/Portuário', unit: 'razão', desc: 'Empregos totais divididos pelos portuários', valueField: 'razao_emprego_total_portuario', interpretation: 'Mais alto = economia mais diversificada em relação ao emprego portuário.', group: 'porto' },
  { code: 'IND-5.21', name: 'Concentração da Atividade Portuária', unit: '0–100', desc: 'Índice composto de dependência econômica do porto', valueField: 'indice_concentracao_portuaria', interpretation: 'Use para comparação relativa entre municípios e para ranking de dependência portuária.', group: 'porto' },
];


function valueToString(value: unknown): string {
  return typeof value === 'undefined' ? '' : String(value);
}

const toSafeArray = toSafeMunicipioIdArray;
const normalizeMunicipioId = normalizeMunicipioIdFromApi;

function toMunicipioIdList(rawIds: string[]): string[] {
  const uniqueIds = new Set<string>();
  for (const rawId of rawIds) {
    const municipioId = normalizeMunicipioId(rawId);
    if (municipioId) {
      uniqueIds.add(municipioId);
    }
  }
  return Array.from(uniqueIds);
}

function toDisplayValue(item: RawIndicatorRow, valueField: string): number {
  const candidates = [valueField, 'valor', 'total'];
  for (const field of candidates) {
    const fieldValue = item[field];
    const parsed = parseToNumber(fieldValue);
    if (parsed !== null) {
      return parsed;
    }
  }

  return NaN;
}

function getLabelFromData(item: RawIndicatorRow, labels: MunicipioLabelMap): string {
  const municipioId = normalizeMunicipioId(item.id_municipio);
  if (municipioId) {
    return toMunicipioLabel(municipioId, labels);
  }

  return (
    (typeof item.nome_municipio === 'string' && item.nome_municipio) ||
    (typeof item.id_municipio === 'string' && item.id_municipio) ||
    (typeof item.id_instalacao === 'string' && item.id_instalacao) ||
    'N/A'
  );
}

function toDisplayNumber(value: unknown): number | null {
  return parseToNumber(value);
}

function toCsvValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }
  const asString = typeof value === 'string' ? value : JSON.stringify(value);
  const escaped = asString.replace(/"/g, '""');
  return `"${escaped}"`;
}

function createCoefficientsCsvPayload(detail: AnalysisDetail | null): string {
  if (!detail?.result_full || typeof detail.result_full !== 'object') {
    return 'tipo,outcome,coef,se,pvalue,n_obs,r2,rel_time,ci_lower,ci_upper\n';
  }

  const header = ['tipo', 'outcome', 'method', 'coef', 'se', 'pvalue', 'n_obs', 'r2', 'rel_time', 'ci_lower', 'ci_upper'];
  const rows: Array<Record<string, string>> = [];

  if (detail.method === 'compare') {
    const comparisonSource = (detail.result_full as Record<string, unknown>).comparison;
    const comparison =
      comparisonSource && typeof comparisonSource === 'object'
        ? (comparisonSource as Record<string, unknown>)
        : undefined;
    if (comparison) {
      for (const outcome of Object.keys(comparison)) {
        const payload = comparison[outcome];
        if (!payload || typeof payload !== 'object') {
          continue;
        }
        const table = (payload as Record<string, unknown>).comparison_table;
        if (Array.isArray(table)) {
          for (const row of table) {
            if (!row || typeof row !== 'object') {
              continue;
            }
            const rowRecord = row as Record<string, unknown>;
            rows.push({
              tipo: 'comparison',
              outcome,
              method: valueToString(rowRecord.Method),
              coef: valueToString(rowRecord.Estimate),
              se: valueToString(rowRecord.SE),
              pvalue: valueToString(rowRecord.P_Value),
              n_obs: '',
              r2: '',
              rel_time: '',
              ci_lower: valueToString(rowRecord.CI_Lower),
              ci_upper: valueToString(rowRecord.CI_Upper),
            });
          }
        }
      }
    }

  return `${header.join(',')}\n${rows
      .map((row) => Object.values(row).map(toCsvValue).join(','))
      .join('\n')}`;
  }

  const resultPayloads = detail.result_full as Record<string, unknown>;
  for (const outcome of Object.keys(resultPayloads)) {
    const payload = resultPayloads[outcome];
    if (!payload || typeof payload !== 'object') {
      continue;
    }
    const payloadRecord = payload as Record<string, unknown>;
    const mainResult = payloadRecord.main_result;
    if (mainResult && typeof mainResult === 'object') {
      const mainResultRecord = mainResult as Record<string, unknown>;
      rows.push({
        tipo: 'main_result',
        outcome,
        method: detail.method,
        coef: valueToString(mainResultRecord.coef),
        se: valueToString(mainResultRecord.std_err ?? mainResultRecord.se),
        pvalue: valueToString(mainResultRecord.p_value ?? mainResultRecord.pvalue),
        n_obs: valueToString(mainResultRecord.n_obs),
        r2: valueToString(mainResultRecord.r2),
        rel_time: '',
        ci_lower: valueToString(mainResultRecord.ci_lower),
        ci_upper: valueToString(mainResultRecord.ci_upper),
      });
    }

    const coefficientsUnknown = payloadRecord.coefficients;
    const coefficients = Array.isArray(coefficientsUnknown) ? coefficientsUnknown : [];
    for (const coefPoint of coefficients) {
      if (coefPoint && typeof coefPoint === 'object') {
        const point = coefPoint as Record<string, unknown>;
        rows.push({
          tipo: 'coefficient',
          outcome,
          method: detail.method,
          coef: valueToString(point.coef),
          se: valueToString(point.se),
          pvalue: valueToString(point.pvalue),
          n_obs: '',
          r2: '',
          rel_time: valueToString(point.rel_time),
          ci_lower: valueToString(point.ci_lower),
          ci_upper: valueToString(point.ci_upper),
        });
      }
    }
  }

  return `${header.join(',')}\n${rows
    .map((row) => Object.values(row).map(toCsvValue).join(','))
    .join('\n')}`;
}

function isAnalysisMethod(method: string): method is AnalysisMethod {
  return ['did', 'iv', 'panel_iv', 'event_study', 'compare', 'scm', 'augmented_scm'].includes(method);
}

function getRequestNumber(params: Record<string, unknown> | undefined, key: string): number | null {
  if (!params) {
    return null;
  }

  const value = params[key];
  const parsed = parseNumericFinite(value);
  return parsed !== null ? parsed : null;
}

function getRequestIds(
  params: Record<string, unknown> | undefined,
  key: 'treated_ids' | 'control_ids',
): string[] {
  if (!params) {
    return [];
  }

  const candidate = params[key];
  if (!Array.isArray(candidate)) {
    return [];
  }

  return candidate
    .map((item) => (typeof item === 'string' ? item.trim() : String(item ?? '').trim()))
    .map((item) => normalizeMunicipioId(item))
    .filter((item): item is string => !!item);
}

function resolveIdsLabel(ids: string[], labels: MunicipioLabelMap): string {
  if (!ids.length) {
    return 'não informado';
  }

  return ids.map((id) => toMunicipioLabel(id, labels)).join('; ');
}

function getOutcomeMeta(outcome: string): OutcomeMetadata {
  return OUTCOME_METADATA[outcome] || {
    label: outcome,
    isLog: outcome.endsWith('_log'),
    kind: outcome.includes('correl') ? 'correlation' : outcome.includes('elastic') ? 'elasticity' : 'unknown',
  };
}

function logEffectToPercent(coef: number): number | null {
  if (!Number.isFinite(coef)) {
    return null;
  }

  const transformed = Math.exp(coef) - 1;
  return Number.isFinite(transformed) ? transformed * 100 : null;
}

function formatCausalEffectValue(coef: number, outcomeMeta: OutcomeMetadata): {
  short: string;
  long: string;
} {
  if (outcomeMeta.kind === 'correlation') {
    const bounded = Math.max(-1, Math.min(1, coef));
    return {
      short: `${formatDecimal(bounded, 4)} (r)`,
      long: `Correlação de ${formatDecimal(bounded, 4)} entre ${outcomeMeta.label.toLowerCase()} e a exposição (faixa [-1,1]).`,
    };
  }

  if (outcomeMeta.kind === 'elasticity') {
    return {
      short: `${formatDecimal(coef, 4)}`,
      long: `Elasticidade estimada de ${formatDecimal(coef, 4)}: uma unidade de impacto do tratamento está associada a ${formatDecimal(coef, 4)} variação relativa no nível de exposição/modelo.`,
    };
  }

  if (outcomeMeta.kind === 'ratio') {
    return {
      short: `${formatDecimal(coef, 4)}`,
      long: `Razão de ${formatDecimal(coef, 4)} entre ${outcomeMeta.label.toLowerCase()} tratado e comparação de grupo.`,
    };
  }

  if (outcomeMeta.kind === 'index') {
    return {
      short: `${formatDecimal(coef, 4)}`,
      long: `Nível de índice calculado em ${formatDecimal(coef, 4)} (sem unidade absoluta).`,
    };
  }

  if (outcomeMeta.kind === 'share' || outcomeMeta.kind === 'difference') {
    return {
      short: `${formatDecimal(coef, 4)}%`,
      long: `Variação de ${formatDecimal(coef, 4)} p.p. no resultado ${outcomeMeta.label.toLowerCase()}.`,
    };
  }

  if (outcomeMeta.kind === 'level' || outcomeMeta.isLog || outcomeMeta.kind === 'unknown') {
    if (outcomeMeta.isLog || outcomeMeta.kind === 'log') {
      const asPercent = logEffectToPercent(coef);
      const absPercent = asPercent === null ? null : formatDecimal(Math.abs(asPercent), 3);
      return {
        short: `${absPercent === null ? '—' : `${absPercent}%`}`,
        long:
          absPercent === null
            ? 'Não foi possível converter coeficiente log em variação percentual estável.'
            : `Efeito log/semilog aproximado de ${absPercent}% no indicador ${outcomeMeta.label.toLowerCase()}.`,
      };
    }

    return {
      short: `${formatDecimal(coef, 4)}`,
      long: `Coeficiente de ` + formatDecimal(coef, 4) + ` no nível de ${outcomeMeta.label.toLowerCase()}.`,
    };
  }

  return {
    short: formatDecimal(coef, 4),
    long: formatDecimal(coef, 4),
  };
}

function buildCausalQuestion({
  outcomeLabel,
  methodLabel,
  treatedLabel,
  controlLabel,
  treatmentYear,
  installationLabel,
}: {
  outcomeLabel: string;
  methodLabel: string;
  treatedLabel: string;
  controlLabel: string;
  treatmentYear: number | null;
  installationLabel?: string | null;
}) {
  const treatmentText = treatmentYear
    ? `a partir de ${Math.trunc(treatmentYear)}`
    : 'no recorte configurado';
  const treatedText = treatedLabel === 'não informado'
    ? 'municípios selecionados'
    : `municípios ${treatedLabel}`;
  const controlText = controlLabel === 'não informado'
    ? 'controles elegíveis'
    : `com comparação por ${controlLabel}`;
  const portoText = installationLabel
    ? ` no porto ${installationLabel}`
    : '';

  return `${methodLabel} responde à pergunta: se o choque de movimentação portuária${portoText} chega aos ${treatedText} (${treatmentText}), ${controlText}, qual o impacto em ${outcomeLabel}?`;
}

function buildSignificanceSummary(pValue: number | null): string {
  if (pValue === null) {
    return 'P-valor indisponível. Use apenas como evidência exploratória.';
  }
  if (pValue < 0.01) {
    return 'Evidência forte (p < 1%)';
  }
  if (pValue < 0.05) {
    return 'Evidência compatível com 5%';
  }
  if (pValue < 0.10) {
    return 'Sinal fraco/médio (10%)';
  }
  return 'Sem evidência estatística convencional';
}

function buildCausalDecision({
  outcomeLabel,
  effectSummary,
  row,
  treatedLabel,
  controlLabel,
  methodLabel,
  significance,
  outcomeMeta,
  installationLabel,
}: {
  outcomeLabel: string;
  effectSummary: { short: string; long: string };
  row: CausalSummaryPoint;
  treatedLabel: string;
  controlLabel: string;
  methodLabel: string;
  significance: string;
  outcomeMeta: OutcomeMetadata;
  installationLabel?: string | null;
}): string {
  if (outcomeMeta.kind === 'correlation') {
    return `${methodLabel} retornou associação estatística (${significance}) entre ${outcomeLabel} e o indicador tratado. Para decisão de impacto, use DiD/SCM/IV com hipótese forte de identificação.`;
  }

  const treatedText = treatedLabel === 'não informado' ? 'municípios selecionados' : `os municípios ${treatedLabel}`;
  const controlText =
    controlLabel && controlLabel !== 'não informado' ? ` comparados com ${controlLabel}` : '';
  const direction = row.coef > 0 ? 'eleva' : row.coef < 0 ? 'reduz' : 'não altera claramente';
  const portoText = installationLabel ? ` no porto ${installationLabel}` : '';
  const magnitudeText =
    effectSummary.short === '—'
      ? 'efeito de baixa precisão'
      : `${effectSummary.long} (${effectSummary.short})`;

  return `Interpretação executiva: sob esse modelo, o cenário em ${treatedText}${controlText}${portoText} indica que o impacto estimado é de ${magnitudeText} em ${outcomeLabel}, em média, ou seja, tende a ${direction} o indicador (${significance}).`;
}

function buildCausalInterpretations(
  detail: AnalysisDetail | null,
  municipioLabels: MunicipioLabelMap,
  installationLabel?: string | null,
): CausalNarrative[] {
  if (
    !detail?.result_full ||
    detail.status !== 'success' ||
    !detail.method ||
    detail.method === 'compare'
  ) {
    return [];
  }

  const rows = buildCausalSummary(detail);
  if (!rows.length) {
    return [];
  }

  const method: AnalysisMethod = isAnalysisMethod(detail.method) ? detail.method : 'did';
  const requestParams = detail.request_params;
  const treatedIds = getRequestIds(requestParams, 'treated_ids');
  const controlIds = getRequestIds(requestParams, 'control_ids');
  const treatmentYear = getRequestNumber(requestParams, 'treatment_year');
  const treatedLabel = resolveIdsLabel(treatedIds, municipioLabels);
  const controlLabel = resolveIdsLabel(controlIds, municipioLabels);
  const methodLabel = ANALYSIS_METHOD_LABELS[method];
  const periodLabel = treatmentYear
    ? `a partir de ${Math.trunc(treatmentYear)}`
    : 'no período estudado';

  return rows.map((row) => {
    const outcomeMeta = getOutcomeMeta(row.outcome);
    const outcomeLabel = outcomeMeta.label;
    const controlText = controlIds.length > 0
      ? `comparando com ${controlLabel}`
      : 'comparando com controles elegíveis';
    const effectSummary = formatCausalEffectValue(row.coef, outcomeMeta);
    const question = buildCausalQuestion({
      outcomeLabel,
      methodLabel,
      treatedLabel,
      controlLabel,
      treatmentYear,
      installationLabel,
    });

    const ciLowerText = row.ciLower === null ? null : formatDecimal(row.ciLower, 4);
    const ciUpperText = row.ciUpper === null ? null : formatDecimal(row.ciUpper, 4);
    const rangeText =
      ciLowerText === null || ciUpperText === null
        ? ''
        : `. IC95% ${ciLowerText} a ${ciUpperText}`;

    let implication = `${effectSummary.long}${rangeText}.`;
    if (outcomeMeta.kind === 'correlation' && Math.abs(row.coef) > 1) {
      implication = `${outcomeLabel}: valor fora do intervalo esperado de correlação [-1, 1].`;
    }

    const significance = buildSignificanceSummary(row.pvalue);
    const decision = buildCausalDecision({
      outcomeLabel,
      effectSummary,
      row,
      treatedLabel,
      controlLabel,
      methodLabel,
      significance,
      outcomeMeta,
      installationLabel,
    });

    const confidence =
      row.nObs === null
        ? 'Observações não informadas.'
        : row.nObs < 30
          ? `Baixa robustez com ${row.nObs} observações.`
          : `Amostra com ${row.nObs} observações.`;

    const interpretation =
      `${methodLabel} com municípios tratados (${treatedLabel}) ${controlText}, aplicado ${periodLabel}. ${implication} ${significance}. ${confidence}`;

      return {
        outcome: row.outcome,
        outcomeLabel,
        question,
        method: methodLabel,
        interpretation,
        implication,
        decision,
        significance,
        confidence,
      };
  });
}

function parseNumeric(value: string): number | null {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function renderWarnings(
  warnings: unknown[],
  municipioLabels: MunicipioLabelMap,
): JSX.Element | null {
  if (!warnings || !warnings.length) {
    return null;
  }

  return (
    <div className="mt-3 rounded border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
      <p className="font-medium mb-1">Observações de qualidade:</p>
      <ul className="list-disc pl-4 space-y-1">
        {warnings.map((warning, index) => {
          const warningRecord = warning as {
            tipo?: unknown;
            campo?: unknown;
            mensagem?: unknown;
            id_municipio?: unknown;
            ano?: unknown;
          };
          const warningTipo = typeof warningRecord.tipo === 'string' ? warningRecord.tipo : 'warn';
          const mensagem = typeof warningRecord.mensagem === 'string' ? warningRecord.mensagem : 'Sem mensagem';
          const campo = typeof warningRecord.campo === 'string' ? warningRecord.campo : '';
          const municipio = warningRecord.id_municipio ? String(warningRecord.id_municipio) : '';
          const municipioLabel = municipio ? resolveMunicipioLabel(municipio, municipioLabels, { showCode: false }) : '';
          const ano = warningRecord.ano ? String(warningRecord.ano) : '';
          const hasSuffix = warningRecord.id_municipio || warningRecord.ano;

          return (
            <li key={`${warningTipo}-${campo}-${index}`}>
              <span className="font-semibold">{warningTipo}</span>: {mensagem}
              {municipioLabel ? ` [município ${municipioLabel}` : ''}
              {ano ? `, ano ${ano}` : ''}
              {hasSuffix ? ']' : ''}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function Module5View() {
  const { selectedYear, selectedInstallation } = useFilterStore();

  const [indicators, setIndicators] = useState<ModuleIndicatorStore>({});
  const [indicatorsLoading, setIndicatorsLoading] = useState(true);
  const [indicatorsError, setIndicatorsError] = useState<string | null>(null);
  const [implementationStatus, setImplementationStatus] = useState<Record<string, ImplementationStatus>>({});

  const [analysisMethod, setAnalysisMethod] = useState<AnalysisMethod>('did');
  const [analysisTreated, setAnalysisTreated] = useState('');
  const [analysisControls, setAnalysisControls] = useState('');
  const [analysisOutcomes, setAnalysisOutcomes] = useState('pib_log');
  const [analysisScope, setAnalysisScope] = useState<AnalysisScope>('state');
  const [analysisInstrument, setAnalysisInstrument] = useState('');
  const [analysisStartYear, setAnalysisStartYear] = useState(2010);
  const [analysisEndYear, setAnalysisEndYear] = useState(selectedYear);
  const [analysisUseMart, setAnalysisUseMart] = useState(true);
  const [municipioLabelIndex, setMunicipioLabelIndex] = useState<MunicipioLabelMap>({});
  const [policyMunicipioIds, setPolicyMunicipioIds] = useState<string[]>([]);
  const [policyAreaInfluence, setPolicyAreaInfluence] = useState<
    Record<string, PolicyMunicipioItem[]>
  >({});
  const [policyError, setPolicyError] = useState<string | null>(null);

  const [activeAnalysisId, setActiveAnalysisId] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [creatingAnalysis, setCreatingAnalysis] = useState(false);
  const [recentAnalyses, setRecentAnalyses] = useState<AnalysisResponse[]>([]);
  const [_analysesLoading, setAnalysesLoading] = useState(false);
  const [_analysesError, setAnalysesError] = useState<string | null>(null);
  const [isDownloadingDocx, setIsDownloadingDocx] = useState(false);
  const [isMatchingControls, setIsMatchingControls] = useState(false);

  const {
    analysis: polledAnalysis,
    result: polledResult,
    isLoading: _isPolling,
    error: pollingError,
    refresh: refreshAnalysis,
  } = useAnalysis(activeAnalysisId);

  const analysisToDisplay: AnalysisDetail | null = polledResult ?? null;
  const activeAnalysis = polledAnalysis;

  const municipioLabelsFromIndicators = useMemo(() => {
    const lookup: MunicipioLabelMap = {};
    Object.values(indicators).forEach((indicator) => {
      toIndicatorRows(indicator).forEach((row) => {
        const id = normalizeMunicipioId(row.id_municipio);
        const nome = row.nome_municipio;
        if (
          id &&
          typeof nome === 'string' &&
          nome.trim() &&
          !isLikelyIdNameMismatch(id, nome) &&
          !normalizeMunicipioId(nome)
        ) {
          lookup[id.trim()] = nome.trim();
        }
      });
    });
    return lookup;
  }, [indicators]);

  const municipioLabels = useMemo(
    () => ({ ...municipioLabelIndex, ...municipioLabelsFromIndicators }),
    [municipioLabelIndex, municipioLabelsFromIndicators],
  );

  const selectedInstallationMunicipioIds = useMemo(() => {
    const candidates = selectedInstallation ? policyAreaInfluence[selectedInstallation] : [];
    if (!Array.isArray(candidates)) {
      return [];
    }

    return toMunicipioIdList(candidates.map((entry) => entry.id_municipio));
  }, [policyAreaInfluence, selectedInstallation]);

  const municipioCatalogIds = useMemo(() => {
    const ids = new Set<string>(Object.keys(municipioLabels));
    for (const municipalityId of policyMunicipioIds) {
      const id = municipalityId.trim();
      if (normalizeMunicipioId(id)) {
        ids.add(id);
      }
    }
    for (const municipalityId of selectedInstallationMunicipioIds) {
      ids.add(municipalityId);
    }
    return toMunicipioIdList(Array.from(ids));
  }, [municipioLabels, policyMunicipioIds, selectedInstallationMunicipioIds]);

  const fetchMetadata = useCallback(async () => {
    try {
      const metadata = await indicatorsService.getMetadata();
      const statusMap = Object.fromEntries(
        metadata.indicadores.map((item: IndicatorMetadata) => [
          item.codigo,
          item.implementation_status === 'technical_debt'
            ? 'technical_debt'
            : 'implemented',
        ]),
      ) as Record<string, ImplementationStatus>;
      setImplementationStatus(statusMap);
    } catch {
      const fallback = Object.fromEntries(
        INDICATORS_INFO.map((item) => [item.code, 'implemented' as ImplementationStatus]),
      ) as Record<string, ImplementationStatus>;
      setImplementationStatus(fallback);
    }
  }, []);

  const loadPolicies = useCallback(async () => {
    try {
      const policies = await indicatorsService.getPolicies();
      const allowed = toMunicipioIdList(policies.allowed_municipios || []);
      const municipioInfluenceIds = Object.values(
        policies.municipio_influencia || policies.area_influencia || {},
      ).flatMap((municipios) =>
        Array.isArray(municipios)
          ? toMunicipioIdList(
              municipios.map((entry) => normalizeMunicipioId(entry.id_municipio)),
            )
            : [],
      );
      const baselineResponse = await indicatorsService.queryIndicator<RawIndicatorRow>({
        codigo_indicador: 'IND-5.01',
        params: { ano: selectedYear },
      });
      const fallbackIds = toMunicipioIdList(
        toIndicatorRows(baselineResponse).map((row) => normalizeMunicipioId(row.id_municipio)),
      );
      const fallbackLabels = toIndicatorRows(baselineResponse).reduce<MunicipioLabelMap>((acc, row) => {
        const id = normalizeMunicipioId(row.id_municipio);
        const nome = typeof row.nome_municipio === 'string' ? row.nome_municipio.trim() : '';
        if (id && nome && !isLikelyIdNameMismatch(id, nome) && !normalizeMunicipioId(nome)) {
          acc[id] = nome;
        }
        return acc;
      }, {});

      setPolicyMunicipioIds(Array.from(new Set([...allowed, ...municipioInfluenceIds, ...fallbackIds])));
      if (Object.keys(fallbackLabels).length > 0) {
        setMunicipioLabelIndex((current) => ({ ...fallbackLabels, ...current }));
      }
      setPolicyAreaInfluence(policies.municipio_influencia || policies.area_influencia || {});
      setPolicyError(null);
    } catch (error: unknown) {
      const errorResponse = error as ApiErrorLike;
      const errorMessage = errorResponse?.response?.data?.detail || '';
      setPolicyError(typeof errorMessage === 'string' ? errorMessage : 'Erro ao carregar políticas.');
      setPolicyMunicipioIds([]);
      setPolicyAreaInfluence({});
    }
  }, [selectedYear]);

  const loadRecentAnalyses = useCallback(async () => {
    setAnalysesLoading(true);
    setAnalysesError(null);
    try {
      const response = await impactoEconomicoService.listAnalyses({ page: 1, page_size: 10 });
      setRecentAnalyses(response.items);
    } catch (error: unknown) {
      const errorResponse = error as ApiErrorLike;
      const errorMessage = errorResponse?.response?.data?.detail || 'Erro ao carregar histórico de análises';
      setAnalysesError(typeof errorMessage === 'string' ? errorMessage : 'Erro ao carregar histórico de análises');
    } finally {
      setAnalysesLoading(false);
    }
  }, []);

  const loadIndicators = useCallback(async () => {
    setIndicatorsLoading(true);
    setIndicatorsError(null);
    try {
      const activeIndicators = INDICATORS_INFO.filter(
        (ind) => implementationStatus[ind.code] !== 'technical_debt',
      );
      const promises = activeIndicators.map((ind) =>
        indicatorsService.queryIndicator({
          codigo_indicador: ind.code,
          params: {
            ano: selectedYear,
            id_instalacao: selectedInstallation || undefined,
          },
        }).catch(() => createEmptyIndicatorResponse(ind.code)),
      );
      const results = await Promise.all(promises);
      const mapped = INDICATORS_INFO.reduce<ModuleIndicatorStore>((acc, ind) => {
        acc[ind.code] = createEmptyIndicatorResponse(ind.code);
        return acc;
      }, {});
      results.forEach((result, i) => {
        mapped[activeIndicators[i].code] = result;
      });
      setIndicators(mapped);
    } catch (err: unknown) {
      const errorResponse = err as ApiErrorLike;
      const errorMessage = errorResponse?.response?.data?.detail || 'Erro ao carregar indicadores';
      setIndicatorsError(typeof errorMessage === 'string' ? errorMessage : 'Erro ao carregar indicadores');
    } finally {
      setIndicatorsLoading(false);
    }
  }, [implementationStatus, selectedYear, selectedInstallation]);

  const resolveMunicipioLabels = useCallback(async (rawIds: string[]) => {
    const ids = Array.from(
      new Set(
        rawIds
          .map((id) => normalizeMunicipioId(id))
          .filter((id) => id && id.length >= 2 && !municipioLabels[id]),
      ),
    );
    if (!ids.length) {
      return;
    }

    const nextLabels: MunicipioLabelMap = {};
    try {
      const response = await indicatorsService.getMunicipioLookup(ids);
      response.municipios.forEach((item) => {
        const municipioId = normalizeMunicipioId(item.id_municipio);
        const nomeMunicipio = item.nome_municipio?.trim();
        if (municipioId && nomeMunicipio) {
          nextLabels[municipioId] = nomeMunicipio;
        }
      });
    } catch {
      // sem retorno
    }

    if (Object.keys(nextLabels).length > 0) {
      setMunicipioLabelIndex((current) => ({ ...current, ...nextLabels }));
    }
  }, [municipioLabels]);

  const selectedTreatedMunicipios = useMemo(
    () => toSafeArray(analysisTreated),
    [analysisTreated],
  );
  const selectedControlMunicipios = useMemo(
    () => toSafeArray(analysisControls),
    [analysisControls],
  );
  const selectedMunicipioInputs = useMemo(
    () => Array.from(new Set([...selectedTreatedMunicipios, ...selectedControlMunicipios])),
    [selectedControlMunicipios, selectedTreatedMunicipios],
  );

  useEffect(() => {
    void resolveMunicipioLabels(selectedMunicipioInputs);
  }, [selectedMunicipioInputs, resolveMunicipioLabels]);

  useEffect(() => {
    void resolveMunicipioLabels(municipioCatalogIds);
  }, [municipioCatalogIds, resolveMunicipioLabels]);

  useEffect(() => {
    fetchMetadata();
    loadRecentAnalyses();
    loadPolicies();
  }, [fetchMetadata, loadRecentAnalyses, loadPolicies]);

  useEffect(() => {
    if (!implementationStatus || Object.keys(implementationStatus).length === 0) {
      return;
    }
    loadIndicators();
  }, [implementationStatus, loadIndicators]);

  useEffect(() => {
    setAnalysisEndYear(selectedYear);
  }, [selectedYear]);

  useEffect(() => {
    if (activeAnalysis && activeAnalysis.status === 'success') {
      loadRecentAnalyses();
    }
  }, [activeAnalysis, loadRecentAnalyses]);

  const handleStartAnalysis = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAnalysisError(null);

    const treatedIds = toSafeArray(analysisTreated);
    if (treatedIds.length === 0) {
      setAnalysisError('Informe pelo menos um id_municipio em "Municípios tratados".');
      return;
    }

    const outcomes = toSafeArray(analysisOutcomes).filter((v: string) => !!v);
    if (outcomes.length === 0) {
      setAnalysisError('Informe pelo menos um outcome.');
      return;
    }

    const treatmentYear = parseNumeric(String(analysisEndYear));
    const anoInicio = parseNumeric(String(analysisStartYear));
    const anoFim = parseNumeric(String(analysisEndYear));
    if (treatmentYear === null || anoInicio === null || anoFim === null) {
      setAnalysisError('Informe períodos numéricos válidos.');
      return;
    }
    if (analysisMethod === 'iv' || analysisMethod === 'panel_iv') {
      const instrument = analysisInstrument.trim();
      if (!instrument) {
        setAnalysisError('Métodos IV exigem instrumento.');
        return;
      }
    }

    const payload: AnalysisCreateRequest = {
      method: analysisMethod,
      treated_ids: treatedIds,
      control_ids: toSafeArray(analysisControls),
      treatment_year: treatmentYear,
      scope: analysisScope,
      outcomes,
      controls: null,
      instrument: analysisInstrument.trim() || null,
      ano_inicio: anoInicio,
      ano_fim: anoFim,
      use_mart: analysisUseMart,
    };

    setCreatingAnalysis(true);
    try {
      const created = await impactoEconomicoService.createAnalysis(payload);
      setActiveAnalysisId(created.id);
      await loadRecentAnalyses();
    } catch (err: unknown) {
      const errorResponse = err as ApiErrorLike;
      const errorMessage = errorResponse?.response?.data?.detail || 'Erro ao iniciar análise.';
      setAnalysisError(typeof errorMessage === 'string' ? errorMessage : 'Erro ao iniciar análise.');
    } finally {
      setCreatingAnalysis(false);
    }
  };

  const handleSuggestControls = async () => {
    const treatedIds = toSafeArray(analysisTreated);
    if (treatedIds.length === 0) {
      setAnalysisError('Informe ao menos um município tratado para sugerir controles.');
      return;
    }

    const treatmentYear = parseNumeric(String(analysisEndYear));
    const anoInicio = parseNumeric(String(analysisStartYear));
    const anoFim = parseNumeric(String(analysisEndYear));
    if (treatmentYear === null || anoInicio === null || anoFim === null) {
      setAnalysisError('Informe períodos válidos para executar o matching.');
      return;
    }

    setAnalysisError(null);
    setIsMatchingControls(true);

    try {
      const payload = {
        treated_ids: treatedIds,
        treatment_year: treatmentYear,
        scope: analysisScope,
        ano_inicio: anoInicio,
        ano_fim: anoFim,
      };
      const response: MatchingResponse = await impactoEconomicoService.suggestMatchingControls(payload);
      const matchedIds = response.suggested_controls.map((control) => control.id_municipio);
      setAnalysisControls(matchedIds.join(', '));
    } catch (err: unknown) {
      const errorResponse = err as ApiErrorLike;
      const errorMessage = errorResponse?.response?.data?.detail || 'Erro ao sugerir controles.';
      setAnalysisError(typeof errorMessage === 'string' ? errorMessage : 'Erro ao sugerir controles.');
    } finally {
      setIsMatchingControls(false);
    }
  };

  // analysisMainRows: substituído por causalSummaryRows no painel técnico (Bloco B)

  const compareData = useMemo(() => {
    if (!analysisToDisplay?.result_full || analysisToDisplay.method !== 'compare') {
      return [];
    }
    const payload = analysisToDisplay.result_full as Record<string, unknown>;
    const comparison = payload?.comparison;
    if (!comparison || typeof comparison !== 'object') {
      return [];
    }
    return Object.entries(comparison as Record<string, unknown>).map(([outcome, sectionAny]) => {
      const section = sectionAny as Record<string, unknown>;
      return {
        outcome,
        recommendation:
          typeof section?.recommended_estimate === 'string'
            ? section.recommended_estimate
            : undefined,
        consistency_assessment:
          typeof section?.consistency_assessment === 'string'
            ? section.consistency_assessment
            : section?.consistency_assessment !== undefined
              ? String(section.consistency_assessment)
              : undefined,
        comparison_table: parseComparisonRows(section?.comparison_table),
      } as ComparisonPayload;
    }) as ComparisonPayload[];
  }, [analysisToDisplay]);

  const causalSummaryRows = useMemo(() => buildCausalSummary(analysisToDisplay), [analysisToDisplay]);
  const eventStudyPayloads = useMemo(() => buildEventStudyPayloads(analysisToDisplay), [analysisToDisplay]);
  const causalNarratives = useMemo(
    () => buildCausalInterpretations(analysisToDisplay, municipioLabels, selectedInstallation),
    [analysisToDisplay, municipioLabels, selectedInstallation],
  );

  const handleDownloadCsv = () => {
    if (!analysisToDisplay) {
      return;
    }
    const csv = createCoefficientsCsvPayload(analysisToDisplay);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `analise_${analysisToDisplay.id}_coefs.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const handleDownloadDocx = async () => {
    if (!analysisToDisplay) {
      return;
    }

    setAnalysisError(null);
    setIsDownloadingDocx(true);

    try {
      const { blob, filename } = await impactoEconomicoService.getAnalysisReport(analysisToDisplay.id);
      const url = window.URL.createObjectURL(
        new Blob([blob], {
          type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        }),
      );
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      const errorResponse = err as ApiErrorLike;
      const errorMessage = errorResponse?.response?.data?.detail || 'Erro ao exportar relatório DOCX.';
      setAnalysisError(typeof errorMessage === 'string' ? errorMessage : 'Erro ao exportar relatório DOCX.');
    } finally {
      setIsDownloadingDocx(false);
    }
  };

  const shouldRenderIndicators = indicators && Object.keys(indicators).length > 0;
  const sortedMunicipioOptions = useMemo(() => {
    const entries = municipioCatalogIds
      .map((id) => ({ id, label: toMunicipioLabel(id, municipioLabels) }))
      .filter((item) => !!item.label);
    entries.sort((a, b) => a.label.localeCompare(b.label, 'pt-BR'));
    return entries;
  }, [municipioCatalogIds, municipioLabels]);

  // ── Estado local de UI ──────────────────────────────────────────────────────
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showTechDetail, setShowTechDetail] = useState(false);
  const [indicatorGroupOpen, setIndicatorGroupOpen] = useState<Record<IndicatorGroup, boolean>>({
    economia: true, porto: true, comercio: false, tendencias: false,
  });

  const toggleGroup = (g: IndicatorGroup) =>
    setIndicatorGroupOpen((prev) => ({ ...prev, [g]: !prev[g] }));

  const GROUP_LABELS: Record<IndicatorGroup, string> = {
    economia:   '🏙 Economia Municipal',
    porto:      '⚓ Atividade Portuária',
    comercio:   '🌐 Comércio Exterior',
    tendencias: '📈 Tendências Anuais',
  };

  // ── Outcomes selecionados como array para checkboxes ─────────────────────
  const selectedOutcomeArray = useMemo(() => toSafeArray(analysisOutcomes), [analysisOutcomes]);
  const toggleOutcome = (value: string) => {
    const current = toSafeArray(analysisOutcomes);
    const next = current.includes(value) ? current.filter((v: string) => v !== value) : [...current, value];
    setAnalysisOutcomes(next.join(', '));
  };

  return (
    <div className="space-y-6">
      {/* ══ Cabeçalho ══════════════════════════════════════════════════════ */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Impacto Econômico do Porto</h1>
          <p className="text-gray-500 mt-1">
            Avalie como a atividade portuária influencia a economia do município sob análise
          </p>
        </div>
        <ExportButton moduleCode="5" />
      </div>

      <FilterBar />

      {/* ══ BLOCO A — Sua Pergunta ══════════════════════════════════════════ */}
      <div className="card space-y-5">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Faça sua pergunta</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Como a movimentação portuária alterou a economia do município selecionado?
            </p>
          </div>
          <button
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 text-sm text-gray-600 hover:bg-gray-50"
            onClick={() => { void loadRecentAnalyses(); refreshAnalysis(); }}
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Atualizar
          </button>
        </div>

        {policyError && <ErrorAlert message={`Políticas: ${policyError}`} />}

        <form onSubmit={handleStartAnalysis} className="space-y-5">
          {/* — Municípios — */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-800">
                Qual município recebe o impacto do porto?
              </label>
              <p className="text-xs text-gray-500">Selecione o(s) município(s) do município de influência</p>
              <select
                value={toSafeArray(analysisTreated)}
                multiple
                size={5}
                onChange={(e) => setAnalysisTreated(Array.from(e.target.selectedOptions).map((o) => o.value).join(', '))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
              >
                {!sortedMunicipioOptions.length && <option disabled>Carregando municípios...</option>}
                {sortedMunicipioOptions.map((m) => (
                  <option key={`t-${m.id}`} value={m.id}>{m.label}</option>
                ))}
              </select>
              {toSafeArray(analysisTreated).length > 0 && (
                <p className="text-xs text-indigo-700 font-medium">
                  ✓ {formatMunicipioLabelList(toSafeArray(analysisTreated), municipioLabels)}
                </p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-800">
                Com quais municípios comparar?
              </label>
              <p className="text-xs text-gray-500">Municípios sem porto para servir de base de comparação</p>
              <div className="flex gap-2">
                <select
                  value={toSafeArray(analysisControls)}
                  multiple
                  size={5}
                  onChange={(e) => setAnalysisControls(Array.from(e.target.selectedOptions).map((o) => o.value).join(', '))}
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm"
                >
                  {!sortedMunicipioOptions.length && <option disabled>Carregando municípios...</option>}
                  {sortedMunicipioOptions.map((m) => (
                    <option key={`c-${m.id}`} value={m.id}>{m.label}</option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => { void handleSuggestControls(); }}
                  disabled={isMatchingControls}
                  className="flex-shrink-0 inline-flex flex-col items-center gap-1 px-3 py-2 rounded-lg border border-indigo-300 bg-indigo-50 text-xs text-indigo-700 hover:bg-indigo-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Search className="h-4 w-4" />
                  {isMatchingControls ? 'Buscando...' : 'Sugerir automaticamente'}
                </button>
              </div>
              {toSafeArray(analysisControls).length > 0 && (
                <p className="text-xs text-gray-600">
                  {formatMunicipioLabelList(toSafeArray(analysisControls), municipioLabels)}
                </p>
              )}
            </div>
          </div>

          {/* — Período — */}
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-800">Início do histórico</label>
              <input
                type="number"
                value={analysisStartYear}
                onChange={(e) => setAnalysisStartYear(parseNumeric(e.target.value) || 2010)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-800">
                Quando ocorreu o evento do porto?
              </label>
              <input
                type="number"
                value={analysisEndYear}
                onChange={(e) => setAnalysisEndYear(parseNumeric(e.target.value) || selectedYear)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
              />
              <p className="text-xs text-gray-500">Ano da intervenção ou mudança analisada</p>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-800">Fim do período</label>
              <input
                type="number"
                value={analysisEndYear}
                onChange={(e) => setAnalysisEndYear(parseNumeric(e.target.value) || selectedYear)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
              />
            </div>
          </div>

          {/* — O que medir — */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-800">O que você quer medir?</label>
            <p className="text-xs text-gray-500">Selecione os indicadores de impacto de interesse</p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {OUTCOME_CHOICES.map((oc) => (
                <label
                  key={oc.value}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer text-sm transition-colors ${
                    selectedOutcomeArray.includes(oc.value)
                      ? 'border-indigo-400 bg-indigo-50 text-indigo-800'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedOutcomeArray.includes(oc.value)}
                    onChange={() => toggleOutcome(oc.value)}
                    className="h-3.5 w-3.5 accent-indigo-600"
                  />
                  {oc.label}
                </label>
              ))}
            </div>
          </div>

          {/* — Método — */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-800">Método de análise</label>
            <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
              {ANALYSIS_METHODS.map((m) => (
                <label
                  key={m.value}
                  className={`flex flex-col gap-0.5 px-3 py-2.5 rounded-lg border cursor-pointer transition-colors ${
                    analysisMethod === m.value
                      ? 'border-indigo-400 bg-indigo-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="analysisMethod"
                      value={m.value}
                      checked={analysisMethod === m.value}
                      onChange={() => setAnalysisMethod(m.value)}
                      className="h-3.5 w-3.5 accent-indigo-600"
                    />
                    <span className={`text-sm font-medium ${analysisMethod === m.value ? 'text-indigo-800' : 'text-gray-800'}`}>
                      {ANALYSIS_METHOD_LABELS[m.value]}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 pl-5">{ANALYSIS_METHOD_DESCRIPTIONS[m.value]}</p>
                </label>
              ))}
            </div>
          </div>

          {/* — Configurações avançadas — */}
          <div>
            <button
              type="button"
              onClick={() => setShowAdvanced((v) => !v)}
              className="inline-flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-700"
            >
              {showAdvanced ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
              Configurações avançadas (instrumento, escopo, cache)
            </button>
            {showAdvanced && (
              <div className="mt-3 grid gap-3 md:grid-cols-3 p-3 rounded-lg bg-gray-50 border border-gray-200">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-gray-700">Variável instrumental</label>
                  <input
                    value={analysisInstrument}
                    onChange={(e) => setAnalysisInstrument(e.target.value)}
                    className="w-full border border-gray-300 rounded px-2 py-1.5 text-xs"
                    placeholder="commodity_index, preco_soja..."
                  />
                  <p className="text-xs text-gray-400">Obrigatório para IV / Painel IV</p>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-gray-700">Escopo de controles</label>
                  <select
                    className="w-full border border-gray-300 rounded px-2 py-1.5 text-xs"
                    value={analysisScope}
                    onChange={(e) => setAnalysisScope(e.target.value as AnalysisScope)}
                  >
                    <option value="state">Mesmo estado</option>
                    <option value="municipal">Nacional</option>
                  </select>
                </div>
                <div className="flex items-end pb-1">
                  <label className="inline-flex items-center gap-2 text-xs text-gray-700">
                    <input
                      type="checkbox"
                      checked={analysisUseMart}
                      onChange={(e) => setAnalysisUseMart(e.target.checked)}
                      className="h-3.5 w-3.5"
                    />
                    Usar dados pré-processados (mais rápido)
                  </label>
                </div>
              </div>
            )}
          </div>

          {analysisError && <ErrorAlert message={analysisError} />}

          <button
            type="submit"
            disabled={creatingAnalysis}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 disabled:opacity-50"
          >
            <Play className="h-4 w-4" />
            {creatingAnalysis ? 'Iniciando análise...' : 'Analisar impacto'}
          </button>
        </form>

        {/* — Histórico resumido — */}
        {recentAnalyses.length > 0 && (
          <div className="pt-3 border-t border-gray-100">
            <p className="text-xs font-medium text-gray-500 mb-2">Análises anteriores</p>
            <div className="flex flex-wrap gap-2">
              {recentAnalyses.slice(0, 5).map((entry) => (
                <button
                  key={entry.id}
                  onClick={() => setActiveAnalysisId(entry.id)}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-gray-200 text-xs text-gray-600 hover:border-indigo-300 hover:text-indigo-700"
                >
                  <AnalysisStatusBadge status={entry.status} />
                  <span>{ANALYSIS_METHOD_LABELS[entry.method as AnalysisMethod] ?? entry.method}</span>
                  <span className="text-gray-400">{new Date(entry.created_at).toLocaleDateString('pt-BR')}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ══ BLOCO B — Resultado Causal ══════════════════════════════════════ */}
      {activeAnalysis && (
        <div className="space-y-4">
          {/* Status */}
          {(activeAnalysis.status === 'queued' || activeAnalysis.status === 'running') && (
            <div className="card flex items-center gap-4 py-5">
              <LoadingSpinner />
              <div>
                <p className="font-medium text-gray-900">
                  {activeAnalysis.status === 'queued' ? 'Análise aguardando processamento...' : 'Calculando o impacto...'}
                </p>
                <p className="text-sm text-gray-500 mt-0.5">
                  Isso pode levar alguns instantes dependendo do tamanho dos dados.
                </p>
              </div>
            </div>
          )}

          {pollingError && <ErrorAlert message={pollingError} />}
          {activeAnalysis.status === 'failed' && analysisToDisplay?.error_message && (
            <div className="card border-red-200 bg-red-50">
              <p className="font-medium text-red-800 mb-1">Não foi possível completar a análise</p>
              <p className="text-sm text-red-700">{analysisToDisplay.error_message}</p>
              <p className="text-xs text-red-500 mt-2">Verifique os parâmetros e tente novamente. Se o problema persistir, tente um período mais longo ou municípios controle diferentes.</p>
            </div>
          )}

          {/* Resultado principal */}
          {analysisToDisplay?.status === 'success' && (
            <div className="space-y-4">

              {/* Cards de impacto por outcome */}
              {causalNarratives.length > 0 && analysisToDisplay.method !== 'compare' && (
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 mb-3">
                    Resultado da Análise
                  </h2>
                  <div className="grid gap-4 md:grid-cols-2">
                    {causalNarratives.map((item, idx) => {
                      const summaryRow = causalSummaryRows[idx];
                      const level = summaryRow ? getConfidenceLevel(summaryRow) : 'weak';
                      const conf = CONFIDENCE_CONFIG[level];
                      const effectStr = summaryRow
                        ? formatCausalEffectValue(summaryRow.coef, getOutcomeMeta(summaryRow.outcome)).short
                        : '—';
                      const isPositive = summaryRow && summaryRow.coef > 0;
                      const isNegative = summaryRow && summaryRow.coef < 0;

                      return (
                        <div
                          key={`${item.outcome}-card`}
                          className={`rounded-xl border-2 p-5 space-y-3 ${conf.border} ${conf.bg}`}
                        >
                          {/* Semáforo + indicador */}
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                                Impacto em
                              </p>
                              <p className="text-base font-semibold text-gray-900 mt-0.5">
                                {item.outcomeLabel}
                              </p>
                            </div>
                            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${conf.border} ${conf.bg} ${conf.color}`}>
                              {level === 'strong' ? '🟢' : level === 'moderate' ? '🟡' : '🔴'} {conf.label}
                            </span>
                          </div>

                          {/* Número grande */}
                          <div className="flex items-end gap-2">
                            <span className={`text-4xl font-bold tabular-nums ${
                              isPositive ? 'text-emerald-700' : isNegative ? 'text-red-600' : 'text-gray-700'
                            }`}>
                              {isPositive ? '+' : ''}{effectStr}
                            </span>
                          </div>

                          {/* Pergunta e conclusão */}
                          <p className="text-sm text-gray-700 font-medium">{item.question}</p>
                          <p className="text-sm text-gray-700">{item.decision}</p>

                          {/* Chips de qualidade */}
                          <div className="flex flex-wrap gap-1.5 pt-1">
                            <span className="text-xs px-2 py-0.5 rounded-full bg-white border border-gray-200 text-gray-600">
                              {item.method}
                            </span>
                            <span className="text-xs px-2 py-0.5 rounded-full bg-white border border-gray-200 text-gray-600">
                              {item.significance}
                            </span>
                            <span className="text-xs px-2 py-0.5 rounded-full bg-white border border-gray-200 text-gray-600">
                              {item.confidence}
                            </span>
                          </div>

                          {/* Nota se evidência fraca */}
                          {level === 'weak' && (
                            <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded p-2">
                              ⚠ Sem significância estatística neste recorte. Resultado não deve ser usado para decisão. Tente um período mais longo ou municípios controle mais similares.
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Gráfico comparativo de efeitos */}
              {causalSummaryRows.length > 1 && analysisToDisplay.method !== 'compare' && (
                <div className="card">
                  <h3 className="font-semibold text-gray-900 mb-1">Comparativo de efeitos por indicador</h3>
                  <p className="text-xs text-gray-500 mb-3">
                    Verde = evidência estatística (p &lt; 5%); Azul = sem evidência suficiente
                  </p>
                  <div className="h-56">
                    <BarChart
                      labels={causalSummaryRows.map((row) => getOutcomeMeta(row.outcome).label)}
                      datasets={[{
                        label: 'Efeito estimado',
                        data: causalSummaryRows.map((row) => {
                          const pct = row.coef !== null ? logEffectToPercent(row.coef) : null;
                          return pct ?? row.coef;
                        }),
                        backgroundColor: causalSummaryRows.map((row) =>
                          row.significant ? '#10b981' : '#93c5fd',
                        ),
                      }]}
                      yAxisLabel="Efeito (%)"
                      horizontal
                      valueFormat="decimal6"
                    />
                  </div>
                </div>
              )}

              {/* Event Study */}
              {eventStudyPayloads.length > 0 && (
                <div className="card space-y-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">Evolução do efeito ao longo do tempo</h3>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Os anos <strong>antes</strong> do evento devem mostrar valores próximos de zero — isso valida que o impacto realmente começou com o porto.
                      Os anos <strong>depois</strong> mostram a trajetória do efeito.
                    </p>
                  </div>
                  {eventStudyPayloads.map(({ outcome, coefficients }) => {
                    const outcomeMeta = getOutcomeMeta(outcome);
                    return (
                      <EventStudyChart
                        key={`${outcome}-es`}
                        outcome={outcome}
                        outcomeLabel={outcomeMeta.label}
                        coefficients={coefficients}
                      />
                    );
                  })}
                </div>
              )}

              {/* Comparação de métodos */}
              {analysisToDisplay.method === 'compare' && compareData.length > 0 && (
                <div className="card">
                  <h3 className="font-semibold text-gray-900 mb-1">Diferentes métodos chegam à mesma conclusão?</h3>
                  <p className="text-xs text-gray-500 mb-3">
                    Quando múltiplos métodos apontam na mesma direção, a evidência é mais robusta (semáforo 🟢).
                  </p>
                  <MethodComparisonTable items={compareData} />
                </div>
              )}

              {/* Detalhe técnico colapsável */}
              <div className="card border-gray-100">
                <button
                  type="button"
                  onClick={() => setShowTechDetail((v) => !v)}
                  className="w-full flex items-center justify-between text-sm text-gray-500 hover:text-gray-700"
                >
                  <span>Ver detalhes técnicos (coeficientes, erros padrão, IC 95%)</span>
                  {showTechDetail ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>

                {showTechDetail && (
                  <div className="mt-4 space-y-4">
                    <AnalysisResultCard detail={analysisToDisplay} />

                    {causalSummaryRows.length > 0 && analysisToDisplay.method !== 'compare' && (
                      <div className="overflow-auto">
                        <p className="text-xs font-medium text-gray-600 mb-2">Tabela de coeficientes</p>
                        <table className="w-full text-xs">
                          <thead className="text-gray-500 border-b">
                            <tr>
                              <th className="py-1.5 pr-3 text-left">Indicador</th>
                              <th className="py-1.5 pr-3 text-left">Efeito (%)</th>
                              <th className="py-1.5 pr-3 text-left">Coef. bruto</th>
                              <th className="py-1.5 pr-3 text-left">Erro padrão</th>
                              <th className="py-1.5 pr-3 text-left">P-valor</th>
                              <th className="py-1.5 pr-3 text-left">IC 95%</th>
                              <th className="py-1.5 pr-3 text-left">N obs.</th>
                            </tr>
                          </thead>
                          <tbody>
                            {causalSummaryRows.map((row) => (
                              <tr key={`tech-${row.outcome}`} className="border-b border-gray-50">
                                <td className="py-1.5 pr-3 font-medium">{getOutcomeMeta(row.outcome).label}</td>
                                <td className="py-1.5 pr-3 font-mono">{formatCausalEffectValue(row.coef, getOutcomeMeta(row.outcome)).short}</td>
                                <td className="py-1.5 pr-3 font-mono">{formatDecimal(row.coef, 6)}</td>
                                <td className="py-1.5 pr-3 font-mono">{row.se === null ? '—' : formatDecimal(row.se, 6)}</td>
                                <td className="py-1.5 pr-3 font-mono">{row.pvalue === null ? '—' : formatDecimal(row.pvalue, 4)}</td>
                                <td className="py-1.5 pr-3 font-mono text-gray-400">
                                  [{row.ciLower === null ? '—' : formatDecimal(row.ciLower, 4)}, {row.ciUpper === null ? '—' : formatDecimal(row.ciUpper, 4)}]
                                </td>
                                <td className="py-1.5 pr-3">{row.nObs ?? '—'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={handleDownloadCsv}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 text-xs text-gray-700 hover:bg-gray-50"
                      >
                        <Download className="h-3.5 w-3.5" />
                        Exportar dados (CSV)
                      </button>
                      <button
                        onClick={handleDownloadDocx}
                        disabled={isDownloadingDocx || analysisToDisplay?.status !== 'success'}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 text-xs text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Download className="h-3.5 w-3.5" />
                        {isDownloadingDocx ? 'Gerando...' : 'Relatório completo (DOCX)'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ══ BLOCO C — Contexto Descritivo ═══════════════════════════════════ */}
      {shouldRenderIndicators && (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Perfil Econômico do Município</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Indicadores descritivos para contextualizar o resultado da análise — não mostram causalidade por si só.
            </p>
          </div>

          {indicatorsLoading && <LoadingSpinner />}
          {indicatorsError && <ErrorAlert message={indicatorsError} />}

          {(['economia', 'porto', 'comercio', 'tendencias'] as IndicatorGroup[]).map((group) => {
            const groupInds = INDICATORS_INFO.filter((i) => i.group === group);
            const isOpen = indicatorGroupOpen[group];
            return (
              <div key={group} className="card">
                <button
                  type="button"
                  onClick={() => toggleGroup(group)}
                  className="w-full flex items-center justify-between"
                >
                  <h3 className="font-semibold text-gray-900">{GROUP_LABELS[group]}</h3>
                  {isOpen ? <ChevronUp className="h-4 w-4 text-gray-400" /> : <ChevronDown className="h-4 w-4 text-gray-400" />}
                </button>

                {isOpen && (
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-5">
                    {groupInds.map((ind) => {
                      const indData = indicators[ind.code];
                      const status = implementationStatus[ind.code] || 'implemented';
                      const isTechnicalDebt = status === 'technical_debt';
                      const hasData = indData?.data && indData.data.length > 0;
                      const warnings = indData?.warnings || [];
                      const indicatorRows = sortedNumericRows(toIndicatorRows(indData), ind.valueField);
                      const hasNumericRows = indicatorRows.length > 0;

                      return (
                        <ChartCard
                          key={ind.code}
                          title={ind.name}
                          description={ind.desc}
                          unit={ind.unit}
                          isLoading={indicatorsLoading}
                        >
                          {/* Dica interpretativa inline */}
                          <p className="text-xs text-gray-500 italic mb-2">{ind.interpretation}</p>

                          {isTechnicalDebt ? (
                            <div className="h-52 flex items-center justify-center text-amber-600 text-sm">
                              Dados em preparação
                            </div>
                          ) : hasNumericRows ? (
                            <BarChart
                              labels={indicatorRows.map((entry) => getLabelFromData(entry.row, municipioLabels))}
                              datasets={[{
                                label: ind.unit,
                                data: indicatorRows.map((entry) => entry.value),
                              }]}
                              yAxisLabel={ind.unit}
                              horizontal
                              valueFormat={getIndicatorFormat(ind.code)}
                            />
                          ) : hasData ? (
                            <div className="h-52 flex items-center justify-center text-gray-400 text-sm">
                              Sem dados numéricos para o filtro atual
                            </div>
                          ) : (
                            <div className="h-52 flex items-center justify-center text-gray-300 text-sm">
                              Dados não disponíveis
                            </div>
                          )}
                          {warnings.length > 0 && renderWarnings(warnings, municipioLabels)}
                        </ChartCard>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
