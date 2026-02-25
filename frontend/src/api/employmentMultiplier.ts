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

export interface EmploymentShockScenario {
  delta_tonelagem_pct: number;
  delta_empregos_diretos: number;
  delta_empregos_indiretos: number;
  delta_empregos_induzidos: number;
  delta_emprego_total: number;
}

export interface EmploymentMultiplierImpactRow {
  municipality_id: string;
  municipality_name: string | null;
  ano: number;
  empregos_diretos: number;
  empregos_totais: number | null;
  participacao_emprego_local: number | null;
  tonelagem_antaq_milhoes: number | null;
  empregos_por_milhao_toneladas: number | null;
  empregos_indiretos_estimados: number;
  empregos_induzidos_estimados: number;
  emprego_total_estimado: number;
  metodologia: string;
  indicador_de_confianca: 'forte' | 'moderado' | 'baixo';
  correlacao_ou_proxy: boolean;
  metodo: string;
  fonte: string;
  scenario?: EmploymentShockScenario | null;
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
  data?: EmploymentMultiplierImpactRow[];
  literature: EmploymentMultiplierLiterature;
  causal?: EmploymentMultiplierCausal | null;
  estimate: EmploymentMultiplierConfidenceEstimate;
  active?: EmploymentMultiplierConfidenceEstimate | null;
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
    deltaTonelagemPct?: number,
  ): Promise<EmploymentMultiplierResponse & CausalEstimateResponse> {
    const params: Record<string, number | boolean | undefined> = {
      ano,
      use_causal: useCausal,
    };
    if (deltaTonelagemPct !== undefined) params.delta_tonelagem_pct = deltaTonelagemPct;

    const response = await apiClient.get<EmploymentMultiplierResponse & CausalEstimateResponse>(
      `/api/v1/employment/multipliers/${encodeURIComponent(municipioId)}`,
      { params },
    );
    return response.data;
  },
};
