import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useAnalysis } from '../hooks/useAnalysis';
import { impactoEconomicoService } from '../api/impactoEconomico';
import type { AnalysisResponse, AnalysisDetail } from '../types/api';

vi.mock('../api/impactoEconomico');

const mockGetAnalysis = vi.mocked(impactoEconomicoService.getAnalysis);
const mockGetResult = vi.mocked(impactoEconomicoService.getAnalysisResult);

function makeAnalysis(overrides: Partial<AnalysisResponse> = {}): AnalysisResponse {
  return {
    id: 'a1',
    tenant_id: 't1',
    status: 'queued',
    method: 'did',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

function makeResult(overrides: Partial<AnalysisDetail> = {}): AnalysisDetail {
  return {
    ...makeAnalysis({ status: 'success' }),
    request_params: { method: 'did', treated_ids: ['3304557'] },
    result_summary: {
      outcome: 'pib_pc_log',
      coef: 0.15,
      std_err: 0.03,
      p_value: 0.001,
      ci_lower: 0.09,
      ci_upper: 0.21,
      n_obs: 500,
    },
    result_full: {
      main_result: { coef: 0.15, std_err: 0.03, p_value: 0.001 },
    },
    ...overrides,
  };
}

describe('useAnalysis', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns idle state when no analysisId', () => {
    const { result } = renderHook(() => useAnalysis(null));
    expect(result.current.analysis).toBeNull();
    expect(result.current.result).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isPolling).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('fetches result when analysis is immediately successful', async () => {
    const success = makeAnalysis({ status: 'success' });
    const detail = makeResult();

    mockGetAnalysis.mockResolvedValueOnce(success);
    mockGetResult.mockResolvedValueOnce(detail);

    const { result } = renderHook(() => useAnalysis('a1'));

    await waitFor(() => {
      expect(result.current.analysis?.status).toBe('success');
      expect(result.current.isPolling).toBe(false);
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.result).not.toBeNull();
    expect(result.current.result?.result_summary?.coef).toBe(0.15);
    expect(mockGetAnalysis).toHaveBeenCalledTimes(1);
    expect(mockGetResult).toHaveBeenCalledTimes(1);
  });

  it('stops polling on failed status', async () => {
    const failed = makeAnalysis({ status: 'failed' });
    const detail = makeResult({ status: 'failed', error_message: 'Not enough data' });

    mockGetAnalysis.mockResolvedValueOnce(failed);
    mockGetResult.mockResolvedValueOnce(detail);

    const { result } = renderHook(() => useAnalysis('a1'));

    await waitFor(() => {
      expect(result.current.analysis?.status).toBe('failed');
      expect(result.current.isPolling).toBe(false);
    });
  });

  it('sets error on network failure', async () => {
    mockGetAnalysis.mockRejectedValueOnce(new Error('Network Error'));

    const { result } = renderHook(() => useAnalysis('a1'));

    await waitFor(() => {
      expect(result.current.error).toBe('Network Error');
      expect(result.current.isPolling).toBe(false);
      expect(result.current.isLoading).toBe(false);
    });
  });

  it('resets state when analysisId becomes null', async () => {
    const success = makeAnalysis({ status: 'success' });
    mockGetAnalysis.mockResolvedValueOnce(success);
    mockGetResult.mockResolvedValueOnce(makeResult());

    const { result, rerender } = renderHook(
      ({ id }) => useAnalysis(id),
      { initialProps: { id: 'a1' as string | null } }
    );

    await waitFor(() => {
      expect(result.current.analysis?.status).toBe('success');
    });

    rerender({ id: null });

    await waitFor(() => {
      expect(result.current.analysis).toBeNull();
      expect(result.current.result).toBeNull();
      expect(result.current.isPolling).toBe(false);
    });
  });

  it('refresh triggers a new poll cycle', async () => {
    const success = makeAnalysis({ status: 'success' });
    mockGetAnalysis.mockResolvedValue(success);
    mockGetResult.mockResolvedValue(makeResult());

    const { result } = renderHook(() => useAnalysis('a1'));

    await waitFor(() => {
      expect(result.current.analysis?.status).toBe('success');
    });

    act(() => {
      result.current.refresh();
    });

    await waitFor(() => {
      expect(mockGetAnalysis).toHaveBeenCalledTimes(2);
    });
  });

  it('extracts error detail from API response', async () => {
    const apiError = {
      response: { data: { detail: 'Rate limit exceeded' } },
    };
    mockGetAnalysis.mockRejectedValueOnce(apiError);

    const { result } = renderHook(() => useAnalysis('a1'));

    await waitFor(() => {
      expect(result.current.error).toBe('Rate limit exceeded');
    });
  });
});
