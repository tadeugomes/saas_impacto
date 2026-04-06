import { Pie, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  type TooltipItem,
  type Plugin,
} from 'chart.js';
import { useMemo } from 'react';
import { CHART_COLORS, CHART_FONT } from '../../styles/chartTheme';

ChartJS.register(ArcElement, Tooltip, Legend);

interface PieChartProps {
  labels: string[];
  data: number[];
  title?: string;
  variant?: 'pie' | 'doughnut';
}

/** Plugin que exibe o total formatado no centro do donut. */
const centerTextPlugin: Plugin<'doughnut'> = {
  id: 'centerText',
  beforeDraw(chart) {
    const { ctx, chartArea, data } = chart;
    if (!chartArea) return;

    const total = (data.datasets[0]?.data as number[])
      .filter((v): v is number => typeof v === 'number' && Number.isFinite(v))
      .reduce((a, b) => a + b, 0);

    if (total === 0) return;

    const formatted =
      total >= 1_000_000
        ? (total / 1_000_000).toLocaleString('pt-BR', { maximumFractionDigits: 1 }) + ' M'
        : total >= 1_000
          ? (total / 1_000).toLocaleString('pt-BR', { maximumFractionDigits: 1 }) + ' K'
          : total.toLocaleString('pt-BR', { maximumFractionDigits: 0 });

    const cx = (chartArea.left + chartArea.right) / 2;
    const cy = (chartArea.top + chartArea.bottom) / 2;

    ctx.save();

    // Linha superior: "Total"
    ctx.font = `400 11px ${CHART_FONT}`;
    ctx.fillStyle = '#94a3b8';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('Total', cx, cy - 11);

    // Linha inferior: valor
    ctx.font = `700 15px ${CHART_FONT}`;
    ctx.fillStyle = '#0f172a';
    ctx.fillText(formatted, cx, cy + 9);

    ctx.restore();
  },
};

export function PieChart({ labels, data, title, variant = 'pie' }: PieChartProps) {
  const options = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          boxWidth: 12,
          boxHeight: 12,
          padding: 16,
          font: { size: 11, family: CHART_FONT },
          color: '#475569',
          usePointStyle: false,
        },
      },
      title: {
        display: !!title,
        text: title,
        font: { size: 13, weight: 'bold' as const, family: CHART_FONT },
        color: '#0f172a',
        padding: { bottom: 12 },
      },
      tooltip: {
        backgroundColor: '#0f172a',
        titleFont: { size: 12, weight: 'bold' as const, family: CHART_FONT },
        bodyFont: { size: 11, family: CHART_FONT },
        padding: 12,
        cornerRadius: 8,
        callbacks: {
          label: (context: TooltipItem<'pie' | 'doughnut'>) => {
            const value = typeof context.raw === 'number' ? context.raw : 0;
            const values = context.dataset.data;
            const numericValues = values.filter((item): item is number => typeof item === 'number');
            const total = numericValues.reduce((acc: number, current: number) => acc + current, 0);
            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
            const formatted = value >= 1_000_000
              ? (value / 1_000_000).toLocaleString('pt-BR', { maximumFractionDigits: 2 }) + ' M'
              : value >= 1_000
                ? (value / 1_000).toLocaleString('pt-BR', { maximumFractionDigits: 1 }) + ' K'
                : value.toLocaleString('pt-BR', { maximumFractionDigits: 0 });
            return `${context.label}: ${formatted} (${percentage}%)`;
          },
        },
      },
    },
    animation: {
      duration: 600,
      easing: 'easeOutCubic' as const,
    },
  }), [title]);

  const chartData = useMemo(() => ({
    labels,
    datasets: [{
      data,
      backgroundColor: CHART_COLORS.slice(0, data.length),
      borderWidth: 3,
      borderColor: '#ffffff',
      hoverBorderWidth: 3,
      hoverOffset: 6,
    }],
  }), [labels, data]);

  const ChartComponent = variant === 'doughnut' ? Doughnut : Pie;
  const plugins = variant === 'doughnut' ? [centerTextPlugin as Plugin<'doughnut' | 'pie'>] : [];

  return (
    <div className="h-64 w-full flex items-center justify-center">
      <div className="w-full max-w-sm">
        <ChartComponent data={chartData} options={options} plugins={plugins} />
      </div>
    </div>
  );
}
