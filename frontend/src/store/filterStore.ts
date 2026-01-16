import { create } from 'zustand';

interface FilterState {
  selectedYear: number;
  selectedYearEnd: number | null;
  selectedInstallation: string | null;
  selectedModule: number | null;
  setYear: (year: number) => void;
  setYearRange: (start: number, end: number) => void;
  setInstallation: (installation: string | null) => void;
  setModule: (module: number | null) => void;
  resetFilters: () => void;
}

const DEFAULT_YEAR = 2023; // Use 2023 as default since database has data for this year

export const useFilterStore = create<FilterState>((set) => ({
  selectedYear: DEFAULT_YEAR,
  selectedYearEnd: null,
  selectedInstallation: null,
  selectedModule: null,
  setYear: (year) => set({ selectedYear: year, selectedYearEnd: null }),
  setYearRange: (start, end) => set({ selectedYear: start, selectedYearEnd: end }),
  setInstallation: (installation) => set({ selectedInstallation: installation }),
  setModule: (module) => set({ selectedModule: module }),
  resetFilters: () =>
    set({
      selectedYear: DEFAULT_YEAR,
      selectedYearEnd: null,
      selectedInstallation: null,
      selectedModule: null,
    }),
}));
