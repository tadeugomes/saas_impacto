import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import { Info } from 'lucide-react';
import type { ReactNode } from 'react';
import { CHART_PALETTE } from '../../styles/chartTheme';

interface ChartCardProps {
  title: string;
  description?: string;
  unit?: string;
  isLoading?: boolean;
  error?: string | null;
  children: ReactNode;
  extraInfo?: string;
  /** Cor do acento lateral esquerdo. Padrão: navy do tema. */
  accentColor?: string;
  /** Fonte dos dados, exibida no rodapé. Ex: "ANTAQ 2024" */
  source?: string;
  /** Número de observações, exibido no rodapé. */
  nObs?: number;
}

export function ChartCard({
  title,
  description,
  unit,
  isLoading,
  error,
  children,
  extraInfo,
  accentColor,
  source,
  nObs,
}: ChartCardProps) {
  const accent = accentColor ?? CHART_PALETTE.navy;

  return (
    <div
      className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 border-l-4 overflow-hidden"
      style={{ borderLeftColor: accent }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0 pr-2">
          <h3 className="font-semibold text-gray-900 text-sm leading-snug">{title}</h3>
          {description && (
            <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{description}</p>
          )}
        </div>
        {unit && (
          <span
            className="flex-shrink-0 px-2 py-0.5 text-xs font-medium rounded-md"
            style={{ backgroundColor: `${accent}18`, color: accent }}
          >
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

      {/* Extra info (warnings) */}
      {extraInfo && (
        <div className="mt-4 pt-3 border-t border-gray-100">
          <div className="flex items-start gap-1.5 text-xs text-gray-500">
            <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
            <span>{extraInfo}</span>
          </div>
        </div>
      )}

      {/* Rodapé de fonte/observações */}
      {(source || nObs != null) && (
        <div className="mt-3 pt-2.5 border-t border-gray-100 flex items-center gap-2 text-xs text-gray-400">
          {source && <span>Fonte: {source}</span>}
          {source && nObs != null && <span>·</span>}
          {nObs != null && <span>{nObs.toLocaleString('pt-BR')} obs.</span>}
        </div>
      )}
    </div>
  );
}
