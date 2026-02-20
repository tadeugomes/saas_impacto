import { apiClient } from './client';
import type {
  AnalysisCreateRequest,
  AnalysisResponse,
  AnalysisDetail,
  AnalysisListResponse,
} from '../types/api';

export const impactoEconomicoService = {
  async createAnalysis(payload: AnalysisCreateRequest): Promise<AnalysisResponse> {
    const response = await apiClient.post<AnalysisResponse>('/api/v1/impacto-economico/analises', payload);
    return response.data;
  },

  async listAnalyses(params?: {
    page?: number;
    page_size?: number;
    status?: string;
    method?: string;
  }): Promise<AnalysisListResponse> {
    const response = await apiClient.get<AnalysisListResponse>('/api/v1/impacto-economico/analises', {
      params,
    });
    return response.data;
  },

  async getAnalysis(id: string): Promise<AnalysisResponse> {
    const response = await apiClient.get<AnalysisResponse>(`/api/v1/impacto-economico/analises/${id}`);
    return response.data;
  },

  async getAnalysisResult(id: string): Promise<AnalysisDetail> {
    const response = await apiClient.get<AnalysisDetail>(`/api/v1/impacto-economico/analises/${id}/result`);
    return response.data;
  },
};
