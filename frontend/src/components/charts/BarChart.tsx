import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  type ChartOptions,
} from 'chart.js';
import { useMemo } from 'react';
import { createFormattedScaleOptions, createTooltipCallback, type ChartValueFormat } from '../../utils/chartFormats';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface BarChartProps {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
  }[];
  title?: string;
  yAxisLabel?: string;
  horizontal?: boolean;
  /** Tipo de formatação dos valores (número, moeda, percentual, etc.) */
  valueFormat?: ChartValueFormat;
  /** Altura customizada do gráfico (em classes Tailwind) */
  height?: string;
}

const COLORS = {
  module1: '#3b82f6', // blue
  module2: '#10b981', // emerald
  module3: '#f59e0b', // amber
  module4: '#8b5cf6', // violet
  module5: '#ec4899', // pink
  module6: '#14b8a6', // teal
  module7: '#6366f1', // indigo
};

// Paleta de cores adicionais para gradiente/múltiplos datasets
const ADDITIONAL_COLORS = [
  '#f97316', // orange
  '#84cc16', // lime
  '#06b6d4', // cyan
  '#a855f7', // purple
  '#ef4444', // red
];

const ALL_COLORS = [...Object.values(COLORS), ...ADDITIONAL_COLORS];

export function BarChart({
  labels,
  datasets,
  title,
  yAxisLabel,
  horizontal,
  valueFormat,
  height = 'h-64',
}: BarChartProps) {
  // Determina o eixo que precisa de formatação baseado na orientação
  const valueAxis = horizontal ? 'x' : 'y';
  const labelAxis = horizontal ? 'y' : 'x';

  const options = useMemo<ChartOptions<'bar'>>(() => {
    // Configuração da escala de valores (com formatação)
    const valueScaleOptions = createFormattedScaleOptions({
      format: valueFormat,
      label: yAxisLabel,
      beginAtZero: true,
    });

    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: horizontal ? ('y' as const) : ('x' as const),
      plugins: {
        legend: {
          position: 'top' as const,
          labels: {
            font: { size: 11, family: "'Inter', system-ui, sans-serif" },
            color: '#6b7280',
            usePointStyle: true,
            padding: 15,
          },
        },
        title: {
          display: !!title,
          text: title,
          font: { size: 14, weight: 'bold' as const, family: "'Inter', system-ui, sans-serif" },
          color: '#1f2937',
          padding: { bottom: 15 },
        },
        tooltip: {
          mode: 'index' as const,
          intersect: false,
          backgroundColor: 'rgba(17, 24, 39, 0.9)',
          titleFont: { size: 12, weight: 'bold' as const, family: "'Inter', system-ui, sans-serif" },
          bodyFont: { size: 11, family: "'Inter', system-ui, sans-serif" },
          padding: 12,
          cornerRadius: 8,
          displayColors: true,
          boxPadding: 4,
          callbacks: valueFormat ? {
            label: createTooltipCallback(valueFormat),
          } : undefined,
        },
      },
      scales: {
        // Escala do eixo de labels (nomes dos municípios, etc.)
        [labelAxis]: {
          grid: {
            display: false,
          },
          border: {
            display: false,
          },
          ticks: {
            font: { size: 11, family: "'Inter', system-ui, sans-serif" },
            color: '#6b7280',
            // Para gráficos horizontais, limitar o tamanho do texto
            ...(horizontal && {
              callback: (value: string | number) => {
                const label = typeof value === 'string' ? value : String(value);
                // Truncar labels muito longos
                return label.length > 25 ? label.substring(0, 22) + '...' : label;
              },
            }),
          },
        },
        // Escala do eixo de valores (com formatação)
        [valueAxis]: valueScaleOptions,
      },
      // Animações mais suaves
      animation: {
        duration: 750,
        easing: 'easeOutQuart' as const,
      },
    } satisfies ChartOptions<'bar'>;

    return baseOptions as ChartOptions<'bar'>;
  }, [title, yAxisLabel, horizontal, valueFormat, valueAxis, labelAxis]);

  const chartData = useMemo(() => ({
    labels,
    datasets: datasets.map((ds, i) => ({
      ...ds,
      backgroundColor: ds.backgroundColor || ALL_COLORS[i % ALL_COLORS.length],
      borderColor: ds.borderColor || ALL_COLORS[i % ALL_COLORS.length],
      borderWidth: 1,
      borderRadius: 6,
      // Adiciona hover effects
      hoverBackgroundColor: ALL_COLORS[i % ALL_COLORS.length] + 'cc', // + cc = 80% opacidade
    })),
  }), [labels, datasets]);

  return (
    <div className={`${height} w-full`}>
      <Bar data={chartData} options={options} />
    </div>
  );
}
