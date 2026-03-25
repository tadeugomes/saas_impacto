import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MethodComparisonTable } from '../components/impactoEconomico/MethodComparisonTable';
import { AnalysisResultCard } from '../components/impactoEconomico/AnalysisResultCard';
import { AnalysisStatusBadge } from '../components/impactoEconomico/AnalysisStatusBadge';
import type { AnalysisDetail } from '../types/api';

// ─── MethodComparisonTable ────────────────────────────────────────────────────

describe('MethodComparisonTable', () => {
  it('renders nothing when items is empty', () => {
    const { container } = render(<MethodComparisonTable items={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders comparison table with DiD and IV rows', () => {
    const items = [
      {
        outcome: 'pib_pc_log',
        recommendation: 'Prefer DiD',
        consistency_assessment: 'consistent',
        comparison_table: [
          {
            Method: 'DiD',
            Estimate: 0.15,
            SE: 0.03,
            CI_Lower: 0.09,
            CI_Upper: 0.21,
            P_Value: 0.001,
            Significant: 'Yes',
            Notes: null,
          },
          {
            Method: 'IV',
            Estimate: 0.13,
            SE: 0.04,
            CI_Lower: 0.05,
            CI_Upper: 0.21,
            P_Value: 0.003,
            Significant: 'Yes',
            Notes: 'First stage F=28',
          },
        ],
      },
    ];

    render(<MethodComparisonTable items={items} />);

    expect(screen.getByText('Comparação de métodos: pib_pc_log')).toBeInTheDocument();
    expect(screen.getByText('DiD')).toBeInTheDocument();
    expect(screen.getByText('IV')).toBeInTheDocument();
    expect(screen.getByText('0.1500')).toBeInTheDocument();
    expect(screen.getByText('0.1300')).toBeInTheDocument();
    expect(screen.getByText('First stage F=28')).toBeInTheDocument();
    expect(screen.getByText('Recomendação: Prefer DiD')).toBeInTheDocument();
    expect(screen.getByText('Consistência: consistent')).toBeInTheDocument();
  });

  it('shows empty comparison message when no table rows', () => {
    const items = [
      {
        outcome: 'pib_pc_log',
        comparison_table: [],
      },
    ];
    render(<MethodComparisonTable items={items} />);
    expect(screen.getByText('Sem tabela de comparação para este outcome.')).toBeInTheDocument();
  });

  it('renders multiple outcome comparisons', () => {
    const items = [
      {
        outcome: 'pib_pc_log',
        comparison_table: [
          { Method: 'DiD', Estimate: 0.15, SE: 0.03, CI_Lower: 0.09, CI_Upper: 0.21, P_Value: 0.001, Significant: 'Yes' },
        ],
      },
      {
        outcome: 'emp_formal_log',
        comparison_table: [
          { Method: 'IV', Estimate: 0.08, SE: 0.02, CI_Lower: 0.04, CI_Upper: 0.12, P_Value: 0.02, Significant: 'Yes' },
        ],
      },
    ];
    render(<MethodComparisonTable items={items} />);
    expect(screen.getByText('Comparação de métodos: pib_pc_log')).toBeInTheDocument();
    expect(screen.getByText('Comparação de métodos: emp_formal_log')).toBeInTheDocument();
  });

  it('displays em-dash for null values', () => {
    const items = [
      {
        outcome: 'pib_pc_log',
        comparison_table: [
          { Method: 'DiD', Estimate: null, SE: null, CI_Lower: null, CI_Upper: null, P_Value: null, Significant: '—', Notes: null },
        ],
      },
    ];
    render(<MethodComparisonTable items={items} />);
    const dashes = screen.getAllByText('—');
    expect(dashes.length).toBeGreaterThan(0);
  });
});

// ─── AnalysisStatusBadge ──────────────────────────────────────────────────────

describe('AnalysisStatusBadge', () => {
  it.each([
    ['queued', 'Na fila'],
    ['running', 'Em execução'],
    ['success', 'Concluída'],
    ['failed', 'Falhou'],
  ] as const)('renders correct label for status "%s"', (status, label) => {
    render(<AnalysisStatusBadge status={status} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it('applies correct color class for success', () => {
    const { container } = render(<AnalysisStatusBadge status="success" />);
    const badge = container.querySelector('span');
    expect(badge?.className).toContain('emerald');
  });

  it('applies correct color class for failed', () => {
    const { container } = render(<AnalysisStatusBadge status="failed" />);
    const badge = container.querySelector('span');
    expect(badge?.className).toContain('red');
  });

  it('applies pulse animation for running', () => {
    const { container } = render(<AnalysisStatusBadge status="running" />);
    const badge = container.querySelector('span');
    expect(badge?.className).toContain('animate-pulse');
  });
});

// ─── AnalysisResultCard ───────────────────────────────────────────────────────

function makeDetail(overrides: Partial<AnalysisDetail> = {}): AnalysisDetail {
  return {
    id: 'a1',
    tenant_id: 't1',
    status: 'success',
    method: 'did',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:10Z',
    duration_seconds: 10.5,
    started_at: '2026-01-01T00:00:00Z',
    completed_at: '2026-01-01T00:00:10Z',
    request_params: { method: 'did', treated_ids: ['3304557'], treatment_year: 2010 },
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
      main_result: { coef: 0.15, p_value: 0.001 },
    },
    ...overrides,
  };
}

describe('AnalysisResultCard', () => {
  it('renders outcome, coefficient and significance', () => {
    render(<AnalysisResultCard detail={makeDetail()} />);
    expect(screen.getByText('pib_pc_log')).toBeInTheDocument();
    expect(screen.getByText('0,1500')).toBeInTheDocument(); // pt-BR decimal
    expect(screen.getByText('Significativo')).toBeInTheDocument();
  });

  it('shows status badge', () => {
    render(<AnalysisResultCard detail={makeDetail({ status: 'success' })} />);
    expect(screen.getByText('Concluída')).toBeInTheDocument();
  });

  it('shows "Não significativo" for p > 0.05', () => {
    render(<AnalysisResultCard detail={makeDetail({ result_summary: { p_value: 0.12, coef: 0.02, n_obs: 200 } })} />);
    expect(screen.getByText('Não significativo')).toBeInTheDocument();
  });

  it('shows error message when present', () => {
    const detail = makeDetail({ status: 'failed', error_message: 'Dados insuficientes para o período.' });
    render(<AnalysisResultCard detail={detail} />);
    expect(screen.getByText('Dados insuficientes para o período.')).toBeInTheDocument();
  });

  it('shows analysis warnings', () => {
    const detail = makeDetail({
      result_summary: {
        coef: 0.15,
        p_value: 0.001,
        n_obs: 500,
        warnings: ['Poucos municípios de controle', 'Alta heterogeneidade'],
      },
    });
    render(<AnalysisResultCard detail={detail} />);
    expect(screen.getByText('Poucos municípios de controle')).toBeInTheDocument();
    expect(screen.getByText('Alta heterogeneidade')).toBeInTheDocument();
  });

  it('shows method in result description', () => {
    render(<AnalysisResultCard detail={makeDetail({ method: 'iv' })} />);
    // method appears in bold within "Método: iv"
    expect(screen.getByText('iv')).toBeInTheDocument();
  });

  it('triggers JSON export on button click', () => {
    const createObjectURL = vi.fn(() => 'blob:mock');
    const revokeObjectURL = vi.fn();
    const clickMock = vi.fn();
    window.URL.createObjectURL = createObjectURL;
    window.URL.revokeObjectURL = revokeObjectURL;

    // Mock createElement to intercept the download link
    const originalCreateElement = document.createElement.bind(document);
    vi.spyOn(document, 'createElement').mockImplementation((tag) => {
      if (tag === 'a') {
        const el = originalCreateElement('a');
        el.click = clickMock;
        return el;
      }
      return originalCreateElement(tag);
    });

    render(<AnalysisResultCard detail={makeDetail()} />);
    const exportButton = screen.getByTitle('Exportar JSON bruto');
    fireEvent.click(exportButton);

    expect(createObjectURL).toHaveBeenCalled();
    expect(clickMock).toHaveBeenCalled();
    expect(revokeObjectURL).toHaveBeenCalled();

    vi.restoreAllMocks();
  });

  it('renders em-dash when coefficient is null', () => {
    render(<AnalysisResultCard detail={makeDetail({ result_summary: { coef: null, p_value: null, n_obs: null } })} />);
    const dashes = screen.getAllByText('—');
    expect(dashes.length).toBeGreaterThan(0);
  });

  it('shows duration in seconds', () => {
    render(<AnalysisResultCard detail={makeDetail({ duration_seconds: 7.3 })} />);
    // toFixed(1) produces "7.3" regardless of locale
    expect(screen.getByText('7.3s')).toBeInTheDocument();
  });
});
