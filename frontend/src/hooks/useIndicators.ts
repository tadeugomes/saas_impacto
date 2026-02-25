import { useState, useCallback } from 'react';
import { indicatorsService } from '../api/indicators';
import type { FilterParams, IndicatorResponse } from '../types/api';

interface UseIndicatorsResult<T = unknown> {
  data: IndicatorResponse<T> | null;
  isLoading: boolean;
  error: string | null;
  fetchIndicator: (code: string, params?: FilterParams) => Promise<void>;
  reset: () => void;
}

export function useIndicators<T = unknown>(): UseIndicatorsResult<T> {
  const [data, setData] = useState<IndicatorResponse<T> | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchIndicator = useCallback(async (code: string, params?: FilterParams) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await indicatorsService.queryIndicator<T>({ codigo_indicador: code, params });
      setData(result);
    } catch (err: unknown) {
      const errorResponse = err as { response?: { data?: { detail?: unknown } } };
      const errorMessage = errorResponse?.response?.data?.detail || 'Erro ao buscar indicador';
      setError(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return {
    data,
    isLoading,
    error,
    fetchIndicator,
    reset,
  };
}

export function useMultipleIndicators(codes: string[]) {
  const [data, setData] = useState<Record<string, IndicatorResponse<unknown>>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async (params?: FilterParams) => {
    setIsLoading(true);
    setError(null);
    try {
      const promises = codes.map((code) =>
        indicatorsService.queryIndicator({ codigo_indicador: code, params })
      );
      const results = await Promise.all(promises);
      const mappedResults: Record<string, IndicatorResponse<unknown>> = {};
      results.forEach((result, index) => {
        mappedResults[codes[index]] = result;
      });
      setData(mappedResults);
    } catch (err: unknown) {
      const errorResponse = err as { response?: { data?: { detail?: unknown } } };
      const errorMessage = errorResponse?.response?.data?.detail || 'Erro ao buscar indicadores';
      setError(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
    } finally {
      setIsLoading(false);
    }
  }, [codes]);

  return {
    data,
    isLoading,
    error,
    fetchAll,
  };
}
