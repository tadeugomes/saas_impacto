import { Pie, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { useMemo } from 'react';

ChartJS.register(ArcElement, Tooltip, Legend);

interface PieChartProps {
  labels: string[];
  data: number[];
  title?: string;
  variant?: 'pie' | 'doughnut';
}

const COLORS = [
  '#3b82f6', // Azul
  '#10b981', // Verde
  '#f59e0b', // Laranja
  '#8b5cf6', // Roxo
  '#ec4899', // Pink
  '#14b8a6', // Teal
  '#6366f1', // Índigo
  '#f97316', // Laranja escuro
  '#84cc16', // Lima
  '#06b6d4', // Ciano
];

export function PieChart({ labels, data, title, variant = 'pie' }: PieChartProps) {
  const options = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          boxWidth: 12,
          padding: 8,
          font: { size: 11 },
        },
      },
      title: {
        display: !!title,
        text: title,
        font: { size: 14, weight: 'bold' as const },
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const value = context.raw || 0;
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${context.label}: ${value} (${percentage}%)`;
          },
        },
      },
    },
  }), [title]);

  const chartData = useMemo(() => ({
    labels,
    datasets: [{
      data,
      backgroundColor: COLORS.slice(0, data.length),
      borderWidth: 2,
      borderColor: '#fff',
    }],
  }), [labels, data]);

  const ChartComponent = variant === 'doughnut' ? Doughnut : Pie;

  return (
    <div className="h-64 w-full flex items-center justify-center">
      <div className="w-full max-w-sm">
        <ChartComponent data={chartData} options={options} />
      </div>
    </div>
  );
}
