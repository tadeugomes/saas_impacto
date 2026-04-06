import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  type ScriptableContext,
} from 'chart.js';
import { useMemo } from 'react';
import { createTooltipCallback, createTickCallback, type ChartValueFormat } from '../../utils/chartFormats';
import { CHART_COLORS, CHART_FONT, GRID_COLOR, hexToRgba } from '../../styles/chartTheme';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface LineChartProps {
  labels: string[];
  datasets: Array<{
    label: string;
    data: Array<number | null>;
    [key: string]: unknown;
  }>;
  title?: string;
  yAxisLabel?: string;
  yAxisBeginAtZero?: boolean;
  yAxisFormat?: ChartValueFormat;
}

export function LineChart({
  labels,
  datasets,
  title,
  yAxisLabel,
  yAxisBeginAtZero = true,
  yAxisFormat,
}: LineChartProps) {
  const options = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          font: { size: 11, family: CHART_FONT },
          color: '#64748b',
          usePointStyle: true,
          pointStyleWidth: 8,
          padding: 16,
        },
      },
      title: {
        display: !!title,
        text: title,
        font: { size: 13, weight: 'bold' as const, family: CHART_FONT },
        color: '#0f172a',
        padding: { bottom: 14 },
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: '#0f172a',
        titleFont: { size: 12, weight: 'bold' as const, family: CHART_FONT },
        bodyFont: { size: 11, family: CHART_FONT },
        padding: 12,
        cornerRadius: 8,
        displayColors: true,
        boxPadding: 4,
        callbacks: {
          label: createTooltipCallback(yAxisFormat || 'number'),
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        border: { display: false },
        ticks: {
          font: { size: 11, family: CHART_FONT },
          color: '#64748b',
        },
      },
      y: {
        beginAtZero: yAxisBeginAtZero,
        grid: { color: GRID_COLOR },
        border: { display: false },
        ticks: {
          font: { size: 11, family: CHART_FONT },
          color: '#64748b',
          padding: 8,
          ...(yAxisFormat ? { callback: createTickCallback({ format: yAxisFormat }) } : {}),
        },
        ...(yAxisLabel ? {
          title: {
            display: true,
            text: yAxisLabel,
            font: { size: 11, family: CHART_FONT },
            color: '#94a3b8',
          },
        } : {}),
      },
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false,
    },
    animation: {
      duration: 600,
      easing: 'easeOutCubic' as const,
    },
  }), [title, yAxisLabel, yAxisBeginAtZero, yAxisFormat]);

  const chartData = useMemo(() => ({
    labels,
    datasets: datasets.map((ds, i) => {
      const lineColor = (ds.borderColor as string | undefined) || CHART_COLORS[i % CHART_COLORS.length];
      return {
        ...ds,
        borderColor: lineColor,
        borderWidth: 2.5,
        tension: 0.35,
        pointRadius: 3,
        pointHoverRadius: 6,
        pointBackgroundColor: lineColor,
        pointBorderColor: '#ffffff',
        pointBorderWidth: 1.5,
        fill: true,
        backgroundColor: (ctx: ScriptableContext<'line'>) => {
          const chart = ctx.chart;
          const { ctx: canvasCtx, chartArea } = chart;
          if (!chartArea) return hexToRgba(lineColor, 0.1);
          const gradient = canvasCtx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
          gradient.addColorStop(0, hexToRgba(lineColor, 0.22));
          gradient.addColorStop(1, hexToRgba(lineColor, 0.02));
          return gradient;
        },
      };
    }),
  }), [labels, datasets]);

  return (
    <div className="h-64 w-full">
      <Line data={chartData} options={options} />
    </div>
  );
}
