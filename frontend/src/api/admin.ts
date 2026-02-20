import { apiClient } from './client';
import type { TenantUsageResponse } from '../types/api';

export const adminService = {
  async getDashboardUsage(): Promise<TenantUsageResponse> {
    const response = await apiClient.get<TenantUsageResponse>('/api/v1/admin/dashboard/usage');
    return response.data;
  },
};
