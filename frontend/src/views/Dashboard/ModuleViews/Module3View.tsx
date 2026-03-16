import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useI18n } from '../../../i18n/I18nContext';
import { AlertCircle } from 'lucide-react';
import { FilterBar } from '../../../components/filters/FilterBar';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { ChartCard } from '../../../components/charts/ChartCard';
import { BarChart } from '../../../components/charts/BarChart';
import { ExportButton } from '../../../components/common/ExportButton';
import { useFilterStore } from '../../../store/filterStore';
import { indicatorsService } from '../../../api/indicators';
import { getIndicatorFormat } from '../../../utils/chartFormats';
import { employmentMultiplierService } from '../../../api/employmentMultiplier';
import type {
  EmploymentMultiplierConfidenceEstimate,
  EmploymentMultiplierResponse,
} from '../../../api/employmentMultiplier';
import { formatCurrency, formatDecimal, formatQuantity } from '../../../utils/numberFormat';

// Indicadores especiais com dados agrupados (visualização dedicada)
const GROUPED_INDICATORS = [
  { code: 'IND-3.03', name: 'Paridade de Gênero por Categoria Profissional' },
  { code: 'IND-3.09', name: 'Distribuição por Escolaridade' },
];

const CATEGORIA_LABELS: Record<string, string> = {
  GESTAO_TECNICO: 'Gestão / Técnico',
  ADMINISTRATIVO: 'Administrativo',
  OPERACIONAL: 'Operacional',
};

// Indicadores do Módulo 3 - Recursos Humanos (RAIS)
const INDICATORS_INFO = [
  { code: 'IND-3.01', name: 'Empregos Portuários', unit: 'Empregos', desc: 'Total de empregos no setor portuário (RAIS)', valueField: 'empregos_portuarios' },
  { code: 'IND-3.02', name: 'Paridade de Gênero', unit: '%', desc: 'Percentual de mulheres no setor portuário', valueField: 'percentual_feminino' },
  { code: 'IND-3.05', name: 'Salário Médio', unit: 'R$', desc: 'Remuneração média mensal', valueField: 'salario_medio' },
  { code: 'IND-3.06', name: 'Massa Salarial', unit: 'R$', desc: 'Massa salarial anual estimada', valueField: 'massa_salarial_anual' },
  { code: 'IND-3.07', name: 'Produtividade', unit: 'ton/emp', desc: 'Toneladas movimentadas por empregado portuário', valueField: 'ton_por_empregado' },
  { code: 'IND-3.08', name: 'Receita por Empregado', unit: 'R$/emp', desc: 'PIB por empregado portuário (proxy)', valueField: 'pib_por_empregado_portuario' },
  { code: 'IND-3.10', name: 'Idade Média', unit: 'Anos', desc: 'Idade média dos trabalhadores portuários', valueField: 'idade_media' },
  { code: 'IND-3.11', name: 'Variação Anual Empregos', unit: '%', desc: 'Variação percentual anual de empregos', valueField: 'variacao_percentual' },
  { code: 'IND-3.12', name: 'Participação Emprego Local', unit: '%', desc: 'Participação do setor portuário no emprego total do município', valueField: 'participacao_emprego_local' },
];

const REMUNERATION_CHART_INDICATORS = [
  { code: 'IND-3.13', name: 'Remuneração por Escolaridade e Sexo' },
  { code: 'IND-3.14', name: 'Remuneração por Raça/Cor e Sexo' },
  { code: 'IND-3.15', name: 'Remuneração por Escolaridade, Raça/Cor e Sexo' },
  { code: 'IND-3.16', name: 'Remuneração Média com Referência Nacional' },
];

const ESCOLARIDADE_CATEGORIES = [
  { key: 'FUNDAMENTAL_INCOMPLETO', label: 'Fundamental Incompleto' },
  { key: 'FUNDAMENTAL_COMPLETO', label: 'Fundamental Completo' },
  { key: 'MEDIO_INCOMPLETO', label: 'Médio Incompleto' },
  { key: 'MEDIO_COMPLETO', label: 'Médio Completo' },
  { key: 'SUPERIOR_INCOMPLETO', label: 'Superior Incompleto' },
  { key: 'SUPERIOR_COMPLETO', label: 'Superior Completo' },
  { key: 'MESTRADO', label: 'Mestrado' },
  { key: 'DOUTORADO', label: 'Doutorado' },
] as const;

const RACA_CATEGORIES = [
  { key: 'BRANCA', label: 'Branca' },
  { key: 'PARDA', label: 'Parda' },
  { key: 'INDIGENA', label: 'Indígena' },
  { key: 'PRETA', label: 'Preta' },
  { key: 'AMARELA', label: 'Amarela' },
] as const;

type SexoOption = 'MASCULINO' | 'FEMININO';

interface InstallationMunicipioResolutionState {
  municipioId: string | null;
  message: string | null;
}

interface RemuneracaoEscolaridadeSexoRow {
  escolaridade: string;
  ordem_escolaridade: number;
  sexo: SexoOption;
  remuneracao_media: number;
}

interface RemuneracaoRacaSexoRow {
  raca_cor: string;
  ordem_raca: number;
  sexo: SexoOption;
  remuneracao_media: number;
}

interface RemuneracaoEscolaridadeRacaSexoRow {
  escolaridade: string;
  ordem_escolaridade: number;
  raca_cor: string;
  ordem_raca: number;
  sexo: SexoOption;
  combinacao: string;
  remuneracao_media: number;
}

interface RemuneracaoComparativoRow {
  nome_municipio?: string;
  id_municipio?: string;
  remuneracao_media: number;
  media_nacional: number;
}

function toNumber(value: unknown): number {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function normalizeText(value: unknown): string {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toUpperCase()
    .replace(/[^A-Z0-9 ]/gu, ' ')
    .replace(/\s+/gu, ' ')
    .trim();
}

function normalizeMunicipioCode(value: string | null | undefined): string | null {
  if (!value) return null;
  const digits = value.replace(/\D/g, '');
  if (!digits) return null;
  if (digits.length === 6) return `0${digits}`;
  return digits.length === 7 ? digits : null;
}

function normalizeEscolaridade(value: unknown): string | null {
  const raw = normalizeText(value);
  if (!raw) return null;
  if (raw.includes('FUNDAMENTAL') && raw.includes('INCOMPL')) return 'FUNDAMENTAL_INCOMPLETO';
  if (raw.includes('FUNDAMENTAL') && raw.includes('COMPLETO')) return 'FUNDAMENTAL_COMPLETO';
  if (raw.includes('MEDIO') && raw.includes('INCOMPL')) return 'MEDIO_INCOMPLETO';
  if (raw.includes('MEDIO') && raw.includes('COMPLETO')) return 'MEDIO_COMPLETO';
  if (raw.includes('SUPERIOR') && raw.includes('INCOMPL')) return 'SUPERIOR_INCOMPLETO';
  if (raw.includes('SUPERIOR') && raw.includes('COMPLETO')) return 'SUPERIOR_COMPLETO';
  if (raw.includes('MESTRADO')) return 'MESTRADO';
  if (raw.includes('DOUTORADO') || raw.includes('DOUTOR')) return 'DOUTORADO';
  return null;
}

function normalizeRacaCor(value: unknown): string | null {
  const raw = normalizeText(value);
  if (!raw) return null;
  if (raw.includes('BRANCA')) return 'BRANCA';
  if (raw.includes('PARDA')) return 'PARDA';
  if (raw.includes('INDIG') || raw.includes('INDIGENA')) return 'INDIGENA';
  if (raw.includes('PRETA') || raw.includes('NEGRA')) return 'PRETA';
  if (raw.includes('AMAREL') || raw.includes('ASIAT')) return 'AMARELA';
  return null;
}

function normalizeSexo(value: unknown): SexoOption | null {
  const sexo = normalizeText(value);
  if (sexo === 'MASCULINO') return 'MASCULINO';
  if (sexo === 'FEMININO') return 'FEMININO';
  if (sexo === '1') return 'MASCULINO';
  if (sexo === '2') return 'FEMININO';
  if (sexo === 'M') return 'MASCULINO';
  if (sexo === 'F') return 'FEMININO';
  if (sexo.startsWith('MALE')) return 'MASCULINO';
  if (sexo.startsWith('FEMALE')) return 'FEMININO';
  return null;
}

function getEscolaridadeLabel(escolaridade: string): string {
  const found = ESCOLARIDADE_CATEGORIES.find((item) => item.key === escolaridade);
  return found?.label || escolaridade;
}

function getRacaLabel(racaCor: string): string {
  const found = RACA_CATEGORIES.find((item) => item.key === racaCor);
  return found?.label || racaCor;
}

function parseRemuneracaoEscolaridadeSexoRows(raw: any[]): RemuneracaoEscolaridadeSexoRow[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .map((row) => {
      const sexo = normalizeSexo(row?.sexo);
      const escolaridade = normalizeEscolaridade(row?.escolaridade) || String(row?.escolaridade || '').toUpperCase();
      if (!sexo || !escolaridade) return null;
      return {
        sexo,
        escolaridade,
        ordem_escolaridade: toNumber(row?.ordem_escolaridade),
        remuneracao_media: toNumber(row?.remuneracao_media),
      };
    })
    .filter((row): row is RemuneracaoEscolaridadeSexoRow => row !== null);
}

function parseRemuneracaoRacaSexoRows(raw: any[]): RemuneracaoRacaSexoRow[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .map((row) => {
      const sexo = normalizeSexo(row?.sexo);
      const racaCor = normalizeRacaCor(row?.raca_cor) || String(row?.raca_cor || '').toUpperCase();
      if (!sexo || !racaCor) return null;
      return {
        sexo,
        raca_cor: racaCor,
        ordem_raca: toNumber(row?.ordem_raca),
        remuneracao_media: toNumber(row?.remuneracao_media),
      };
    })
    .filter((row): row is RemuneracaoRacaSexoRow => row !== null);
}

function parseRemuneracaoEscolaridadeRacaSexoRows(raw: any[]): RemuneracaoEscolaridadeRacaSexoRow[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .map((row) => {
      const sexo = normalizeSexo(row?.sexo);
      const escolaridade = normalizeEscolaridade(row?.escolaridade) || String(row?.escolaridade || '').toUpperCase();
      const racaCor = normalizeRacaCor(row?.raca_cor) || String(row?.raca_cor || '').toUpperCase();
      if (!sexo || !escolaridade || !racaCor) return null;
      return {
        sexo,
        escolaridade,
        ordem_escolaridade: toNumber(row?.ordem_escolaridade),
        raca_cor: racaCor,
        ordem_raca: toNumber(row?.ordem_raca),
        combinacao: String(row?.combinacao || `${escolaridade} | ${racaCor}`),
        remuneracao_media: toNumber(row?.remuneracao_media),
      };
    })
    .filter((row): row is RemuneracaoEscolaridadeRacaSexoRow => row !== null);
}

function parseRemuneracaoComparativoRows(raw: any[]): RemuneracaoComparativoRow[] {
  if (!Array.isArray(raw)) return [];
  return raw.map((row) => ({
    nome_municipio: row?.nome_municipio,
    id_municipio: row?.id_municipio,
    remuneracao_media: toNumber(row?.remuneracao_media),
    media_nacional: toNumber(row?.media_nacional),
  }));
}

function renderDataStatus(hasError?: string, helperText?: string) {
  return (
    <div className="h-64 flex flex-col items-center justify-center text-gray-400">
      {hasError ? (
        <>
          <p className="text-red-500 mb-2">Erro ao carregar dados</p>
          <p className="text-sm text-gray-500">{hasError}</p>
          {helperText && <p className="text-xs text-gray-400 mt-2 text-center max-w-xs">{helperText}</p>}
        </>
      ) : (
        <>
          <p>Dados não disponíveis</p>
          <p className="text-sm text-gray-500 mt-1">
            Verifique os filtros ou aguarde disponibilização dos dados RAIS
          </p>
          {helperText && <p className="text-xs text-gray-400 mt-2 text-center max-w-xs">{helperText}</p>}
        </>
      )}
    </div>
  );
}

// Extrai os IDs de município válidos do resultado do IND-3.01,
// ordenados por volume de emprego (maiores primeiro), máximo 3.
function extractMunicipioIds(data: any[]): string[] {
  return (data || [])
    .filter((d: any) => /^\d{6,7}$/.test(String(d.id_municipio || '')))
    .sort((a: any, b: any) => (b.empregos_portuarios || 0) - (a.empregos_portuarios || 0))
    .slice(0, 3)
    .map((d: any) => String(d.id_municipio));
}

function getValueFromData(item: any, valueField: string): number {
  return item[valueField] ?? item.valor ?? item.total ?? 0;
}

function getLabelFromData(item: any): string {
  return item.nome_municipio || item.municipio || item.id_municipio || item.id_instalacao || 'N/A';
}

function isLikelyMunicipioCode(value: string | null | undefined): value is string {
  if (!value) return false;
  return /^\d{6,7}$/.test(value.trim());
}

function resolveImpactEstimate(
  response: EmploymentMultiplierResponse,
  preferCausal: boolean,
): EmploymentMultiplierConfidenceEstimate | null {
  if (preferCausal) {
    return response.active ?? response.causal_estimate ?? response.estimate ?? null;
  }
  return response.active ?? response.estimate ?? response.causal_estimate ?? null;
}

export function Module3View() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const { selectedYear, selectedInstallation } = useFilterStore();
  const [indicators, setIndicators] = useState<Record<string, any>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [installationMunicipioResolution, setInstallationMunicipioResolution] = useState<InstallationMunicipioResolutionState>({
    municipioId: null,
    message: null,
  });
  const [isResolvingMunicipio, setIsResolvingMunicipio] = useState(false);
  const [municipioResolutionError, setMunicipioResolutionError] = useState<string | null>(null);
  const [impactData, setImpactData] = useState<EmploymentMultiplierResponse[]>([]);
  const [isImpactLoading, setIsImpactLoading] = useState(false);
  const [deltaPct, setDeltaPct] = useState<number>(10);
  const [scenarioDeltas, setScenarioDeltas] = useState<number[]>([10]);
  const [useCausalEstimate, setUseCausalEstimate] = useState(false);
  const [selectedSexoChart3, setSelectedSexoChart3] = useState<SexoOption>('MASCULINO');

  useEffect(() => {
    let isActive = true;
    const resolveInstallationMunicipio = async () => {
      setIsResolvingMunicipio(true);
      setIsLoading(true);
      setMunicipioResolutionError(null);

      if (!selectedInstallation) {
        if (isActive) {
          setInstallationMunicipioResolution({ municipioId: null, message: null });
          setIsResolvingMunicipio(false);
        }
        return;
      }

        if (isLikelyMunicipioCode(selectedInstallation)) {
          const normalizedMunicipio = normalizeMunicipioCode(selectedInstallation);
          if (isActive) {
            setInstallationMunicipioResolution({
              municipioId: normalizedMunicipio,
              message: `Município selecionado diretamente por código IBGE: ${normalizedMunicipio}.`,
            });
            setIsResolvingMunicipio(false);
          }
          return;
        }

      try {
        const response = await indicatorsService.resolveInstallationToMunicipio(selectedInstallation);
        if (!isActive) {
          return;
        }
        const resolvedMunicipio = normalizeMunicipioCode(response.id_municipio);
        setInstallationMunicipioResolution({
          municipioId: resolvedMunicipio,
          message: response.message,
        });
        if (!response.municipio_found) {
          setMunicipioResolutionError(response.message);
        }
      } catch (err: any) {
        if (!isActive) {
          return;
        }
        setInstallationMunicipioResolution({
          municipioId: null,
          message: 'Não foi possível validar a associação porto-município.',
        });
        setMunicipioResolutionError(
          err?.response?.data?.detail || err?.message || 'Falha ao associar porto ao município.'
        );
      } finally {
        if (isActive) {
          setIsResolvingMunicipio(false);
        }
      }
    };

    void resolveInstallationMunicipio();

    return () => {
      isActive = false;
    };
  }, [selectedInstallation]);

  useEffect(() => {
    if (selectedInstallation && isResolvingMunicipio) {
      return;
    }

    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      setImpactData([]);

      try {
        const requestCodes = [
          ...INDICATORS_INFO.map((ind) => ind.code),
          ...GROUPED_INDICATORS.map((ind) => ind.code),
          ...REMUNERATION_CHART_INDICATORS.map((ind) => ind.code),
        ];

        const promises = requestCodes.map((code) =>
          indicatorsService.queryIndicator({
            codigo_indicador: code,
            params: {
              ano: selectedYear,
              id_instalacao: selectedInstallation || undefined,
              id_municipio: installationMunicipioResolution.municipioId || undefined,
            },
          }).catch((err) => {
            console.error(`Erro ao buscar indicador ${code}:`, err);
            return { data: [], error: err.response?.data?.detail || err.message };
          })
        );

        const results = await Promise.all(promises);
        const mapped: Record<string, any> = {};
        results.forEach((result, i) => {
          mapped[requestCodes[i]] = result;
        });
        setIndicators(mapped);
        setIsLoading(false);

        // Extrai IDs de município do IND-3.01 para o painel de impacto
        const municipioIds = extractMunicipioIds(mapped['IND-3.01']?.data || []);
        if (municipioIds.length > 0) {
          setIsImpactLoading(true);
          try {
            const impactPromises = municipioIds.map((id) =>
              employmentMultiplierService.getMultiplierEstimate(id, selectedYear, useCausalEstimate)
                .catch(() => null)
            );
            const raw = await Promise.all(impactPromises);
            const valid: EmploymentMultiplierResponse[] = [];
            for (const r of raw) {
              if (r !== null && Array.isArray(r.data) && r.data.length > 0) {
                valid.push(r as unknown as EmploymentMultiplierResponse);
              }
            }
            setImpactData(valid);
          } catch {
            // falha no painel de impacto não bloqueia o restante da página
          } finally {
            setIsImpactLoading(false);
          }
        }
      } catch (err: any) {
        console.error('Erro ao carregar indicadores do Módulo 3:', err);
        setError(err.response?.data?.detail || 'Erro ao carregar indicadores');
        setIsLoading(false);
      }
    };

    fetchData();
  }, [selectedYear, selectedInstallation, installationMunicipioResolution.municipioId, isResolvingMunicipio, useCausalEstimate]);

  const installationScopeLabel = useMemo(() => {
    if (!selectedInstallation) {
      return 'Todas as instalações';
    }

    if (isResolvingMunicipio) {
      return `Selecionado: ${selectedInstallation} (associando ao município...)`;
    }

    if (municipioResolutionError || !installationMunicipioResolution.municipioId) {
      return (
        `Selecionado: ${selectedInstallation}. Não foi possível associar ao município cadastrado.` +
        ' O resultado pode refletir recorte agregado por instalação não aplicado.'
      );
    }

    return `Selecionado: ${selectedInstallation} → Município ${installationMunicipioResolution.municipioId}.`;
  }, [selectedInstallation, isResolvingMunicipio, municipioResolutionError, installationMunicipioResolution.municipioId]);

  const chartMunicipioHint = useMemo<string | undefined>(() => {
    if (!selectedInstallation) {
      return undefined;
    }
    if (isResolvingMunicipio) {
      return 'Aguarde, associando a instalação selecionada ao município IBGE...';
    }
    if (municipioResolutionError || !installationMunicipioResolution.municipioId) {
      return 'Sem associação porto-município disponível para este recorte. Os dados podem ser retornados de forma agregada.';
    }
    return `Recorte aplicado por município: ${installationMunicipioResolution.municipioId}.`;
  }, [isResolvingMunicipio, municipioResolutionError, selectedInstallation, installationMunicipioResolution.municipioId]);

  const remEscolSexoRows = useMemo(
    () => parseRemuneracaoEscolaridadeSexoRows(indicators['IND-3.13']?.data || []),
    [indicators]
  );

  const remRacaSexoRows = useMemo(
    () => parseRemuneracaoRacaSexoRows(indicators['IND-3.14']?.data || []),
    [indicators]
  );

  const remEscolRacaSexoRows = useMemo(
    () => parseRemuneracaoEscolaridadeRacaSexoRows(indicators['IND-3.15']?.data || []),
    [indicators]
  );

  const remComparativoRows = useMemo(
    () => parseRemuneracaoComparativoRows(indicators['IND-3.16']?.data || []),
    [indicators]
  );

  const chart1Data = useMemo(() => {
    const values = new Map<string, number>();
    remEscolSexoRows.forEach((row) => {
      values.set(`${row.escolaridade}|${row.sexo}`, row.remuneracao_media);
    });

    return {
      labels: ESCOLARIDADE_CATEGORIES.map((item) => item.label),
      masculino: ESCOLARIDADE_CATEGORIES.map((item) => values.get(`${item.key}|MASCULINO`) || 0),
      feminino: ESCOLARIDADE_CATEGORIES.map((item) => values.get(`${item.key}|FEMININO`) || 0),
    };
  }, [remEscolSexoRows]);

  const chart2Data = useMemo(() => {
    const values = new Map<string, number>();
    remRacaSexoRows.forEach((row) => {
      values.set(`${row.raca_cor}|${row.sexo}`, row.remuneracao_media);
    });

    return {
      labels: RACA_CATEGORIES.map((item) => item.label),
      masculino: RACA_CATEGORIES.map((item) => values.get(`${item.key}|MASCULINO`) || 0),
      feminino: RACA_CATEGORIES.map((item) => values.get(`${item.key}|FEMININO`) || 0),
    };
  }, [remRacaSexoRows]);

  const chart3Data = useMemo(() => {
    const filtered = remEscolRacaSexoRows
      .filter((row) => row.sexo === selectedSexoChart3)
      .sort((a, b) => {
        if (a.ordem_escolaridade !== b.ordem_escolaridade) {
          return a.ordem_escolaridade - b.ordem_escolaridade;
        }
        return a.ordem_raca - b.ordem_raca;
      });

    return {
      labels: filtered.map((row) => `${getEscolaridadeLabel(row.escolaridade)} · ${getRacaLabel(row.raca_cor)}`),
      values: filtered.map((row) => row.remuneracao_media),
    };
  }, [remEscolRacaSexoRows, selectedSexoChart3]);

  const chart4Data = useMemo(() => {
    const sorted = [...remComparativoRows]
      .sort((a, b) => b.remuneracao_media - a.remuneracao_media)
      .slice(0, 12);

    const mediaNacional = sorted.length > 0 ? sorted[0].media_nacional : null;

    return {
      labels: sorted.map((row) => row.nome_municipio || row.id_municipio || 'N/A'),
      values: sorted.map((row) => row.remuneracao_media),
      mediaNacional,
    };
  }, [remComparativoRows]);

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Módulo 3 - Recursos Humanos</h1>
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Módulo 3 — Capital Humano e Emprego Portuário</h1>
          <p className="text-gray-500 mt-1">
            Indicadores de emprego, remuneração, produtividade e diversidade para decisão de investimento — dados RAIS + ANTAQ
          </p>
        </div>
        <ExportButton
          moduleCode="3"
          deltaTonelagemPct={scenarioDeltas.length > 0 ? scenarioDeltas[0] : undefined}
        />
      </div>

      <FilterBar />
      <p className="text-sm text-gray-600 mb-4">
        <span className="font-medium">Filtro ativo:</span>{' '}
        {installationScopeLabel}
      </p>
      {municipioResolutionError && (
        <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4">
          {municipioResolutionError}
        </p>
      )}
      {installationMunicipioResolution.message && !municipioResolutionError && (
        <p className="text-sm text-gray-500 mb-4">{installationMunicipioResolution.message}</p>
      )}

      {error && <ErrorAlert message={error} className="mb-6" />}

      {/* ── Alertas de qualidade de dados ────────────────────────────────────── */}
      {(() => {
        const allWarnings: Array<{ code: string; msg: string }> = [];
        for (const [code, indResp] of Object.entries(indicators)) {
          if (!indResp?.warnings || !Array.isArray(indResp.warnings)) continue;
          for (const w of indResp.warnings) {
            const msg = typeof w === 'string' ? w : typeof w?.mensagem === 'string' ? w.mensagem : null;
            if (msg) allWarnings.push({ code, msg });
          }
        }
        if (allWarnings.length === 0) return null;
        return (
          <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3">
            <p className="text-xs font-semibold text-amber-800 mb-1">{t('module3.warnings.title')} ({allWarnings.length})</p>
            <ul className="list-disc pl-4 space-y-0.5">
              {allWarnings.slice(0, 10).map((w, i) => (
                <li key={`w-${i}`} className="text-xs text-amber-700">
                  <span className="font-medium">{w.code}</span>: {w.msg}
                </li>
              ))}
              {allWarnings.length > 10 && (
                <li className="text-xs text-amber-600 italic">… e mais {allWarnings.length - 10} observações</li>
              )}
            </ul>
          </div>
        );
      })()}

      {/* ── Visão Executiva: Indicadores-Chave para Investidores ─────────────── */}
      {!isLoading && (
        <div className="mb-8 rounded-xl border border-blue-200 bg-blue-50 p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Visão Executiva — Capital Humano Portuário</h2>
          <p className="text-sm text-gray-500 mb-4">
            Leitura orientada a investidores e tomadores de decisão · Dados RAIS {selectedYear}
            {!selectedInstallation && ' · Visão Nacional (selecione um porto para detalhar)'}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Emprego e dependência econômica */}
            {(() => {
              const empData = indicators['IND-3.01']?.data;
              const partData = indicators['IND-3.12']?.data;
              if (!Array.isArray(empData) || empData.length === 0) return null;
              const isNacional = !selectedInstallation && empData.length > 1;
              const totalEmpregos = empData.reduce((sum: number, d: any) => sum + toNumber(d.empregos_portuarios), 0);
              const topMunicipio = empData.length === 1 ? empData[0] : empData.slice().sort((a: any, b: any) => toNumber(b.empregos_portuarios) - toNumber(a.empregos_portuarios))[0];
              const participacao = Array.isArray(partData) && partData.length > 0
                ? toNumber(partData[0]?.participacao_emprego_local)
                : null;
              return (
                <div className="bg-white rounded-lg border border-blue-100 p-4">
                  <h3 className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Geração de Emprego</h3>
                  <p className="text-2xl font-bold text-gray-900">{formatQuantity(totalEmpregos)}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {isNacional
                      ? `empregos diretos no setor portuário (${empData.length} municípios)`
                      : `empregos diretos no setor portuário`}
                  </p>
                  {isNacional && (
                    <p className="text-sm text-gray-500 mt-2">
                      Maior empregador: {getLabelFromData(topMunicipio)} com {formatQuantity(toNumber(topMunicipio?.empregos_portuarios))} empregos.
                    </p>
                  )}
                  {!isNacional && participacao != null && participacao > 0 && (
                    <p className="text-sm text-gray-500 mt-2">
                      {participacao >= 10
                        ? `Alta dependência: o porto representa ${formatDecimal(participacao, 1)}% do emprego local em ${getLabelFromData(topMunicipio)}, sinalizando risco de concentração econômica.`
                        : participacao >= 5
                        ? `Relevância moderada: ${formatDecimal(participacao, 1)}% do emprego local vinculado ao porto em ${getLabelFromData(topMunicipio)}.`
                        : `Participação de ${formatDecimal(participacao, 1)}% no emprego local — espaço para crescimento da cadeia portuária.`}
                    </p>
                  )}
                </div>
              );
            })()}

            {/* Remuneração e competitividade */}
            {(() => {
              const salData = indicators['IND-3.05']?.data;
              const compData = indicators['IND-3.16']?.data;
              if (!Array.isArray(salData) || salData.length === 0) return null;
              const isNacional = !selectedInstallation && salData.length > 1;
              // Para visão nacional: média ponderada não disponível, usar média simples dos municípios
              const salMedio = isNacional
                ? salData.reduce((sum: number, d: any) => sum + toNumber(d.salario_medio), 0) / salData.length
                : toNumber(salData[0]?.salario_medio);
              const compRow = Array.isArray(compData) && compData.length > 0 ? compData[0] : null;
              const mediaNacional = compRow ? toNumber(compRow.media_nacional) : null;
              const premiumPct = mediaNacional && mediaNacional > 0
                ? ((salMedio - mediaNacional) / mediaNacional) * 100
                : null;
              return (
                <div className="bg-white rounded-lg border border-blue-100 p-4">
                  <h3 className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Competitividade Salarial</h3>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(salMedio)}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {isNacional ? 'remuneração média mensal (média nacional)' : 'remuneração média mensal'}
                  </p>
                  {!isNacional && premiumPct != null && (
                    <p className="text-sm text-gray-500 mt-2">
                      {premiumPct > 5
                        ? `Salários ${formatDecimal(premiumPct, 1)}% acima da média nacional portuária — indica capacidade de retenção de talentos e produtividade superior.`
                        : premiumPct < -5
                        ? `Salários ${formatDecimal(Math.abs(premiumPct), 1)}% abaixo da média nacional — risco de perda de mão-de-obra qualificada para portos concorrentes.`
                        : `Alinhado à média nacional portuária — condições competitivas equilibradas para atração de talentos.`}
                    </p>
                  )}
                </div>
              );
            })()}

            {/* Produtividade e eficiência operacional */}
            {(() => {
              const prodData = indicators['IND-3.07']?.data;
              if (!Array.isArray(prodData) || prodData.length === 0) return null;
              const isNacional = !selectedInstallation && prodData.length > 1;
              const tonEmp = isNacional
                ? prodData.reduce((sum: number, d: any) => sum + toNumber(d.ton_por_empregado), 0) / prodData.filter((d: any) => toNumber(d.ton_por_empregado) > 0).length
                : toNumber(prodData[0]?.ton_por_empregado);
              return (
                <div className="bg-white rounded-lg border border-blue-100 p-4">
                  <h3 className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Eficiência Operacional</h3>
                  <p className="text-2xl font-bold text-gray-900">{formatDecimal(tonEmp, 0)}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {isNacional ? 'toneladas por empregado/ano (média nacional)' : 'toneladas por empregado/ano'}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    {tonEmp > 5000
                      ? 'Alta produtividade por trabalhador — indica operação mecanizada e eficiente, favorecendo o retorno sobre investimentos em infraestrutura.'
                      : tonEmp > 1000
                      ? 'Produtividade intermediária — há espaço para ganhos de eficiência via automação e capacitação.'
                      : 'Operação intensiva em mão-de-obra — investimentos em modernização podem gerar saltos significativos de produtividade.'}
                  </p>
                </div>
              );
            })()}

            {/* Dinâmica de emprego */}
            {(() => {
              const varData = indicators['IND-3.11']?.data;
              if (!Array.isArray(varData) || varData.length === 0) return null;
              const isNacional = !selectedInstallation && varData.length > 1;
              const variacao = isNacional
                ? varData.reduce((sum: number, d: any) => sum + toNumber(d.variacao_percentual), 0) / varData.length
                : toNumber(varData[0]?.variacao_percentual);
              return (
                <div className="bg-white rounded-lg border border-blue-100 p-4">
                  <h3 className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Tendência de Emprego</h3>
                  <p className={`text-2xl font-bold ${variacao >= 0 ? 'text-green-700' : 'text-red-600'}`}>
                    {variacao >= 0 ? '+' : ''}{formatDecimal(variacao, 1)}%
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    {isNacional ? 'variação anual de empregos (média nacional)' : 'variação anual de empregos'}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    {variacao > 3
                      ? 'Crescimento expressivo — a cadeia portuária está em expansão, indicando aquecimento do comércio exterior e/ou investimentos recentes.'
                      : variacao > 0
                      ? 'Crescimento moderado — estabilidade no mercado de trabalho portuário com tendência positiva.'
                      : variacao > -3
                      ? 'Leve retração — monitorar se reflete ajustes sazonais ou tendência estrutural de queda de movimentação.'
                      : 'Contração significativa — pode indicar perda de competitividade do porto ou desaceleração do comércio exterior regional.'}
                  </p>
                </div>
              );
            })()}

            {/* Diversidade de gênero (ESG) */}
            {(() => {
              const genData = indicators['IND-3.02']?.data;
              if (!Array.isArray(genData) || genData.length === 0) return null;
              const isNacional = !selectedInstallation && genData.length > 1;
              const pctFem = isNacional
                ? genData.reduce((sum: number, d: any) => sum + toNumber(d.percentual_feminino), 0) / genData.length
                : toNumber(genData[0]?.percentual_feminino);
              return (
                <div className="bg-white rounded-lg border border-blue-100 p-4">
                  <h3 className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Diversidade (ESG)</h3>
                  <p className="text-2xl font-bold text-gray-900">{formatDecimal(pctFem, 1)}%</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {isNacional ? 'participação feminina no setor (média nacional)' : 'participação feminina no setor'}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    {pctFem >= 30
                      ? 'Participação feminina acima da média setorial — diferencial positivo em critérios ESG e governança.'
                      : pctFem >= 15
                      ? 'Participação feminina moderada — avanços em diversidade podem melhorar pontuação ESG e atrair capital sustentável.'
                      : 'Baixa representatividade feminina — indicador típico do setor, mas com espaço para políticas de inclusão que valorizem o ativo perante investidores ESG.'}
                  </p>
                </div>
              );
            })()}

            {/* Qualificação da força de trabalho */}
            {(() => {
              const escolData = indicators['IND-3.09']?.data;
              if (!Array.isArray(escolData) || escolData.length === 0) return null;
              const escolMap = new Map<string, number>();
              let total = 0;
              for (const row of escolData) {
                const key = normalizeEscolaridade(row?.grau_instrucao);
                if (!key) continue;
                const qtd = toNumber(row?.qtd);
                escolMap.set(key, (escolMap.get(key) || 0) + qtd);
                total += qtd;
              }
              if (total === 0) return null;
              const superior = ((escolMap.get('SUPERIOR_COMPLETO') || 0) + (escolMap.get('MESTRADO') || 0) + (escolMap.get('DOUTORADO') || 0)) / total * 100;
              const medio = ((escolMap.get('MEDIO_COMPLETO') || 0) + (escolMap.get('MEDIO_INCOMPLETO') || 0)) / total * 100;
              return (
                <div className="bg-white rounded-lg border border-blue-100 p-4">
                  <h3 className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Qualificação</h3>
                  <p className="text-2xl font-bold text-gray-900">{formatDecimal(superior, 1)}%</p>
                  <p className="text-sm text-gray-600 mt-1">com nível superior ou pós-graduação</p>
                  <p className="text-sm text-gray-500 mt-2">
                    {superior > 25
                      ? `Força de trabalho altamente qualificada (${formatDecimal(medio, 0)}% com ensino médio) — favorece operações complexas e atrai investimentos em logística de alto valor.`
                      : superior > 10
                      ? `Qualificação intermediária com ${formatDecimal(medio, 0)}% no ensino médio — investimentos em capacitação podem elevar produtividade e competitividade.`
                      : `Perfil predominantemente operacional (${formatDecimal(medio, 0)}% ensino médio) — programas de qualificação são estratégicos para modernização das operações.`}
                  </p>
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* ── Painel de Impacto em Emprego (PR-31) ──────────────────────────────── */}
      <div className="mb-8 rounded-xl border border-amber-200 bg-amber-50 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Painel de Impacto em Emprego</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Fonte: RAIS + ANTAQ · {selectedYear} · {useCausalEstimate
                ? t('module3.multiplier.causalBeta')
                : 'Multiplicadores de literatura (UNCTAD / MInfra)'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setUseCausalEstimate(false)}
              className={`px-3 py-1.5 rounded-md border text-xs font-semibold ${
                !useCausalEstimate
                  ? 'bg-amber-100 text-amber-700 border-amber-200'
                  : 'bg-white text-gray-600 border-gray-200'
              }`}
            >
              Literatura
            </button>
            <button
              type="button"
              onClick={() => setUseCausalEstimate(true)}
              className={`px-3 py-1.5 rounded-md border text-xs font-semibold ${
                useCausalEstimate
                  ? 'bg-blue-100 text-blue-700 border-blue-200'
                  : 'bg-white text-gray-600 border-gray-200'
              }`}
            >
              Causal
            </button>
            <span className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border whitespace-nowrap ${
              useCausalEstimate
                ? 'bg-blue-100 text-blue-700 border-blue-200'
                : 'bg-amber-100 text-amber-700 border-amber-200'
            }`}>
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              {useCausalEstimate ? t('module3.multiplier.causalActive') : t('module3.multiplier.literaryProxy')}
            </span>
          </div>
        </div>

        {isImpactLoading ? (
          <div className="py-6"><LoadingSpinner /></div>
        ) : impactData.length === 0 ? (
          <p className="text-sm text-gray-400 py-4 text-center">
            Selecione um porto para visualizar o painel de impacto, ou aguarde disponibilização dos dados RAIS para os filtros atuais.
          </p>
        ) : (
          <>
            {/* Cards de impacto por município */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              {impactData.map((resp) => {
                const row = resp.data?.[0];
                if (!row) return null;
                const estimate = resolveImpactEstimate(resp, useCausalEstimate);
                const empregosDiretos = estimate?.direct_jobs ?? row.empregos_diretos ?? 0;
                const empregosIndiretos = estimate?.indirect_estimated ?? row.empregos_indiretos_estimados ?? 0;
                const empregosInduzidos = estimate?.induced_estimated ?? row.empregos_induzidos_estimados ?? 0;
                const empregosTotais = estimate?.total_impact ?? row.emprego_total_estimado ?? 0;
                const nomeMunicipio = row.municipality_name || resp.municipality_name || resp.municipality_id;
                return (
                  <div key={resp.municipality_id} className="bg-white rounded-lg border border-amber-100 p-4 shadow-sm">
                    <h3 className="font-semibold text-gray-800 mb-3 text-sm truncate" title={nomeMunicipio}>
                      {nomeMunicipio}
                    </h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-500">Empregos diretos</span>
                        <span className="font-semibold text-gray-900">{formatQuantity(Math.round(empregosDiretos))}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-500">Indiretos (est.)</span>
                        <span className="font-medium text-gray-700">{formatQuantity(Math.round(empregosIndiretos))}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-500">Induzidos (est.)</span>
                        <span className="font-medium text-gray-700">{formatQuantity(Math.round(empregosInduzidos))}</span>
                      </div>
                      <div className="flex justify-between items-center border-t border-gray-100 pt-2">
                        <span className="font-semibold text-gray-700">Total estimado</span>
                        <span className="font-bold text-amber-700 text-base">{formatQuantity(Math.round(empregosTotais))}</span>
                      </div>
                      {estimate?.multiplier_type && (
                        <div className="flex justify-between items-center text-xs text-gray-400 pt-1 border-t border-gray-50">
                          <span>Tipo de multiplicador</span>
                          <span className="font-medium">
                            {estimate.multiplier_type === 'causal' ? 'Causal' : 'Literatura'}
                          </span>
                        </div>
                      )}
                      {row.participacao_emprego_local != null && (
                        <div className="flex justify-between items-center text-xs text-gray-400 pt-1 border-t border-gray-50">
                          <span>Participação no emprego local</span>
                          <span className="font-medium">{formatDecimal(row.participacao_emprego_local, 2)}%</span>
                        </div>
                      )}
                      {row.empregos_por_milhao_toneladas != null && (
                        <div className="flex justify-between items-center text-xs text-gray-400">
                          <span>Eficiência (emp / 1 mi t)</span>
                          <span className="font-medium">{formatDecimal(row.empregos_por_milhao_toneladas, 1)}</span>
                        </div>
                      )}
                      {/* Metadata do multiplicador para credibilidade */}
                      {resp.literature && (
                        <div className="mt-2 pt-2 border-t border-gray-100 space-y-1">
                          <p className="text-xs font-medium text-gray-500">Fonte do multiplicador</p>
                          <div className="flex justify-between items-start text-xs text-gray-400 gap-2">
                            <span className="flex-shrink-0">Referência</span>
                            <span className="font-medium text-gray-600 text-right min-w-0 break-words">{resp.literature.source}</span>
                          </div>
                          <div className="flex justify-between items-center text-xs text-gray-400">
                            <span>{t('module3.multiplier.coefficient')}</span>
                            <span className="font-medium">{formatDecimal(resp.literature.coefficient, 1)}x</span>
                          </div>
                          <div className="flex justify-between items-center text-xs text-gray-400">
                            <span>{t('module3.multiplier.range')}</span>
                            <span className="font-medium">{formatDecimal(resp.literature.range_low, 1)}x – {formatDecimal(resp.literature.range_high, 1)}x</span>
                          </div>
                          {resp.literature.confidence && (
                            <div className="flex justify-between items-center text-xs text-gray-400">
                              <span>{t('module3.multiplier.confidence')}</span>
                              <span className={`font-medium ${
                                resp.literature.confidence === 'strong' ? 'text-green-600'
                                  : resp.literature.confidence === 'moderate' ? 'text-amber-600'
                                  : 'text-red-500'
                              }`}>
                                {resp.literature.confidence === 'strong' ? 'Alta' : resp.literature.confidence === 'moderate' ? 'Moderada' : 'Baixa'}
                              </span>
                            </div>
                          )}
                          {resp.literature.region && (
                            <div className="flex justify-between items-center text-xs text-gray-400">
                              <span>{t('module3.multiplier.region')}</span>
                              <span className="font-medium">{resp.literature.region}</span>
                            </div>
                          )}
                        </div>
                      )}
                      {resp.causal && estimate?.multiplier_type === 'causal' && (
                        <div className="mt-2 pt-2 border-t border-gray-100 space-y-1">
                          <p className="text-xs font-medium text-gray-500">Estimativa causal</p>
                          <div className="flex justify-between items-center text-xs text-gray-400">
                            <span>Método</span>
                            <span className="font-medium text-gray-600">
                              {resp.causal.method === 'iv_2sls' ? 'IV / 2SLS' : resp.causal.method === 'panel_iv' ? 'Panel IV' : resp.causal.method}
                            </span>
                          </div>
                          {resp.causal.coefficient != null && (
                            <div className="flex justify-between items-center text-xs text-gray-400">
                              <span>{t('module3.multiplier.coefficient')}</span>
                              <span className="font-medium">{formatDecimal(resp.causal.coefficient, 2)}x</span>
                            </div>
                          )}
                          {resp.causal.p_value != null && (
                            <div className="flex justify-between items-center text-xs text-gray-400">
                              <span>p-valor</span>
                              <span className={`font-medium ${resp.causal.p_value < 0.05 ? 'text-green-600' : resp.causal.p_value < 0.10 ? 'text-amber-600' : 'text-red-500'}`}>
                                {resp.causal.p_value < 0.001 ? '< 0,001' : formatDecimal(resp.causal.p_value, 3)}
                              </span>
                            </div>
                          )}
                          {resp.causal.ci_lower != null && resp.causal.ci_upper != null && (
                            <div className="flex justify-between items-center text-xs text-gray-400">
                              <span>IC 95%</span>
                              <span className="font-medium">[{formatDecimal(resp.causal.ci_lower, 2)} – {formatDecimal(resp.causal.ci_upper, 2)}]</span>
                            </div>
                          )}
                          {resp.causal.n_obs != null && (
                            <div className="flex justify-between items-center text-xs text-gray-400">
                              <span>Observações</span>
                              <span className="font-medium">{resp.causal.n_obs.toLocaleString('pt-BR')}</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Simulação de choque de carga — multi-cenário */}
            <div className="bg-white rounded-lg border border-amber-100 p-4">
              <div className="mb-4">
                <h3 className="font-semibold text-gray-800 mb-2">{t('module3.shock.title')}</h3>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs text-gray-500">{t('module3.shock.quickScenarios')}</span>
                  {[-20, -10, 5, 10, 20, 50].map((pct) => (
                    <button
                      key={pct}
                      type="button"
                      onClick={() => {
                        setScenarioDeltas((prev) =>
                          prev.includes(pct) ? prev.filter((d) => d !== pct) : [...prev, pct].sort((a, b) => a - b)
                        );
                      }}
                      className={`px-2 py-0.5 rounded-full text-xs font-medium border transition-colors ${
                        scenarioDeltas.includes(pct)
                          ? pct >= 0 ? 'bg-green-100 border-green-300 text-green-700' : 'bg-red-100 border-red-300 text-red-700'
                          : 'bg-gray-50 border-gray-200 text-gray-500 hover:bg-gray-100'
                      }`}
                    >
                      {pct >= 0 ? '+' : ''}{pct}%
                    </button>
                  ))}
                  <div className="flex items-center gap-1 ml-2">
                    <input
                      type="number"
                      min={-50}
                      max={100}
                      step={5}
                      value={deltaPct}
                      onChange={(e) => setDeltaPct(Number(e.target.value))}
                      className="w-16 px-2 py-0.5 text-xs border border-gray-300 rounded-md"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        if (!scenarioDeltas.includes(deltaPct)) {
                          setScenarioDeltas((prev) => [...prev, deltaPct].sort((a, b) => a - b));
                        }
                      }}
                      className="px-2 py-0.5 text-xs rounded-md border border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100"
                    >
                      {t('module3.shock.add')}
                    </button>
                  </div>
                </div>
              </div>

              {scenarioDeltas.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-4">Selecione ao menos um cenário acima para comparar.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-gray-500 border-b border-gray-100">
                        <th className="pb-2 pr-3 font-medium">{t('module3.shock.municipality')}</th>
                        {scenarioDeltas.map((pct) => (
                          <th key={pct} className={`pb-2 px-2 font-medium text-right whitespace-nowrap ${pct >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                            {pct >= 0 ? '+' : ''}{pct}%
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {impactData.map((resp) => {
                        const row = resp.data?.[0];
                        if (!row) return null;
                        const estimate = resolveImpactEstimate(resp, useCausalEstimate);
                        const baseTotal = estimate?.total_impact ?? row.emprego_total_estimado ?? 0;
                        const nomeMunicipio = row.municipality_name || resp.municipality_name || resp.municipality_id;
                        return (
                          <tr key={resp.municipality_id} className="border-b border-gray-50 last:border-0">
                            <td className="py-2 pr-3 text-gray-700 font-medium">{nomeMunicipio}</td>
                            {scenarioDeltas.map((pct) => {
                              const delta = Math.round(baseTotal * pct / 100);
                              const positive = delta >= 0;
                              return (
                                <td key={pct} className={`py-2 px-2 text-right font-semibold tabular-nums ${positive ? 'text-green-600' : 'text-red-600'}`}>
                                  {positive ? '+' : ''}{formatQuantity(delta)}
                                </td>
                              );
                            })}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              <p className="text-xs text-gray-400 mt-3">
                {t('module3.shock.disclaimer')}
              </p>
            </div>

            {/* Link para análise causal completa no Módulo 5 */}
            <div className="mt-4 pt-3 border-t border-amber-200">
              <p className="text-xs text-gray-600 mb-2">
                {t('module3.causal.linkDescription')}
              </p>
              <button
                type="button"
                onClick={() => navigate('/dashboard/module5')}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-blue-300 bg-blue-50 text-sm font-medium text-blue-700 hover:bg-blue-100 transition-colors"
              >
                {t('module3.causal.linkButton')}
              </button>
            </div>
          </>
        )}
      </div>

      {/* ── Indicadores Descritivos de Recursos Humanos ───────────────────────── */}
      <h2 className="text-base font-semibold text-gray-700 mb-1">Indicadores Descritivos de Recursos Humanos</h2>
      <p className="text-sm text-gray-400 mb-4">Dados individuais por município — base RAIS e fontes complementares (ANTAQ, IBGE PIB)</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {INDICATORS_INFO.map((ind) => {
          const indData = indicators[ind.code];
          const hasData = indData?.data && indData.data.length > 0;
          const hasError = indData?.error;

          return (
            <ChartCard
              key={ind.code}
              title={ind.name}
              description={ind.desc}
              unit={ind.unit}
              isLoading={isLoading}
            >
              {hasData ? (
                <BarChart
                  labels={indData.data.slice(0, 10).map((d: any) => getLabelFromData(d))}
                  datasets={[{
                    label: ind.unit,
                    data: indData.data.slice(0, 10).map((d: any) => getValueFromData(d, ind.valueField)),
                  }]}
                  yAxisLabel={ind.unit}
                  horizontal
                  valueFormat={getIndicatorFormat(ind.code)}
                  {...(ind.code === 'IND-3.02' && {
                    maxValue: 100,
                    referenceLine: { value: 50, label: 'Paridade (50%)', color: '#9ca3af' },
                  })}
                />
              ) : (
                renderDataStatus(hasError)
              )}
            </ChartCard>
          );
        })}
      </div>

      {/* ── Indicadores Agrupados: Capital Humano ──────────────────────────────── */}
      <h2 className="text-base font-semibold text-gray-700 mb-4">Perfil do Capital Humano Portuário</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* IND-3.03 — Paridade de Gênero por Categoria Profissional (CBO da RAIS) */}
        <ChartCard
          title="Paridade de Gênero por Categoria (CBO)"
          description="Percentual de mulheres por categoria profissional derivada do código CBO-2002 da RAIS"
          unit="%"
          isLoading={isLoading}
        >
          {(() => {
            const raw = indicators['IND-3.03']?.data;
            if (!Array.isArray(raw) || raw.length === 0) {
              return renderDataStatus(indicators['IND-3.03']?.error, chartMunicipioHint);
            }
            const catMap = new Map<string, { sum: number; count: number }>();
            for (const row of raw) {
              const cat = String(row?.categoria || '').toUpperCase().trim();
              if (!cat) continue;
              const val = toNumber(row?.percentual_feminino);
              const prev = catMap.get(cat) || { sum: 0, count: 0 };
              catMap.set(cat, { sum: prev.sum + val, count: prev.count + 1 });
            }
            const categories = ['GESTAO_TECNICO', 'ADMINISTRATIVO', 'OPERACIONAL'];
            const labels = categories.map((c) => CATEGORIA_LABELS[c] || c);
            const values = categories.map((c) => {
              const entry = catMap.get(c);
              return entry && entry.count > 0 ? Math.round((entry.sum / entry.count) * 100) / 100 : 0;
            });
            return (
              <BarChart
                labels={labels}
                datasets={[{
                  label: '% Feminino',
                  data: values,
                  backgroundColor: '#ec4899',
                }]}
                yAxisLabel="% Feminino"
                valueFormat="percent"
                maxValue={100}
                referenceLine={{ value: 50, label: 'Paridade (50%)', color: '#9ca3af' }}
              />
            );
          })()}
        </ChartCard>

        {/* IND-3.09 — Distribuição por Escolaridade (campo grau_instrucao da RAIS) */}
        <ChartCard
          title="Distribuição por Escolaridade"
          description="Distribuição percentual dos trabalhadores portuários por nível de escolaridade"
          unit="%"
          isLoading={isLoading}
        >
          {(() => {
            const raw = indicators['IND-3.09']?.data;
            if (!Array.isArray(raw) || raw.length === 0) {
              return renderDataStatus(indicators['IND-3.09']?.error, chartMunicipioHint);
            }
            // Agregar por escolaridade (soma de qtd entre municípios)
            const escolMap = new Map<string, number>();
            let totalGeral = 0;
            for (const row of raw) {
              const rawEscol = normalizeEscolaridade(row?.grau_instrucao);
              if (!rawEscol) continue;
              const qtd = toNumber(row?.qtd);
              escolMap.set(rawEscol, (escolMap.get(rawEscol) || 0) + qtd);
              totalGeral += qtd;
            }
            if (totalGeral === 0) {
              return renderDataStatus(undefined, 'Sem dados de escolaridade disponíveis para os filtros atuais.');
            }
            const labels = ESCOLARIDADE_CATEGORIES.map((c) => c.label);
            const values = ESCOLARIDADE_CATEGORIES.map((c) => {
              const qtd = escolMap.get(c.key) || 0;
              return Math.round((qtd / totalGeral) * 10000) / 100;
            });
            return (
              <BarChart
                labels={labels}
                datasets={[{
                  label: '% dos trabalhadores',
                  data: values,
                  backgroundColor: '#6366f1',
                }]}
                yAxisLabel="% do total"
                valueFormat="percent"
              />
            );
          })()}
        </ChartCard>
      </div>

      {/* ── Novos Gráficos de Remuneração ─────────────────────────────────────── */}
      <h2 className="text-base font-semibold text-gray-700 mb-1">Recortes de Remuneração</h2>
      <p className="text-sm text-gray-400 mb-4">
        Análise de equidade salarial por gênero, raça e escolaridade — indicadores relevantes para governança ESG e due diligence trabalhista
      </p>

      <div className="grid grid-cols-1 gap-6">
        <ChartCard
          title="Gráfico 1 - Remuneração média por sexo e grau de instrução"
          description="Eixo X: escolaridade. Eixo Y: remuneração média (R$)."
          unit="R$"
          isLoading={isLoading}
        >
          {Array.isArray(indicators['IND-3.13']?.data) &&
          indicators['IND-3.13']?.data.length > 0 &&
          remEscolSexoRows.length > 0 ? (
            <BarChart
              labels={chart1Data.labels}
              datasets={[
                { label: 'Masculino', data: chart1Data.masculino, backgroundColor: '#3b82f6' },
                { label: 'Feminino', data: chart1Data.feminino, backgroundColor: '#ec4899' },
              ]}
              yAxisLabel="Remuneração média (R$)"
              valueFormat="currency-compact"
              height="h-80"
            />
          ) : (
            renderDataStatus(indicators['IND-3.13']?.error, chartMunicipioHint)
          )}
        </ChartCard>

        <ChartCard
          title="Gráfico 2 - Remuneração média por cor/raça e sexo"
          description="Eixo X: cor/raça. Eixo Y: remuneração média (R$)."
          unit="R$"
          isLoading={isLoading}
        >
          {Array.isArray(indicators['IND-3.14']?.data) &&
          indicators['IND-3.14']?.data.length > 0 &&
          remRacaSexoRows.length > 0 ? (
            <BarChart
              labels={chart2Data.labels}
              datasets={[
                { label: 'Masculino', data: chart2Data.masculino, backgroundColor: '#3b82f6' },
                { label: 'Feminino', data: chart2Data.feminino, backgroundColor: '#ec4899' },
              ]}
              yAxisLabel="Remuneração média (R$)"
              valueFormat="currency-compact"
              height="h-80"
            />
          ) : (
            renderDataStatus(indicators['IND-3.14']?.error, chartMunicipioHint)
          )}
        </ChartCard>

        <ChartCard
          title="Gráfico 3 - Remuneração por escolaridade, raça/cor e sexo"
          description="Filtro de sexo com combinações de escolaridade e raça/cor no eixo X."
          unit="R$"
          isLoading={isLoading}
        >
          {Array.isArray(indicators['IND-3.15']?.data) &&
          indicators['IND-3.15']?.data.length > 0 &&
          remEscolRacaSexoRows.length > 0 ? (
            <>
              <div className="mb-3 flex items-center justify-end gap-2">
                <label htmlFor="sexoChart3" className="text-sm text-gray-500">Sexo:</label>
                <select
                  id="sexoChart3"
                  value={selectedSexoChart3}
                  onChange={(e) => setSelectedSexoChart3(e.target.value as SexoOption)}
                  className="px-2 py-1 text-sm border border-gray-300 rounded-md bg-white"
                >
                  <option value="MASCULINO">Masculino</option>
                  <option value="FEMININO">Feminino</option>
                </select>
              </div>

              <BarChart
                labels={chart3Data.labels}
                datasets={[
                  {
                    label: selectedSexoChart3 === 'MASCULINO' ? 'Masculino' : 'Feminino',
                    data: chart3Data.values,
                    backgroundColor: selectedSexoChart3 === 'MASCULINO' ? '#2563eb' : '#db2777',
                  },
                ]}
                yAxisLabel="Remuneração média (R$)"
                valueFormat="currency-compact"
                height="h-[32rem]"
              />
            </>
          ) : (
            renderDataStatus(indicators['IND-3.15']?.error, chartMunicipioHint)
          )}
        </ChartCard>

        <ChartCard
          title="Gráfico 4 - Remuneração média com média geral nacional"
          description="Barras de remuneração média por município com linha horizontal da média nacional."
          unit="R$"
          isLoading={isLoading}
        >
          {Array.isArray(indicators['IND-3.16']?.data) && indicators['IND-3.16']?.data.length > 0 ? (
            <>
              <BarChart
                labels={chart4Data.labels}
                datasets={[
                  {
                    label: 'Remuneração média (R$)',
                    data: chart4Data.values,
                    backgroundColor: '#0ea5e9',
                  },
                ]}
                yAxisLabel="Remuneração média (R$)"
                valueFormat="currency-compact"
                height="h-80"
                referenceLine={chart4Data.mediaNacional != null ? {
                  value: chart4Data.mediaNacional,
                  label: 'Média nacional',
                } : undefined}
              />

              {chart4Data.mediaNacional != null && (
                <p className="text-xs text-gray-500 mt-2">
                  Linha de referência (média geral nacional): {formatCurrency(chart4Data.mediaNacional)}
                </p>
              )}
            </>
          ) : (
            renderDataStatus(indicators['IND-3.16']?.error, chartMunicipioHint)
          )}
        </ChartCard>
      </div>
    </div>
  );
}
