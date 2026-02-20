import { useState } from 'react';
import { FileText, Download } from 'lucide-react';
import { reportsService } from '../../api/reports';
import { useFilterStore } from '../../store/filterStore';

interface ExportButtonProps {
  moduleCode: string;
  indicatorCode?: string;
  label?: string;
  variant?: 'primary' | 'secondary';
  className?: string;
  disabled?: boolean;
  includeFormats?: Array<'docx' | 'pdf' | 'xlsx'>;
}

export function ExportButton({
  moduleCode,
  indicatorCode,
  label = indicatorCode ? 'Exportar Indicador' : 'Exportar Módulo',
  variant = 'secondary',
  className = '',
  disabled = false,
  includeFormats = ['docx', 'pdf', 'xlsx'],
}: ExportButtonProps) {
  const { selectedYear, selectedInstallation } = useFilterStore();
  const [isExporting, setIsExporting] = useState(false);
  const [format, setFormat] = useState<'docx' | 'pdf' | 'xlsx'>('docx');

  const handleExport = async () => {
    setIsExporting(true);
    try {
      if (indicatorCode) {
        await reportsService.exportIndicator({
          indicatorCode,
          id_instalacao: selectedInstallation || undefined,
          ano: selectedYear || undefined,
          format,
        });
      } else {
        await reportsService.exportModule({
          moduleCode,
          id_instalacao: selectedInstallation || undefined,
          ano: selectedYear || undefined,
          format,
        });
      }
    } catch (error) {
      console.error('Erro ao exportar:', error);
      alert('Erro ao exportar relatório. Tente novamente.');
    } finally {
      setIsExporting(false);
    }
  };

  const baseStyles = 'inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed';
  const variantStyles = variant === 'primary'
    ? 'bg-blue-600 text-white hover:bg-blue-700'
    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50';

  return (
    <div className="inline-flex items-stretch gap-2">
      <select
        value={format}
        onChange={(event) =>
          setFormat(event.target.value as 'docx' | 'pdf' | 'xlsx')
        }
        disabled={disabled || isExporting}
        className="rounded-lg border border-gray-300 bg-white px-2 text-sm"
        aria-label="Formato de exportação"
      >
        {includeFormats.map((option) => (
          <option key={option} value={option}>
            {option.toUpperCase()}
          </option>
        ))}
      </select>
      <button
        onClick={handleExport}
        disabled={disabled || isExporting}
        className={`${baseStyles} ${variantStyles} ${className}`}
        title="Exportar relatório"
      >
        {isExporting ? (
          <>
            <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
            Gerando...
          </>
        ) : (
          <>
            {variant === 'primary' ? <FileText className="w-4 h-4" /> : <Download className="w-4 h-4" />}
            {label}
          </>
        )}
      </button>
    </div>
  );
}
