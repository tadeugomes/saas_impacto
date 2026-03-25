import { useCallback, useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { useI18n } from '../../../i18n/I18nContext';
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
  SimulationShockMode,
  ImpactSimulationRequest,
  ImpactSimulationResponse,
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

const IMPACT_SIMULATION_REFERENCE_DEFAULT = 'toneladas_antaq_log';


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

function parseImpactValue(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return '—';
  }
  const rounded = formatDecimal(value, 4);
  if (rounded === '—') {
    return '—';
  }
  const fixedSign = value > 0 ? `+${rounded}` : rounded;
  return `${fixedSign}%`;
}

function formatImpactRange(
  low: number | null | undefined,
  high: number | null | undefined,
): string {
  if (
    low === null
    || low === undefined
    || high === null
    || high === undefined
    || !Number.isFinite(low)
    || !Number.isFinite(high)
  ) {
    return '—';
  }
  return `${parseImpactValue(low)} a ${parseImpactValue(high)}`;
}

function formatSimulationDate(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  });
}

function buildSimulationConfidenceTag(confidence: ImpactSimulationResponse['projected_outcomes'][number]['confidence']): string {
  if (confidence === 'forte') {
    return '🟢 Forte';
  }
  if (confidence === 'moderada') {
    return '🟡 Moderada';
  }
  return '🔴 Fraca';
}

function resolveSimulationOutcomes(detail: AnalysisDetail | null): string[] {
  if (!detail?.result_full) {
    return [];
  }
  if (detail.request_params && Array.isArray(detail.request_params.outcomes)) {
    return (detail.request_params.outcomes as unknown[]).filter(
      (outcome): outcome is string => typeof outcome === 'string' && outcome.trim().length > 0,
    );
  }
  return Object.keys(detail.result_full as Record<string, unknown>);
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
  const { t } = useI18n();
  const { selectedYear, selectedInstallation } = useFilterStore();

  const [indicators, setIndicators] = useState<ModuleIndicatorStore>({});
  const [indicatorsLoading, setIndicatorsLoading] = useState(true);
  const [indicatorsError, setIndicatorsError] = useState<string | null>(null);
  const [implementationStatus, setImplementationStatus] = useState<Record<string, ImplementationStatus>>({});

  const [analysisMethod, setAnalysisMethod] = useState<AnalysisMethod>('did');
  const [analysisTreated, setAnalysisTreated] = useState('2111300');
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
  const [isDownloadingReport, setIsDownloadingReport] = useState(false);
  const [reportFormat, setReportFormat] = useState<'docx' | 'pdf' | 'xlsx'>('docx');
  const [isMatchingControls, setIsMatchingControls] = useState(false);
  const [simulationShockMode, setSimulationShockMode] = useState<SimulationShockMode>('movement');
  const [simulationShockPct, setSimulationShockPct] = useState(10);
  const [simulationInvestmentElasticity, setSimulationInvestmentElasticity] =
    useState<number>(0.8);
  const [simulationLoading, setSimulationLoading] = useState(false);
  const [simulationResult, setSimulationResult] =
    useState<ImpactSimulationResponse | null>(null);
  const [simulationError, setSimulationError] = useState<string | null>(null);

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
      // When no installation is selected but treated municipalities are set,
      // use the first treated municipality to filter BLOCO C indicators
      const treatedMunicipios = toSafeArray(analysisTreated);
      const filterParams: Record<string, unknown> = { ano: selectedYear };
      if (selectedInstallation) {
        filterParams.id_instalacao = selectedInstallation;
      } else if (treatedMunicipios.length > 0) {
        filterParams.id_municipio = treatedMunicipios[0];
      }
      const promises = activeIndicators.map((ind) =>
        indicatorsService.queryIndicator({
          codigo_indicador: ind.code,
          params: filterParams,
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
  }, [implementationStatus, selectedYear, selectedInstallation, analysisTreated]);

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

  // Only set analysisEndYear from selectedYear on initial mount,
  // not on every filter change (which would overwrite user input)
  useEffect(() => {
    setAnalysisEndYear((prev) => prev === 0 ? selectedYear : prev);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (activeAnalysis && activeAnalysis.status === 'success') {
      loadRecentAnalyses();
    }
  }, [activeAnalysis, loadRecentAnalyses]);

  useEffect(() => {
    setSimulationResult(null);
    setSimulationError(null);
  }, [analysisToDisplay?.id]);

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
      setSimulationResult(null);
      setSimulationError(null);
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

  const handleRunSimulation = async () => {
    if (!analysisToDisplay) {
      setSimulationError('Nenhuma análise carregada para simular.');
      return;
    }
    if (analysisToDisplay.status !== 'success') {
      setSimulationError('A análise precisa estar concluída para executar a simulação.');
      return;
    }

    const shockInput = Number(simulationShockPct);
    if (!Number.isFinite(shockInput)) {
      setSimulationError('Informe uma intensidade de choque válida.');
      return;
    }

    if (
      simulationShockMode === 'investment'
      && (!Number.isFinite(simulationInvestmentElasticity) || simulationInvestmentElasticity <= 0)
    ) {
      setSimulationError('Informe uma elasticidade maior que zero no modo investimento.');
      return;
    }

    const request: ImpactSimulationRequest = {
      shock_mode: simulationShockMode,
      shock_intensity_pct: shockInput,
      investment_to_movement_elasticity:
        simulationShockMode === 'investment' ? simulationInvestmentElasticity : undefined,
      reference_outcome: IMPACT_SIMULATION_REFERENCE_DEFAULT,
      target_outcomes: simulationTargetOutcomes,
    };
    if (!request.target_outcomes || request.target_outcomes.length === 0) {
      setSimulationError('Não há outcome disponível para simulação nesta análise.');
      setSimulationLoading(false);
      return;
    }

    setSimulationLoading(true);
    setSimulationError(null);
    try {
      const response = await impactoEconomicoService.simulateImpact(
        analysisToDisplay.id,
        request,
      );
      setSimulationResult(response);
    } catch (err: unknown) {
      const errorResponse = err as ApiErrorLike;
      const errorMessage = errorResponse?.response?.data?.detail || 'Erro ao calcular simulação.';
      setSimulationError(typeof errorMessage === 'string' ? errorMessage : 'Erro ao calcular simulação.');
      setSimulationResult(null);
    } finally {
      setSimulationLoading(false);
    }
  };

  // analysisMainRows: substituído por causalSummaryRows no painel técnico (Bloco B)

  const simulationTargetOutcomes = useMemo(
    () => resolveSimulationOutcomes(analysisToDisplay),
    [analysisToDisplay],
  );

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

  // SCM/ASCM: extract synthetic control data (weights, donors, fit metrics, time series)
  const scmData = useMemo(() => {
    if (!analysisToDisplay?.result_full) return [];
    const method = analysisToDisplay.method;
    if (method !== 'scm' && method !== 'augmented_scm') return [];
    const result = analysisToDisplay.result_full as Record<string, unknown>;
    return Object.entries(result).map(([outcome, payloadAny]) => {
      const payload = payloadAny as Record<string, unknown> | null;
      if (!payload || typeof payload !== 'object') return null;
      const main = payload.main_result as Record<string, unknown> | null;
      const placebo = payload.placebo_test as Record<string, unknown> | null;
      const eventStudy = Array.isArray(payload.event_study) ? payload.event_study as Array<Record<string, unknown>> : [];
      return {
        outcome,
        postAtt: main?.post_att as number | null ?? null,
        preRmspe: main?.pre_rmspe as number | null ?? null,
        postRmspe: main?.post_rmspe as number | null ?? null,
        ratioPostPre: main?.ratio_post_pre as number | null ?? null,
        weights: Array.isArray(main?.w_optimal) ? main.w_optimal as number[] : [],
        donorUnits: Array.isArray(main?.donor_units) ? main.donor_units as string[] : [],
        ridgeLambda: main?.ridge_lambda as number | null ?? null,
        placeboP: placebo?.p_value as number | null ?? null,
        timeSeries: eventStudy.map((pt) => ({
          year: pt.year as number,
          treated: pt.treated as number,
          synthetic: pt.synthetic as number,
          effect: pt.effect as number | null ?? null,
        })),
      };
    }).filter(Boolean) as Array<{
      outcome: string; postAtt: number | null; preRmspe: number | null;
      postRmspe: number | null; ratioPostPre: number | null;
      weights: number[]; donorUnits: string[]; ridgeLambda: number | null;
      placeboP: number | null;
      timeSeries: Array<{ year: number; treated: number; synthetic: number; effect: number | null }>;
    }>;
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

  const handleDownloadReport = async (format: 'docx' | 'pdf' | 'xlsx' = reportFormat) => {
    if (!analysisToDisplay) {
      return;
    }

    setAnalysisError(null);
    setIsDownloadingReport(true);

    const mimeTypes: Record<string, string> = {
      docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      pdf: 'application/pdf',
      xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    };

    try {
      const { blob, filename } = await impactoEconomicoService.getAnalysisReport(analysisToDisplay.id, format);
      const url = window.URL.createObjectURL(
        new Blob([blob], { type: mimeTypes[format] || 'application/octet-stream' }),
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
      const errorMessage = errorResponse?.response?.data?.detail || `Erro ao exportar relatório ${format.toUpperCase()}.`;
      setAnalysisError(typeof errorMessage === 'string' ? errorMessage : `Erro ao exportar relatório ${format.toUpperCase()}.`);
    } finally {
      setIsDownloadingReport(false);
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
        <ExportButton
          moduleCode="5"
          analysisId={analysisToDisplay?.id}
          compareAnalysisIds={
            recentAnalyses
              .filter((a) => a.status === 'success' && a.id !== analysisToDisplay?.id)
              .slice(0, 5)
              .map((a) => a.id)
          }
        />
      </div>

      <FilterBar />

      {/* ══ Visão Executiva — Impacto Econômico ════════════════════════════ */}
      {!indicatorsLoading && Object.keys(indicators).length > 0 && (
        <div className="mb-2 rounded-xl border border-blue-200 bg-blue-50 p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Visão Executiva — Impacto Econômico Portuário</h2>
          <p className="text-sm text-gray-500 mb-4">
            Leitura orientada a investidores e tomadores de decisão · Dados {selectedYear}
            {!selectedInstallation && ' · Visão Nacional (selecione um porto para detalhar)'}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* PIB Municipal */}
            {(() => {
              const data = toIndicatorRows(indicators['IND-5.01'] || createEmptyIndicatorResponse('IND-5.01'));
              if (data.length === 0) return null;
              const isNacional = !selectedInstallation && data.length > 1;
              const totalPib = data.reduce((sum, d) => sum + (parseToNumber(d.pib_municipal) || 0), 0);
              const topRow = data.slice().sort((a, b) => (parseToNumber(b.pib_municipal) || 0) - (parseToNumber(a.pib_municipal) || 0))[0];
              const pibValue = isNacional ? totalPib : (parseToNumber(data[0]?.pib_municipal) || 0);
              const pibLabel = pibValue >= 1e9
                ? `R$ ${formatDecimal(pibValue / 1e9, 1)} bi`
                : pibValue >= 1e6
                ? `R$ ${formatDecimal(pibValue / 1e6, 0)} mi`
                : `R$ ${formatDecimal(pibValue, 0)}`;
              return (
                <div className="bg-white rounded-lg border border-blue-100 p-4">
                  <h3 className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Economia Local</h3>
                  <p className="text-2xl font-bold text-gray-900">{pibLabel}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {isNacional ? `PIB agregado (${data.length} municípios)` : 'PIB Municipal'}
                  </p>
                  {isNacional && topRow && (
                    <p className="text-sm text-gray-500 mt-2">
                      Maior economia: {getLabelFromData(topRow as RawIndicatorRow, municipioLabels)}
                    </p>
                  )}
                </div>
              );
            })()}

            {/* Intensidade Portuária */}
            {(() => {
              const data = toIndicatorRows(indicators['IND-5.08'] || createEmptyIndicatorResponse('IND-5.08'));
              if (data.length === 0) return null;
              const isNacional = !selectedInstallation && data.length > 1;
              const concEmprego = isNacional
                ? data.reduce((sum, d) => sum + (parseToNumber(d.concentracao_emprego_pct) || 0), 0) / data.length
                : (parseToNumber(data[0]?.concentracao_emprego_pct) || 0);
              return (
                <div className="bg-white rounded-lg border border-blue-100 p-4">
                  <h3 className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Dependência Portuária</h3>
                  <p className="text-2xl font-bold text-gray-900">{formatDecimal(concEmprego, 1)}%</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {isNacional ? 'empregos portuários no total (média nacional)' : 'empregos portuários no total local'}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    {concEmprego > 10
                      ? 'Alta dependência — variações no fluxo portuário impactam diretamente o mercado de trabalho local.'
                      : concEmprego > 3
                      ? 'Dependência moderada — o porto é empregador relevante mas a economia é diversificada.'
                      : 'Baixa dependência direta — impacto portuário se dá mais por cadeia produtiva do que por emprego direto.'}
                  </p>
                </div>
              );
            })()}

            {/* Crescimento PIB */}
            {(() => {
              const data = toIndicatorRows(indicators['IND-5.10'] || createEmptyIndicatorResponse('IND-5.10'));
              if (data.length === 0) return null;
              const isNacional = !selectedInstallation && data.length > 1;
              const crescPib = isNacional
                ? data.reduce((sum, d) => sum + (parseToNumber(d.crescimento_pib_percentual) || 0), 0) / data.length
                : (parseToNumber(data[0]?.crescimento_pib_percentual) || 0);
              return (
                <div className="bg-white rounded-lg border border-blue-100 p-4">
                  <h3 className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Dinamismo Econômico</h3>
                  <p className={`text-2xl font-bold ${crescPib >= 0 ? 'text-green-700' : 'text-red-600'}`}>
                    {crescPib >= 0 ? '+' : ''}{formatDecimal(crescPib, 1)}%
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    {isNacional ? 'crescimento médio do PIB (média nacional)' : 'crescimento do PIB municipal'}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    {crescPib > 5
                      ? 'Expansão acelerada — oportunidade para capturar valor da cadeia portuária em crescimento.'
                      : crescPib > 0
                      ? 'Crescimento estável — base sólida para investimentos de longo prazo no setor portuário.'
                      : 'Retração econômica — cautela para novos investimentos; analisar causalidade com o método adequado.'}
                  </p>
                </div>
              );
            })()}

            {/* Abertura Comercial */}
            {(() => {
              const data = toIndicatorRows(indicators['IND-5.07'] || createEmptyIndicatorResponse('IND-5.07'));
              if (data.length === 0) return null;
              const isNacional = !selectedInstallation && data.length > 1;
              const intComercial = isNacional
                ? data.reduce((sum, d) => sum + (parseToNumber(d.intensidade_comercial) || 0), 0) / data.length
                : (parseToNumber(data[0]?.intensidade_comercial) || 0);
              return (
                <div className="bg-white rounded-lg border border-blue-100 p-4">
                  <h3 className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Abertura Comercial</h3>
                  <p className="text-2xl font-bold text-gray-900">{formatDecimal(intComercial, 2)}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {isNacional ? 'comércio exterior / PIB (média nacional)' : 'comércio exterior / PIB local'}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    {intComercial > 0.5
                      ? 'Economia altamente integrada ao comércio exterior — porto é peça-chave para a competitividade local.'
                      : intComercial > 0.1
                      ? 'Integração comercial moderada — potencial para expansão das exportações via infraestrutura portuária.'
                      : 'Baixa abertura comercial — o impacto portuário é mais logístico-doméstico do que voltado ao comércio exterior.'}
                  </p>
                </div>
              );
            })()}

            {/* Crescimento da Movimentação */}
            {(() => {
              const data = toIndicatorRows(indicators['IND-5.11'] || createEmptyIndicatorResponse('IND-5.11'));
              if (data.length === 0) return null;
              const isNacional = !selectedInstallation && data.length > 1;
              const crescTon = isNacional
                ? data.reduce((sum, d) => sum + (parseToNumber(d.crescimento_tonelagem_pct) || 0), 0) / data.length
                : (parseToNumber(data[0]?.crescimento_tonelagem_pct) || 0);
              return (
                <div className="bg-white rounded-lg border border-blue-100 p-4">
                  <h3 className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Movimentação Portuária</h3>
                  <p className={`text-2xl font-bold ${crescTon >= 0 ? 'text-green-700' : 'text-red-600'}`}>
                    {crescTon >= 0 ? '+' : ''}{formatDecimal(crescTon, 1)}%
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    {isNacional ? 'variação anual de carga (média nacional)' : 'variação anual de carga'}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    {crescTon > 5
                      ? 'Expansão robusta da movimentação — sinal de aquecimento que antecede impacto econômico positivo.'
                      : crescTon > 0
                      ? 'Crescimento moderado — sustentabilidade logística com tendência favorável.'
                      : 'Queda na movimentação — investigar se há perda de competitividade ou efeito conjuntural.'}
                  </p>
                </div>
              );
            })()}

            {/* Associação Carga × PIB */}
            {(() => {
              const data = toIndicatorRows(indicators['IND-5.14'] || createEmptyIndicatorResponse('IND-5.14'));
              if (data.length === 0) return null;
              const isNacional = !selectedInstallation && data.length > 1;
              const corr = isNacional
                ? data.reduce((sum, d) => sum + (parseToNumber(d.correlacao_tonelagem_pib) || 0), 0) / data.length
                : (parseToNumber(data[0]?.correlacao_tonelagem_pib) || 0);
              return (
                <div className="bg-white rounded-lg border border-blue-100 p-4">
                  <h3 className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Associação Porto-PIB</h3>
                  <p className="text-2xl font-bold text-gray-900">{formatDecimal(corr, 2)}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {isNacional ? 'correlação carga × PIB (média nacional)' : 'correlação carga × PIB'}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    {Math.abs(corr) > 0.7
                      ? 'Forte associação entre movimentação portuária e crescimento econômico — use a análise causal abaixo para verificar causalidade.'
                      : Math.abs(corr) > 0.3
                      ? 'Associação moderada — o porto influencia a economia local, mas outros fatores também são relevantes.'
                      : 'Associação fraca — o impacto do porto pode ser indireto ou concentrado em setores específicos.'}
                  </p>
                </div>
              );
            })()}
          </div>
        </div>
      )}

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
                  {isMatchingControls ? t('module5.matching.searching') : t('module5.matching.suggest')}
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

              {/* Simulador de impacto (cenário) */}
              <div className="card">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">Simulador de Impacto</h3>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Projete cenário gerencial usando os coeficientes causais da análise ativa.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleRunSimulation}
                    disabled={simulationLoading || !analysisToDisplay || analysisToDisplay.method === 'compare'}
                    className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {simulationLoading ? 'Calculando...' : 'Calcular cenário'}
                  </button>
                </div>

                <div className="mt-3 space-y-2">
                  <p className="text-xs font-medium text-gray-700">Fonte do cenário:</p>
                  <div className="flex flex-wrap gap-3">
                    <label className="inline-flex items-center gap-2 text-xs text-gray-600">
                      <input
                        type="radio"
                        name="simulationShockMode"
                        value="movement"
                        checked={simulationShockMode === 'movement'}
                        onChange={() => setSimulationShockMode('movement')}
                        className="h-3.5 w-3.5 accent-indigo-600"
                      />
                      Choque de movimentação (%)
                    </label>
                    <label className="inline-flex items-center gap-2 text-xs text-gray-600">
                      <input
                        type="radio"
                        name="simulationShockMode"
                        value="investment"
                        checked={simulationShockMode === 'investment'}
                        onChange={() => setSimulationShockMode('investment')}
                        className="h-3.5 w-3.5 accent-indigo-600"
                      />
                      Choque de investimento (%)
                    </label>
                  </div>
                </div>

                <div className="mt-2 flex flex-wrap items-end gap-3">
                  <label className="text-xs text-gray-600">
                    {simulationShockMode === 'investment'
                      ? 'Variação de investimento (%)'
                      : 'Variação de movimentação (%)'}
                  </label>
                  <input
                    type="number"
                    min={-100}
                    max={500}
                    step={1}
                    value={simulationShockPct}
                    onChange={(e) => setSimulationShockPct(parseNumeric(e.target.value) || 0)}
                    className="w-28 border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
                  />
                  <span className="text-xs text-gray-500">Comparado ao cenário base</span>
                </div>

                {simulationShockMode === 'investment' && (
                  <div className="mt-3 flex flex-wrap items-end gap-3">
                    <label className="text-xs text-gray-600">
                      Elasticidade (Δmovimentação / Δinvestimento):
                    </label>
                    <input
                      type="number"
                      min={0.01}
                      step={0.01}
                      value={simulationInvestmentElasticity}
                      onChange={(e) => setSimulationInvestmentElasticity(parseNumeric(e.target.value) || 0)}
                      className="w-28 border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
                    />
                    <span className="text-xs text-gray-500">
                      Ex.: 0,8 = 10% investimento gera ~8% movimentação
                    </span>
                  </div>
                )}

                <p className="text-xs text-gray-500 mt-2">
                  Referência fixa: <strong>{IMPACT_SIMULATION_REFERENCE_DEFAULT}</strong> (movimentação)
                </p>

                {simulationError && <ErrorAlert message={simulationError} />}

                    {simulationResult ? (
                      <>
                        <div className="mt-3 rounded-md border border-emerald-100 bg-emerald-50 p-3 text-xs text-emerald-700">
                          {simulationResult.assumptions.map((item) => (
                            <p key={item} className="leading-6">
                          • {item}
                        </p>
                      ))}
                        </div>

                        <div className="mt-3 space-y-1.5 rounded-md border border-gray-100 bg-gray-50 p-3 text-xs text-gray-600">
                          <p className="font-medium text-gray-800">Parâmetros técnicos</p>
                          <p>
                            Modelo: {simulationResult.simulation_metadata.model_version}
                            {' '}| gerado em {formatSimulationDate(simulationResult.simulation_metadata.as_of)}
                            {' '}| origem: {simulationResult.simulation_metadata.generated_by}
                          </p>
                          <p>
                            Impacto referência para cenário de 100%: {parseImpactValue(simulationResult.reference_effect_100pct)} em {IMPACT_SIMULATION_REFERENCE_DEFAULT}
                          </p>
                          {simulationResult.simulation_metadata.notes.length > 0 && (
                            <ul className="list-disc pl-4 space-y-1 mt-2">
                              {simulationResult.simulation_metadata.notes.map((note) => (
                                <li key={note}>{note}</li>
                              ))}
                            </ul>
                          )}
                        </div>

                        {simulationResult.projected_outcomes.length > 0 && (
                          <div className="mt-4 grid gap-3 md:grid-cols-2">
                            {simulationResult.projected_outcomes.map((projection) => {
                              const deltaText = parseImpactValue(projection.projected_delta_pct);
                              const effect100Text = parseImpactValue(projection.treatment_effect_100pct);
                              const effect100CiText = projection.treatment_effect_100pct_ci_lower !== null
                                && projection.treatment_effect_100pct_ci_upper !== null
                                ? `${parseImpactValue(projection.treatment_effect_100pct_ci_lower)} a ${parseImpactValue(projection.treatment_effect_100pct_ci_upper)}`
                                : '—';
                              const conservativeText = formatImpactRange(
                                projection.projected_delta_pct_conservative,
                                projection.projected_delta_pct_optimistic,
                              );
                              return (
                                <div
                                  key={projection.outcome}
                                  className="rounded-lg border border-gray-200 p-3 space-y-2"
                                >
                              <div className="flex items-center justify-between gap-2">
                                <p className="text-sm font-medium text-gray-800">{projection.outcome_label}</p>
                                <span className="text-[11px] px-2 py-1 rounded-full bg-gray-100 text-gray-600 border border-gray-200">
                                  {buildSimulationConfidenceTag(projection.confidence)}
                                </span>
                              </div>
                              <p className="text-2xl font-bold text-gray-900">
                                {deltaText}
                              </p>
                              <p className="text-xs text-gray-500">
                                Projeção para choque de {simulationResult.applied_shock_intensity_pct.toFixed(1)}%
                              </p>
                              <p className="text-xs text-gray-500">
                                Efeito 100%: {effect100Text}.
                                Método: {projection.method_used}
                              </p>
                              <p className="text-xs text-gray-500">
                                IC 95% do efeito 100%: {effect100CiText}
                              </p>
                              <p className="text-xs text-gray-500">
                                Faixa conservador/otimista:
                                {' '}
                                {conservativeText}
                              </p>
                              {projection.warning && (
                                <p className="text-xs text-amber-700">{projection.warning}</p>
                              )}
                              <p className="text-xs text-gray-400">
                                Resultado em português: {simulationResult.applied_shock_intensity_pct.toFixed(1)}% de choque de movimentação equivalente pode alterar {projection.outcome_label}
                                {' '}em {deltaText}.
                              </p>
                              {projection.notes.length > 0 && (
                                <ul className="list-disc pl-4 text-xs text-gray-500 space-y-1">
                                  {projection.notes.map((note) => (
                                    <li key={`${projection.outcome}-${note}`}>{note}</li>
                                  ))}
                                </ul>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {simulationResult.executive_summary.length > 0 && (
                      <div className="mt-4 space-y-1.5">
                        <p className="text-sm font-medium text-gray-800">Resumo executivo</p>
                        <ul className="list-disc pl-5 text-xs text-gray-600 space-y-1">
                          {simulationResult.executive_summary.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </>
                ) : (
                  !simulationLoading && (
                    <p className="text-xs text-gray-400 mt-3">
                      Execute o cálculo para visualizar a simulação de impacto com base na análise ativa.
                    </p>
                  )
                )}
              </div>

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

              {/* SCM / ASCM — controle sintético */}
              {scmData.length > 0 && (
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {analysisToDisplay.method === 'augmented_scm' ? 'Controle Sintético Aumentado (ASCM)' : 'Controle Sintético (SCM)'}
                    </h3>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Constroi um contrafactual ponderando municípios doadores para replicar a trajetória pré-tratamento do município tratado.
                    </p>
                  </div>

                  {scmData.map((scm) => {
                    const outcomeMeta = getOutcomeMeta(scm.outcome);
                    const fitOk = scm.preRmspe !== null && scm.preRmspe < 0.1;
                    const placeboOk = scm.placeboP !== null && scm.placeboP < 0.1;

                    return (
                      <div key={`scm-${scm.outcome}`} className="card space-y-4">
                        <h4 className="text-sm font-semibold text-gray-800">{outcomeMeta.label}</h4>

                        {/* Métricas principais */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          <div className="text-center p-3 bg-gray-50 rounded-lg">
                            <p className="text-xs text-gray-500">Efeito (ATT)</p>
                            <p className={`text-lg font-bold ${scm.postAtt !== null && scm.postAtt > 0 ? 'text-emerald-700' : 'text-red-600'}`}>
                              {scm.postAtt !== null ? `${scm.postAtt > 0 ? '+' : ''}${formatDecimal(scm.postAtt, 3)}` : '--'}
                            </p>
                          </div>
                          <div className="text-center p-3 bg-gray-50 rounded-lg">
                            <p className="text-xs text-gray-500">Ajuste pré (RMSPE)</p>
                            <p className={`text-lg font-bold ${fitOk ? 'text-green-600' : 'text-amber-600'}`}>
                              {scm.preRmspe !== null ? formatDecimal(scm.preRmspe, 4) : '--'}
                            </p>
                          </div>
                          <div className="text-center p-3 bg-gray-50 rounded-lg">
                            <p className="text-xs text-gray-500">Ratio pós/pré</p>
                            <p className="text-lg font-bold text-gray-900">
                              {scm.ratioPostPre !== null ? `${formatDecimal(scm.ratioPostPre, 1)}x` : '--'}
                            </p>
                          </div>
                          <div className="text-center p-3 bg-gray-50 rounded-lg">
                            <p className="text-xs text-gray-500">Placebo p-valor</p>
                            <p className={`text-lg font-bold ${placeboOk ? 'text-green-600' : scm.placeboP !== null ? 'text-red-500' : 'text-gray-400'}`}>
                              {scm.placeboP !== null ? formatDecimal(scm.placeboP, 3) : '--'}
                            </p>
                          </div>
                        </div>

                        {/* Pesos dos doadores */}
                        {scm.donorUnits.length > 0 && scm.weights.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-gray-600 mb-2">Composição do controle sintético</p>
                            <div className="flex flex-wrap gap-2">
                              {scm.donorUnits.map((donorId, idx) => {
                                const w = scm.weights[idx] ?? 0;
                                const label = resolveMunicipioLabel(donorId, municipioLabels);
                                return (
                                  <span key={donorId} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-gray-200 bg-white text-xs">
                                    <span className="font-medium text-gray-800">{label}</span>
                                    <span className="text-gray-400">|</span>
                                    <span className="font-semibold text-blue-600">{formatDecimal(w * 100, 1)}%</span>
                                  </span>
                                );
                              })}
                            </div>
                          </div>
                        )}

                        {/* Série temporal: tratado vs sintético */}
                        {scm.timeSeries.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-gray-600 mb-2">Tratado vs. Controle Sintético</p>
                            <div className="h-52">
                              <BarChart
                                labels={scm.timeSeries.map((pt) => String(pt.year))}
                                datasets={[
                                  { label: 'Tratado', data: scm.timeSeries.map((pt) => pt.treated), backgroundColor: '#3b82f6' },
                                  { label: 'Sintético', data: scm.timeSeries.map((pt) => pt.synthetic), backgroundColor: '#d1d5db' },
                                ]}
                                yAxisLabel={outcomeMeta.label}
                              />
                            </div>
                          </div>
                        )}

                        {scm.ridgeLambda !== null && (
                          <p className="text-xs text-gray-400">Ridge λ = {formatDecimal(scm.ridgeLambda, 3)} (regularização ASCM)</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Diagnósticos causais — qualidade da estimativa */}
              {analysisToDisplay.method !== 'compare' && analysisToDisplay.result_full && (() => {
                const result = analysisToDisplay.result_full as Record<string, unknown>;
                const diagnostics: Array<{ outcome: string; label: string; items: Array<{ name: string; value: string; ok: boolean | null }> }> = [];
                for (const [outcome, payloadAny] of Object.entries(result)) {
                  const payload = payloadAny as Record<string, unknown> | null;
                  if (!payload || typeof payload !== 'object') continue;
                  const main = (payload.main_result ?? payload) as Record<string, unknown>;
                  const items: Array<{ name: string; value: string; ok: boolean | null }> = [];

                  // N observations
                  if (main.n_obs != null) items.push({ name: t('module5.diagnostics.observations'), value: String(main.n_obs).replace(/\B(?=(\d{3})+(?!\d))/g, '.'), ok: (main.n_obs as number) >= 30 });
                  // R²
                  if (main.r2 != null) items.push({ name: 'R²', value: formatDecimal(main.r2 as number, 3), ok: (main.r2 as number) > 0.1 });
                  // First-stage F-stat (IV)
                  if (main.f_stat != null) items.push({ name: 'F-stat (1º estágio)', value: formatDecimal(main.f_stat as number, 1), ok: (main.f_stat as number) > 10 });
                  // Parallel trends p-value
                  if (main.parallel_trends_p != null) items.push({ name: t('module5.diagnostics.parallelTrends'), value: formatDecimal(main.parallel_trends_p as number, 3), ok: (main.parallel_trends_p as number) > 0.05 });
                  // Pre-RMSPE (SCM)
                  if (main.pre_rmspe != null) items.push({ name: 'Pre-RMSPE', value: formatDecimal(main.pre_rmspe as number, 4), ok: (main.pre_rmspe as number) < 0.1 });
                  // Placebo
                  const placebo = payload.placebo_test as Record<string, unknown> | null;
                  if (placebo?.p_value != null) items.push({ name: 'Placebo (p)', value: formatDecimal(placebo.p_value as number, 3), ok: (placebo.p_value as number) < 0.1 });

                  if (items.length > 0) {
                    diagnostics.push({ outcome, label: getOutcomeMeta(outcome).label, items });
                  }
                }
                if (diagnostics.length === 0) return null;
                return (
                  <div className="card">
                    <h3 className="font-semibold text-gray-900 mb-1">{t('module5.diagnostics.title')}</h3>
                    <p className="text-xs text-gray-500 mb-3">
                      Métricas de qualidade estatística — verde indica condição satisfeita, vermelho indica cautela.
                    </p>
                    <div className="space-y-3">
                      {diagnostics.map((diag) => (
                        <div key={`diag-${diag.outcome}`}>
                          <p className="text-xs font-medium text-gray-700 mb-1.5">{diag.label}</p>
                          <div className="flex flex-wrap gap-2">
                            {diag.items.map((item) => (
                              <span key={item.name} className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs border ${
                                item.ok === true ? 'bg-green-50 border-green-200 text-green-700'
                                  : item.ok === false ? 'bg-red-50 border-red-200 text-red-600'
                                  : 'bg-gray-50 border-gray-200 text-gray-600'
                              }`}>
                                {item.ok === true ? '✓' : item.ok === false ? '✗' : '–'} {item.name}: {item.value}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })()}

              {/* Comparação de métodos — visão executiva para investidores */}
              {analysisToDisplay.method === 'compare' && compareData.length > 0 && (
                <div className="space-y-4">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Validação Cruzada de Resultados
                  </h2>
                  <p className="text-sm text-gray-600 -mt-2">
                    Para cada indicador, dois métodos independentes (DiD e IV) foram executados. Quando ambos
                    apontam na mesma direção e magnitude, a evidência é considerada robusta para decisão.
                  </p>

                  {/* Cards executivos por outcome */}
                  <div className="grid gap-4 md:grid-cols-2">
                    {compareData.map((item) => {
                      const rows = item.comparison_table || [];
                      const allSignificant = rows.length > 0 && rows.every((r) => r.Significant === 'Yes');
                      const someSignificant = rows.some((r) => r.Significant === 'Yes');
                      const estimates = rows.map((r) => r.Estimate).filter((e): e is number => e !== null);
                      const sameDirection = estimates.length >= 2 && estimates.every((e) => e > 0) || estimates.every((e) => e < 0);
                      const consistent = sameDirection && someSignificant;
                      const robust = consistent && allSignificant;

                      const level = robust ? 'strong' : consistent ? 'moderate' : 'weak';
                      const conf = CONFIDENCE_CONFIG[level];
                      const outcomeMeta = getOutcomeMeta(item.outcome);
                      const avgEstimate = estimates.length > 0 ? estimates.reduce((a, b) => a + b, 0) / estimates.length : null;
                      const effectStr = avgEstimate !== null
                        ? formatCausalEffectValue(avgEstimate, outcomeMeta).short
                        : '--';
                      const isPositive = avgEstimate !== null && avgEstimate > 0;
                      const isNegative = avgEstimate !== null && avgEstimate < 0;

                      const consistencyText = item.consistency_assessment
                        ? String(item.consistency_assessment)
                        : robust
                          ? 'Ambos os metodos concordam na direcao e significancia.'
                          : consistent
                            ? 'Metodos apontam na mesma direcao, mas nem todos sao significativos.'
                            : 'Metodos divergem — resultado requer cautela.';

                      return (
                        <div
                          key={`compare-card-${item.outcome}`}
                          className={`rounded-xl border-2 p-5 space-y-3 ${conf.border} ${conf.bg}`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                                Impacto em
                              </p>
                              <p className="text-base font-semibold text-gray-900 mt-0.5">
                                {outcomeMeta.label}
                              </p>
                            </div>
                            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${conf.border} ${conf.bg} ${conf.color}`}>
                              {level === 'strong' ? '🟢' : level === 'moderate' ? '🟡' : '🔴'} {conf.label}
                            </span>
                          </div>

                          <div className="flex items-end gap-2">
                            <span className={`text-3xl font-bold tabular-nums ${
                              isPositive ? 'text-emerald-700' : isNegative ? 'text-red-600' : 'text-gray-700'
                            }`}>
                              {isPositive ? '+' : ''}{effectStr}
                            </span>
                            <span className="text-xs text-gray-500 mb-1">media entre metodos</span>
                          </div>

                          <p className="text-sm text-gray-700">{consistencyText}</p>

                          {item.recommendation && (
                            <p className="text-xs text-gray-600 bg-white/60 rounded p-2 border border-gray-200">
                              Recomendacao: {item.recommendation}
                            </p>
                          )}

                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {rows.map((r) => (
                              <span key={r.Method} className="text-xs px-2 py-0.5 rounded-full bg-white border border-gray-200 text-gray-600">
                                {r.Method}: {r.Significant === 'Yes' ? 'significativo' : 'nao significativo'}
                              </span>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Tabela técnica detalhada */}
                  <div className="card">
                    <h3 className="font-semibold text-gray-900 mb-1">Detalhes da Comparacao</h3>
                    <p className="text-xs text-gray-500 mb-3">
                      Tabela completa com coeficientes, erros padrao e intervalos de confianca por metodo.
                    </p>
                    <MethodComparisonTable items={compareData} />
                  </div>
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

                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        onClick={handleDownloadCsv}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 text-xs text-gray-700 hover:bg-gray-50"
                      >
                        <Download className="h-3.5 w-3.5" />
                        Exportar dados (CSV)
                      </button>
                      <select
                        value={reportFormat}
                        onChange={(e) => setReportFormat(e.target.value as 'docx' | 'pdf' | 'xlsx')}
                        className="h-8 rounded-lg border border-gray-300 text-xs text-gray-700 pl-2 pr-6 bg-white"
                      >
                        <option value="docx">DOCX</option>
                        <option value="pdf">PDF</option>
                        <option value="xlsx">XLSX</option>
                      </select>
                      <button
                        onClick={() => { void handleDownloadReport(); }}
                        disabled={isDownloadingReport || analysisToDisplay?.status !== 'success'}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 text-xs text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Download className="h-3.5 w-3.5" />
                        {isDownloadingReport ? t('module5.report.generating') : `${t('module5.report.button')} (${reportFormat.toUpperCase()})`}
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
            <h2 className="text-lg font-semibold text-gray-900">
              {selectedInstallation
                ? 'Perfil Econômico do Município'
                : selectedTreatedMunicipios.length > 0
                  ? `Perfil Econômico — ${resolveMunicipioLabel(selectedTreatedMunicipios[0], municipioLabels)}`
                  : 'Perfil Econômico — Visão Nacional'}
            </h2>
            <p className="text-sm text-gray-500 mt-0.5">
              {selectedInstallation
                ? 'Indicadores descritivos para contextualizar o resultado da análise — não mostram causalidade por si só.'
                : selectedTreatedMunicipios.length > 0
                  ? 'Indicadores filtrados pelo município tratado da análise causal — contexto econômico local.'
                  : 'Dados agregados de todos os municípios. Selecione um porto nos filtros para ver o perfil de um município específico.'}
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
