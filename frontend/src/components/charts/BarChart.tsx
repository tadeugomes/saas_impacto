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
  type Plugin,
} from 'chart.js';
import { useRef, useEffect, useMemo } from 'react';
import { createFormattedScaleOptions, createTooltipCallback, type ChartValueFormat } from '../../utils/chartFormats';
import { formatByType } from '../../utils/numberFormat';
import { CHART_COLORS, CHART_FONT, GRID_COLOR, hexToRgba } from '../../styles/chartTheme';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface BarChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
}

interface BarChartProps {
  labels: string[];
  datasets: BarChartDataset[];
  title?: string;
  yAxisLabel?: string;
  horizontal?: boolean;
  valueFormat?: ChartValueFormat;
  height?: string;
  referenceLine?: {
    value: number;
    label?: string;
    color?: string;
  };
  maxValue?: number;
}

export function BarChart({
  labels,
  datasets,
  title,
  yAxisLabel,
  horizontal,
  valueFormat,
  height = 'h-64',
  referenceLine,
  maxValue,
}: BarChartProps) {
  const chartRef = useRef<ChartJS<'bar'>>(null);

  const valueAxis = horizontal ? 'x' : 'y';
  const labelAxis = horizontal ? 'y' : 'x';

  // Resolve cor base para cada dataset (respeita cor customizada se passada)
  const resolvedColors = useMemo(
    () => datasets.map((ds, i) =>
      typeof ds.backgroundColor === 'string' ? ds.backgroundColor : CHART_COLORS[i % CHART_COLORS.length]
    ),
    [datasets],
  );

  // Aplica gradientes após o render do canvas
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart?.chartArea) return;

    chart.data.datasets.forEach((dataset, i) => {
      const baseColor = resolvedColors[i] ?? CHART_COLORS[0];
      const { ctx, chartArea } = chart;
      const gradient = horizontal
        ? ctx.createLinearGradient(chartArea.left, 0, chartArea.right, 0)
        : ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);

      gradient.addColorStop(0, hexToRgba(baseColor, 0.42));
      gradient.addColorStop(0.72, hexToRgba(baseColor, 0.82));
      gradient.addColorStop(1, baseColor);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (dataset as any).backgroundColor = gradient;
    });

    chart.update('none');
  }, [labels, datasets, horizontal, resolvedColors]);

  // Plugin: labels inline nas barras
  const dataLabelPlugin = useMemo<Plugin<'bar'>>(() => ({
    id: 'inlineDataLabels',
    afterDatasetsDraw(chart) {
      const { ctx } = chart;
      chart.data.datasets.forEach((dataset, datasetIndex) => {
        const meta = chart.getDatasetMeta(datasetIndex);
        meta.data.forEach((bar, index) => {
          const raw = dataset.data[index];
          if (raw === null || raw === undefined) return;
          const value = Number(raw);
          if (!Number.isFinite(value) || value === 0) return;

          const formatted = valueFormat ? formatByType(value, valueFormat) : String(value);
          ctx.save();
          ctx.font = `600 11px ${CHART_FONT}`;
          ctx.fillStyle = '#0f172a';

          if (horizontal) {
            ctx.textAlign = 'left';
            ctx.textBaseline = 'middle';
            const chartRight = chart.chartArea?.right ?? Infinity;
            const textWidth = ctx.measureText(formatted).width;
            const labelX = Math.min(bar.x + 6, chartRight - textWidth - 4);
            ctx.fillText(formatted, labelX, bar.y);
          } else {
            ctx.textAlign = 'center';
            ctx.textBaseline = 'bottom';
            ctx.fillText(formatted, bar.x, bar.y - 4);
          }
          ctx.restore();
        });
      });
    },
  }), [valueFormat, horizontal]);

  // Plugin: linha de referência melhorada
  const referenceLinePlugin = useMemo<Plugin<'bar'> | undefined>(() => {
    if (!referenceLine || typeof referenceLine.value !== 'number' || Number.isNaN(referenceLine.value)) {
      return undefined;
    }
    const lineColor = referenceLine.color || '#dc2626';
    const label = referenceLine.label || '';

    return {
      id: 'referenceLinePlugin',
      afterDraw: (chart) => {
        const { ctx, chartArea } = chart;
        if (!chartArea) return;

        const valueScale = horizontal ? chart.scales.x : chart.scales.y;
        if (!valueScale) return;
        const pixel = valueScale.getPixelForValue(referenceLine.value);
        if (!Number.isFinite(pixel)) return;

        ctx.save();
        ctx.strokeStyle = lineColor;
        ctx.fillStyle = lineColor;
        ctx.setLineDash([6, 4]);
        ctx.lineWidth = 2.0;

        if (horizontal) {
          ctx.beginPath();
          ctx.moveTo(pixel, chartArea.top);
          ctx.lineTo(pixel, chartArea.bottom);
          ctx.stroke();
          if (label) {
            ctx.setLineDash([]);
            ctx.font = `600 12px ${CHART_FONT}`;
            ctx.textAlign = 'left';
            ctx.textBaseline = 'top';
            ctx.fillText(label, pixel + 6, chartArea.top + 4);
          }
        } else {
          ctx.beginPath();
          ctx.moveTo(chartArea.left, pixel);
          ctx.lineTo(chartArea.right, pixel);
          ctx.stroke();
          if (label) {
            ctx.setLineDash([]);
            ctx.font = `600 12px ${CHART_FONT}`;
            ctx.textAlign = 'right';
            ctx.textBaseline = 'bottom';
            ctx.fillText(label, chartArea.right - 4, pixel - 4);
          }
        }
        ctx.restore();
      },
    };
  }, [referenceLine, horizontal]);

  const options = useMemo<ChartOptions<'bar'>>(() => {
    const valueScaleOptions = createFormattedScaleOptions({
      format: valueFormat,
      label: yAxisLabel,
      beginAtZero: true,
      ...(maxValue !== undefined && { max: maxValue }),
    });

    // Aplicar cor de grid do tema
    const gridObj = (valueScaleOptions.grid ?? {}) as Record<string, unknown>;
    gridObj.color = GRID_COLOR;
    (valueScaleOptions as Record<string, unknown>).grid = gridObj;

    return {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: horizontal ? ('y' as const) : ('x' as const),
      layout: {
        padding: horizontal ? { right: 64 } : { top: 20 },
      },
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
          footerFont: { size: 10, family: CHART_FONT },
          padding: 12,
          cornerRadius: 8,
          displayColors: true,
          boxPadding: 4,
          callbacks: {
            ...(valueFormat ? { label: createTooltipCallback(valueFormat) } : {}),
            afterLabel: (context) => {
              const allData = (context.dataset.data as (number | null)[])
                .map(Number)
                .filter((v): v is number => Number.isFinite(v));
              if (allData.length === 0) return '';
              const max = Math.max(...allData);
              if (max === 0) return '';
              const pct = Math.round((Number(context.raw) / max) * 100);
              const sorted = allData.slice().sort((a, b) => b - a);
              const rank = sorted.indexOf(Number(context.raw)) + 1;
              return `Rank #${rank} · ${pct}% do máximo`;
            },
          },
        },
      },
      scales: {
        [labelAxis]: {
          grid: { display: false },
          border: { display: false },
          ticks: {
            font: { size: 11, family: CHART_FONT },
            color: '#64748b',
            ...(horizontal && {
              callback: (value: string | number) => {
                const lbl = typeof value === 'string' ? value : String(value);
                return lbl.length > 25 ? lbl.substring(0, 22) + '…' : lbl;
              },
            }),
          },
        },
        [valueAxis]: {
          ...valueScaleOptions,
          ticks: {
            ...(valueScaleOptions.ticks ?? {}),
            font: { size: 11, family: CHART_FONT },
            color: '#64748b',
          },
        },
      },
      animation: {
        duration: 600,
        easing: 'easeOutCubic' as const,
      },
    } as ChartOptions<'bar'>;
  }, [title, yAxisLabel, horizontal, valueFormat, valueAxis, labelAxis, maxValue]);

  const chartData = useMemo(() => ({
    labels,
    datasets: datasets.map((ds, i) => ({
      ...ds,
      backgroundColor: resolvedColors[i],
      borderColor: 'transparent',
      borderWidth: 0,
      borderRadius: 6,
      hoverBackgroundColor: hexToRgba(resolvedColors[i], 0.75),
    })),
  }), [labels, datasets, resolvedColors]);

  const plugins: Plugin<'bar'>[] = [dataLabelPlugin];
  if (referenceLinePlugin) plugins.push(referenceLinePlugin);

  return (
    <div className={`${height} w-full`}>
      <Bar ref={chartRef} data={chartData} options={options} plugins={plugins} />
    </div>
  );
}
