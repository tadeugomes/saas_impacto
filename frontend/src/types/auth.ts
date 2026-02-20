export interface User {
  id: string;
  email: string;
  name: string;
  nome?: string;
  tenant_id?: string;
  roles?: string[];
  ativo?: boolean;
  created_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  nome: string;
  tenant_slug: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface OnboardingCompanyRequest {
  empresa: string;
  cnpj?: string;
  plano: string;
  nome_admin: string;
  email_admin: string;
  senha_admin: string;
}

export interface OnboardingCompanyResponse {
  tenant_id: string;
  user_id: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface MeResponse {
  id: string;
  email: string;
  nome: string;
  tenant_id: string;
  roles: string[];
  ativo: boolean;
  created_at: string;
}
