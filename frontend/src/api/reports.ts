import { apiClient } from './client';

export interface ReportExportParams {
  moduleCode?: string;
  indicatorCode?: string;
  id_instalacao?: string;
  id_municipio?: string;
  ano?: number;
  ano_inicio?: number;
  ano_fim?: number;
}

export const reportsService = {
  /**
   * Exporta um módulo completo para DOCX
   */
  async exportModule(params: ReportExportParams): Promise<void> {
    const { moduleCode, ...queryParams } = params;

    if (!moduleCode) {
      throw new Error('Código do módulo é obrigatório');
    }

    const response = await apiClient.post(
      `/api/v1/reports/module/${moduleCode}`,
      {},
      {
        params: queryParams,
        responseType: 'blob',
      }
    );

    // Download do arquivo
    const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }));
    const link = document.createElement('a');
    link.href = url;

    // Extrai filename do header Content-Disposition
    const contentDisposition = response.headers['content-disposition'];
    let filename = `relatorio_${moduleCode}.docx`;
    if (contentDisposition) {
      const matches = /filename="([^"]+)"/.exec(contentDisposition);
      if (matches && matches[1]) {
        filename = matches[1];
      }
    }

    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  /**
   * Exporta um indicador individual para DOCX
   */
  async exportIndicator(params: ReportExportParams): Promise<void> {
    const { indicatorCode, ...queryParams } = params;

    if (!indicatorCode) {
      throw new Error('Código do indicador é obrigatório');
    }

    const response = await apiClient.post(
      `/api/v1/reports/indicator/${indicatorCode}`,
      {},
      {
        params: queryParams,
        responseType: 'blob',
      }
    );

    // Download do arquivo
    const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }));
    const link = document.createElement('a');
    link.href = url;

    // Extrai filename do header Content-Disposition
    const contentDisposition = response.headers['content-disposition'];
    let filename = `relatorio_${indicatorCode}.docx`;
    if (contentDisposition) {
      const matches = /filename="([^"]+)"/.exec(contentDisposition);
      if (matches && matches[1]) {
        filename = matches[1];
      }
    }

    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};
