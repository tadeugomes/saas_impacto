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
  porto?: string;
  tipo_navegacao?: string;
  tipo_carga?: string;
}

export interface IndicatorRequest {
  codigo_indicador: string;
  params?: FilterParams;
}

export interface IndicatorResponse<T = any> {
  codigo: string;
  nome: string;
  descricao: string;
  unidade: string;
  unctad_compliant: boolean;
  data: T[];
}

export interface IndicatorMetadata {
  codigo: string;
  nome: string;
  descricao: string;
  modulo: number;
  unidade: string;
  unctad_compliant: boolean;
  formula?: string;
  fontes_dados?: string[];
}
