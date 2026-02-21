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
} from 'chart.js';
import { useMemo } from 'react';
import { createTooltipCallback, createTickCallback, type ChartValueFormat } from '../../utils/chartFormats';

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

const COLORS = {
  module1: '#3b82f6',
  module2: '#10b981',
  module3: '#f59e0b',
  module4: '#8b5cf6',
  module5: '#ec4899',
  module6: '#14b8a6',
  module7: '#6366f1',
};

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
      },
      title: {
        display: !!title,
        text: title,
        font: { size: 14, weight: 'bold' as const },
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        callbacks: {
          label: createTooltipCallback(yAxisFormat || 'number'),
        },
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
      },
      y: {
        beginAtZero: yAxisBeginAtZero,
        ticks: yAxisFormat
          ? {
              callback: createTickCallback({ format: yAxisFormat }),
            }
          : undefined,
        title: {
          display: !!yAxisLabel,
          text: yAxisLabel,
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
      },
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false,
    },
  }), [title, yAxisLabel, yAxisBeginAtZero, yAxisFormat]);

  const chartData = useMemo(() => ({
    labels,
    datasets: datasets.map((ds, i) => ({
      ...ds,
      borderColor: ds.borderColor || Object.values(COLORS)[i % 7],
      backgroundColor: ds.backgroundColor || `${Object.values(COLORS)[i % 7]}20`,
      tension: 0.3,
      pointRadius: 4,
      pointHoverRadius: 6,
    })),
  }), [labels, datasets]);

  return (
    <div className="h-64 w-full">
      <Line data={chartData} options={options} />
    </div>
  );
}
