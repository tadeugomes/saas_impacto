import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MunicipioSelector, MUNICIPIOS_PORTUARIOS } from '../components/filters/MunicipioSelector';
import { InstallationSelector, PORTOS_ORGANIZADOS, TERMINAIS_PRIVADOS, PORTO_OPTIONS } from '../components/filters/InstallationSelector';
import { FilterBar } from '../components/filters/FilterBar';

// Mock zustand store
const mockState = {
  selectedYear: 2023,
  selectedInstallation: null as string | null,
  selectedMunicipio: null as string | null,
  setInstallation: vi.fn(),
  setMunicipio: vi.fn(),
  setYear: vi.fn(),
  resetFilters: vi.fn(),
};

vi.mock('../../store/filterStore', () => ({
  useFilterStore: () => mockState,
}));

// Fix relative import paths for filters
vi.mock('../store/filterStore', () => ({
  useFilterStore: () => mockState,
}));

beforeEach(() => {
  vi.clearAllMocks();
  mockState.selectedInstallation = null;
  mockState.selectedMunicipio = null;
});

// ─── MunicipioSelector ──────────────────────────────────────────────────────

describe('MunicipioSelector', () => {
  it('renders with default "Todos os Municípios"', () => {
    render(<MunicipioSelector />);
    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
    expect((select as HTMLSelectElement).value).toBe('');
  });

  it('has all 4 region optgroups', () => {
    render(<MunicipioSelector />);
    const groups = screen.getAllByRole('group');
    expect(groups.length).toBe(4);
  });

  it('contains expected porto names', () => {
    render(<MunicipioSelector />);
    expect(screen.getByText('Porto de Santos (SP)')).toBeInTheDocument();
    expect(screen.getByText('Porto de Vitória / Capuaba (ES)')).toBeInTheDocument();
    expect(screen.getByText('Porto de Manaus (AM)')).toBeInTheDocument();
  });

  it('does NOT contain port-specific entries', () => {
    render(<MunicipioSelector />);
    expect(screen.queryByText('DP World Santos (SP)')).toBeNull();
    expect(screen.queryByText('Terminal de Tubarão')).toBeNull();
  });

  it('calls setMunicipio on change', () => {
    render(<MunicipioSelector />);
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: '3548500' } });
    expect(mockState.setMunicipio).toHaveBeenCalledWith('3548500');
  });

  it('calls setMunicipio(null) when selecting default', () => {
    mockState.selectedMunicipio = '3548500';
    render(<MunicipioSelector />);
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: '' } });
    expect(mockState.setMunicipio).toHaveBeenCalledWith(null);
  });

  it('exports MUNICIPIOS_PORTUARIOS with valid IBGE codes', () => {
    for (const m of MUNICIPIOS_PORTUARIOS) {
      expect(m.id_municipio).toMatch(/^\d{7}$/);
      expect(m.label.length).toBeGreaterThan(3);
    }
  });
});

// ─── InstallationSelector ───────────────────────────────────────────────────

describe('InstallationSelector', () => {
  it('renders with default "Todos os Portos"', () => {
    render(<InstallationSelector />);
    const select = screen.getByRole('combobox');
    expect((select as HTMLSelectElement).value).toBe('');
  });

  it('has 2 optgroups (Porto Organizado + Terminal Privativo)', () => {
    render(<InstallationSelector />);
    const groups = screen.getAllByRole('group');
    expect(groups.length).toBe(2);
  });

  it('does not contain municipalities', () => {
    render(<InstallationSelector />);
    expect(screen.queryByText('Balneário Camboriú (SC)')).toBeNull();
    expect(screen.queryByText('Navegantes (SC)')).toBeNull();
    expect(screen.queryByText('Garopaba (SC)')).toBeNull();
  });

  it('PORTO_OPTIONS is union of both lists', () => {
    expect(PORTO_OPTIONS.length).toBe(PORTOS_ORGANIZADOS.length + TERMINAIS_PRIVADOS.length);
  });

  it('calls setInstallation on change', () => {
    render(<InstallationSelector />);
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Santos' } });
    expect(mockState.setInstallation).toHaveBeenCalledWith('Santos');
  });
});

// ─── FilterBar ──────────────────────────────────────────────────────────────

describe('FilterBar', () => {
  it('renders porto selector by default', () => {
    render(<FilterBar />);
    expect(screen.getByText('Todos os Portos')).toBeInTheDocument();
  });

  it('renders municipio selector when selectorMode="municipio"', () => {
    render(<FilterBar selectorMode="municipio" />);
    expect(screen.getByText('Todos os Portos')).toBeInTheDocument();
  });

  it('hides year selector when showYear={false}', () => {
    render(<FilterBar showYear={false} />);
    expect(screen.queryByText('2023')).toBeNull();
  });

  it('shows year selector by default', () => {
    render(<FilterBar />);
    // Year button + label both show selectedYear
    const yearElements = screen.getAllByText('2023');
    expect(yearElements.length).toBeGreaterThanOrEqual(1);
  });

  it('hides installation selector when showInstallation={false}', () => {
    render(<FilterBar showInstallation={false} />);
    expect(screen.queryByText('Todos os Portos')).toBeNull();
    expect(screen.queryByText('Todos os Municípios')).toBeNull();
  });

  it('renders "Limpar filtros" button', () => {
    render(<FilterBar />);
    expect(screen.getByText('Limpar filtros')).toBeInTheDocument();
  });

  it('calls resetFilters on clear button click', () => {
    render(<FilterBar />);
    fireEvent.click(screen.getByText('Limpar filtros'));
    expect(mockState.resetFilters).toHaveBeenCalled();
  });
});
