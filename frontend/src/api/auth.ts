import { apiClient } from './client';
import type { LoginRequest, LoginResponse, RegisterRequest, User } from '../types/auth';

export const authService = {
  async login(data: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/api/v1/auth/login', data);
    // Salvar tokens
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    return response.data;
  },

  async register(data: RegisterRequest): Promise<void> {
    await apiClient.post('/api/v1/auth/register', data);
  },

  async logout(): Promise<void> {
    await apiClient.post('/api/v1/auth/logout');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/api/v1/auth/me');
    return response.data;
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },
};
