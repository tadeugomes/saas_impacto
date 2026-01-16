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
}

export function ExportButton({
  moduleCode,
  indicatorCode,
  label = indicatorCode ? 'Exportar Indicador' : 'Exportar Módulo',
  variant = 'secondary',
  className = '',
  disabled = false,
}: ExportButtonProps) {
  const { selectedYear, selectedInstallation } = useFilterStore();
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      if (indicatorCode) {
        await reportsService.exportIndicator({
          indicatorCode,
          id_instalacao: selectedInstallation || undefined,
          ano: selectedYear || undefined,
        });
      } else {
        await reportsService.exportModule({
          moduleCode,
          id_instalacao: selectedInstallation || undefined,
          ano: selectedYear || undefined,
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
    <button
      onClick={handleExport}
      disabled={disabled || isExporting}
      className={`${baseStyles} ${variantStyles} ${className}`}
      title="Exportar para DOCX"
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
  );
}
