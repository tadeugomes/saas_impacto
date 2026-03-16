import { describe, it, expect, vi, beforeEach } from 'vitest';
import { impactoEconomicoService } from '../api/impactoEconomico';
import { apiClient } from '../api/client';
import type {
  AnalysisResponse,
  AnalysisDetail,
  MatchingResponse,
  ImpactSimulationResponse,
} from '../types/api';

vi.mock('../api/client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

const mockPost = vi.mocked(apiClient.post);
const mockGet = vi.mocked(apiClient.get);

describe('impactoEconomicoService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('createAnalysis', () => {
    it('posts to /analises and returns analysis', async () => {
      const response: AnalysisResponse = {
        id: 'a1',
        tenant_id: 't1',
        status: 'queued',
        method: 'did',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      };
      mockPost.mockResolvedValueOnce({ data: response } as never);

      const result = await impactoEconomicoService.createAnalysis({
        method: 'did',
        treated_ids: ['3304557'],
        treatment_year: 2010,
        outcomes: ['pib_pc_log'],
      });

      expect(mockPost).toHaveBeenCalledWith('/api/v1/impacto-economico/analises', {
        method: 'did',
        treated_ids: ['3304557'],
        treatment_year: 2010,
        outcomes: ['pib_pc_log'],
      });
      expect(result.id).toBe('a1');
      expect(result.status).toBe('queued');
    });
  });

  describe('getAnalysis (polling)', () => {
    it('fetches analysis status by id', async () => {
      const running: AnalysisResponse = {
        id: 'a1',
        tenant_id: 't1',
        status: 'running',
        method: 'did',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:01Z',
      };
      mockGet.mockResolvedValueOnce({ data: running } as never);

      const result = await impactoEconomicoService.getAnalysis('a1');
      expect(mockGet).toHaveBeenCalledWith('/api/v1/impacto-economico/analises/a1');
      expect(result.status).toBe('running');
    });
  });

  describe('getAnalysisResult', () => {
    it('fetches full result with summary and coefficients', async () => {
      const detail: AnalysisDetail = {
        id: 'a1',
        tenant_id: 't1',
        status: 'success',
        method: 'did',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:10Z',
        duration_seconds: 10,
        request_params: { method: 'did', treated_ids: ['3304557'] },
        result_summary: {
          outcome: 'pib_pc_log',
          coef: 0.15,
          std_err: 0.03,
          p_value: 0.001,
          ci_lower: 0.09,
          ci_upper: 0.21,
          n_obs: 500,
          r2: 0.42,
        },
        result_full: {
          main_result: {
            coef: 0.15,
            std_err: 0.03,
            p_value: 0.001,
            ci_lower: 0.09,
            ci_upper: 0.21,
          },
        },
      };
      mockGet.mockResolvedValueOnce({ data: detail } as never);

      const result = await impactoEconomicoService.getAnalysisResult('a1');
      expect(mockGet).toHaveBeenCalledWith('/api/v1/impacto-economico/analises/a1/result');
      expect(result.result_summary?.coef).toBe(0.15);
      expect(result.result_summary?.p_value).toBe(0.001);
      expect(result.result_full?.main_result).toBeDefined();
    });
  });

  describe('suggestMatchingControls', () => {
    it('posts matching request and returns candidates', async () => {
      const matching: MatchingResponse = {
        suggested_controls: [
          { id_municipio: '3301702', similarity_score: 0.92, distance: 0.08, is_treated: false },
          { id_municipio: '3305109', similarity_score: 0.88, distance: 0.12, is_treated: false },
        ],
        balance_table: {},
        scope: 'municipal',
        treatment_year: 2010,
        n_treated: 1,
        n_candidates: 50,
        features: ['pib_pc_log', 'pop_log'],
      };
      mockPost.mockResolvedValueOnce({ data: matching } as never);

      const result = await impactoEconomicoService.suggestMatchingControls({
        treated_ids: ['3304557'],
        treatment_year: 2010,
        scope: 'municipal',
        n_controls: 10,
      });

      expect(mockPost).toHaveBeenCalledWith('/api/v1/impacto-economico/matching', {
        treated_ids: ['3304557'],
        treatment_year: 2010,
        scope: 'municipal',
        n_controls: 10,
      });
      expect(result.suggested_controls).toHaveLength(2);
      expect(result.suggested_controls[0].similarity_score).toBe(0.92);
    });
  });

  describe('simulateImpact', () => {
    it('posts simulation request and returns projections', async () => {
      const sim: ImpactSimulationResponse = {
        analysis_id: 'a1',
        method: 'did',
        shock_intensity_pct: 10,
        shock_mode: 'movement',
        applied_shock_intensity_pct: 10,
        reference_outcome: 'pib_pc_log',
        reference_effect_100pct: 0.15,
        projected_outcomes: [
          {
            outcome: 'pib_pc_log',
            outcome_label: 'PIB per capita (log)',
            treatment_effect_100pct: 0.15,
            projected_delta_pct: 1.5,
            method_used: 'did',
            std_err: 0.03,
            coef: 0.15,
            p_value: 0.001,
            treatment_effect_100pct_ci_lower: 0.09,
            treatment_effect_100pct_ci_upper: 0.21,
            projected_delta_pct_conservative: 0.9,
            projected_delta_pct_optimistic: 2.1,
            notes: ['Efeito estatisticamente significativo'],
            confidence: 'forte',
            warning: null,
          },
        ],
        simulation_metadata: {
          model_version: '1.0',
          as_of: '2026-01-01',
          generated_by: 'saas_impacto',
          notes: [],
        },
        assumptions: ['Hipótese de linearidade'],
        executive_summary: ['Aumento de 10% na movimentação → +1.5% no PIB pc'],
      };
      mockPost.mockResolvedValueOnce({ data: sim } as never);

      const result = await impactoEconomicoService.simulateImpact('a1', {
        shock_mode: 'movement',
        shock_intensity_pct: 10,
        reference_outcome: 'pib_pc_log',
      });

      expect(mockPost).toHaveBeenCalledWith('/api/v1/impacto-economico/analises/a1/simulacao', {
        shock_mode: 'movement',
        shock_intensity_pct: 10,
        reference_outcome: 'pib_pc_log',
      });
      expect(result.projected_outcomes).toHaveLength(1);
      expect(result.projected_outcomes[0].confidence).toBe('forte');
      expect(result.projected_outcomes[0].projected_delta_pct).toBe(1.5);
    });
  });

  describe('getAnalysisReport', () => {
    it.each(['docx', 'pdf', 'xlsx'] as const)('downloads %s format', async (format) => {
      const blob = new Blob(['data'], { type: 'application/octet-stream' });
      mockGet.mockResolvedValueOnce({
        data: blob,
        headers: {
          'content-disposition': `attachment; filename="report.${format}"`,
        },
      } as never);

      const result = await impactoEconomicoService.getAnalysisReport('a1', format);
      expect(mockGet).toHaveBeenCalledWith('/api/v1/impacto-economico/analises/a1/report', {
        responseType: 'blob',
        params: { format },
      });
      expect(result.filename).toBe(`report.${format}`);
      expect(result.blob).toBeInstanceOf(Blob);
    });

    it('falls back to default filename when no content-disposition', async () => {
      const blob = new Blob(['data']);
      mockGet.mockResolvedValueOnce({
        data: blob,
        headers: {},
      } as never);

      const result = await impactoEconomicoService.getAnalysisReport('a1', 'pdf');
      expect(result.filename).toBe('analise_a1.pdf');
    });
  });

  describe('listAnalyses', () => {
    it('fetches paginated analysis list', async () => {
      const list = {
        total: 25,
        items: [
          { id: 'a1', tenant_id: 't1', status: 'success', method: 'did', created_at: '', updated_at: '' },
        ],
        page: 1,
        page_size: 10,
      };
      mockGet.mockResolvedValueOnce({ data: list } as never);

      const result = await impactoEconomicoService.listAnalyses({ page: 1, page_size: 10, status: 'success' });
      expect(mockGet).toHaveBeenCalledWith('/api/v1/impacto-economico/analises', {
        params: { page: 1, page_size: 10, status: 'success' },
      });
      expect(result.total).toBe(25);
      expect(result.items).toHaveLength(1);
    });
  });
});
