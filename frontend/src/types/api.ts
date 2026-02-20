export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
}

export interface ModulesOverview {
  sistema: string;
  total_indicadores: number;
  unctad_compliant: number;
  total_modulos: number;
  modulos: ModuleOverview[];
}

export interface ModuleOverview {
  modulo: number;
  nome: string;
  total_indicadores: number;
  unctad_compliant: number;
}

export interface FilterParams {
  ano?: number;
  ano_inicio?: number;
  ano_fim?: number;
  id_instalacao?: string;
  id_municipio?: string;
  porto?: string;
  tipo_navegacao?: string;
  tipo_carga?: string;
}

export interface IndicatorRequest {
  codigo_indicador: string;
  params?: FilterParams;
}

export interface IndicatorResponse<T = unknown> {
  codigo_indicador: string;
  nome: string;
  unidade: string;
  unctad: boolean;
  modulo?: number;
  data_referencia?: string;
  warnings?: Array<{
    tipo: string;
    codigo_indicador: string;
    campo?: string;
    id_municipio?: string;
    ano?: number;
    valor?: number;
    mensagem: string;
  }>;
  data: T[];
}

export interface IndicatorMetadata {
  codigo: string;
  nome: string;
  modulo: number;
  unidade: string;
  unctad: boolean;
  implementation_status: 'implemented' | 'technical_debt';
  descricao?: string;
  granularidade?: string;
  fonte_dados?: string;
}

export interface AllIndicatorsMetadataResponse {
  total_indicadores: number;
  unctad_compliant: number;
  technical_debt_indicators: string[];
  indicadores: IndicatorMetadata[];
}

export type AnalysisStatus = 'queued' | 'running' | 'success' | 'failed';

export type AnalysisMethod =
  | 'did'
  | 'iv'
  | 'panel_iv'
  | 'event_study'
  | 'compare'
  | 'scm'
  | 'augmented_scm';

export type AnalysisScope = 'state' | 'municipal';

export interface MatchingCandidate {
  id_municipio: string;
  similarity_score: number | null;
  distance: number | null;
  is_treated: boolean;
}

export interface MatchingRequest {
  treated_ids: string[];
  treatment_year: number;
  scope?: AnalysisScope;
  n_controls?: number;
  ano_inicio?: number;
  ano_fim?: number;
  features?: string[] | null;
}

export interface MatchingResponse {
  suggested_controls: MatchingCandidate[];
  balance_table: Record<string, unknown>;
  scope: AnalysisScope;
  treatment_year: number;
  n_treated: number;
  n_candidates: number;
  features: string[];
}

export interface AnalysisCreateRequest {
  method: AnalysisMethod;
  treated_ids: string[];
  control_ids?: string[] | null;
  treatment_year: number;
  scope?: AnalysisScope;
  outcomes: string[];
  controls?: string[] | null;
  instrument?: string | null;
  ano_inicio?: number;
  ano_fim?: number;
  use_mart?: boolean;
}

export interface AnalysisResponse {
  id: string;
  tenant_id: string;
  user_id?: string | null;
  status: AnalysisStatus;
  method: string;
  created_at: string;
  updated_at: string;
}

export interface AnalysisListResponse {
  total: number;
  items: AnalysisResponse[];
  page: number;
  page_size: number;
}

export interface AnalysisSummary {
  outcome?: string | null;
  coef?: number | null;
  std_err?: number | null;
  p_value?: number | null;
  ci_lower?: number | null;
  ci_upper?: number | null;
  n_obs?: number | null;
  r2?: number | null;
  warnings?: string[];
  method?: string;
  outcomes?: string[];
  treatment_year?: number | null;
  treated_ids?: string[];
  n_treated?: number;
  n_control?: number;
  ano_inicio?: number;
  ano_fim?: number;
  [key: string]: unknown;
}

export interface AnalysisDetail extends AnalysisResponse {
  started_at?: string | null;
  completed_at?: string | null;
  duration_seconds?: number | null;
  request_params: Record<string, unknown>;
  result_summary?: AnalysisSummary | null;
  result_full?: Record<string, unknown> | null;
  artifact_path?: string | null;
  error_message?: string | null;
}
