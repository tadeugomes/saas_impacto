import { Scatter } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  type Plugin,
  type ChartOptions,
} from 'chart.js';
import { useMemo } from 'react';
import { CHART_COLORS, CHART_FONT, GRID_COLOR, CHART_PALETTE, hexToRgba } from '../../styles/chartTheme';

ChartJS.register(LinearScale, PointElement, Tooltip, Legend);

export interface ScatterPoint {
  x: number;
  y: number;
  label: string;
  uf?: string;
  ano?: number;
  highlighted?: boolean;
}

interface ScatterChartProps {
  points: ScatterPoint[];
  /** Coeficientes para desenhar linha de regressão: ln(y) = intercept + slope * ln(x) */
  regressionLine?: { slope: number; intercept: number };
  xLabel?: string;
  yLabel?: string;
  height?: string;
  title?: string;
}

/** Cria plugin para desenhar linha de regressão log-log e labels dos pontos destacados. */
function makeRegressionPlugin(
  slope: number,
  intercept: number,
): Plugin<'scatter'> {
  return {
    id: 'regressionLine',
    afterDatasetsDraw(chart) {
      const { ctx, scales } = chart;
      const xScale = scales.x;
      const yScale = scales.y;
      if (!xScale || !yScale) return;

      const xMin = xScale.min;
      const xMax = xScale.max;
      if (xMin <= 0 || xMax <= 0) return;

      // Calcular pontos da linha: y = exp(intercept + slope * ln(x))
      const steps = 80;
      const logXMin = Math.log(xMin);
      const logXMax = Math.log(xMax);
      const stepSize = (logXMax - logXMin) / steps;

      ctx.save();
      ctx.beginPath();
      ctx.strokeStyle = CHART_PALETTE.navy;
      ctx.lineWidth = 2;
      ctx.setLineDash([]);
      ctx.globalAlpha = 0.6;

      let started = false;
      for (let i = 0; i <= steps; i++) {
        const logX = logXMin + i * stepSize;
        const x = Math.exp(logX);
        const y = Math.exp(intercept + slope * logX);

        const px = xScale.getPixelForValue(x);
        const py = yScale.getPixelForValue(y);

        if (!started) {
          ctx.moveTo(px, py);
          started = true;
        } else {
          ctx.lineTo(px, py);
        }
      }
      ctx.stroke();
      ctx.restore();
    },
  };
}

/** Plugin para desenhar labels dos pontos destacados. */
const highlightLabelPlugin: Plugin<'scatter'> = {
  id: 'highlightLabels',
  afterDatasetsDraw(chart) {
    const { ctx, data } = chart;
    data.datasets.forEach((dataset, datasetIndex) => {
      const meta = chart.getDatasetMeta(datasetIndex);
      const pts = dataset.data as (ScatterPoint & { x: number; y: number })[];
      pts.forEach((point, index) => {
        if (!point.highlighted) return;
        const el = meta.data[index];
        if (!el) return;
        ctx.save();
        ctx.font = `600 10px ${CHART_FONT}`;
        ctx.fillStyle = CHART_PALETTE.navy;
        ctx.textAlign = 'left';
        ctx.textBaseline = 'bottom';
        ctx.fillText(point.label, el.x + 6, el.y - 4);
        ctx.restore();
      });
    });
  },
};

export function ScatterChart({
  points,
  regressionLine,
  xLabel = 'Tonelagem (M ton)',
  yLabel = 'ISS (R$ mi)',
  height = 'h-72',
  title,
}: ScatterChartProps) {
  // Separar pontos normais e destacados
  const normalPoints = points.filter((p) => !p.highlighted);
  const highlightedPoints = points.filter((p) => p.highlighted);

  const chartData = useMemo(() => ({
    datasets: [
      {
        label: 'Portos',
        data: normalPoints as unknown as { x: number; y: number }[],
        backgroundColor: hexToRgba(CHART_COLORS[1], 0.55),
        borderColor: CHART_COLORS[1],
        borderWidth: 1,
        pointRadius: 5,
        pointHoverRadius: 7,
      },
      ...(highlightedPoints.length > 0
        ? [{
            label: 'Porto selecionado',
            data: highlightedPoints as unknown as { x: number; y: number }[],
            backgroundColor: CHART_PALETTE.navy,
            borderColor: CHART_PALETTE.navy,
            borderWidth: 2,
            pointRadius: 8,
            pointHoverRadius: 10,
            pointStyle: 'circle' as const,
          }]
        : []),
    ],
  }), [normalPoints, highlightedPoints]);

  const options = useMemo<ChartOptions<'scatter'>>(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: highlightedPoints.length > 0,
        position: 'top' as const,
        labels: { font: { size: 11, family: CHART_FONT }, color: '#64748b', padding: 12 },
      },
      title: {
        display: !!title,
        text: title,
        font: { size: 13, weight: 'bold' as const, family: CHART_FONT },
        color: '#0f172a',
      },
      tooltip: {
        backgroundColor: '#0f172a',
        titleFont: { size: 11, family: CHART_FONT },
        bodyFont: { size: 11, family: CHART_FONT },
        padding: 10,
        cornerRadius: 8,
        callbacks: {
          title: (items) => {
            const raw = items[0]?.raw as ScatterPoint;
            return raw?.label ?? '';
          },
          label: (item) => {
            const raw = item.raw as ScatterPoint;
            return [
              `${xLabel}: ${raw.x.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}`,
              `${yLabel}: R$ ${raw.y.toLocaleString('pt-BR', { maximumFractionDigits: 1 })} mi`,
              ...(raw.ano ? [`Ano: ${raw.ano}`] : []),
            ];
          },
        },
      },
    },
    scales: {
      x: {
        type: 'linear' as const,
        position: 'bottom',
        title: {
          display: true,
          text: xLabel,
          font: { size: 11, family: CHART_FONT },
          color: '#64748b',
        },
        grid: { color: GRID_COLOR },
        border: { display: false },
        ticks: { font: { size: 10, family: CHART_FONT }, color: '#64748b' },
      },
      y: {
        type: 'linear' as const,
        title: {
          display: true,
          text: yLabel,
          font: { size: 11, family: CHART_FONT },
          color: '#64748b',
        },
        grid: { color: GRID_COLOR },
        border: { display: false },
        ticks: { font: { size: 10, family: CHART_FONT }, color: '#64748b' },
      },
    },
    animation: { duration: 400 },
  }), [xLabel, yLabel, title, highlightedPoints.length]);

  const plugins: Plugin<'scatter'>[] = [highlightLabelPlugin];
  if (regressionLine) {
    plugins.push(makeRegressionPlugin(regressionLine.slope, regressionLine.intercept));
  }

  return (
    <div className={`${height} w-full`}>
      <Scatter data={chartData} options={options} plugins={plugins} />
    </div>
  );
}
