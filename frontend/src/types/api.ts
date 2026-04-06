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

export interface PolicyMunicipioItem {
  id_municipio: string;
  peso?: number;
}

export interface PolicyInstallationItem {
  id_instalacao: string;
  peso?: number;
}

export interface TenantPoliciesResponse {
  tenant_id: string;
  allowed_installations: string[];
  allowed_municipios: string[];
  municipio_influencia?: Record<string, PolicyMunicipioItem[]>;
  municipio_to_installations?: Record<string, PolicyInstallationItem[]>;
  area_influencia?: Record<string, PolicyMunicipioItem[]>;
  max_bytes_per_query?: number | null;
}

export interface MunicipioLookupItem {
  id_municipio: string;
  nome_municipio: string;
}

export interface MunicipioLookupResponse {
  municipios: MunicipioLookupItem[];
}

export interface InstallationMunicipioResolution {
  id_instalacao: string;
  id_municipio: string | null;
  municipio_found: boolean;
  message: string;
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

export type SimulationShockMode = 'movement' | 'investment';

export interface AdminDashboardItem {
  codigo: string;
  nome: string;
  acessos: number;
}

export interface TenantUsageResponse {
  total_analises: number;
  analises_sucesso: number;
  analises_falha: number;
  usuarios_ativos_7d: number;
  usuarios_ativos_30d: number;
  bq_bytes_last_30d: number;
  taxa_rate_limit?: number | null;
  top_indicadores: AdminDashboardItem[];
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

export interface ImpactSimulationRequest {
  shock_mode?: SimulationShockMode;
  shock_intensity_pct: number;
  investment_to_movement_elasticity?: number | null;
  reference_outcome?: string;
  target_outcomes?: string[];
}

export interface ImpactSimulationProjection {
  outcome: string;
  outcome_label: string;
  treatment_effect_100pct: number | null;
  projected_delta_pct: number | null;
  method_used: string;
  std_err: number | null;
  coef: number | null;
  p_value: number | null;
  treatment_effect_100pct_ci_lower: number | null;
  treatment_effect_100pct_ci_upper: number | null;
  projected_delta_pct_conservative: number | null;
  projected_delta_pct_optimistic: number | null;
  notes: string[];
  confidence: 'forte' | 'moderada' | 'fraca';
  warning: string | null;
}

export interface ImpactSimulationMetadata {
  model_version: string;
  as_of: string;
  generated_by: string;
  notes: string[];
}

export interface ImpactSimulationResponse {
  analysis_id: string;
  method: string;
  shock_intensity_pct: number;
  shock_mode: SimulationShockMode;
  applied_shock_intensity_pct: number;
  investment_to_movement_elasticity?: number | null;
  reference_outcome: string;
  reference_effect_100pct: number | null;
  projected_outcomes: ImpactSimulationProjection[];
  simulation_metadata: ImpactSimulationMetadata;
  assumptions: string[];
  executive_summary: string[];
}

// ── Módulo 6: Contribuição Fiscal Direta ─────────────────────────────────────

export interface ElasticidadeResult {
  beta: number;
  ci_lower: number;
  ci_upper: number;
  r2: number;
  p_value: number;
  n_obs: number;
  n_portos: number;
  especificacao?: string;
  fe_result?: Record<string, number> | null;
}

export interface ScatterPoint {
  porto: string;
  uf: string;
  ano: number;
  tonelagem_m_ton: number;
  iss_r_mi: number;
  trib_federais_r_mi?: number | null;
}

export interface CompositionItem {
  porto: string;
  uf: string;
  municipal_r_mi: number;
  federal_r_mi: number;
  total_r_mi: number;
  pct_municipal: number;
  pct_federal: number;
}

export interface FiscalElasticidadeResponse {
  elasticidade_municipal: ElasticidadeResult | null;
  elasticidade_federal: ElasticidadeResult | null;
  scatter_points: ScatterPoint[];
  composition: CompositionItem[];
  portos_disponiveis: string[];
  nota_metodologica: string;
}

export interface ParticipacaoISSItem {
  porto: string;
  uf: string;
  nome_municipio: string;
  ano: number;
  iss_df_r_mi: number;
  iss_finbra_r_mi: number;
  participacao_pct: number;
}

export interface ParticipacaoISSPorto {
  porto: string;
  uf: string;
  nome_municipio: string;
  participacao_atual_pct: number;
  ano_referencia: number;
  iss_df_r_mi: number;
  iss_finbra_r_mi: number;
  tendencia: 'crescente' | 'estavel' | 'decrescente' | 'sem_dados';
  serie: ParticipacaoISSItem[];
}

export interface ParticipacaoISSResponse {
  portos: ParticipacaoISSPorto[];
  nota_metodologica: string;
}

export interface SimulacaoFiscalResponse {
  porto: string;
  ano_referencia: number | null;
  shock_pct: number;
  baseline_municipal_r_mi: number | null;
  baseline_federal_r_mi: number | null;
  delta_municipal_r_mi: number | null;
  delta_federal_r_mi: number | null;
  delta_municipal_ci: [number, number] | null;
  delta_federal_ci: [number, number] | null;
  elasticidade_usada: string;
  nota: string;
}
