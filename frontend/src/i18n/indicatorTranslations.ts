/**
 * Traduções EN para nomes e descrições de indicadores.
 * Os indicadores são definidos em PT-BR nos arrays INDICATORS_INFO de cada módulo.
 * Este mapa fornece as traduções EN para troca de idioma.
 */

import { useI18n } from './I18nContext';

interface IndicatorTranslation {
  name: string;
  desc: string;
  unit?: string;
}

const EN_TRANSLATIONS: Record<string, IndicatorTranslation> = {
  // Module 1 — Ship Operations
  'IND-1.01': { name: 'Average Waiting Time', desc: 'Time between arrival and berthing' },
  'IND-1.02': { name: 'Average Time in Port', desc: 'Total time in port' },
  'IND-1.03': { name: 'Gross Berthing Time', desc: 'Berthing to unberthing time' },
  'IND-1.04': { name: 'Net Operating Time', desc: 'Effective operating time' },
  'IND-1.05': { name: 'Berth Occupancy Rate', desc: 'Average berth occupancy' },
  'IND-1.06': { name: 'Average Idle Time', desc: 'Downtime duration' },
  'IND-1.07': { name: 'Average Gross Tonnage', desc: 'Average vessel size' },
  'IND-1.08': { name: 'Average Length', desc: 'Average vessel length' },
  'IND-1.09': { name: 'Maximum Draft', desc: 'Maximum operational draft' },
  'IND-1.10': { name: 'Distribution by Type', desc: 'By navigation type' },
  'IND-1.11': { name: 'Number of Berthings', desc: 'Total berthings' },
  'IND-1.12': { name: 'Idle Index', desc: 'Idle time / berthing time' },
  // Module 2 — Cargo Operations
  'IND-2.01': { name: 'Total Cargo Moved', desc: 'Sum of loaded and unloaded cargo' },
  'IND-2.05': { name: 'Average Cargo per Berthing', desc: 'Average cargo per berthing' },
  'IND-2.06': { name: 'Berth Productivity', desc: 'Tonnes per hour of operation' },
  'IND-2.10': { name: 'Total Tonnage (Ranking)', desc: 'Ranking by tonnage' },
  'IND-2.11': { name: 'Cargo Concentration', desc: 'Concentration index' },
  'IND-2.12': { name: 'Cargo Mix', desc: 'Distribution by cargo type' },
  'IND-2.13': { name: 'Seasonality', desc: 'Monthly cargo variation' },
  // Module 4 — International Trade
  'IND-4.01': { name: 'Exports', desc: 'Total export value' },
  'IND-4.02': { name: 'Imports', desc: 'Total import value' },
  'IND-4.03': { name: 'Trade Balance', desc: 'Trade surplus (Exp - Imp)' },
  'IND-4.04': { name: 'Export Weight', desc: 'Net weight of exports' },
  'IND-4.05': { name: 'Import Weight', desc: 'Net weight of imports' },
  'IND-4.10': { name: 'Market Share', desc: 'National market share' },
  // Module 6 — Public Finance
  'IND-6.01': { name: 'ICMS Revenue', desc: 'Total ICMS tax collected in the municipality' },
  'IND-6.02': { name: 'ISS Revenue', desc: 'Total ISS tax collected in the municipality' },
  'IND-6.03': { name: 'Total Municipal Revenue', desc: 'Total municipal revenue' },
  'IND-6.04': { name: 'Per Capita Revenue', desc: 'Revenue per inhabitant' },
  'IND-6.05': { name: 'Revenue Growth', desc: 'Annual revenue change (%)' },
  'IND-6.06': { name: 'ICMS per Tonne', desc: 'Fiscal efficiency of port movement' },
  'IND-6.07': { name: 'Total Tax Revenue', desc: 'ICMS + ISS by municipality' },
  'IND-6.08': { name: 'Tax Revenue per Capita', desc: 'Tax revenue per inhabitant' },
  'IND-6.09': { name: 'Tax Revenue per Tonne', desc: 'Total tax on physical movement' },
  'IND-6.10': { name: 'Tonnage-Revenue Correlation', desc: 'Statistical association between tonnage and fiscal revenue' },
  'IND-6.11': { name: 'Tonnage/Revenue Elasticity', desc: 'Historical log-log elasticity' },
  // Module 7 — Performance Indices
  'IND-7.01': { name: 'Port Efficiency Index', desc: 'Combined measure of operational efficiency' },
  'IND-7.02': { name: 'Relevance Index', desc: 'Measure of economic importance' },
  'IND-7.03': { name: 'Integration Index', desc: 'Measure of connection with local economy' },
  'IND-7.04': { name: 'Concentration Index', desc: 'Concentration index' },
  'IND-7.08': { name: 'Municipal Port Development (IDPM)', desc: 'Municipal Port Development' },
  'IND-7.09': { name: 'Operational Risk (IRO)', desc: 'Operational Risk' },
  'IND-7.10': { name: 'Port Governance (IGP)', desc: 'Port Governance' },
  // Module 8 — Macroeconomic Context
  'IND-8.01': { name: 'Base Interest Rate (Selic)', desc: 'Cost of capital for investors' },
  'IND-8.02': { name: 'Cumulative Inflation (12 months)', desc: 'Purchasing power loss in the period' },
  'IND-8.03': { name: 'Exchange Rate (BRL/USD)', desc: 'Export competitiveness' },
  'IND-8.04': { name: 'Monthly Economic Activity', desc: 'Monthly indicator of economic performance' },
  'IND-8.05': { name: 'Municipal Population', desc: 'Port municipality population' },
  'IND-8.06': { name: 'GDP per Capita', desc: 'Local economy size' },
  // Module 9 — Environmental Risk
  'IND-9.01': { name: 'Water Risk', desc: 'River level vs. minimum draft' },
  'IND-9.02': { name: 'Fire Hotspots', desc: 'Hotspots within 50km radius' },
  'IND-9.03': { name: 'Combined Environmental Risk', desc: 'Water + fire risk combination' },
  // Module 10 — Compliance & Governance
  'IND-10.01': { name: 'Port Procurement', desc: 'Public procurement in the port sector' },
  'IND-10.02': { name: 'Port Sanctions', desc: 'Sanctioned operators (Ineligible Registry)' },
  'IND-10.03': { name: 'Court of Auditors Decisions', desc: 'TCU decisions on ports' },
  'IND-10.04': { name: 'Official Gazette Mentions', desc: 'Analysis of mentions in official publications' },
  'IND-10.05': { name: 'Judicial Proceedings', desc: 'Port ecosystem litigation' },
  'IND-10.06': { name: 'Procurement Regularity', desc: 'Regular publication in PNCP' },
  'IND-10.07': { name: 'Regulatory Risk', desc: 'Combined risk measure' },
  'IND-10.08': { name: 'Port Governance', desc: 'Governance quality measure' },
};

/**
 * Hook que retorna nome e descrição do indicador no idioma ativo.
 * Se o idioma for PT-BR, retorna os valores originais do INDICATORS_INFO.
 * Se EN-US, busca no mapa de traduções.
 */
export function useIndicatorLabel() {
  const { locale } = useI18n();

  return (code: string, originalName: string, originalDesc: string) => {
    if (locale === 'pt-BR') {
      return { name: originalName, desc: originalDesc };
    }
    const translation = EN_TRANSLATIONS[code];
    return {
      name: translation?.name ?? originalName,
      desc: translation?.desc ?? originalDesc,
    };
  };
}

/**
 * Versão sem hook para uso em contextos não-React.
 */
export function getIndicatorLabel(
  locale: string,
  code: string,
  originalName: string,
  originalDesc: string,
) {
  if (locale === 'pt-BR') {
    return { name: originalName, desc: originalDesc };
  }
  const translation = EN_TRANSLATIONS[code];
  return {
    name: translation?.name ?? originalName,
    desc: translation?.desc ?? originalDesc,
  };
}
