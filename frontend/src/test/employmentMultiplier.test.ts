import { describe, it, expect, vi, beforeEach } from 'vitest';
import { employmentMultiplierService } from '../api/employmentMultiplier';
import type { EmploymentMultiplierResponse, CausalEstimateResponse } from '../api/employmentMultiplier';
import { apiClient } from '../api/client';

vi.mock('../api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

const mockGet = vi.mocked(apiClient.get);

describe('employmentMultiplierService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches literature-based multiplier estimate', async () => {
    const response: EmploymentMultiplierResponse & CausalEstimateResponse = {
      municipality_id: '3304557',
      municipality_name: 'Rio de Janeiro',
      year: 2023,
      data: [
        {
          municipality_id: '3304557',
          municipality_name: 'Rio de Janeiro',
          ano: 2023,
          empregos_diretos: 17392,
          empregos_totais: 52000,
          participacao_emprego_local: 3.2,
          tonelagem_antaq_milhoes: 45.0,
          empregos_por_milhao_toneladas: 386,
          empregos_indiretos_estimados: 20870,
          empregos_induzidos_estimados: 13914,
          emprego_total_estimado: 52176,
          metodologia: 'UNCTAD port-city coefficients',
          indicador_de_confianca: 'moderado',
          correlacao_ou_proxy: false,
          metodo: 'literature',
          fonte: 'UNCTAD/ECLAC',
        },
      ],
      literature: {
        source: 'UNCTAD/ECLAC',
        coefficient: 2.0,
        range_low: 1.5,
        range_high: 3.0,
        confidence: 'moderate',
        year_published: 2019,
        region: 'Latin America',
      },
      estimate: {
        confidence: 'moderate',
        municipality_id: '3304557',
        municipality_name: 'Rio de Janeiro',
        year: 2023,
        multiplier_type: 'literature',
        multiplier_used: 2.0,
        direct_jobs: 17392,
        indirect_estimated: 20870,
        induced_estimated: 13914,
        total_impact: 52176,
        source: 'UNCTAD/ECLAC',
      },
    };

    mockGet.mockResolvedValueOnce({ data: response } as never);

    const result = await employmentMultiplierService.getMultiplierEstimate('3304557', 2023, false);

    expect(mockGet).toHaveBeenCalledWith(
      '/api/v1/employment/multipliers/3304557',
      { params: { ano: 2023, use_causal: false } },
    );
    expect(result.literature.coefficient).toBe(2.0);
    expect(result.literature.confidence).toBe('moderate');
    expect(result.literature.region).toBe('Latin America');
    expect(result.estimate.total_impact).toBe(52176);
    expect(result.data).toHaveLength(1);
  });

  it('includes delta_tonelagem_pct for shock scenario', async () => {
    const response: EmploymentMultiplierResponse & CausalEstimateResponse = {
      municipality_id: '3304557',
      municipality_name: 'Rio de Janeiro',
      year: 2023,
      data: [
        {
          municipality_id: '3304557',
          municipality_name: 'Rio de Janeiro',
          ano: 2023,
          empregos_diretos: 17392,
          empregos_totais: null,
          participacao_emprego_local: null,
          tonelagem_antaq_milhoes: null,
          empregos_por_milhao_toneladas: null,
          empregos_indiretos_estimados: 20870,
          empregos_induzidos_estimados: 13914,
          emprego_total_estimado: 52176,
          metodologia: 'UNCTAD',
          indicador_de_confianca: 'moderado',
          correlacao_ou_proxy: false,
          metodo: 'literature',
          fonte: 'UNCTAD',
          scenario: {
            delta_tonelagem_pct: 10,
            delta_empregos_diretos: 1739,
            delta_empregos_indiretos: 2087,
            delta_empregos_induzidos: 1391,
            delta_emprego_total: 5218,
          },
        },
      ],
      literature: {
        source: 'UNCTAD',
        coefficient: 2.0,
        range_low: 1.5,
        range_high: 3.0,
      },
      estimate: {
        confidence: 'moderate',
        municipality_id: '3304557',
        municipality_name: 'Rio de Janeiro',
        year: 2023,
        multiplier_type: 'literature',
        multiplier_used: 2.0,
        direct_jobs: 17392,
        indirect_estimated: 20870,
        induced_estimated: 13914,
        total_impact: 52176,
        source: 'UNCTAD',
      },
    };

    mockGet.mockResolvedValueOnce({ data: response } as never);

    const result = await employmentMultiplierService.getMultiplierEstimate('3304557', 2023, false, 10);

    expect(mockGet).toHaveBeenCalledWith(
      '/api/v1/employment/multipliers/3304557',
      { params: { ano: 2023, use_causal: false, delta_tonelagem_pct: 10 } },
    );
    expect(result.data![0].scenario?.delta_emprego_total).toBe(5218);
    expect(result.data![0].scenario?.delta_tonelagem_pct).toBe(10);
  });

  it('fetches causal estimate with IV method', async () => {
    const response: EmploymentMultiplierResponse & CausalEstimateResponse = {
      municipality_id: '3304557',
      municipality_name: 'Rio de Janeiro',
      year: 2023,
      literature: {
        source: 'UNCTAD',
        coefficient: 2.0,
        range_low: 1.5,
        range_high: 3.0,
      },
      causal: {
        source: 'IV 2SLS: tonnage → employment',
        method: 'iv_2sls',
        n_obs: 320,
        r2: 0.35,
        coefficient: 1.8,
        p_value: 0.012,
        ci_lower: 0.4,
        ci_upper: 3.2,
      },
      estimate: {
        confidence: 'moderate',
        municipality_id: '3304557',
        municipality_name: 'Rio de Janeiro',
        year: 2023,
        multiplier_type: 'literature',
        multiplier_used: 2.0,
        direct_jobs: 17392,
        indirect_estimated: 20870,
        induced_estimated: 13914,
        total_impact: 52176,
        source: 'UNCTAD',
      },
      causal_estimate: {
        confidence: 'moderate',
        municipality_id: '3304557',
        municipality_name: 'Rio de Janeiro',
        year: 2023,
        multiplier_type: 'causal',
        multiplier_used: 1.8,
        direct_jobs: 17392,
        indirect_estimated: 18344,
        induced_estimated: 12230,
        total_impact: 47966,
        source: 'IV 2SLS',
      },
    };

    mockGet.mockResolvedValueOnce({ data: response } as never);

    const result = await employmentMultiplierService.getMultiplierEstimate('3304557', 2023, true);

    expect(mockGet).toHaveBeenCalledWith(
      '/api/v1/employment/multipliers/3304557',
      { params: { ano: 2023, use_causal: true } },
    );
    expect(result.causal?.method).toBe('iv_2sls');
    expect(result.causal?.p_value).toBe(0.012);
    expect(result.causal_estimate?.multiplier_used).toBe(1.8);
    expect(result.causal_estimate?.total_impact).toBe(47966);
  });
});
