import { useFilterStore } from '../../store/filterStore';
import { ChevronDown } from 'lucide-react';
import { useState } from 'react';

const YEARS = Array.from({ length: 26 }, (_, i) => 2024 - i); // 1999-2024

export function YearSelector() {
  const { selectedYear, setYear } = useFilterStore();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors min-w-[120px]"
      >
        <span className="font-medium">{selectedYear}</span>
        <ChevronDown className="w-4 h-4 text-gray-400" />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute z-20 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto">
            {YEARS.map((year) => (
              <button
                key={year}
                onClick={() => {
                  setYear(year);
                  setIsOpen(false);
                }}
                className={`w-full px-4 py-2 text-left hover:bg-gray-50 transition-colors ${
                  selectedYear === year ? 'bg-primary text-white' : ''
                }`}
              >
                {year}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
