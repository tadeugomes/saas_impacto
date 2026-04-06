import { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertCircle } from 'lucide-react';
import { ContribuicaoFiscalSection } from '../../../components/fiscalElasticity/ContribuicaoFiscalSection';

import { FilterBar } from '../../../components/filters/FilterBar';
import { MUNICIPIOS_PORTUARIOS } from '../../../components/filters/MunicipioSelector';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { ChartCard } from '../../../components/charts/ChartCard';
import { BarChart } from '../../../components/charts/BarChart';
import { LineChart } from '../../../components/charts/LineChart';
import { ExportButton } from '../../../components/common/ExportButton';
import { useFilterStore } from '../../../store/filterStore';
import {
  type MunicipioLabelMap,
  isLikelyIdNameMismatch,
  normalizeMunicipioId,
  toMunicipioLabel,
} from '../../../utils/municipioLabels';
import { indicatorsService } from '../../../api/indicators';
import { getIndicatorFormat } from '../../../utils/chartFormats';
import { useI18n } from '../../../i18n/I18nContext';
import { useIndicatorLabel } from '../../../i18n/indicatorTranslations';
import type { IndicatorResponse } from '../../../types/api';

type IndicatorRow = Record<string, unknown>;
type ModuleIndicatorResponse = IndicatorResponse<IndicatorRow>;
type IndicatorMap = Record<string, ModuleIndicatorResponse>;

type IndicatorGroup = 'tributacao' | 'percapita' | 'desempenho' | 'causal';

// Módulo 6 usa janela temporal fixa (2018-2023) — TREND_YEARS_BACK não é mais usado
// const TREND_YEARS_BACK = 6;

const INDICATORS_INFO = [
  {
    code: 'IND-6.01',
    name: 'ICMS Municipal',
    unit: 'R$',
    desc: 'Cota-parte do ICMS recebida pelo município (FINBRA/SICONFI). Nota: o ICMS tem incidência mínima em operações portuárias — o tributo relevante para portos é o ISS.',
    valueField: 'arrecadacao_icms',
    group: 'tributacao',
    interpretation:
      'O ICMS vem principalmente da circulação de mercadorias e indústria local. Em municípios portuários, pode crescer junto com a atividade logística associada ao porto, mas não é atribuível diretamente à operação de carga.',
    question: 'O ICMS municipal cresce nos anos de maior movimentação portuária? (associação indicativa)',
  },
  {
    code: 'IND-6.02',
    name: 'ISS Municipal Total',
    unit: 'R$',
    desc: 'ISS arrecadado pelo município de todos os prestadores de serviço (FINBRA/SICONFI). Inclui serviços portuários e não-portuários.',
    valueField: 'arrecadacao_iss',
    group: 'tributacao',
    interpretation:
      'O ISS municipal agrega todos os serviços locais. Para isolar a contribuição direta do porto ao ISS, veja "Participação do Porto no ISS Municipal" na seção Contribuição Fiscal Direta acima.',
    question: 'O ISS municipal total evolui junto com o volume de carga movimentada no porto?',
  },
  {
    code: 'IND-6.03',
    name: 'Receita Total Municipal',
    unit: 'R$',
    desc: 'Receitas correntes totais do município (FINBRA/SICONFI). Base fiscal completa, inclui tributos e transferências intergovernamentais.',
    valueField: 'receita_total',
    group: 'tributacao',
    interpretation:
      'Base fiscal agregada do município. Útil para comparar escala de arrecadação entre municípios portuários.',
    question: 'A receita municipal total acompanha o crescimento portuário?',
  },
  {
    code: 'IND-6.04',
    name: 'Receita Municipal per Capita',
    unit: 'R$/hab',
    desc: 'Receita corrente total dividida pela população estimada. Neutraliza diferenças de porte entre municípios para comparação mais justa.',
    valueField: 'receita_per_capita',
    group: 'percapita',
    interpretation:
      'Permite comparar capacidade fiscal por pessoa ao longo do tempo, reduzindo o viés de porte populacional.',
    question: 'A receita por habitante é maior em municípios com mais atividade portuária?',
  },
  {
    code: 'IND-6.05',
    name: 'Crescimento Anual da Receita',
    unit: '%',
    desc: 'Variação percentual da receita corrente em relação ao ano anterior.',
    valueField: 'crescimento_receita_pct',
    group: 'desempenho',
    interpretation:
      'Não é causal isoladamente. Use junto da tendência de tonelagem e da análise causal do Módulo 5 para inferir atribuição.',
    question: 'A receita municipal cresceu mais nos anos de maior movimentação portuária?',
  },
  {
    code: 'IND-6.06',
    name: 'ISS Municipal por Tonelada',
    unit: 'R$/ton',
    desc: 'ISS total do município (FINBRA) ÷ tonelagem portuária ANTAQ. Proxy do retorno fiscal por tonelada usando arrecadação municipal. Nota: difere do ISS pago diretamente pelo operador, que está na seção Contribuição Fiscal Direta.',
    valueField: 'iss_por_tonelada',
    group: 'desempenho',
    interpretation:
      'Quanto ISS municipal é gerado por tonelada movimentada. Inclui todo o ISS do município — não apenas o ISS do operador portuário. Portos em municípios com alta base de serviços terão valores mais altos.',
    question: 'Qual o retorno fiscal municipal por tonelada movimentada no porto?',
  },
  {
    code: 'IND-6.07',
    name: 'Receita Fiscal Total (ICMS + ISS)',
    unit: 'R$',
    desc: 'Soma do ICMS e ISS arrecadados pelo município (FINBRA/SICONFI). Agrega os dois principais tributos municipais ligados à atividade econômica.',
    valueField: 'receita_fiscal_total',
    group: 'tributacao',
    interpretation:
      'Indicador mais abrangente do impacto fiscal local. Combina ICMS (mercadorias e indústria) e ISS (serviços), capturando os dois canais fiscais associados à dinâmica portuária.',
    question: 'A arrecadação de tributos municipais cresceu com a atividade do porto?',
  },
  {
    code: 'IND-6.08',
    name: 'Receita Fiscal (ICMS+ISS) per Capita',
    unit: 'R$/hab',
    desc: 'Soma ICMS+ISS por habitante. Permite comparar municípios de portes diferentes.',
    valueField: 'receita_fiscal_per_capita',
    group: 'percapita',
    interpretation:
      'Avalia exposição fiscal por residente, não apenas pelo tamanho absoluto do município. Municípios pequenos com porto grande tendem a ter valores elevados.',
    question: 'A receita fiscal por habitante é maior onde os portos são mais ativos?',
  },
  {
    code: 'IND-6.09',
    name: 'Receita Fiscal (ICMS+ISS) por Tonelada',
    unit: 'R$/ton',
    desc: 'Receita fiscal total (ICMS+ISS) ÷ tonelagem portuária. Retorno fiscal amplo por unidade de carga.',
    valueField: 'receita_fiscal_por_tonelada',
    group: 'desempenho',
    interpretation:
      'Mede o retorno fiscal combinado (ICMS + ISS) por tonelada movimentada, evitando comparar municípios só por porte absoluto.',
    question: 'Qual o retorno fiscal total por tonelada movimentada neste porto?',
  },
  {
    code: 'IND-6.10',
    name: 'Correlação: Tonelagem × Receita Fiscal',
    unit: 'coef.',
    desc: 'Coeficiente de correlação (Pearson) entre a série histórica de tonelagem e receita fiscal do município (2018-2023).',
    valueField: 'correlacao',
    valueAlias: 'correlacao_tonelagem_receita_fiscal',
    group: 'causal',
    interpretation:
      'Próximo de +1: tonelagem e receita crescem juntos. Próximo de 0: sem associação clara. É uma correlação histórica — não implica causalidade.',
    question: 'Tonelagem e receita fiscal se movem na mesma direção historicamente neste porto?',
  },
  {
    code: 'IND-6.11',
    name: 'Sensibilidade: Tonelagem × Receita Fiscal',
    unit: 'coef.',
    desc: 'Elasticidade log-log histórica entre tonelagem portuária e receita fiscal municipal (2018-2023).',
    valueField: 'elasticidade',
    valueAlias: 'elasticidade_tonelagem_receita_fiscal',
    group: 'causal',
    interpretation:
      'Elasticidade > 1: tonelagem responde mais que proporcionalmente às variações fiscais. Entre 0 e 1: resposta menor. Associação histórica — não implica causalidade.',
    question: 'Quanto a tonelagem se associa às variações da receita fiscal neste porto?',
  },
] as const;

type IndicatorInfo = {
  code: string;
  name: string;
  unit: string;
  desc: string;
  valueField: string;
  group: IndicatorGroup;
  interpretation: string;
  question: string;
  valueAlias?: string;
};

const INDICATORS_BY_GROUP: Record<IndicatorGroup, IndicatorInfo[]> = INDICATORS_INFO.reduce(
  (acc, indicator) => {
    if (!acc[indicator.group]) {
      acc[indicator.group] = [];
    }
    acc[indicator.group].push(indicator);
    return acc;
  },
  {} as Record<IndicatorGroup, IndicatorInfo[]>,
);

const createEmptyIndicatorResponse = (codigoIndicador: string): ModuleIndicatorResponse => ({
  codigo_indicador: codigoIndicador,
  nome: codigoIndicador,
  unidade: '',
  unctad: false,
  data: [],
});

function parseNumericValue(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

function parseYear(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return Math.trunc(value);
  }

  if (typeof value === 'string') {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

function getMetricValue(row: IndicatorRow, metric: IndicatorInfo): number | null {
  const candidates = [
    metric.valueAlias,
    metric.valueField,
    'valor',
    'total',
  ].filter((candidate): candidate is string => Boolean(candidate));

  for (const candidate of candidates) {
    const parsed = parseNumericValue(row[candidate]);
    if (parsed !== null) {
      return parsed;
    }
  }

  return null;
}

function getLabelFromData(item: IndicatorRow, labels: MunicipioLabelMap): string {
  const idMunicipio = normalizeMunicipioId(item.id_municipio);
  if (idMunicipio) {
    return toMunicipioLabel(idMunicipio, labels);
  }

  return (
    (typeof item.nome_municipio === 'string' && item.nome_municipio) ||
    (typeof item.porto === 'string' && item.porto) ||
    (typeof item.id_instalacao === 'string' && item.id_instalacao) ||
    'N/A'
  );
}

function getIndicatorRows(response: ModuleIndicatorResponse | undefined): IndicatorRow[] {
  if (!response) {
    return [];
  }

  return response.data.filter((item): item is IndicatorRow => item !== null && typeof item === 'object');
}

function isSingleMunicipioSeries(rows: Array<{ row: IndicatorRow; value: number }>): boolean {
  const ids = new Set<string>();

  for (const { row } of rows) {
    const id = normalizeMunicipioId(row.id_municipio) || '';
    ids.add(id || '');
  }

  const idsWithoutEmpty = ids.size === 1 ? (ids.has('') ? 1 : 1) : ids.size;
  return idsWithoutEmpty === 1;
}

function buildTrendRows(rows: Array<{ row: IndicatorRow; value: number }>) {
  const byYear = rows
    .map((entry) => ({ ...entry, ano: parseYear(entry.row.ano) }))
    .filter((entry): entry is { row: IndicatorRow; value: number; ano: number } => entry.ano !== null);

  const uniqueYears = new Set(byYear.map((entry) => entry.ano));
  const hasMultipleYears = uniqueYears.size > 1;
  const singleMunicipio = isSingleMunicipioSeries(byYear);

  if (!hasMultipleYears || !singleMunicipio) {
    return null;
  }

  byYear.sort((a, b) => a.ano - b.ano);

  return {
    labels: byYear.map((entry) => String(entry.ano)),
    values: byYear.map((entry) => entry.value),
  };
}

function extractWarningsSummary(response: ModuleIndicatorResponse): string[] {
  if (!response.warnings || response.warnings.length === 0) {
    return [];
  }

  return response.warnings.slice(0, 2).map((warning) => warning.mensagem);
}

function GroupTitle({ title, isOpen, onToggle }: { title: string; isOpen: boolean; onToggle: () => void }) {
  const { t } = useI18n();
  return (
    <button
      type="button"
      className="w-full flex items-center justify-between text-left"
      onClick={onToggle}
    >
      <h3 className="font-semibold text-gray-900">{title}</h3>
      <span className="text-sm text-indigo-600">{isOpen ? t('common.hide') : t('common.show')}</span>
    </button>
  );
}

export function Module6View() {
  const { t } = useI18n();
  const tInd = useIndicatorLabel();
  const { selectedMunicipio } = useFilterStore();
  const [indicators, setIndicators] = useState<IndicatorMap>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [municipioLabelIndex, setMunicipioLabelIndex] = useState<MunicipioLabelMap>({});
  const [openGroups, setOpenGroups] = useState<Record<IndicatorGroup, boolean>>({
    tributacao: true,
    percapita: true,
    desempenho: true,
    causal: true,
  });

  const toggleGroup = useCallback((group: IndicatorGroup) => {
    setOpenGroups((current) => ({ ...current, [group]: !current[group] }));
  }, []);

  const localizedIndicatorsByGroup = useMemo(() => {
    const result = {} as Record<IndicatorGroup, IndicatorInfo[]>;
    for (const [group, items] of Object.entries(INDICATORS_BY_GROUP)) {
      result[group as IndicatorGroup] = items.map(ind => {
        const { name, desc } = tInd(ind.code, ind.name, ind.desc);
        return { ...ind, name, desc };
      });
    }
    return result;
  }, [tInd]);

  const resolveMunicipioLabels = useCallback(
    async (rawIds: string[]) => {
      const ids = Array.from(
        new Set(
          rawIds
            .map((id) => normalizeMunicipioId(id))
            .filter((id) => id && id.length >= 2 && !municipioLabelIndex[id]),
        ),
      );

      if (!ids.length) {
        return;
      }

      try {
        const response = await indicatorsService.getMunicipioLookup(ids);
        const nextLabels: MunicipioLabelMap = {};

        response.municipios.forEach((item) => {
          const municipioId = normalizeMunicipioId(item.id_municipio);
          const nomeMunicipio = item.nome_municipio?.trim();
          if (municipioId && nomeMunicipio) {
            nextLabels[municipioId] = nomeMunicipio;
          }
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

  const municipiosFromIndicators = useMemo(() => {
    const lookup: MunicipioLabelMap = {};
    Object.values(indicators).forEach((indicator) => {
      indicator.data.forEach((itemUnknown) => {
        if (!itemUnknown || typeof itemUnknown !== 'object') {
          return;
        }

        const item = itemUnknown as IndicatorRow;
        const id = normalizeMunicipioId(item.id_municipio);
        const nome = item.nome_municipio;

        if (
          id &&
          typeof nome === 'string' &&
          nome.trim() &&
          !isLikelyIdNameMismatch(id, nome) &&
          !normalizeMunicipioId(nome)
        ) {
          lookup[id] = nome.trim();
        }
      });
    });

    return lookup;
  }, [indicators]);

  const municipioLabels = useMemo(
    () => ({ ...municipioLabelIndex, ...municipiosFromIndicators }),
    [municipioLabelIndex, municipiosFromIndicators],
  );

  const allMunicipioIds = useMemo(() => {
    const ids = new Set<string>(Object.keys(municipioLabels));

    Object.values(indicators).forEach((indicator) => {
      indicator.data.forEach((itemUnknown) => {
        if (!itemUnknown || typeof itemUnknown !== 'object') {
          return;
        }
        const id = normalizeMunicipioId((itemUnknown as IndicatorRow).id_municipio);
        if (id) {
          ids.add(id);
        }
      });
    });

    return Array.from(ids);
  }, [indicators, municipioLabels]);

  useEffect(() => {
    void resolveMunicipioLabels(allMunicipioIds);
  }, [allMunicipioIds, resolveMunicipioLabels]);

  useEffect(() => {
    const loadIndicators = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Janela temporal fixa: 2018-2023 (dados mais completos).
        // Módulo 6 não usa seletor de ano — os indicadores precisam de séries multi-ano.
        const ANO_INICIO = 2018;
        const ANO_FIM = 2023;

        // Params para indicadores tributação/percapita (FINBRA municipal)
        const paramsFinbra = selectedMunicipio
          ? { id_municipio: selectedMunicipio, ano_inicio: ANO_INICIO, ano_fim: ANO_FIM }
          : { ano: ANO_FIM };

        // Params para desempenho (ISS/ton, receita/ton) — precisam de múltiplos anos
        const paramsDesempenho = selectedMunicipio
          ? { id_municipio: selectedMunicipio, ano_inicio: ANO_INICIO, ano_fim: ANO_FIM }
          : { ano: ANO_FIM };

        // Params para causal (correlação, elasticidade) — precisam de ≥5 anos
        // Sem município selecionado: retorna ranking dos top municípios
        const paramsCausal = selectedMunicipio
          ? { id_municipio: selectedMunicipio, min_anos: 5 }
          : { min_anos: 5 };

        const promises = INDICATORS_INFO.map((ind) => {
          const isCausal = ind.code === 'IND-6.10' || ind.code === 'IND-6.11';
          const isDesempenho = ind.group === 'desempenho';
          const params = isCausal
            ? paramsCausal
            : isDesempenho
              ? paramsDesempenho
              : paramsFinbra;

          return indicatorsService
            .queryIndicator<IndicatorRow>({ codigo_indicador: ind.code, params })
            .catch(() => createEmptyIndicatorResponse(ind.code));
        });

        const results = await Promise.all(promises);
        const nextIndicators: IndicatorMap = {};

        results.forEach((result, index) => {
          const code = INDICATORS_INFO[index].code;
          nextIndicators[code] = result;
        });

        setIndicators(nextIndicators);
      } catch (err: unknown) {
        const errorResponse = err as { response?: { data?: { detail?: unknown } } };
        const msg = errorResponse?.response?.data?.detail;
        setError(typeof msg === 'string' ? msg : t('common.errorLoading'));
      } finally {
        setIsLoading(false);
      }
    };

    void loadIndicators();
  }, [selectedMunicipio]);

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">{t('module6.title')}</h1>
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('module6.title')}</h1>
          <p className="text-gray-500 mt-1">
            {t('module6.subtitle')}
          </p>
        </div>
        <ExportButton moduleCode="6" />
      </div>

      {/* Ano não se aplica aos indicadores de Módulo 6 — dados são multi-ano ou independentes */}
      <FilterBar selectorMode="municipio" showYear={false} />

      {error && <ErrorAlert message={error} className="mb-6" />}

      {/* ── Contribuição Fiscal Direta ────────────────────────────────────── */}
      <div className="mt-6 mb-6">
        <section className="card space-y-4">
          <details open>
            <summary className="w-full flex items-center justify-between text-left cursor-pointer">
              <h2 className="text-base font-semibold text-gray-800">
                Contribuição Fiscal Direta dos Portos
              </h2>
              <span className="text-xs text-gray-400 ml-2">
                ISS + tributos federais por operadores — DFs 2018-2024
              </span>
            </summary>
            <div className="mt-4">
              <ContribuicaoFiscalSection />
            </div>
          </details>
        </section>
      </div>

      {/* ── Cabeçalho contextual: indica qual porto está sendo analisado ─── */}
      {(() => {
        const portoLabel = selectedMunicipio
          ? (MUNICIPIOS_PORTUARIOS.find((p) => p.id_municipio === selectedMunicipio)?.label ?? selectedMunicipio)
          : null;
        return (
          <div className="flex items-center justify-between mb-2 mt-2">
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-gray-700">
                Indicadores de Finanças Municipais
              </h2>
              {portoLabel ? (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#0f2d52] text-white">
                  {portoLabel}
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
                  Todos os portos · ano base 2023
                </span>
              )}
            </div>
            {portoLabel && (
              <p className="text-xs text-gray-400">
                Dados do município onde o porto está localizado · FINBRA/SICONFI 2018-2023
              </p>
            )}
          </div>
        );
      })()}

      <div className="space-y-6">
        {Object.entries(localizedIndicatorsByGroup).map(([group, indicatorsOfGroup]) => {
          const groupOpen = openGroups[group as IndicatorGroup];
          const groupTitle =
            group === 'tributacao'
              ? t('module6.group.taxation')
              : group === 'percapita'
                ? t('module6.group.perCapita')
                : group === 'desempenho'
                  ? t('module6.group.performance')
                  : t('module6.group.causal');

          return (
            <section key={group} className="card space-y-4">
              <GroupTitle
                title={groupTitle}
                isOpen={!!groupOpen}
                onToggle={() => toggleGroup(group as IndicatorGroup)}
              />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {groupOpen &&
                  indicatorsOfGroup.map((ind) => {
                    const response = indicators[ind.code];
                    const rows = getIndicatorRows(response);
                    const validRows = rows
                      .map((row) => ({ row, value: getMetricValue(row, ind) }))
                      .filter((entry): entry is { row: IndicatorRow; value: number } => entry.value !== null);

                    const warnings = extractWarningsSummary(response);
                    const trend = buildTrendRows(validRows);
                    const chartDataRows = trend
                      ? validRows
                          .map((entry) => ({ row: entry.row, value: entry.value, year: parseYear(entry.row.ano) }))
                          .filter((entry): entry is { row: IndicatorRow; value: number; year: number } => entry.year !== null)
                          .sort((a, b) => a.year - b.year)
                      : validRows
                          .sort((a, b) => b.value - a.value)
                          .slice(0, 10);

                    const hasData = validRows.length > 0;

                    return (
                      <ChartCard
                        key={ind.code}
                        title={ind.name}
                        description={ind.desc}
                        unit={ind.unit}
                        extraInfo={
                          warnings.length
                            ? `Observações de validação: ${warnings.join(' | ')}`
                            : ind.interpretation
                        }
                      >
                        {hasData ? (
                          trend ? (
                            <LineChart
                              labels={trend.labels}
                              datasets={[
                                {
                                  label: ind.unit,
                                  data: trend.values,
                                },
                              ]}
                              yAxisLabel={ind.unit}
                              yAxisFormat={getIndicatorFormat(ind.code)}
                              yAxisBeginAtZero={ind.group === 'causal'}
                            />
                          ) : (
                            <BarChart
                              labels={chartDataRows.map((entry) => getLabelFromData(entry.row, municipioLabels))}
                              datasets={[
                                {
                                  label: ind.unit,
                                  data: chartDataRows.map((entry) => entry.value),
                                },
                              ]}
                              yAxisLabel={ind.unit}
                              valueFormat={getIndicatorFormat(ind.code)}
                              horizontal
                            />
                          )
                        ) : (
                          <div className="h-64 flex flex-col items-center justify-center text-center gap-2 px-6">
                            {(ind.group === 'desempenho' || ind.group === 'causal') && !selectedMunicipio ? (
                              <>
                                <p className="text-sm font-medium text-gray-600">
                                  Selecione um porto no filtro acima
                                </p>
                                <p className="text-xs text-gray-400">
                                  {ind.group === 'causal'
                                    ? 'Este indicador requer a série histórica de um porto específico (mínimo 5 anos).'
                                    : 'Selecione um porto para visualizar o retorno fiscal por tonelada ao longo do tempo.'}
                                </p>
                              </>
                            ) : (
                              <p className="text-sm text-gray-500">
                                {ind.group === 'causal'
                                  ? 'Sem observações suficientes para o cálculo (n < 5 anos com dados completos).'
                                  : 'Sem dados disponíveis para este porto no período 2018-2023.'}
                              </p>
                            )}
                          </div>
                        )}
                        <div className="mt-3 flex items-start gap-2 text-xs text-gray-500">
                          <AlertCircle className="w-4 h-4 mt-0.5 text-indigo-500" />
                          <p>{ind.question}</p>
                        </div>
                      </ChartCard>
                    );
                  })}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
