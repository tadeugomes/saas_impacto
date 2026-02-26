import { useEffect, useState } from 'react';
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
import type { EmploymentMultiplierResponse } from '../../../api/employmentMultiplier';
import { formatQuantity, formatDecimal } from '../../../utils/numberFormat';

// Indicadores do Módulo 3 - Recursos Humanos (RAIS)
// Nota: IND-3.03 e IND-3.09 necessitam visualização especial (dados agrupados)
const INDICATORS_INFO = [
  { code: 'IND-3.01', name: 'Empregos Portuários', unit: 'Empregos', desc: 'Total de empregos no setor portuário (RAIS)', valueField: 'empregos_portuarios' },
  { code: 'IND-3.02', name: 'Paridade de Gênero', unit: '%', desc: 'Percentual de mulheres no setor portuário', valueField: 'percentual_feminino' },
  { code: 'IND-3.04', name: 'Taxa Emprego Temporário', unit: '%', desc: 'Percentual de contratos temporários', valueField: 'taxa_temporario' },
  { code: 'IND-3.05', name: 'Salário Médio', unit: 'R$', desc: 'Remuneração média mensal', valueField: 'salario_medio' },
  { code: 'IND-3.06', name: 'Massa Salarial', unit: 'R$', desc: 'Massa salarial anual estimada', valueField: 'massa_salarial_anual' },
  { code: 'IND-3.07', name: 'Produtividade', unit: 'ton/emp', desc: 'Toneladas movimentadas por empregado portuário', valueField: 'ton_por_empregado' },
  { code: 'IND-3.08', name: 'Receita por Empregado', unit: 'R$/emp', desc: 'PIB por empregado portuário (proxy)', valueField: 'pib_por_empregado_portuario' },
  { code: 'IND-3.10', name: 'Idade Média', unit: 'Anos', desc: 'Idade média dos trabalhadores portuários', valueField: 'idade_media' },
  { code: 'IND-3.11', name: 'Variação Anual Empregos', unit: '%', desc: 'Variação percentual anual de empregos', valueField: 'variacao_percentual' },
  { code: 'IND-3.12', name: 'Participação Emprego Local', unit: '%', desc: 'Participação do setor portuário no emprego total do município', valueField: 'participacao_emprego_local' },
];

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

export function Module3View() {
  const { selectedYear, selectedInstallation } = useFilterStore();
  const [indicators, setIndicators] = useState<Record<string, any>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [impactData, setImpactData] = useState<EmploymentMultiplierResponse[]>([]);
  const [isImpactLoading, setIsImpactLoading] = useState(false);
  const [deltaPct, setDeltaPct] = useState<number>(10);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      setImpactData([]);

      try {
        const promises = INDICATORS_INFO.map((ind) =>
          indicatorsService.queryIndicator({
            codigo_indicador: ind.code,
            params: {
              ano: selectedYear,
              id_instalacao: selectedInstallation || undefined,
            },
          }).catch((err) => {
            console.error(`Erro ao buscar indicador ${ind.code}:`, err);
            return { data: [], error: err.response?.data?.detail || err.message };
          })
        );

        const results = await Promise.all(promises);
        const mapped: Record<string, any> = {};
        results.forEach((result, i) => {
          mapped[INDICATORS_INFO[i].code] = result;
        });
        setIndicators(mapped);
        setIsLoading(false);

        // Extrai IDs de município do IND-3.01 para o painel de impacto
        const municipioIds = extractMunicipioIds(results[0]?.data || []);
        if (municipioIds.length > 0) {
          setIsImpactLoading(true);
          try {
            const impactPromises = municipioIds.map((id) =>
              employmentMultiplierService.getMultiplierEstimate(id, selectedYear)
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
  }, [selectedYear, selectedInstallation]);

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
          <h1 className="text-2xl font-bold text-gray-900">Módulo 3 - Recursos Humanos</h1>
          <p className="text-gray-500 mt-1">
            Painel de impacto em emprego e indicadores descritivos — dados RAIS + ANTAQ
          </p>
        </div>
        <ExportButton moduleCode="3" />
      </div>

      <FilterBar />

      {error && <ErrorAlert message={error} className="mb-6" />}

      {/* ── Painel de Impacto em Emprego (PR-31) ──────────────────────────────── */}
      <div className="mb-8 rounded-xl border border-amber-200 bg-amber-50 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Painel de Impacto em Emprego</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Fonte: RAIS + ANTAQ · {selectedYear} · Multiplicadores de literatura (UNCTAD / MInfra)
            </p>
          </div>
          <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-700 border border-amber-200 whitespace-nowrap">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
            Proxy literário · não causal
          </span>
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
                const nomeMunicipio = row.municipality_name || resp.municipality_name || resp.municipality_id;
                return (
                  <div key={resp.municipality_id} className="bg-white rounded-lg border border-amber-100 p-4 shadow-sm">
                    <h3 className="font-semibold text-gray-800 mb-3 text-sm truncate" title={nomeMunicipio}>
                      {nomeMunicipio}
                    </h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-500">Empregos diretos</span>
                        <span className="font-semibold text-gray-900">{formatQuantity(row.empregos_diretos)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-500">Indiretos (est.)</span>
                        <span className="font-medium text-gray-700">{formatQuantity(Math.round(row.empregos_indiretos_estimados))}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-500">Induzidos (est.)</span>
                        <span className="font-medium text-gray-700">{formatQuantity(Math.round(row.empregos_induzidos_estimados))}</span>
                      </div>
                      <div className="flex justify-between items-center border-t border-gray-100 pt-2">
                        <span className="font-semibold text-gray-700">Total estimado</span>
                        <span className="font-bold text-amber-700 text-base">{formatQuantity(Math.round(row.emprego_total_estimado))}</span>
                      </div>
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
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Simulação de choque de carga */}
            <div className="bg-white rounded-lg border border-amber-100 p-4">
              <div className="flex flex-wrap items-center gap-4 mb-4">
                <h3 className="font-semibold text-gray-800">Simulação de Choque de Carga</h3>
                <div className="flex items-center gap-2">
                  <label htmlFor="deltaPct" className="text-sm text-gray-500">
                    Variação de tonelagem:
                  </label>
                  <input
                    id="deltaPct"
                    type="number"
                    min={-50}
                    max={100}
                    step={5}
                    value={deltaPct}
                    onChange={(e) => setDeltaPct(Number(e.target.value))}
                    className="w-20 px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-400"
                  />
                  <span className="text-sm text-gray-500">%</span>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500 border-b border-gray-100">
                      <th className="pb-2 pr-4 font-medium">Município</th>
                      <th className="pb-2 pr-4 font-medium text-right">Δ Diretos</th>
                      <th className="pb-2 pr-4 font-medium text-right">Δ Indiretos</th>
                      <th className="pb-2 pr-4 font-medium text-right">Δ Induzidos</th>
                      <th className="pb-2 font-medium text-right">Δ Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {impactData.map((resp) => {
                      const row = resp.data?.[0];
                      if (!row) return null;
                      const ratio = deltaPct / 100;
                      const dDiretos = Math.round(row.empregos_diretos * ratio);
                      const dIndiretos = Math.round(row.empregos_indiretos_estimados * ratio);
                      const dInduzidos = Math.round(row.empregos_induzidos_estimados * ratio);
                      const dTotal = Math.round(row.emprego_total_estimado * ratio);
                      const positive = dTotal >= 0;
                      const sign = positive ? '+' : '';
                      const colorCls = positive ? 'text-green-600' : 'text-red-600';
                      const nomeMunicipio = row.municipality_name || resp.municipality_name || resp.municipality_id;
                      return (
                        <tr key={resp.municipality_id} className="border-b border-gray-50 last:border-0">
                          <td className="py-2 pr-4 text-gray-700">{nomeMunicipio}</td>
                          <td className={`py-2 pr-4 text-right font-medium ${colorCls}`}>{sign}{formatQuantity(dDiretos)}</td>
                          <td className={`py-2 pr-4 text-right font-medium ${colorCls}`}>{sign}{formatQuantity(dIndiretos)}</td>
                          <td className={`py-2 pr-4 text-right font-medium ${colorCls}`}>{sign}{formatQuantity(dInduzidos)}</td>
                          <td className={`py-2 text-right font-bold ${colorCls}`}>{sign}{formatQuantity(dTotal)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <p className="text-xs text-gray-400 mt-3">
                Estimativa proporcional com base em multiplicadores de literatura. Hipótese linear simplificada — não constitui previsão causal.
              </p>
            </div>
          </>
        )}
      </div>

      {/* ── Indicadores Descritivos de Recursos Humanos ───────────────────────── */}
      <h2 className="text-base font-semibold text-gray-700 mb-4">Indicadores Descritivos de Recursos Humanos</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
                />
              ) : (
                <div className="h-64 flex flex-col items-center justify-center text-gray-400">
                  {hasError ? (
                    <>
                      <p className="text-red-500 mb-2">Erro ao carregar dados</p>
                      <p className="text-sm text-gray-500">{hasError}</p>
                    </>
                  ) : (
                    <>
                      <p>Dados não disponíveis</p>
                      <p className="text-sm text-gray-500 mt-1">
                        Verifique os filtros ou aguarde disponibilização dos dados RAIS
                      </p>
                    </>
                  )}
                </div>
              )}
            </ChartCard>
          );
        })}
      </div>
    </div>
  );
}
