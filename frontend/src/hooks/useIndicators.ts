import { useState, useCallback } from 'react';
import { indicatorsService } from '../api/indicators';
import type { FilterParams, IndicatorResponse } from '../types/api';

interface UseIndicatorsResult<T = any> {
  data: IndicatorResponse<T> | null;
  isLoading: boolean;
  error: string | null;
  fetchIndicator: (code: string, params?: FilterParams) => Promise<void>;
  reset: () => void;
}

export function useIndicators<T = any>(): UseIndicatorsResult<T> {
  const [data, setData] = useState<IndicatorResponse<T> | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchIndicator = useCallback(async (code: string, params?: FilterParams) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await indicatorsService.queryIndicator<T>({ codigo_indicador: code, params });
      setData(result);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Erro ao buscar indicador';
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

// Hook para buscar múltiplos indicadores em paralelo
export function useMultipleIndicators(codes: string[]) {
  const [data, setData] = useState<Record<string, any>>({});
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
      const mappedResults: Record<string, any> = {};
      results.forEach((result, index) => {
        mappedResults[codes[index]] = result;
      });
      setData(mappedResults);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Erro ao buscar indicadores';
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
