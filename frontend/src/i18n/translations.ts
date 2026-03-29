export type Locale = 'pt-BR' | 'en-US';

export type TranslationKey =
  | 'app.title'
  | 'app.userFallback'
  | 'app.logout'
  | 'navigation.dashboard'
  | 'navigation.module1'
  | 'navigation.module2'
  | 'navigation.module3'
  | 'navigation.module4'
  | 'navigation.module5'
  | 'navigation.module6'
  | 'navigation.module7'
  | 'navigation.module8'
  | 'navigation.module9'
  | 'navigation.module10'
  | 'navigation.module11'
  // Module 3 — multiplier panel
  | 'module3.multiplier.causalBeta'
  | 'module3.multiplier.causalActive'
  | 'module3.multiplier.literaryProxy'
  | 'module3.multiplier.coefficient'
  | 'module3.multiplier.range'
  | 'module3.multiplier.confidence'
  | 'module3.multiplier.region'
  // Module 3 — quality warnings
  | 'module3.warnings.title'
  // Module 3 — shock simulator
  | 'module3.shock.title'
  | 'module3.shock.quickScenarios'
  | 'module3.shock.add'
  | 'module3.shock.municipality'
  | 'module3.shock.disclaimer'
  // Module 3 — causal link
  | 'module3.causal.linkDescription'
  | 'module3.causal.linkButton'
  // Module 5 — matching
  | 'module5.matching.suggest'
  | 'module5.matching.searching'
  // Module 5 — report download
  | 'module5.report.generating'
  | 'module5.report.button'
  // Module 5 — diagnostics
  | 'module5.diagnostics.title'
  | 'module5.diagnostics.observations'
  | 'module5.diagnostics.parallelTrends'
  // Common
  | 'common.errorLoading'
  | 'common.noData'
  | 'common.filters'
  | 'common.clearFilters'
  // Module titles & subtitles
  | 'module1.title'
  | 'module1.subtitle'
  | 'module2.title'
  | 'module2.subtitle'
  | 'module4.title'
  | 'module4.subtitle'
  | 'module6.title'
  | 'module6.subtitle'
  | 'module7.title'
  | 'module7.subtitle'
  | 'module7.compositeSection'
  | 'module8.title'
  | 'module8.subtitle'
  | 'module9.title'
  | 'module9.subtitle'
  | 'module10.title'
  | 'module10.subtitle'
  | 'module11.title'
  | 'module11.subtitle'
  | 'module11.selectPort'
  | 'module11.selectPortHint'
  | 'dashboard.title'
  | 'dashboard.totalIndicators'
  | 'dashboard.internationalStandard'
  | 'dashboard.totalModules'
  | 'dashboard.status';

type MessageCatalog = Record<TranslationKey, string>;

const messages: Record<Locale, MessageCatalog> = {
  'pt-BR': {
    'app.title': 'SaaS Impacto Portuário',
    'app.userFallback': 'Usuário',
    'app.logout': 'Sair',
    'navigation.dashboard': 'Dashboard',
    'navigation.module1': 'Módulo 1',
    'navigation.module2': 'Módulo 2',
    'navigation.module3': 'Módulo 3',
    'navigation.module4': 'Módulo 4',
    'navigation.module5': 'Módulo 5',
    'navigation.module6': 'Módulo 6',
    'navigation.module7': 'Módulo 7',
    'navigation.module8': 'Contexto Macro',
    'navigation.module9': 'Risco Ambiental',
    'navigation.module10': 'Compliance',
    'navigation.module11': 'Previsão de Cargas',
    // Module 3 — multiplier panel
    'module3.multiplier.causalBeta': 'Estimativa de impacto aproximada',
    'module3.multiplier.causalActive': 'Estimativa de impacto ativa',
    'module3.multiplier.literaryProxy': 'Estimativa de referência · não causal',
    'module3.multiplier.coefficient': 'Fator de impacto',
    'module3.multiplier.range': 'Intervalo',
    'module3.multiplier.confidence': 'Confiança',
    'module3.multiplier.region': 'Região',
    // Module 3 — quality warnings
    'module3.warnings.title': 'Observações de qualidade',
    // Module 3 — shock simulator
    'module3.shock.title': 'Simulação de Choque de Carga',
    'module3.shock.quickScenarios': 'Cenários rápidos:',
    'module3.shock.add': 'Adicionar',
    'module3.shock.municipality': 'Município',
    'module3.shock.disclaimer': 'Δ Total estimado de empregos (diretos + indiretos + induzidos) para cada cenário de variação de tonelagem. Base: multiplicadores de referência internacional. Hipótese linear — não constitui previsão causal.',
    // Module 3 — causal link
    'module3.causal.linkDescription': 'Para verificar se o impacto no emprego é causal (e não apenas correlação), execute uma análise de impacto no Módulo 5 com o indicador de vínculos.',
    'module3.causal.linkButton': 'Analisar impacto causal no emprego →',
    // Module 5 — matching
    'module5.matching.suggest': 'Sugerir automaticamente',
    'module5.matching.searching': 'Buscando...',
    // Module 5 — report download
    'module5.report.generating': 'Gerando...',
    'module5.report.button': 'Relatório',
    // Module 5 — diagnostics
    'module5.diagnostics.title': 'Diagnósticos do Resultado',
    'module5.diagnostics.observations': 'Observações',
    'module5.diagnostics.parallelTrends': 'Parallel trends (p)',
    // Common
    'common.errorLoading': 'Erro ao carregar dados',
    'common.noData': 'Sem dados disponíveis',
    'common.filters': 'Filtros:',
    'common.clearFilters': 'Limpar filtros',
    // Module titles
    'module1.title': 'Módulo 1 - Operações de Navios',
    'module1.subtitle': 'Indicadores operacionais padronizados e análises para investidores',
    'module2.title': 'Módulo 2 - Operações de Carga',
    'module2.subtitle': '7 indicadores de operações de carga',
    'module4.title': 'Módulo 4 - Comércio Exterior',
    'module4.subtitle': '6 indicadores de comércio exterior',
    'module6.title': 'Módulo 6 - Finanças Públicas',
    'module6.subtitle': '11 indicadores de impacto fiscal com leitura causal e associativa',
    'module7.title': 'Módulo 7 - Índices de Desempenho',
    'module7.subtitle': '10 indicadores de desempenho (7 operacionais + 3 integrados entre módulos)',
    'module7.compositeSection': 'Indicadores Integrados',
    'module8.title': 'Contexto Macroeconômico',
    'module8.subtitle': 'Indicadores econômicos nacionais para contexto de investimento no setor portuário',
    'module9.title': 'Risco Ambiental',
    'module9.subtitle': 'Monitoramento de riscos hídricos e ambientais para instalações portuárias',
    'module10.title': 'Conformidade e Governança',
    'module10.subtitle': 'Monitoramento regulatório do ecossistema portuário',
    'module11.title': 'Previsão de Movimentação de Cargas',
    'module11.subtitle': 'Projeção de 5 anos com base em indicadores econômicos, operacionais, safra e clima',
    'module11.selectPort': 'Selecione um porto para gerar a previsão de cargas.',
    'module11.selectPortHint': 'A projeção utiliza o histórico operacional da instalação selecionada.',
    'dashboard.title': 'Dashboard',
    'dashboard.totalIndicators': 'Total Indicadores',
    'dashboard.internationalStandard': 'Padrão Internacional',
    'dashboard.totalModules': 'Total Módulos',
    'dashboard.status': 'Status',
  },
  'en-US': {
    'app.title': 'SaaS Port Economic Impact',
    'app.userFallback': 'User',
    'app.logout': 'Sign out',
    'navigation.dashboard': 'Dashboard',
    'navigation.module1': 'Module 1',
    'navigation.module2': 'Module 2',
    'navigation.module3': 'Module 3',
    'navigation.module4': 'Module 4',
    'navigation.module5': 'Module 5',
    'navigation.module6': 'Module 6',
    'navigation.module7': 'Module 7',
    'navigation.module8': 'Macro Context',
    'navigation.module9': 'Environmental Risk',
    'navigation.module10': 'Compliance',
    'navigation.module11': 'Cargo Forecast',
    // Module 3 — multiplier panel
    'module3.multiplier.causalBeta': 'Approximate impact estimate',
    'module3.multiplier.causalActive': 'Active impact estimate',
    'module3.multiplier.literaryProxy': 'Reference estimate · non-causal',
    'module3.multiplier.coefficient': 'Impact factor',
    'module3.multiplier.range': 'Range',
    'module3.multiplier.confidence': 'Confidence',
    'module3.multiplier.region': 'Region',
    // Module 3 — quality warnings
    'module3.warnings.title': 'Quality notes',
    // Module 3 — shock simulator
    'module3.shock.title': 'Cargo Shock Simulation',
    'module3.shock.quickScenarios': 'Quick scenarios:',
    'module3.shock.add': 'Add',
    'module3.shock.municipality': 'Municipality',
    'module3.shock.disclaimer': 'Δ Estimated total jobs (direct + indirect + induced) for each tonnage variation scenario. Based on international reference multipliers. Linear assumption — does not constitute a causal forecast.',
    // Module 3 — causal link
    'module3.causal.linkDescription': 'To verify whether the employment impact is causal (not just correlation), run an impact analysis in Module 5 using the employment indicator.',
    'module3.causal.linkButton': 'Analyze causal employment impact →',
    // Module 5 — matching
    'module5.matching.suggest': 'Auto-suggest',
    'module5.matching.searching': 'Searching...',
    // Module 5 — report download
    'module5.report.generating': 'Generating...',
    'module5.report.button': 'Report',
    // Module 5 — diagnostics
    'module5.diagnostics.title': 'Result Diagnostics',
    'module5.diagnostics.observations': 'Observations',
    'module5.diagnostics.parallelTrends': 'Parallel trends (p)',
    // Common
    'common.errorLoading': 'Error loading data',
    'common.noData': 'No data available',
    'common.filters': 'Filters:',
    'common.clearFilters': 'Clear filters',
    // Module titles
    'module1.title': 'Module 1 - Ship Operations',
    'module1.subtitle': 'Standardized operational indicators and investor analytics',
    'module2.title': 'Module 2 - Cargo Operations',
    'module2.subtitle': '7 cargo operations indicators',
    'module4.title': 'Module 4 - International Trade',
    'module4.subtitle': '6 international trade indicators',
    'module6.title': 'Module 6 - Public Finance',
    'module6.subtitle': '11 fiscal impact indicators with causal and associative analysis',
    'module7.title': 'Module 7 - Performance Indices',
    'module7.subtitle': '10 performance indicators (7 operational + 3 cross-module)',
    'module7.compositeSection': 'Integrated Indicators',
    'module8.title': 'Macroeconomic Context',
    'module8.subtitle': 'National economic indicators for port investment context',
    'module9.title': 'Environmental Risk',
    'module9.subtitle': 'Monitoring water and environmental risks for port facilities',
    'module10.title': 'Compliance & Governance',
    'module10.subtitle': 'Regulatory monitoring of the port ecosystem',
    'module11.title': 'Cargo Movement Forecast',
    'module11.subtitle': '5-year projection based on economic, operational, crop, and climate indicators',
    'module11.selectPort': 'Select a port to generate the cargo forecast.',
    'module11.selectPortHint': 'The projection uses the operational history of the selected facility.',
    'dashboard.title': 'Dashboard',
    'dashboard.totalIndicators': 'Total Indicators',
    'dashboard.internationalStandard': 'International Standard',
    'dashboard.totalModules': 'Total Modules',
    'dashboard.status': 'Status',
  },
};

export const DEFAULT_LOCALE: Locale = 'pt-BR';
const STORAGE_KEY = 'saas-impacto-locale';

export function normalizeLocale(value: string): Locale {
  if (value === 'en-US') {
    return 'en-US';
  }
  return DEFAULT_LOCALE;
}

export function getInitialLocale(): Locale {
  if (typeof window === 'undefined') {
    return DEFAULT_LOCALE;
  }

  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored) {
    return normalizeLocale(stored);
  }

  const acceptLanguage = navigator.language || navigator.languages?.[0];
  if (acceptLanguage?.toLowerCase().startsWith('en')) {
    return 'en-US';
  }

  return DEFAULT_LOCALE;
}

export function persistLocale(locale: Locale): void {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, locale);
}

export function t(locale: Locale, key: TranslationKey): string {
  return messages[locale][key];
}
