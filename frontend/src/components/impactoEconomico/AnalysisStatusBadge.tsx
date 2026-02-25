import { CheckCircle, Clock3, Loader2, XCircle } from 'lucide-react';

import type { AnalysisStatus } from '../../types/api';

const STYLE_BY_STATUS: Record<
  AnalysisStatus,
  {
    label: string;
    icon: typeof CheckCircle;
    className: string;
  }
> = {
  queued: {
    label: 'Na fila',
    icon: Clock3,
    className: 'bg-amber-50 text-amber-700 border-amber-200',
  },
  running: {
    label: 'Em execução',
    icon: Loader2,
    className: 'bg-blue-50 text-blue-700 border-blue-200 animate-pulse',
  },
  success: {
    label: 'Concluída',
    icon: CheckCircle,
    className: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  },
  failed: {
    label: 'Falhou',
    icon: XCircle,
    className: 'bg-red-50 text-red-700 border-red-200',
  },
};

export function AnalysisStatusBadge({ status }: { status: AnalysisStatus }) {
  const cfg = STYLE_BY_STATUS[status];
  const Icon = cfg.icon;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full border text-xs font-medium ${cfg.className}`}>
      <Icon className="h-3.5 w-3.5" />
      {cfg.label}
    </span>
  );
}
