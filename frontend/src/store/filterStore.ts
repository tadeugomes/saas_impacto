import { create } from 'zustand';

interface FilterState {
  selectedYear: number;
  selectedYearEnd: number | null;
  selectedInstallation: string | null;
  selectedMunicipio: string | null;
  selectedModule: number | null;
  setYear: (year: number) => void;
  setYearRange: (start: number, end: number) => void;
  setInstallation: (installation: string | null) => void;
  setMunicipio: (municipio: string | null) => void;
  setModule: (module: number | null) => void;
  resetFilters: () => void;
}

const DEFAULT_YEAR = 2026; // Use 2026 as default — BigQuery has data up to Jan 2026

export const useFilterStore = create<FilterState>((set) => ({
  selectedYear: DEFAULT_YEAR,
  selectedYearEnd: null,
  selectedInstallation: null,
  selectedMunicipio: null,
  selectedModule: null,
  setYear: (year) => set({ selectedYear: year, selectedYearEnd: null }),
  setYearRange: (start, end) => set({ selectedYear: start, selectedYearEnd: end }),
  setInstallation: (installation) => set({ selectedInstallation: installation }),
  setMunicipio: (municipio) => set({ selectedMunicipio: municipio }),
  setModule: (module) => set({ selectedModule: module }),
  resetFilters: () =>
    set({
      selectedYear: DEFAULT_YEAR,
      selectedYearEnd: null,
      selectedInstallation: null,
      selectedMunicipio: null,
      selectedModule: null,
    }),
}));
