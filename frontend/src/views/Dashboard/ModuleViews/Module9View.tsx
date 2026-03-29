import { useEffect, useState } from 'react';
import { FilterBar } from '../../../components/filters/FilterBar';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { useFilterStore } from '../../../store/filterStore';
import { indicatorsService } from '../../../api/indicators';
import { useI18n } from '../../../i18n/I18nContext';
import { IndicatorDashboardCard } from '../../../components/dashboard/IndicatorDashboardCard';
import type { IndicatorResponse } from '../../../types/api';
import { Droplets, Flame, Shield, AlertTriangle, CheckCircle } from 'lucide-react';

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
  { code: 'IND-9.01', name: 'Risco Hídrico', unit: 'Índice (0-1)', desc: 'Nível do rio vs. calado mínimo', chartType: 'metric', valueField: 'risco_normalizado' },
  { code: 'IND-9.02', name: 'Focos de Incêndio', unit: 'Contagem', desc: 'Focos em raio de 50km', chartType: 'metric', valueField: 'focos_detectados' },
  { code: 'IND-9.03', name: 'Risco Ambiental Composto', unit: 'Índice (0-1)', desc: 'Combinação hídrico + incêndio', chartType: 'metric', valueField: 'valor' },
];

type RawIndicatorRow = Record<string, unknown>;
type ModuleIndicatorResponse = IndicatorResponse<RawIndicatorRow>;
type IndicatorMap = Record<string, ModuleIndicatorResponse>;

interface ComposicaoComponente {
  nome: string;
  codigo_fonte: string;
  valor_normalizado: number | null;
  peso: number;
  fonte: string;
  periodo_dados?: string;
  ultima_atualizacao?: string;
  descricao?: string;
  [key: string]: unknown;
}

interface Composicao {
  formula: string;
  componentes: ComposicaoComponente[];
  nota_metodologica?: string;
}

const RISK_ICONS: Record<string, typeof Droplets> = {
  'IND-9.01': Droplets,
  'IND-9.02': Flame,
  'IND-9.03': Shield,
};

function getRiskColor(classificacao: string): string {
  switch (classificacao) {
    case 'baixo': return 'text-green-600 bg-green-50';
    case 'moderado': return 'text-amber-600 bg-amber-50';
    case 'alto': return 'text-red-600 bg-red-50';
    default: return 'text-gray-600 bg-gray-50';
  }
}

function getRiskBadge(classificacao: string) {
  const Icon = classificacao === 'alto' ? AlertTriangle : classificacao === 'baixo' ? CheckCircle : AlertTriangle;
  const colorClass = getRiskColor(classificacao);
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${colorClass}`}>
      <Icon className="w-3 h-3" />
      {classificacao.charAt(0).toUpperCase() + classificacao.slice(1)}
    </span>
  );
}

export function Module9View() {
  const { t } = useI18n();
  const { selectedInstallation } = useFilterStore();
  const [indicators, setIndicators] = useState<IndicatorMap>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      setError(null);

      try {
        const results: IndicatorMap = {};
        await Promise.allSettled(
          INDICATORS_INFO.map(async (ind) => {
            try {
              const resp = await indicatorsService.queryIndicator<RawIndicatorRow>({
                codigo_indicador: ind.code,
                params: {
                  id_instalacao: selectedInstallation || undefined,
                },
              });
              results[ind.code] = resp;
            } catch {
              results[ind.code] = { codigo_indicador: ind.code, nome: ind.code, unidade: '', unctad: false, data: [] };
            }
          })
        );
        setIndicators(results);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : t('common.errorLoading'));
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, [selectedInstallation]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;

  // Extract composite data for IND-9.03
  const compositeData = indicators['IND-9.03']?.data?.[0] as RawIndicatorRow | undefined;
  const composicao = compositeData?.composicao as Composicao | undefined;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('module9.title')}</h1>
        <p className="text-gray-600 mt-1">
          {t('module9.subtitle')}
        </p>
      </div>

      <FilterBar />

      {/* Risk Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {INDICATORS_INFO.map((ind) => {
          const Icon = RISK_ICONS[ind.code] || Shield;
          const data = indicators[ind.code]?.data?.[0] as RawIndicatorRow | undefined;
          const valor = data?.[ind.valueField];
          const classif = (data?.classificacao as string) || 'sem_dados';

          return (
            <div key={ind.code} className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${getRiskColor(classif)}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">{ind.name}</p>
                    <p className="text-xs text-gray-400">{ind.desc}</p>
                  </div>
                </div>
                {getRiskBadge(classif)}
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {valor !== null && valor !== undefined ? String(valor) : '—'}
              </p>
              <p className="text-xs text-gray-500 mt-1">{ind.unit}</p>
            </div>
          );
        })}
      </div>

      {/* Composicao Transparency Block */}
      {composicao && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-gray-500" />
            Composição do Índice de Risco Ambiental
          </h2>

          {/* Formula */}
          <div className="bg-gray-50 rounded-lg p-3 mb-4">
            <p className="text-sm font-mono text-gray-700">{composicao.formula}</p>
          </div>

          {/* Components */}
          <div className="space-y-3 mb-4">
            {composicao.componentes.map((comp, idx) => (
              <div key={idx} className="border border-gray-100 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-gray-800">{comp.nome}</h3>
                  <span className="text-sm text-gray-500">Peso: {(comp.peso * 100).toFixed(0)}%</span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-gray-600">
                  <div>
                    <span className="text-gray-400">Valor:</span>{' '}
                    <span className="font-medium">
                      {comp.valor_normalizado !== null ? comp.valor_normalizado.toFixed(3) : '—'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Fonte:</span>{' '}
                    <span className="font-medium">{comp.fonte}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Período:</span>{' '}
                    <span className="font-medium">{comp.periodo_dados || '—'}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Código:</span>{' '}
                    <span className="font-mono">{comp.codigo_fonte}</span>
                  </div>
                </div>
                {comp.descricao && (
                  <p className="text-xs text-gray-500 mt-2">{comp.descricao}</p>
                )}
              </div>
            ))}
          </div>

          {/* Methodological Note */}
          {composicao.nota_metodologica && (
            <div className="bg-blue-50 rounded-lg p-3">
              <p className="text-xs text-blue-700">
                <span className="font-semibold">Nota metodológica:</span>{' '}
                {composicao.nota_metodologica}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Detailed Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {INDICATORS_INFO.slice(0, 2).map((ind) => (
          <IndicatorDashboardCard
            key={ind.code}
            title={ind.name}
            description={ind.desc}
            unit={ind.unit}
            isLoading={loading}
            data={indicators[ind.code] || { codigo_indicador: ind.code, nome: ind.code, unidade: '', unctad: false, data: [] }}
            chartType={ind.chartType}
            valueField={ind.valueField}
            labelField={ind.labelField}
            indicatorCode={ind.code}
          />
        ))}
      </div>
    </div>
  );
}
