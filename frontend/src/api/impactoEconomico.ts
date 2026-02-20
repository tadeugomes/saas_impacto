import { apiClient } from './client';
import type {
  AnalysisCreateRequest,
  AnalysisResponse,
  AnalysisDetail,
  AnalysisListResponse,
  MatchingRequest,
  MatchingResponse,
} from '../types/api';

type BlobDownload = {
  blob: Blob;
  filename: string;
};

function extractFilename(contentDisposition: string | undefined, fallback: string): string {
  if (!contentDisposition) {
    return fallback;
  }
  const match = /filename="([^"]+)"/.exec(contentDisposition);
  return match && match[1] ? match[1] : fallback;
}

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

  async getAnalysisReport(id: string): Promise<BlobDownload> {
    const response = await apiClient.get<Blob>(`/api/v1/impacto-economico/analises/${id}/report`, {
      responseType: 'blob',
    });
    return {
      blob: response.data,
      filename: extractFilename(
        response.headers['content-disposition'],
        `analise_${id}.docx`,
      ),
    };
  },

  async suggestMatchingControls(payload: MatchingRequest): Promise<MatchingResponse> {
    const response = await apiClient.post<MatchingResponse>('/api/v1/impacto-economico/matching', payload);
    return response.data;
  },
};
