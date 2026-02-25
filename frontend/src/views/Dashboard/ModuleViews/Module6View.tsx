import { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertCircle } from 'lucide-react';

import { FilterBar } from '../../../components/filters/FilterBar';
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
import type { IndicatorResponse } from '../../../types/api';

type IndicatorRow = Record<string, unknown>;
type ModuleIndicatorResponse = IndicatorResponse<IndicatorRow>;
type IndicatorMap = Record<string, ModuleIndicatorResponse>;

type IndicatorGroup = 'tributacao' | 'percapita' | 'desempenho' | 'causal';

const TREND_YEARS_BACK = 6;

const INDICATORS_INFO = [
  {
    code: 'IND-6.01',
    name: 'Arrecadação de ICMS',
    unit: 'R$',
    desc: 'ICMS arrecadado total no município.',
    valueField: 'arrecadacao_icms',
    group: 'tributacao',
    interpretation:
      'Mostra a capacidade fiscal municipal. Crescimentos fortes em anos de pico portuário sugerem potencial vínculo com atividade logística.',
    question: 'Como uma melhora do porto X se reflete na arrecadação do município Y?',
  },
  {
    code: 'IND-6.02',
    name: 'Arrecadação de ISS',
    unit: 'R$',
    desc: 'ISS arrecadada total no município.',
    valueField: 'arrecadacao_iss',
    group: 'tributacao',
    interpretation:
      'Indicador de dinâmica da prestação de serviços. Em municípios com base portuária, sobe com serviços logísticos e manutenção.',
    question: 'Qual parte do movimento econômico local está vinculada ao serviço associado ao porto?',
  },
  {
    code: 'IND-6.03',
    name: 'Receita Total Municipal',
    unit: 'R$',
    desc: 'Receita municipal total conforme FINBRA.',
    valueField: 'receita_total',
    group: 'tributacao',
    interpretation:
      'Base fiscal agregada do município. Útil para comparar escala de arrecadação entre municípios.',
    question: 'O município com mais atividade portuária também concentra mais capacidade fiscal?',
  },
  {
    code: 'IND-6.04',
    name: 'Receita per Capita',
    unit: 'R$/hab',
    desc: 'Receita per capita.',
    valueField: 'receita_per_capita',
    group: 'percapita',
    interpretation:
    'Permite comparar capacidade fiscal por pessoa no tempo e reduzir viés de porte populacional.',
    question: 'Como a carga econômica do porto altera a arrecadação disponível por habitante?',
  },
  {
    code: 'IND-6.05',
    name: 'Crescimento da Receita',
    unit: '%',
    desc: 'Variação percentual anual da receita.',
    valueField: 'crescimento_receita_pct',
    group: 'desempenho',
    interpretation:
      'Não é causal isoladamente. Use junto de tendência de tonelagem e análise causal para inferir atribuição.',
    question: 'A arrecadação cresce mais nos anos com maior movimento portuário?',
  },
  {
    code: 'IND-6.06',
    name: 'ICMS por Tonelada',
    unit: 'R$/ton',
    desc: 'Eficiência fiscal da movimentação portuária.',
    valueField: 'icms_por_tonelada',
    group: 'desempenho',
    interpretation:
      'Quanto ICMS é gerado por tonelada movimentada. Útil para avaliar retorno fiscal da operação.',
    question: 'Quanto de ICMS o município ganha em média por tonelada movimentada?',
  },
  {
    code: 'IND-6.07',
    name: 'Receita Fiscal Total',
    unit: 'R$',
    desc: 'Soma de ICMS + ISS por município.',
    valueField: 'receita_fiscal_total',
    group: 'tributacao',
    interpretation:
      'Indicador mais comparável para impacto fiscal total ligado à atividade econômica local.',
    question: 'Qual o impacto fiscal total potencialmente associado à dinâmica portuária?',
  },
  {
    code: 'IND-6.08',
    name: 'Receita Fiscal per Capita',
    unit: 'R$/hab',
    desc: 'Receita fiscal por habitante.',
    valueField: 'receita_fiscal_per_capita',
    group: 'percapita',
    interpretation:
      'Permite avaliar exposição fiscal por residente, não apenas pelo tamanho absoluto do município.',
    question: 'O crescimento do movimento portuário melhora a arrecadação fiscal por habitante?',
  },
  {
    code: 'IND-6.09',
    name: 'Receita Fiscal por Tonelada',
    unit: 'R$/ton',
    desc: 'Receita fiscal total sobre movimentação física.',
    valueField: 'receita_fiscal_por_tonelada',
    group: 'desempenho',
    interpretation:
      'Mede retorno fiscal da operação portuária por unidade de tonelagem, evitando comparar municípios só por porte.',
    question: 'A expansão do porto aumenta retorno fiscal por tonelada no município Y?',
  },
  {
    code: 'IND-6.10',
    name: 'Correlação Tonelagem e Receita Fiscal',
    unit: 'coef.',
    desc: 'Associação estatística entre tonelagem e receita fiscal.',
    valueField: 'correlacao',
    valueAlias: 'correlacao_tonelagem_receita_fiscal',
    group: 'causal',
    interpretation:
      'Sem causalidade: mede associação (ou direção conjunta), não prova que a tonelagem causou a variação fiscal.',
    question: 'O município é sensível à movimentação? (o sinal indica direção associativa).',
  },
  {
    code: 'IND-6.11',
    name: 'Elasticidade Tonelagem/Receita Fiscal',
    unit: 'elastic.',
    desc: 'Elasticidade log-log histórica.',
    valueField: 'elasticidade',
    valueAlias: 'elasticidade_tonelagem_receita_fiscal',
    group: 'causal',
    interpretation:
      'Elasticidade > 0 indica relação direta histórica; |elasticidade| alto significa resposta mais intensa.',
    question: 'Quanto a tonelagem tende a responder quando a base fiscal varia historicamente?',
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
  return (
    <button
      type="button"
      className="w-full flex items-center justify-between text-left"
      onClick={onToggle}
    >
      <h3 className="font-semibold text-gray-900">{title}</h3>
      <span className="text-sm text-indigo-600">{isOpen ? 'Ocultar' : 'Mostrar'}</span>
    </button>
  );
}

export function Module6View() {
  const { selectedYear, selectedInstallation } = useFilterStore();
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
        const startYear = selectedYear - TREND_YEARS_BACK;
        const yearParams = selectedInstallation
          ? {
              id_instalacao: selectedInstallation,
              ano_inicio: startYear,
              ano_fim: selectedYear,
            }
          : {
              ano: selectedYear,
            };

        const promises = INDICATORS_INFO.map((ind) => {
          const params = ind.code === 'IND-6.10' || ind.code === 'IND-6.11'
            ? (selectedInstallation
              ? { id_instalacao: selectedInstallation, min_anos: 5 }
              : {})
            : selectedYear
              ? yearParams
              : {};

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
        setError(typeof msg === 'string' ? msg : 'Erro ao carregar indicadores');
      } finally {
        setIsLoading(false);
      }
    };

    void loadIndicators();
  }, [selectedYear, selectedInstallation]);

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Módulo 6 - Finanças Públicas</h1>
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Módulo 6 - Finanças Públicas</h1>
          <p className="text-gray-500 mt-1">
            11 indicadores de impacto fiscal com leitura causal e associativa
          </p>
        </div>
        <ExportButton moduleCode="6" />
      </div>

      <FilterBar />

      {error && <ErrorAlert message={error} className="mb-6" />}

      <div className="space-y-6">
        {Object.entries(INDICATORS_BY_GROUP).map(([group, indicatorsOfGroup]) => {
          const groupOpen = openGroups[group as IndicatorGroup];
          const groupTitle =
            group === 'tributacao'
              ? 'Imposição e Capacidade Fiscal'
              : group === 'percapita'
                ? 'Indicadores per capita'
                : group === 'desempenho'
                  ? 'Eficiência e Retorno do Porto'
                  : 'Relação e Sensibilidade (Associação)';

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
                          <div className="h-64 flex items-center justify-center text-gray-500 text-sm">
                            {ind.group === 'causal'
                              ? 'Sem observações suficientes para cálculo causal (n<5 ou série insuficiente).'
                              : 'Dados não disponíveis para o filtro atual.'}
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
