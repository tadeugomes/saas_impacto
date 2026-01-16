import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import { Info } from 'lucide-react';
import type { ReactNode } from 'react';

interface ChartCardProps {
  title: string;
  description?: string;
  unit?: string;
  isLoading?: boolean;
  error?: string | null;
  children: ReactNode;
  extraInfo?: string;
}

export function ChartCard({
  title,
  description,
  unit,
  isLoading,
  error,
  children,
  extraInfo,
}: ChartCardProps) {
  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-semibold text-gray-900">{title}</h3>
          {description && (
            <p className="text-sm text-gray-500 mt-1">{description}</p>
          )}
        </div>
        {unit && (
          <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-md">
            {unit}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="relative">
        {isLoading ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorAlert message={error} />
        ) : (
          children
        )}
      </div>

      {/* Extra info */}
      {extraInfo && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex items-start gap-2 text-sm text-gray-500">
            <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{extraInfo}</span>
          </div>
        </div>
      )}
    </div>
  );
}
