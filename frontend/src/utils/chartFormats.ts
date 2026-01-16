/**
 * Utilitários para formatação de gráficos Chart.js.
 * Fornece callbacks e opções de escala para formatação brasileira de valores.
 */

import type { ScaleOptions, Tick, TooltipItem } from 'chart.js';
import { formatByType, type ChartValueFormat } from './numberFormat';

export type { ChartValueFormat } from './numberFormat';

/**
 * Parâmetros para criação de callback de ticks.
 */
interface TickCallbackParams {
  format: ChartValueFormat;
  /** Valor máximo esperado (para ajustar formatação) */
  maxValue?: number;
}

/**
 * Cria uma função de callback para formatação de ticks dos eixos.
 * @param params - Parâmetros de formatação
 * @returns Função de callback para Chart.js
 */
export function createTickCallback(params: TickCallbackParams) {
  const { format, maxValue } = params;

  return function(value: string | number, _index: number, _ticks: Tick[]): string {
    const num = typeof value === 'number' ? value : parseFloat(String(value));

    if (isNaN(num)) {
      return String(value);
    }

    // Para valores muito grandes, usar formatação compacta
    if (maxValue && maxValue >= 1_000_000 && format === 'currency') {
      return formatByType(num, 'currency-compact');
    }

    return formatByType(num, format);
  };
}

/**
 * Cria uma função de callback personalizada para tooltips.
 * @param format - Tipo de formatação a ser aplicada
 * @returns Função para formatar labels de tooltips
 */
export function createTooltipCallback(format: ChartValueFormat) {
  return function(context: TooltipItem<'bar' | 'line'>): string {
    const label = context.dataset.label || '';
    const value = context.parsed.y !== undefined ? context.parsed.y : context.parsed.x;

    if (value === null || value === undefined) {
      return label;
    }

    const num = typeof value === 'number' ? value : parseFloat(String(value));
    if (isNaN(num)) {
      return `${label}: ${value}`;
    }

    const formattedValue = formatByType(num, format);

    // Se label já existe, combinar com valor
    if (label) {
      return `${label}: ${formattedValue}`;
    }

    return formattedValue;
  };
}

/**
 * Cria label para tooltip com contexto personalizado.
 * @param itemName - Nome do item (ex: nome do município)
 * @param value - Valor a ser formatado
 * @param format - Tipo de formatação
 * @returns String formatada para exibição no tooltip
 */
export function createTooltipLabel(itemName: string, value: number, format: ChartValueFormat): string {
  const formattedValue = formatByType(value, format);
  return `${itemName}: ${formattedValue}`;
}

/**
 * Configurações de escala base para gráficos.
 */
interface ScaleConfig {
  format?: ChartValueFormat;
  label?: string;
  min?: number;
  max?: number;
  beginAtZero?: boolean;
}

/**
 * Cria opções de escala com formatação brasileira.
 * @param config - Configurações da escala
 * @returns Objeto de opções de escala para Chart.js
 */
export function createFormattedScaleOptions(config: ScaleConfig = {}): ScaleOptions<'linear'> {
  const { format, label, min, max, beginAtZero = true } = config;

  const scaleOptions: ScaleOptions<'linear'> = {
    beginAtZero,
    ...(min !== undefined && { min }),
    ...(max !== undefined && { max }),
    grid: {
      color: 'rgba(0, 0, 0, 0.05)',
    },
    border: {
      display: false,
    },
    ticks: {
      font: {
        size: 11,
        family: "'Inter', system-ui, sans-serif",
      },
      color: '#6b7280',
      padding: 8,
    },
  };

  // Adicionar título da escala (eixo)
  if (label) {
    scaleOptions.title = {
      display: true,
      align: 'center',
      text: label,
      font: {
        size: 12,
        weight: 'normal',
        family: "'Inter', system-ui, sans-serif",
      },
      color: '#374151',
      padding: { top: 0, bottom: 10, y: 10 },
    };
  }

  // Adicionar formatação de ticks
  if (format) {
    const maxValue = max !== undefined ? max : 0;
    (scaleOptions.ticks as any).callback = createTickCallback({ format, maxValue });
  }

  return scaleOptions;
}

/**
 * Opções de formatação por tipo de indicador.
 */
export const INDICATOR_FORMATS: Record<string, ChartValueFormat> = {
  // Módulo 1 - Operações de Navios
  'IND-1.01': 'number',       // Tempo em horas
  'IND-1.02': 'number',
  'IND-1.03': 'number',
  'IND-1.04': 'number',
  'IND-1.05': 'percent',
  'IND-1.06': 'number',
  'IND-1.07': 'number',
  'IND-1.08': 'number',
  'IND-1.09': 'number',
  'IND-1.10': 'percent',
  'IND-1.11': 'quantity',
  'IND-1.12': 'percent',

  // Módulo 2 - Operações de Carga
  'IND-2.01': 'quantity',     // Toneladas
  'IND-2.02': 'quantity',     // TEUs
  'IND-2.03': 'quantity',     // Passageiros
  'IND-2.04': 'quantity',
  'IND-2.05': 'quantity',
  'IND-2.06': 'number',       // ton/hora
  'IND-2.07': 'number',
  'IND-2.08': 'number',
  'IND-2.09': 'number',
  'IND-2.10': 'quantity',
  'IND-2.11': 'quantity',
  'IND-2.12': 'percent',
  'IND-2.13': 'number',

  // Módulo 3 - Recursos Humanos
  'IND-3.01': 'quantity',     // Empregos
  'IND-3.02': 'percent',      // % feminino
  'IND-3.03': 'percent',
  'IND-3.04': 'percent',
  'IND-3.05': 'currency-compact',  // Salário R$
  'IND-3.06': 'currency-compact',  // Massa salarial R$
  'IND-3.07': 'number',       // ton/empregado
  'IND-3.08': 'currency-compact',
  'IND-3.09': 'percent',
  'IND-3.10': 'number',       // Idade média
  'IND-3.11': 'percent',
  'IND-3.12': 'percent',

  // Módulo 4 - Comércio Exterior
  'IND-4.01': 'currency-compact',  // US$
  'IND-4.02': 'currency-compact',
  'IND-4.03': 'currency-compact',
  'IND-4.04': 'quantity',     // kg
  'IND-4.05': 'quantity',
  'IND-4.06': 'number',       // US$/kg
  'IND-4.07': 'percent',
  'IND-4.08': 'percent',
  'IND-4.09': 'percent',
  'IND-4.10': 'percent',

  // Módulo 5 - Impacto Econômico
  'IND-5.01': 'currency-compact',
  'IND-5.02': 'currency-compact',
  'IND-5.03': 'quantity',
  'IND-5.04': 'percent',
  'IND-5.05': 'percent',
  'IND-5.06': 'number',
  'IND-5.07': 'number',
  'IND-5.08': 'percent',
  'IND-5.09': 'percent',
  'IND-5.10': 'percent',
  'IND-5.11': 'percent',
  'IND-5.12': 'percent',
  'IND-5.13': 'percent',
  'IND-5.14': 'number',       // correlação
  'IND-5.15': 'number',
  'IND-5.16': 'number',
  'IND-5.17': 'number',       // elasticidade
  'IND-5.18': 'percent',
  'IND-5.19': 'number',
  'IND-5.20': 'number',
  'IND-5.21': 'number',       // índice 0-100

  // Módulo 6 - Finanças Públicas
  'IND-6.01': 'currency-compact',
  'IND-6.02': 'currency-compact',
  'IND-6.03': 'currency-compact',
  'IND-6.04': 'currency-compact',
  'IND-6.05': 'percent',
  'IND-6.06': 'number',

  // Módulo 7 - Índices Sintéticos
  'IND-7.01': 'number',
  'IND-7.02': 'number',
  'IND-7.03': 'number',
  'IND-7.04': 'percent',
  'IND-7.05': 'number',
  'IND-7.06': 'number',
  'IND-7.07': 'percent',
};

/**
 * Retorna o tipo de formatação para um indicador.
 * @param indicatorCode - Código do indicador (ex: 'IND-3.01')
 * @returns Tipo de formatação ou 'number' como padrão
 */
export function getIndicatorFormat(indicatorCode: string): ChartValueFormat {
  return INDICATOR_FORMATS[indicatorCode] || 'number';
}
