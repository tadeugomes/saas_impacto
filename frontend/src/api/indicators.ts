import { apiClient } from './client';
import type {
  FilterParams,
  IndicatorRequest,
  IndicatorResponse,
  ModulesOverview,
  IndicatorMetadata,
} from '../types/api';

export const indicatorsService = {
  async queryIndicator<T = any>(request: IndicatorRequest): Promise<IndicatorResponse<T>> {
    const { params, ...rest } = request;
    const body = { ...rest, ...params };
    const response = await apiClient.post<IndicatorResponse<T>>('/api/v1/indicators/query', body);
    return response.data;
  },

  async getMetadata(): Promise<{ indicadores: IndicatorMetadata[] }> {
    const response = await apiClient.get('/api/v1/indicators/metadata');
    return response.data;
  },

  async getIndicatorMetadata(code: string): Promise<IndicatorMetadata> {
    const response = await apiClient.get(`/api/v1/indicators/metadata/${code}`);
    return response.data;
  },

  async getModulesOverview(): Promise<ModulesOverview> {
    const response = await apiClient.get('/api/v1/indicators/modules');
    return response.data;
  },

  // Módulo 1 - Operações de Navios
  async getTempoMedioEspera(params?: FilterParams) {
    return this.queryIndicator({ codigo_indicador: 'IND-1.01', params });
  },

  async getTempoMedioPorto(params?: FilterParams) {
    return this.queryIndicator({ codigo_indicador: 'IND-1.02', params });
  },

  async getTempoBrutoAtracacao(params?: FilterParams) {
    return this.queryIndicator({ codigo_indicador: 'IND-1.03', params });
  },

  async getTempoLiquidoOperacao(params?: FilterParams) {
    return this.queryIndicator({ codigo_indicador: 'IND-1.04', params });
  },

  async getTaxaOcupacaoBercoes(params?: FilterParams) {
    return this.queryIndicator({ codigo_indicador: 'IND-1.05', params });
  },

  async getTempoOciosoTurno(params?: FilterParams) {
    return this.queryIndicator({ codigo_indicador: 'IND-1.06', params });
  },

  async getArqueacaoBrutaMedia(params?: FilterParams) {
    return this.queryIndicator({ codigo_indicador: 'IND-1.07', params });
  },

  async getComprimentoMedioNavios(params?: FilterParams) {
    return this.queryIndicator({ codigo_indicador: 'IND-1.08', params });
  },

  async getCaladoMaximoOperacional(params?: FilterParams) {
    return this.queryIndicator({ codigo_indicador: 'IND-1.09', params });
  },

  async getDistribuicaoTipoNavio(params?: FilterParams) {
    return this.queryIndicator({ codigo_indicador: 'IND-1.10', params });
  },

  async getNumeroAtracacoes(params?: FilterParams) {
    return this.queryIndicator({ codigo_indicador: 'IND-1.11', params });
  },

  async getIndiceParalisacao(params?: FilterParams) {
    return this.queryIndicator({ codigo_indicador: 'IND-1.12', params });
  },
};
