/**
 * Tema visual premium para gráficos Chart.js.
 * Paleta financeiro-premium (Bloomberg/Refinitiv) com navy, teal e gold.
 */

export const CHART_PALETTE = {
  navy:    '#0f2d52', // deep navy — cor primária
  navyMid: '#1e4d7b', // navy médio
  teal:    '#0d9488', // teal — sucesso/crescimento
  gold:    '#c9860e', // gold — destaque
  slate:   '#475569', // slate — neutro
  sky:     '#0284c7', // sky blue
  violet:  '#6d28d9', // violeta
  crimson: '#b91c1c', // vermelho — alerta
  emerald: '#047857', // emerald verde
  amber:   '#b45309', // âmbar
} as const;

/** Ordem preferida para múltiplos datasets */
export const CHART_COLORS: string[] = [
  CHART_PALETTE.navy,
  CHART_PALETTE.teal,
  CHART_PALETTE.gold,
  CHART_PALETTE.sky,
  CHART_PALETTE.violet,
  CHART_PALETTE.emerald,
  CHART_PALETTE.amber,
  CHART_PALETTE.slate,
  CHART_PALETTE.crimson,
];

/** Acento de borda por número de módulo */
export const MODULE_ACCENT: Record<number, string> = {
  1: CHART_PALETTE.navy,
  2: CHART_PALETTE.teal,
  3: CHART_PALETTE.gold,
  4: CHART_PALETTE.violet,
  5: CHART_PALETTE.sky,
  6: CHART_PALETTE.emerald,
  7: CHART_PALETTE.slate,
};

/**
 * Converte hex #RRGGBB para rgba(r,g,b,alpha).
 * Aceita apenas strings hex de 6 dígitos.
 */
export function hexToRgba(hex: string, alpha: number): string {
  const clean = hex.replace('#', '');
  if (clean.length !== 6) return hex;
  const r = parseInt(clean.slice(0, 2), 16);
  const g = parseInt(clean.slice(2, 4), 16);
  const b = parseInt(clean.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

/**
 * Extrai número do módulo a partir do código de indicador.
 * Ex: "IND-3.01" → 3
 */
export function moduleFromIndicatorCode(code: string): number {
  const m = code.match(/IND-(\d+)\./);
  return m ? parseInt(m[1], 10) : 1;
}

/** Família tipográfica padrão para rótulos e labels */
export const CHART_FONT = "'Inter', system-ui, -apple-system, sans-serif";

/** Cor de grid visível mas discreta */
export const GRID_COLOR = 'rgba(100, 116, 139, 0.15)';
