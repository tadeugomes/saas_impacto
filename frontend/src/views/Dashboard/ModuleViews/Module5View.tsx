import { useCallback, useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { Download, Play, RefreshCw, Sparkles } from 'lucide-react';

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
import { impactoEconomicoService } from '../../../api/impactoEconomico';
import { indicatorsService } from '../../../api/indicators';
import type {
  AnalysisCreateRequest,
  AnalysisDetail,
  AnalysisMethod,
  AnalysisScope,
  AnalysisResponse,
  IndicatorMetadata,
  IndicatorResponse,
} from '../../../types/api';

type ImplementationStatus = 'implemented' | 'technical_debt';

type CoeffTableRow = {
  outcome: string;
  method: string;
  key: string;
  coef: number | null;
  se: number | null;
  pvalue: number | null;
  n_obs: number | null;
  r2: number | null;
};

interface CoeffPoint {
  rel_time: number;
  coef: number;
  se?: number | null;
  ci_lower?: number | null;
  ci_upper?: number | null;
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

const ANALYSIS_METHODS: { value: AnalysisMethod; label: string }[] = [
  { value: 'did', label: 'DiD (Difference-in-Differences)' },
  { value: 'iv', label: 'IV (Variáveis Instrumentais)' },
  { value: 'panel_iv', label: 'Panel IV' },
  { value: 'event_study', label: 'Event Study' },
  { value: 'compare', label: 'Comparar métodos' },
];

const INDICATORS_INFO = [
  { code: 'IND-5.01', name: 'PIB Municipal', unit: 'R$', desc: 'PIB Total do Município', valueField: 'pib_municipal' },
  { code: 'IND-5.02', name: 'PIB per Capita', unit: 'R$/hab', desc: 'PIB per capita do município', valueField: 'pib_per_capita' },
  { code: 'IND-5.03', name: 'População', unit: 'Hab', desc: 'População municipal estimada', valueField: 'populacao' },
  { code: 'IND-5.04', name: 'PIB Setorial - Serviços', unit: '%', desc: 'Participação do setor serviços no PIB', valueField: 'pib_servicos_percentual' },
  { code: 'IND-5.05', name: 'PIB Setorial - Indústria', unit: '%', desc: 'Participação do setor indústria no PIB', valueField: 'pib_industria_percentual' },
  { code: 'IND-5.06', name: 'Intensidade Portuária', unit: 'ton/R$', desc: 'Tonelagem movimentada por unidade de PIB', valueField: 'intensidade_portuaria' },
  { code: 'IND-5.07', name: 'Intensidade Comercial', unit: 'US$/R$', desc: 'Comércio exterior por unidade de PIB', valueField: 'intensidade_comercial' },
  { code: 'IND-5.08', name: 'Concentração de Emprego Portuário', unit: '%', desc: 'Participação do emprego portuário', valueField: 'concentracao_emprego_pct' },
  { code: 'IND-5.09', name: 'Concentração Salarial Portuária', unit: '%', desc: 'Participação da massa salarial portuária', valueField: 'concentracao_salarial_pct' },
  { code: 'IND-5.10', name: 'Crescimento PIB Municipal', unit: '%', desc: 'Variação percentual anual do PIB', valueField: 'crescimento_pib_percentual' },
  { code: 'IND-5.11', name: 'Crescimento de Tonelagem', unit: '%', desc: 'Variação percentual anual da tonelagem', valueField: 'crescimento_tonelagem_pct' },
  { code: 'IND-5.12', name: 'Crescimento de Empregos', unit: '%', desc: 'Variação percentual anual de empregos portuários', valueField: 'crescimento_empregos_pct' },
  { code: 'IND-5.13', name: 'Crescimento Comércio Exterior', unit: '%', desc: 'Variação percentual anual do comércio exterior', valueField: 'crescimento_comercio_pct' },
  { code: 'IND-5.14', name: 'Correlação Tonelagem × PIB', unit: 'coef.', desc: 'Correlação entre tonelagem e PIB', valueField: 'correlacao_tonelagem_pib' },
  { code: 'IND-5.15', name: 'Correlação Tonelagem × Empregos', unit: 'coef.', desc: 'Correlação entre tonelagem e empregos', valueField: 'correlacao_tonelagem_empregos' },
  { code: 'IND-5.16', name: 'Correlação Comércio × PIB', unit: 'coef.', desc: 'Correlação entre comércio exterior e PIB', valueField: 'correlacao_comercio_pib' },
  { code: 'IND-5.17', name: 'Elasticidade Tonelagem/PIB', unit: 'elastic.', desc: 'Elasticidade da tonelagem em relação ao PIB', valueField: 'elasticidade_tonelagem_pib' },
  { code: 'IND-5.18', name: 'Participação no PIB Regional', unit: '%', desc: 'Participação no PIB da microrregião', valueField: 'participacao_pib_regional_pct' },
  { code: 'IND-5.19', name: 'Crescimento Relativo ao Estado', unit: 'p.p.', desc: 'Diferença de crescimento entre município e estado', valueField: 'crescimento_relativo_uf_pp' },
  { code: 'IND-5.20', name: 'Razão Emprego Total/Portuário', unit: 'razão', desc: 'Relação entre empregos totais e portuários', valueField: 'razao_emprego_total_portuario' },
  { code: 'IND-5.21', name: 'Índice de Concentração Portuária', unit: '0-100', desc: 'Índice composto de concentração econômica', valueField: 'indice_concentracao_portuaria' },
];


function valueToString(value: unknown): string {
  return typeof value === 'undefined' ? '' : String(value);
}

function toSafeArray(raw: string | null | undefined): string[] {
  if (!raw) {
    return [];
  }
  return raw
    .split(/[\n;,]/g)
    .map((item) => item.trim())
    .filter(Boolean);
}

function toDisplayValue(item: RawIndicatorRow, valueField: string): number {
  const fieldValue = item[valueField];
  if (typeof fieldValue === 'number') {
    return fieldValue;
  }
  const fallback = item.valor ?? item.total;
  return typeof fallback === 'number' ? fallback : 0;
}

function getLabelFromData(item: RawIndicatorRow): string {
  return (
    (typeof item.nome_municipio === 'string' && item.nome_municipio) ||
    (typeof item.id_municipio === 'string' && item.id_municipio) ||
    (typeof item.id_instalacao === 'string' && item.id_instalacao) ||
    'N/A'
  );
}

function toDisplayNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
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

function parseNumeric(value: string): number | null {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function renderWarnings(warnings: unknown[]): JSX.Element | null {
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
          const ano = warningRecord.ano ? String(warningRecord.ano) : '';
          const hasSuffix = warningRecord.id_municipio || warningRecord.ano;

          return (
            <li key={`${warningTipo}-${campo}-${index}`}>
              <span className="font-semibold">{warningTipo}</span>: {mensagem}
              {municipio ? ` [município ${municipio}` : ''}
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

  const [activeAnalysisId, setActiveAnalysisId] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [creatingAnalysis, setCreatingAnalysis] = useState(false);
  const [recentAnalyses, setRecentAnalyses] = useState<AnalysisResponse[]>([]);
  const [analysesLoading, setAnalysesLoading] = useState(false);
  const [analysesError, setAnalysesError] = useState<string | null>(null);

  const {
    analysis: polledAnalysis,
    result: polledResult,
    isLoading: isPolling,
    error: pollingError,
    refresh: refreshAnalysis,
  } = useAnalysis(activeAnalysisId);

  const analysisToDisplay: AnalysisDetail | null = polledResult ?? null;
  const activeAnalysis = polledAnalysis;

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

  useEffect(() => {
    fetchMetadata();
    loadRecentAnalyses();
  }, [fetchMetadata, loadRecentAnalyses]);

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

    const outcomes = toSafeArray(analysisOutcomes).filter((v) => !!v);
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

  const analysisMainRows = useMemo<CoeffTableRow[]>(() => {
    if (!analysisToDisplay?.result_full || analysisToDisplay.status !== 'success') {
      return [];
    }
    const items = analysisToDisplay.result_full as Record<string, unknown>;
    const rows: CoeffTableRow[] = [];
    for (const [outcome, payloadAny] of Object.entries(items)) {
      const payload = payloadAny as Record<string, unknown>;
      const mainResult = payload.main_result;
      if (mainResult && typeof mainResult === 'object') {
        const mainResultRecord = mainResult as Record<string, unknown>;
        rows.push({
          outcome,
          method: analysisToDisplay.method,
          key: `${outcome}-main`,
          coef: toDisplayNumber(mainResultRecord.coef),
          se: toDisplayNumber(mainResultRecord.std_err ?? mainResultRecord.se),
          pvalue: toDisplayNumber(mainResultRecord.p_value ?? mainResultRecord.pvalue),
          n_obs: toDisplayNumber(mainResultRecord.n_obs),
          r2: toDisplayNumber(mainResultRecord.r2),
        });
      }
    }
    return rows;
  }, [analysisToDisplay]);

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

  const shouldRenderIndicators = indicators && Object.keys(indicators).length > 0;

  return (
    <div className="space-y-8">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Módulo 5 - Impacto Econômico Regional</h1>
          <p className="text-gray-500 mt-1">
            21 indicadores + execução de análises causais com polling
          </p>
        </div>
        <ExportButton moduleCode="5" />
      </div>

      <FilterBar />

      <div className="card space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-indigo-600" />
              Análise causal (PR-16)
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Dispara análise, faz polling automático e exibe status, resultado e visualização.
            </p>
          </div>
          <button
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
            onClick={() => {
              void loadRecentAnalyses();
              refreshAnalysis();
            }}
          >
            <RefreshCw className="h-4 w-4" />
            Atualizar
          </button>
        </div>

        <form onSubmit={handleStartAnalysis} className="grid gap-3 md:grid-cols-2">
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-700">Método</label>
            <select
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              value={analysisMethod}
              onChange={(event) => setAnalysisMethod(event.target.value as AnalysisMethod)}
            >
              {ANALYSIS_METHODS.map((method) => (
                <option key={method.value} value={method.value}>
                  {method.label}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-700">Escopo</label>
            <select
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              value={analysisScope}
              onChange={(event) => setAnalysisScope(event.target.value as AnalysisScope)}
            >
              <option value="state">state</option>
              <option value="municipal">municipal</option>
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-700">Municípios tratados</label>
            <input
              value={analysisTreated}
              onChange={(event) => setAnalysisTreated(event.target.value)}
              placeholder="2100055, 2100105"
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-700">Controle (opcional)</label>
            <input
              value={analysisControls}
              onChange={(event) => setAnalysisControls(event.target.value)}
              placeholder="3304557, 3548500"
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-700">Outcomes</label>
            <input
              value={analysisOutcomes}
              onChange={(event) => setAnalysisOutcomes(event.target.value)}
              placeholder="pib_log, n_vinculos_log"
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-700">Ano do evento (treatment_year)</label>
            <input
              type="number"
              value={analysisEndYear}
              onChange={(event) => setAnalysisEndYear(parseNumeric(event.target.value) || selectedYear)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-700">Período inicial</label>
            <input
              type="number"
              value={analysisStartYear}
              onChange={(event) => setAnalysisStartYear(parseNumeric(event.target.value) || 2010)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-700">Período final</label>
            <input
              type="number"
              value={analysisEndYear}
              onChange={(event) => setAnalysisEndYear(parseNumeric(event.target.value) || selectedYear)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-700">Instrumento</label>
            <input
              value={analysisInstrument}
              onChange={(event) => setAnalysisInstrument(event.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              placeholder="commodity_index, preco_soja..."
            />
          </div>
          <div className="flex items-end">
            <label className="inline-flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={analysisUseMart}
                onChange={(event) => setAnalysisUseMart(event.target.checked)}
                className="h-4 w-4"
              />
              Usar mart (mais rápido)
            </label>
          </div>

          <div className="md:col-span-2">
            {analysisError && <ErrorAlert message={analysisError} className="mb-3" />}
            <button
              type="submit"
              disabled={creatingAnalysis}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 disabled:opacity-50"
            >
              <Play className="h-4 w-4" />
              {creatingAnalysis ? 'Iniciando análise...' : 'Iniciar análise'}
            </button>
          </div>
        </form>

        {activeAnalysis && (
          <div className="rounded-lg border border-gray-200 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
              <div>
                <p className="text-sm text-gray-500">Análise ativa</p>
                <p className="font-semibold text-gray-900">{activeAnalysis.id}</p>
              </div>
              <div className="text-right">
                <AnalysisStatusBadge status={activeAnalysis.status} />
                <p className="text-xs text-gray-500 mt-2">
                  {isPolling ? 'Sincronizando status...' : 'Sincronização pausada'}
                </p>
              </div>
            </div>

            {isPolling && <LoadingSpinner />}

            {pollingError && <ErrorAlert message={pollingError} />}
            {activeAnalysis.status === 'failed' && analysisToDisplay?.error_message && (
              <ErrorAlert message={analysisToDisplay.error_message} />
            )}

            {analysisToDisplay && <AnalysisResultCard detail={analysisToDisplay} />}

            {analysisToDisplay && (
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  onClick={handleDownloadCsv}
                  className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-300 text-sm text-gray-700 hover:bg-gray-50"
                >
                  <Download className="h-4 w-4" />
                  Baixar coeficientes CSV
                </button>
              </div>
            )}

            {analysisToDisplay?.result_full && analysisToDisplay.method === 'event_study' && (
              <div className="mt-4 space-y-3">
                <h3 className="font-semibold text-gray-900">Event Study</h3>
                {analysisToDisplay &&
                  analysisToDisplay.result_full &&
                  Object.entries(analysisToDisplay.result_full).map(([outcome, payload]) => {
                    const points = Array.isArray((payload as Record<string, unknown>)?.coefficients)
                      ? (payload as Record<string, unknown>).coefficients as CoeffPoint[]
                      : [];
                    return points.length > 0 ? (
                      <EventStudyChart
                        key={`${outcome}-es`}
                        outcome={outcome}
                        coefficients={points}
                      />
                    ) : null;
                  })}
              </div>
            )}

            {analysisToDisplay?.result_full && analysisToDisplay.method === 'compare' && (
              <div className="mt-4">
                <MethodComparisonTable items={compareData} />
              </div>
            )}

            {analysisToDisplay?.result_full && analysisToDisplay.method !== 'event_study' && analysisToDisplay.method !== 'compare' && (
              <div className="mt-4">
                <h3 className="font-semibold text-gray-900 mb-2">Coeficientes estimados</h3>
                {analysisMainRows.length > 0 ? (
                  <div className="overflow-auto">
                    <table className="w-full text-sm">
                      <thead className="text-xs text-gray-500 border-b">
                        <tr>
                          <th className="py-2 pr-3 text-left">Outcome</th>
                          <th className="py-2 pr-3 text-left">Coef.</th>
                          <th className="py-2 pr-3 text-left">SE</th>
                          <th className="py-2 pr-3 text-left">P-valor</th>
                          <th className="py-2 pr-3 text-left">N</th>
                          <th className="py-2 pr-3 text-left">R²</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analysisMainRows.map((row) => (
                          <tr key={row.key} className="border-b border-gray-100">
                            <td className="py-2 pr-3">{row.outcome}</td>
                            <td className="py-2 pr-3 font-mono">{row.coef === null ? '—' : formatDecimal(row.coef, 4)}</td>
                            <td className="py-2 pr-3 font-mono">{row.se === null ? '—' : formatDecimal(row.se, 4)}</td>
                            <td className="py-2 pr-3 font-mono">{row.pvalue === null ? '—' : formatDecimal(row.pvalue, 4)}</td>
                            <td className="py-2 pr-3">{row.n_obs ?? '—'}</td>
                            <td className="py-2 pr-3 font-mono">{row.r2 === null ? '—' : formatDecimal(row.r2, 4)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">Resultado ainda sem tabela de coeficientes.</p>
                )}
              </div>
            )}
          </div>
        )}

        {analysesError && <ErrorAlert message={analysesError} />}
        {analysesLoading ? (
          <div className="text-sm text-gray-500">Carregando histórico...</div>
        ) : (
          recentAnalyses.length > 0 && (
            <div>
              <h3 className="font-medium text-gray-800 mb-2">Últimas análises</h3>
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500">
                      <th className="py-1 pr-3">Método</th>
                      <th className="py-1 pr-3">Status</th>
                      <th className="py-1 pr-3">Criada</th>
                      <th className="py-1 pr-3">Ação</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentAnalyses.map((entry) => (
                      <tr key={entry.id} className="border-b border-gray-100">
                        <td className="py-1 pr-3">{entry.method}</td>
                        <td className="py-1 pr-3">
                          <AnalysisStatusBadge status={entry.status} />
                        </td>
                        <td className="py-1 pr-3">
                          {new Date(entry.created_at).toLocaleString('pt-BR')}
                        </td>
                        <td className="py-1 pr-3">
                          <button
                            className="text-indigo-600 hover:underline"
                            onClick={() => setActiveAnalysisId(entry.id)}
                          >
                            Abrir
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )
        )}
      </div>

      {indicatorsLoading && (
        <div>
          <LoadingSpinner />
        </div>
      )}
      {indicatorsError && <ErrorAlert message={indicatorsError} />}

      {shouldRenderIndicators && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {INDICATORS_INFO.map((ind) => {
            const indData = indicators[ind.code];
            const status = implementationStatus[ind.code] || 'implemented';
            const isTechnicalDebt = status === 'technical_debt';
            const hasData = indData?.data && indData.data.length > 0;
            const warnings = indData?.warnings || [];

            return (
              <ChartCard
                key={ind.code}
                title={ind.name}
                description={ind.desc}
                unit={ind.unit}
                isLoading={indicatorsLoading}
              >
                {isTechnicalDebt ? (
                  <div className="h-64 flex items-center justify-center text-amber-600">
                    Implementação pendente (dívida técnica)
                  </div>
                ) : hasData ? (
                  <BarChart
                    labels={toIndicatorRows(indData).slice(0, 10).map((d) => getLabelFromData(d))}
                    datasets={[
                      {
                        label: ind.unit,
                        data: toIndicatorRows(indData)
                          .slice(0, 10)
                          .map((d) => toDisplayValue(d, ind.valueField)),
                      },
                    ]}
                    yAxisLabel={ind.unit}
                    horizontal
                    valueFormat={getIndicatorFormat(ind.code)}
                  />
                ) : (
                  <div className="h-64 flex items-center justify-center text-gray-400">
                    Dados não disponíveis para os filtros selecionados
                  </div>
                )}
                {warnings.length > 0 && renderWarnings(warnings)}
              </ChartCard>
            );
          })}
        </div>
      )}
    </div>
  );
}
