import { useEffect, useState } from 'react';
import { FilterBar } from '../../../components/filters/FilterBar';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { ChartCard } from '../../../components/charts/ChartCard';
import { BarChart } from '../../../components/charts/BarChart';
import { ExportButton } from '../../../components/common/ExportButton';
import { useFilterStore } from '../../../store/filterStore';
import { indicatorsService } from '../../../api/indicators';
import type { IndicatorResponse } from '../../../types/api';
import { TrendingUp, Shield, Building } from 'lucide-react';

const INDICATORS_INFO = [
  { code: 'IND-7.01', name: 'Índice de Eficiência Portuária', unit: '0-100', desc: 'Índice composto de eficiência', valueField: 'indice_eficiencia' },
  { code: 'IND-7.02', name: 'Índice de Relevância', unit: '0-100', desc: 'Índice composto de relevância', valueField: 'indice_relevancia' },
  { code: 'IND-7.03', name: 'Índice de Integração', unit: '0-100', desc: 'Índice composto de integração', valueField: 'indice_integracao' },
  { code: 'IND-7.04', name: 'Índice de Concentração', unit: '0-100', desc: 'Índice de concentração', valueField: 'indice_concentracao' },
];

// Composite indices (Fase 3) — each returns composicao block
const COMPOSITE_INDICES = [
  { code: 'IND-7.08', name: 'Desenvolvimento Portuário Municipal (IDPM)', icon: TrendingUp, color: 'text-blue-600 bg-blue-50', valueField: 'valor', scale: '0-100' },
  { code: 'IND-7.09', name: 'Risco Operacional (IRO)', icon: Shield, color: 'text-orange-600 bg-orange-50', valueField: 'valor', scale: '0-1' },
  { code: 'IND-7.10', name: 'Governança Portuária (IGP)', icon: Building, color: 'text-purple-600 bg-purple-50', valueField: 'valor', scale: '0-100' },
];

interface ComposicaoComponente {
  nome: string;
  codigo_fonte: string;
  valor_normalizado: number | null;
  peso: number;
  fonte: string;
  periodo_dados?: string;
  descricao?: string;
  [key: string]: unknown;
}

interface Composicao {
  formula: string;
  componentes: ComposicaoComponente[];
  nota_metodologica?: string;
}

type IndicatorRow = Record<string, unknown>;
type ModuleIndicatorResponse = IndicatorResponse<IndicatorRow>;
type IndicatorMap = Record<string, ModuleIndicatorResponse>;

const createEmptyIndicatorResponse = (codigoIndicador: string): ModuleIndicatorResponse => ({
  codigo_indicador: codigoIndicador,
  nome: codigoIndicador,
  unidade: '',
  unctad: false,
  data: [],
});

function getValueFromData(item: IndicatorRow, valueField: string): number {
  const value = item[valueField];
  return typeof value === 'number' ? value : 0;
}

function getLabelFromData(item: IndicatorRow): string {
  return typeof item.id_instalacao === 'string' ? item.id_instalacao : 'N/A';
}

export function Module7View() {
  const { selectedYear, selectedInstallation } = useFilterStore();
  const [indicators, setIndicators] = useState<IndicatorMap>({});
  const [compositeIndicators, setCompositeIndicators] = useState<IndicatorMap>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchIndicators = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // Fetch BQ-based indices
        const promises = INDICATORS_INFO.map((ind) =>
          indicatorsService.queryIndicator<IndicatorRow>({
            codigo_indicador: ind.code,
            params: {
              ano: selectedYear,
              id_instalacao: selectedInstallation || undefined
            },
          }).catch(() => createEmptyIndicatorResponse(ind.code))
        );
        // Fetch composite indices (async API)
        const compositePromises = COMPOSITE_INDICES.map((ind) =>
          indicatorsService.queryIndicator<IndicatorRow>({
            codigo_indicador: ind.code,
            params: {
              ano: selectedYear,
              id_instalacao: selectedInstallation || undefined,
            },
          }).catch(() => createEmptyIndicatorResponse(ind.code))
        );

        const [results, compositeResults] = await Promise.all([
          Promise.all(promises),
          Promise.all(compositePromises),
        ]);
        const mapped: IndicatorMap = {};
        results.forEach((result, i) => {
          mapped[INDICATORS_INFO[i].code] = result;
        });
        setIndicators(mapped);

        const compMapped: IndicatorMap = {};
        compositeResults.forEach((result, i) => {
          compMapped[COMPOSITE_INDICES[i].code] = result;
        });
        setCompositeIndicators(compMapped);
      } catch (err: unknown) {
        const errorResponse = err as { response?: { data?: { detail?: unknown } } };
        const errorMessage = errorResponse?.response?.data?.detail || 'Erro ao carregar indicadores';
        setError(typeof errorMessage === 'string' ? errorMessage : 'Erro ao carregar indicadores');
      } finally {
        setIsLoading(false);
      }
    };

    fetchIndicators();
  }, [selectedYear, selectedInstallation]);

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Módulo 7 - Índices Sintéticos</h1>
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Módulo 7 - Índices Sintéticos</h1>
          <p className="text-gray-500 mt-1">
            10 indicadores de índices sintéticos (7 operacionais + 3 compostos cross-module)
          </p>
        </div>
        <ExportButton moduleCode="7" />
      </div>

      <FilterBar />

      {error && <ErrorAlert message={error} className="mb-6" />}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {INDICATORS_INFO.map((ind) => {
          const indData = indicators[ind.code];
          const hasData = indData?.data && indData.data.length > 0;

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
                labels={indData.data
                  .slice(0, 10)
                  .map((d: IndicatorRow) => getLabelFromData(d))}
                  datasets={[{
                    label: ind.unit,
                    data: indData.data
                      .slice(0, 10)
                      .map((d: IndicatorRow) => getValueFromData(d, ind.valueField)),
                  }]}
                  yAxisLabel={ind.unit}
                  horizontal
                />
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-400">
                  Dados não disponíveis
                </div>
              )}
            </ChartCard>
          );
        })}
      </div>

      {/* Composite Indices (Fase 3) */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Índices Compostos</h2>
        <p className="text-gray-500 mb-6 text-sm">
          Índices cross-module que combinam dados operacionais, macroeconômicos, fiscais e ambientais.
          Cada índice inclui transparência total sobre os componentes utilizados.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
          {COMPOSITE_INDICES.map((ind) => {
            const Icon = ind.icon;
            const data = compositeIndicators[ind.code]?.data?.[0] as IndicatorRow | undefined;
            const valor = data?.[ind.valueField];
            const classif = (data?.classificacao as string) || 'sem_dados';
            const disponiveis = data?.componentes_disponiveis as number | undefined;
            const total = data?.componentes_total as number | undefined;

            return (
              <div key={ind.code} className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                <div className="flex items-center gap-3 mb-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${ind.color}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-800">{ind.name}</p>
                    <p className="text-xs text-gray-400">Escala {ind.scale}</p>
                  </div>
                </div>
                <p className="text-3xl font-bold text-gray-900">
                  {valor !== null && valor !== undefined ? String(valor) : '—'}
                </p>
                <div className="flex items-center justify-between mt-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    classif === 'alto' ? 'bg-green-50 text-green-700' :
                    classif === 'medio' || classif === 'moderado' ? 'bg-amber-50 text-amber-700' :
                    classif === 'baixo' ? 'bg-red-50 text-red-700' :
                    'bg-gray-50 text-gray-500'
                  }`}>
                    {classif === 'sem_dados' ? 'Sem dados' : classif.charAt(0).toUpperCase() + classif.slice(1)}
                  </span>
                  {disponiveis !== undefined && total !== undefined && (
                    <span className="text-xs text-gray-400">{disponiveis}/{total} componentes</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Composicao detail panels */}
        {COMPOSITE_INDICES.map((ind) => {
          const data = compositeIndicators[ind.code]?.data?.[0] as IndicatorRow | undefined;
          const composicao = data?.composicao as Composicao | undefined;
          if (!composicao) return null;

          const Icon = ind.icon;

          return (
            <div key={`comp-${ind.code}`} className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-4">
              <h3 className="text-base font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Icon className="w-4 h-4 text-gray-500" />
                Composição: {ind.name}
              </h3>

              <div className="bg-gray-50 rounded-lg p-3 mb-4">
                <p className="text-sm font-mono text-gray-700">{composicao.formula}</p>
              </div>

              <div className="space-y-2 mb-4">
                {composicao.componentes.map((comp, idx) => (
                  <div key={idx} className="border border-gray-100 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-800">{comp.nome}</span>
                      <span className="text-xs text-gray-500">Peso: {(comp.peso * 100).toFixed(0)}%</span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-1 text-xs text-gray-600">
                      <div>
                        <span className="text-gray-400">Valor: </span>
                        <span className="font-medium">
                          {comp.valor_normalizado !== null && comp.valor_normalizado !== undefined
                            ? comp.valor_normalizado.toFixed(3) : '—'}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">Fonte: </span>
                        <span className="font-medium">{comp.fonte}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Período: </span>
                        <span className="font-medium">{comp.periodo_dados || '—'}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Ref: </span>
                        <span className="font-mono">{comp.codigo_fonte}</span>
                      </div>
                    </div>
                    {comp.descricao && (
                      <p className="text-xs text-gray-500 mt-1">{comp.descricao}</p>
                    )}
                  </div>
                ))}
              </div>

              {composicao.nota_metodologica && (
                <div className="bg-blue-50 rounded-lg p-3">
                  <p className="text-xs text-blue-700">
                    <span className="font-semibold">Nota metodológica: </span>
                    {composicao.nota_metodologica}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
