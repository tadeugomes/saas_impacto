/**
 * Utilitários de formatação de números para português brasileiro.
 * Fornece funções para formatar números, moedas, percentuais e quantidades
 * seguindo as convenções do Brasil (ponto como separador de milhar, vírgula como decimal).
 */

/**
 * Formata um número para o padrão brasileiro.
 * @param value - Valor a ser formatado
 * @param decimals - Número de casas decimais (padrão: 2)
 * @returns String formatada (ex: "1.234,56")
 */
export function formatNumber(value: number, decimals: number = 2): string {
  if (typeof value !== 'number' || isNaN(value)) {
    return '0';
  }
  return value.toLocaleString('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Formata um número de forma compacta para valores grandes.
 * @param value - Valor a ser formatado
 * @returns String formatada com sufixo (ex: "1,2 mi", "3,4 bi", "5,6 mil")
 */
export function formatCompact(value: number): string {
  if (typeof value !== 'number' || isNaN(value)) {
    return '0';
  }

  const abs = Math.abs(value);

  // Bilhões
  if (abs >= 1_000_000_000) {
    return (value / 1_000_000_000).toLocaleString('pt-BR', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }) + ' bi';
  }

  // Milhões
  if (abs >= 1_000_000) {
    return (value / 1_000_000).toLocaleString('pt-BR', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }) + ' mi';
  }

  // Milhares
  if (abs >= 1_000) {
    return (value / 1_000).toLocaleString('pt-BR', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }) + ' mil';
  }

  // Abaixo de mil - sem decimal
  return value.toLocaleString('pt-BR', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

/**
 * Formata um valor monetário em Reais de forma compacta.
 * @param value - Valor em Reais
 * @returns String formatada (ex: "R$ 1,2 mi", "R$ 450 mil")
 */
export function formatCurrencyCompact(value: number): string {
  if (typeof value !== 'number' || isNaN(value)) {
    return 'R$ 0';
  }
  return 'R$ ' + formatCompact(value);
}

/**
 * Formata um valor monetário em Reais com formato completo.
 * @param value - Valor em Reais
 * @returns String formatada (ex: "R$ 1.234.567,89")
 */
export function formatCurrency(value: number): string {
  if (typeof value !== 'number' || isNaN(value)) {
    return 'R$ 0,00';
  }
  return value.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });
}

/**
 * Formata um valor como percentual.
 * @param value - Valor decimal (ex: 0.25 para 25%)
 * @returns String formatada (ex: "25,0%")
 */
export function formatPercent(value: number): string {
  if (typeof value !== 'number' || isNaN(value)) {
    return '0,0%';
  }
  return value.toLocaleString('pt-BR', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }) + '%';
}

/**
 * Formata um valor como percentual com até 2 casas decimais.
 * @param value - Valor decimal (ex: 0.2555 para 25.55%)
 * @returns String formatada (ex: "25,55%")
 */
export function formatPercentPrecise(value: number): string {
  if (typeof value !== 'number' || isNaN(value)) {
    return '0,00%';
  }
  return value.toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }) + '%';
}

/**
 * Formata uma quantidade (número inteiro sem decimal).
 * @param value - Valor a ser formatado
 * @returns String formatada (ex: "1.234")
 */
export function formatQuantity(value: number): string {
  if (typeof value !== 'number' || isNaN(value)) {
    return '0';
  }
  return value.toLocaleString('pt-BR', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

/**
 * Formata um valor decimal com número específico de casas.
 * @param value - Valor a ser formatado
 * @param decimals - Número de casas decimais (padrão: 2)
 * @returns String formatada
 */
export function formatDecimal(value: number, decimals: number = 2): string {
  if (typeof value !== 'number' || isNaN(value)) {
    return '0';
  }
  return value.toLocaleString('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Tipos de formatação suportados pelos gráficos.
 */
export type ChartValueFormat = 'number' | 'currency' | 'currency-compact' | 'percent' | 'quantity';

/**
 * Formata um valor de acordo com o tipo especificado.
 * @param value - Valor a ser formatado
 * @param format - Tipo de formatação
 * @returns String formatada
 */
export function formatByType(value: number, format: ChartValueFormat): string {
  if (typeof value !== 'number' || isNaN(value)) {
    return '0';
  }

  switch (format) {
    case 'currency':
      return formatCurrency(value);
    case 'currency-compact':
      return formatCurrencyCompact(value);
    case 'percent':
      return formatPercent(value);
    case 'quantity':
      return formatQuantity(value);
    case 'number':
    default:
      return formatCompact(value);
  }
}
