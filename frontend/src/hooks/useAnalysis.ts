import { useCallback, useEffect, useRef, useState } from 'react';

import { impactoEconomicoService } from '../api/impactoEconomico';
import type { AnalysisDetail, AnalysisResponse, AnalysisStatus } from '../types/api';

type UseAnalysisState = {
  analysis: AnalysisResponse | null;
  result: AnalysisDetail | null;
  isLoading: boolean;
  isPolling: boolean;
  error: string | null;
  refresh: () => void;
};

const POLLING_BY_STATUS: Record<AnalysisStatus, number> = {
  queued: 2000,
  running: 5000,
  success: 0,
  failed: 0,
};

function isTerminal(status: AnalysisStatus): boolean {
  return status === 'success' || status === 'failed';
}

function normalizeAnalysisStatus(value: string | undefined): AnalysisStatus | undefined {
  if (value === 'queued' || value === 'running' || value === 'success' || value === 'failed') {
    return value;
  }
  return undefined;
}

export function useAnalysis(analysisId: string | null | undefined): UseAnalysisState {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [result, setResult] = useState<AnalysisDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timeoutRef = useRef<number | null>(null);

  const clearTimeoutIfNeeded = () => {
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  };

  const loadStatus = useCallback(
    async (id: string) => {
      const status = await impactoEconomicoService.getAnalysis(id);
      const normalized = normalizeAnalysisStatus(status.status);

      if (!normalized) {
        throw new Error(`Status inesperado: ${status.status}`);
      }

      const normalizedAnalysis: AnalysisResponse = {
        ...status,
        status: normalized,
      };

      setAnalysis(normalizedAnalysis);
      return normalizedAnalysis;
    },
    []
  );

  const loadResult = useCallback(async (id: string) => {
    const detail = await impactoEconomicoService.getAnalysisResult(id);
    setResult(detail);
    return detail;
  }, []);

  const poll = useCallback(
    async (id: string) => {
      try {
        const status = await loadStatus(id);

        if (isTerminal(status.status)) {
          setIsPolling(false);
          try {
            await loadResult(id);
          } catch {
            // Fallback: caso o processamento falhe entre chamadas de status e resultado
            // mantemos o estado de sucesso/failed sem bloquear a UI.
            setResult(null);
          }
          return;
        }

        const delay = POLLING_BY_STATUS[status.status];
        setIsPolling(true);
        timeoutRef.current = window.setTimeout(() => {
          poll(id);
        }, delay);
      } catch (err: unknown) {
        clearTimeoutIfNeeded();
        setIsPolling(false);
        const errorResponse = err as { response?: { data?: { detail?: unknown } } };
        setError(
          errorResponse?.response?.data?.detail
            ? String(errorResponse.response.data.detail)
            : err instanceof Error
              ? err.message
              : 'Erro ao consultar análise.'
        );
      } finally {
        setIsLoading(false);
      }
    },
    [loadResult, loadStatus]
  );

  const refresh = useCallback(() => {
    if (!analysisId) {
      return;
    }
    clearTimeoutIfNeeded();
    setError(null);
    setResult(null);
    setAnalysis(null);
    setIsPolling(true);
    setIsLoading(true);
    poll(analysisId);
  }, [analysisId, poll]);

  useEffect(() => {
    if (!analysisId) {
      clearTimeoutIfNeeded();
      setIsPolling(false);
      setAnalysis(null);
      setResult(null);
      setIsLoading(false);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);
    poll(analysisId);

    return () => {
      clearTimeoutIfNeeded();
    };
  }, [analysisId, poll]);

  return {
    analysis,
    result,
    isLoading,
    isPolling,
    error,
    refresh,
  };
}
