import { YearSelector } from './YearSelector';
import { InstallationSelector } from './InstallationSelector';
import { useFilterStore } from '../../store/filterStore';
import { Filter, X } from 'lucide-react';

interface FilterBarProps {
  showInstallation?: boolean;
}

export function FilterBar({ showInstallation = true }: FilterBarProps) {
  const { selectedYear, resetFilters } = useFilterStore();

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-gray-600">
          <Filter className="w-5 h-5" />
        <span className="font-medium">Filtros:</span>
        </div>
        <YearSelector />
        {showInstallation && <InstallationSelector />}
        <span className="text-sm text-gray-500">
          {selectedYear}
        </span>
      </div>

      <button
        onClick={resetFilters}
        className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
      >
        <X className="w-4 h-4" />
        Limpar filtros
      </button>
    </div>
  );
}
