import { apiClient } from './client';

export interface EmploymentMultiplierConfidenceEstimate {
  confidence: 'strong' | 'moderate' | 'weak';
  municipality_id: string;
  municipality_name: string;
  year: number;
  multiplier_type: 'causal' | 'literature';
  multiplier_used: number;
  direct_jobs: number;
  indirect_estimated: number;
  induced_estimated: number;
  total_impact: number;
  source: string;
}

export interface EmploymentMultiplierLiterature {
  source: string;
  coefficient: number;
  range_low: number;
  range_high: number;
}

export interface EmploymentMultiplierCausal {
  source: string;
  method: 'iv_2sls' | 'panel_iv' | 'other';
  n_obs: number;
  r2: number;
}

export interface EmploymentMultiplierResponse {
  municipality_id: string;
  municipality_name: string;
  year: number;
  literature: EmploymentMultiplierLiterature;
  causal?: EmploymentMultiplierCausal | null;
  estimate: EmploymentMultiplierConfidenceEstimate;
  causal_estimate?: EmploymentMultiplierConfidenceEstimate | null;
}

export interface CausalEstimateResponse {
  active?: EmploymentMultiplierConfidenceEstimate;
}

export const employmentMultiplierService = {
  async getMultiplierEstimate(
    municipioId: string,
    ano?: number,
    useCausal: boolean = false,
  ): Promise<EmploymentMultiplierResponse & CausalEstimateResponse> {
    const response = await apiClient.get<EmploymentMultiplierResponse & CausalEstimateResponse>(
      `/api/v1/employment/multipliers/${encodeURIComponent(municipioId)}`,
      { params: { ano, use_causal: useCausal } },
    );
    return response.data;
  },
};

