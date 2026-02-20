import { useEffect, useMemo, useState } from 'react';
import { FilterBar } from '../../../components/filters/FilterBar';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../../components/common/ErrorAlert';
import { ExportButton } from '../../../components/common/ExportButton';
import { useFilterStore } from '../../../store/filterStore';
import { indicatorsService } from '../../../api/indicators';
import { IndicatorDashboardCard } from '../../../components/dashboard/IndicatorDashboardCard';
import type { IndicatorResponse } from '../../../types/api';

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
  { code: 'IND-1.01', name: 'Tempo Médio de Espera', unit: 'Horas', desc: 'Tempo entre chegada e atracação', chartType: 'bar', valueField: 'tempo_medio_espera_horas', labelField: 'id_instalacao' },
  { code: 'IND-1.02', name: 'Tempo Médio em Porto', unit: 'Horas', desc: 'Tempo total no porto', chartType: 'bar', valueField: 'tempo_medio_porto_horas', labelField: 'id_instalacao' },
  { code: 'IND-1.03', name: 'Tempo Bruto de Atracação', unit: 'Horas', desc: 'Tempo de atracação até desatracação', chartType: 'bar', valueField: 'tempo_bruto_atracacao_horas', labelField: 'id_instalacao' },
  { code: 'IND-1.04', name: 'Tempo Líquido de Operação', unit: 'Horas', desc: 'Tempo efetivo de operação', chartType: 'bar', valueField: 'tempo_liquido_operacao_horas', labelField: 'id_instalacao' },
  { code: 'IND-1.05', name: 'Taxa de Ocupação de Berços', unit: '%', desc: 'Ocupação média dos berços', chartType: 'bar', valueField: 'taxa_ocupacao_percentual', labelField: 'id_instalacao' },
  { code: 'IND-1.06', name: 'Tempo Ocioso Médio', unit: 'Horas', desc: 'Tempo de paralisação', chartType: 'bar', valueField: 'tempo_ocioso_medio_horas', labelField: 'id_instalacao' },
  { code: 'IND-1.07', name: 'Arqueação Bruta Média', unit: 'GT', desc: 'Tamanho médio dos navios', chartType: 'bar', valueField: 'arqueacao_bruta_media', labelField: 'id_instalacao' },
  { code: 'IND-1.08', name: 'Comprimento Médio', unit: 'Metros', desc: 'Comprimento médio dos navios', chartType: 'bar', valueField: 'comprimento_medio_metros', labelField: 'id_instalacao' },
  { code: 'IND-1.09', name: 'Calado Máximo', unit: 'Metros', desc: 'Maior calado operacional', chartType: 'metric', valueField: 'calado_maximo_metros', labelField: 'id_instalacao' },
  { code: 'IND-1.10', name: 'Distribuição por Tipo', unit: '%', desc: 'Por tipo de navegação', chartType: 'pie', valueField: 'qtd_atracacoes', labelField: 'tipo_navegacao' },
  { code: 'IND-1.11', name: 'Número de Atracações', unit: 'Contagem', desc: 'Total de atracações', chartType: 'bar', valueField: 'total_atracacoes', labelField: 'id_instalacao' },
  { code: 'IND-1.12', name: 'Índice de Paralisação', unit: '%', desc: 'Tempo ocioso / tempo atracado', chartType: 'bar', valueField: 'indice_paralisacao_percentual', labelField: 'id_instalacao' },
];

type RawIndicatorRow = Record<string, unknown>;
type ModuleIndicatorResponse = IndicatorResponse<RawIndicatorRow>;
type IndicatorMap = Record<string, ModuleIndicatorResponse>;

const createEmptyIndicatorResponse = (codigoIndicador: string): ModuleIndicatorResponse => ({
  codigo_indicador: codigoIndicador,
  nome: codigoIndicador,
  unidade: '',
  unctad: false,
  data: [],
});

export function Module1View() {
  const { selectedYear, selectedInstallation } = useFilterStore();
  const [indicators, setIndicators] = useState<IndicatorMap>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tableSearch, setTableSearch] = useState('');
  const [selectedIndicator, setSelectedIndicator] = useState('all');

  useEffect(() => {
    const fetchIndicators = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const promises = INDICATORS_INFO.map((ind) =>
          indicatorsService
            .queryIndicator<RawIndicatorRow>({
              codigo_indicador: ind.code,
              params: {
                ano: selectedYear,
                id_instalacao: selectedInstallation || undefined,
              },
            })
            .catch(() => createEmptyIndicatorResponse(ind.code))
        );

        const results = await Promise.all(promises);
        const mapped: IndicatorMap = {};
        results.forEach((result, i) => {
          mapped[INDICATORS_INFO[i].code] = result;
        });
        setIndicators(mapped);
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

  const visibleIndicators = useMemo(() => {
    if (selectedIndicator === 'all') {
      return INDICATORS_INFO;
    }
    return INDICATORS_INFO.filter((item) => item.code === selectedIndicator);
  }, [selectedIndicator]);

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Módulo 1 - Operações de Navios</h1>
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Módulo 1 - Operações de Navios</h1>
          <p className="text-gray-500 mt-1">12 indicadores de operações de navios seguindo padrão UNCTAD</p>
        </div>
        <ExportButton moduleCode="1" />
      </div>

      <FilterBar />

      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <div>
          <label className="text-xs text-gray-500">Buscar na série</label>
          <input
            className="w-full border border-gray-300 rounded-lg px-3 py-2 mt-1"
            placeholder="Filtrar nome no ranking"
            value={tableSearch}
            onChange={(event) => setTableSearch(event.target.value)}
          />
        </div>
        <div>
          <label className="text-xs text-gray-500">Indicador</label>
          <select
            className="w-full border border-gray-300 rounded-lg px-3 py-2 mt-1"
            value={selectedIndicator}
            onChange={(event) => setSelectedIndicator(event.target.value)}
          >
            <option value="all">Todos</option>
            {INDICATORS_INFO.map((indicator) => (
              <option key={indicator.code} value={indicator.code}>
                {indicator.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <ErrorAlert message={error} className="mb-6" />}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {visibleIndicators.map((ind) => (
          <IndicatorDashboardCard
            key={ind.code}
            title={ind.name}
            description={ind.desc}
            unit={ind.unit}
            isLoading={isLoading}
            data={indicators[ind.code]}
            chartType={ind.chartType}
            valueField={ind.valueField}
            labelField={ind.labelField}
            filterText={tableSearch}
            indicatorCode={ind.code}
          />
        ))}
      </div>
    </div>
  );
}
