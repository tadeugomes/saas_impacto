import { apiClient } from './client';
import type {
  OnboardingCompanyRequest,
  OnboardingCompanyResponse,
} from '../types/auth';

export const onboardingService = {
  async registerCompany(
    payload: OnboardingCompanyRequest,
  ): Promise<OnboardingCompanyResponse> {
    const response = await apiClient.post<OnboardingCompanyResponse>(
      '/api/v1/onboarding/register',
      payload,
    );
    return response.data;
  },
};
