import React, { useEffect, useState } from 'react';
import { FilterBar } from '../../../components/filters/FilterBar';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { ExportButton } from '../../../components/common/ExportButton';
import { useFilterStore } from '../../../store/filterStore';
import { indicatorsService } from '../../../api/indicators';
import { useI18n } from '../../../i18n/I18nContext';
import type { IndicatorResponse } from '../../../types/api';
import {
  FileCheck, AlertTriangle, Scale, Newspaper, Gavel, CheckCircle,
  Shield, Award, TrendingDown, TrendingUp, Minus,
} from 'lucide-react';

interface IndicatorConfig {
  code: string;
  name: string;
  unit: string;
  desc: string;
  chartType: 'bar' | 'pie' | 'metric';
  valueField: string;
}

const INDICATORS_INFO: IndicatorConfig[] = [
  { code: 'IND-10.01', name: 'Licitações Portuárias', unit: 'Contagem + R$', desc: 'Contratação pública portuária', chartType: 'metric', valueField: 'total_contratacoes' },
  { code: 'IND-10.02', name: 'Sanções Portuárias', unit: 'Contagem', desc: 'Operadores sancionados (Cadastro de Inelegíveis)', chartType: 'metric', valueField: 'empresas_sancionadas' },
  { code: 'IND-10.03', name: 'Decisões do Tribunal de Contas', unit: 'Contagem', desc: 'Decisões do TCU sobre portos', chartType: 'metric', valueField: 'total_acordaos' },
  { code: 'IND-10.04', name: 'Menções em Diário Oficial', unit: 'Avaliação', desc: 'Análise de menções em publicações oficiais', chartType: 'metric', valueField: 'total_mencoes' },
  { code: 'IND-10.05', name: 'Processos Judiciais', unit: 'Contagem', desc: 'Litígios do ecossistema portuário', chartType: 'metric', valueField: 'total_processos' },
  { code: 'IND-10.06', name: 'Regularidade Licitatória', unit: 'Razão (0-1)', desc: 'Publicação regular no PNCP', chartType: 'metric', valueField: 'regularidade' },
];

const COMPOSITE_INDICATORS = [
  { code: 'IND-10.07', name: 'Risco Regulatório', desc: 'Medida combinada de risco (0-1)' },
  { code: 'IND-10.08', name: 'Governança Portuária', desc: 'Medida de qualidade de governança (0-100)' },
];

type RawRow = Record<string, unknown>;
type ModuleResponse = IndicatorResponse<RawRow>;
type IndicatorMap = Record<string, ModuleResponse>;

interface Tema {
  tema: string;
  mencoes: number;
  sentimento: string;
  score: number;
  exemplos: string[];
  justificativa: string;
}

interface Componente {
  nome: string;
  valor_normalizado: number | null;
  peso: number;
  fonte: string;
  valor_bruto?: string;
  descricao?: string;
  ultima_atualizacao?: string;
  [key: string]: unknown;
}

interface Composicao {
  formula: string;
  componentes: Componente[];
  nota_metodologica?: string;
}

const INDICATOR_ICONS: Record<string, typeof FileCheck> = {
  'IND-10.01': FileCheck,
  'IND-10.02': AlertTriangle,
  'IND-10.03': Scale,
  'IND-10.04': Newspaper,
  'IND-10.05': Gavel,
  'IND-10.06': CheckCircle,
  'IND-10.07': Shield,
  'IND-10.08': Award,
};

function getSentimentIcon(sentiment: string) {
  switch (sentiment) {
    case 'positivo': return <TrendingUp className="w-4 h-4 text-green-600" />;
    case 'negativo': return <TrendingDown className="w-4 h-4 text-red-600" />;
    default: return <Minus className="w-4 h-4 text-gray-400" />;
  }
}

function getRiskColor(cls: string): string {
  switch (cls) {
    case 'baixo': case 'bom': return 'text-green-600 bg-green-50';
    case 'moderado': case 'regular': return 'text-amber-600 bg-amber-50';
    case 'alto': case 'fraco': return 'text-red-600 bg-red-50';
    default: return 'text-gray-600 bg-gray-50';
  }
}

export function Module10View() {
  const { t } = useI18n();
  const { selectedInstallation, selectedYear } = useFilterStore();
  const [indicators, setIndicators] = useState<IndicatorMap>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      setError(null);
      try {
        const results: IndicatorMap = {};
        const allCodes = [...INDICATORS_INFO.map(i => i.code), ...COMPOSITE_INDICATORS.map(i => i.code)];
        await Promise.allSettled(
          allCodes.map(async (code) => {
            try {
              const resp = await indicatorsService.queryIndicator<RawRow>({
                codigo_indicador: code,
                params: {
                  id_instalacao: selectedInstallation || undefined,
                  ano: selectedYear || undefined,
                },
              });
              results[code] = resp;
            } catch {
              results[code] = { codigo_indicador: code, nome: code, unidade: '', unctad: false, data: [] };
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
  }, [selectedInstallation, selectedYear]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;

  const riskData = indicators['IND-10.07']?.data?.[0] as RawRow | undefined;
  const govData = indicators['IND-10.08']?.data?.[0] as RawRow | undefined;
  const mencoesData = indicators['IND-10.04']?.data?.[0] as RawRow | undefined;
  const temas = (mencoesData?.temas as Tema[]) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('module10.title')}</h1>
          <p className="text-gray-600 mt-1">
            {t('module10.subtitle')}
          </p>
        </div>
        <ExportButton moduleCode="10" />
      </div>

      <FilterBar />

      {/* Composite Indices */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Risk Index */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${getRiskColor((riskData?.classificacao as string) || '')}`}>
                <Shield className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">{t('module10.risk.title')}</p>
                <p className="text-xs text-gray-400">IND-10.07 (0-1, menor = melhor)</p>
              </div>
            </div>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskColor((riskData?.classificacao as string) || '')}`}>
              {((riskData?.classificacao as string) || 'sem dados').charAt(0).toUpperCase() + ((riskData?.classificacao as string) || 'sem dados').slice(1)}
            </span>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {riskData?.valor !== null && riskData?.valor !== undefined ? String(riskData?.valor) : '—'}
          </p>
        </div>

        {/* Governance Index */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${getRiskColor((govData?.classificacao as string) || '')}`}>
                <Award className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">{t('module10.governance.title')}</p>
                <p className="text-xs text-gray-400">IND-10.08 (0-100, maior = melhor)</p>
              </div>
            </div>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskColor((govData?.classificacao as string) || '')}`}>
              {((govData?.classificacao as string) || 'sem dados').charAt(0).toUpperCase() + ((govData?.classificacao as string) || 'sem dados').slice(1)}
            </span>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {govData?.valor !== null && govData?.valor !== undefined ? `${String(govData?.valor)}/100` : '—'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {INDICATORS_INFO.map((ind): React.ReactNode => {
          const Icon: typeof FileCheck = INDICATOR_ICONS[ind.code] || FileCheck;
          const data = indicators[ind.code]?.data?.[0] as RawRow | undefined;
          const rawValor = data?.[ind.valueField];
          const valor: string = rawValor !== null && rawValor !== undefined ? String(rawValor) : '—';

          return (
            <div key={ind.code} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
              <div className="flex items-center gap-3 mb-2">
                <Icon className="w-5 h-5 text-gray-500" />
                <div>
                  <p className="text-sm font-medium text-gray-700">{ind.name}</p>
                  <p className="text-xs text-gray-400">{ind.desc}</p>
                </div>
              </div>
              <p className="text-xl font-bold text-gray-900">
                {valor}
              </p>
              <p className="text-xs text-gray-500 mt-1">{ind.unit}</p>
            </div>
          );
        })}
      </div>

      {/* Sentiment Analysis (IND-10.04) */}
      {temas.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-1 flex items-center gap-2">
            <Newspaper className="w-5 h-5 text-gray-500" />
            {t('module10.sentiment.title')}
          </h2>
          <p className="text-sm text-gray-500 mb-4">
            Avaliação geral: <span className="font-medium">{mencoesData?.score_sentimento !== undefined ? String(mencoesData.score_sentimento) : '—'}</span>
            {' '}({mencoesData?.sentimento_geral !== undefined ? String(mencoesData.sentimento_geral) : '—'}) — {mencoesData?.total_mencoes !== undefined ? String(mencoesData.total_mencoes) : 0} menções
          </p>

          <div className="space-y-3">
            {temas.map((tema, idx) => (
              <div key={idx} className="border border-gray-100 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getSentimentIcon(tema.sentimento)}
                    <h3 className="font-medium text-gray-800">{tema.tema}</h3>
                    <span className="text-xs text-gray-400">({tema.mencoes} menções)</span>
                  </div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    tema.sentimento === 'positivo' ? 'bg-green-50 text-green-700' :
                    tema.sentimento === 'negativo' ? 'bg-red-50 text-red-700' :
                    'bg-gray-50 text-gray-600'
                  }`}>
                    {tema.score > 0 ? '+' : ''}{tema.score}
                  </span>
                </div>
                <p className="text-xs text-gray-600 mb-2">{tema.justificativa}</p>
                {tema.exemplos.length > 0 && (
                  <div className="text-xs text-gray-400 italic">
                    {tema.exemplos.slice(0, 2).map((ex, i) => (
                      <p key={i} className="truncate">&ldquo;{ex}&rdquo;</p>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Composicao block for IND-10.07 */}
      {!!riskData?.composicao && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-gray-500" />
            {t('module10.composition.title')}
          </h2>

          <div className="bg-gray-50 rounded-lg p-3 mb-4">
            <p className="text-sm font-mono text-gray-700">{(riskData.composicao as Composicao).formula}</p>
          </div>

          <div className="space-y-2 mb-4">
            {(riskData.composicao as Composicao).componentes.map((comp, idx) => (
              <div key={idx} className="flex items-center justify-between border border-gray-100 rounded-lg p-3">
                <div>
                  <p className="text-sm font-medium text-gray-700">{comp.nome}</p>
                  <p className="text-xs text-gray-400">{comp.fonte}</p>
                  {comp.valor_bruto && <p className="text-xs text-gray-500">{comp.valor_bruto as string}</p>}
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-gray-900">
                    {comp.valor_normalizado !== null ? comp.valor_normalizado.toFixed(3) : '—'}
                  </p>
                  <p className="text-xs text-gray-400">peso {(comp.peso * 100).toFixed(0)}%</p>
                </div>
              </div>
            ))}
          </div>

          {(riskData.composicao as Composicao).nota_metodologica && (
            <div className="bg-blue-50 rounded-lg p-3">
              <p className="text-xs text-blue-700">
                <span className="font-semibold">Nota metodológica:</span>{' '}
                {(riskData.composicao as Composicao).nota_metodologica}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
