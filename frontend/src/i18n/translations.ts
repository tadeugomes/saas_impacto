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
  | 'navigation.module12'
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
  | 'common.noDataAvailable'
  | 'common.noDataForFilter'
  | 'common.filters'
  | 'common.clearFilters'
  | 'common.all'
  | 'common.searchSeries'
  | 'common.indicator'
  | 'common.year'
  | 'common.source'
  | 'common.period'
  | 'common.value'
  | 'common.weight'
  | 'common.scale'
  | 'common.composition'
  | 'common.methodNote'
  | 'common.hide'
  | 'common.show'
  | 'common.indicators'
  | 'common.current'
  | 'common.previous'
  | 'common.active'
  | 'common.exportModule'
  | 'common.exportIndicator'
  | 'common.generating'
  | 'common.selectInstallation'
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
  | 'module12.title'
  | 'module12.subtitle'
  | 'module11.selectPort'
  | 'module11.selectPortHint'
  // Module 1 — tabs & sections
  | 'module1.tab.descriptive'
  | 'module1.tab.trend'
  | 'module1.tab.score'
  | 'module1.trend.selectHint'
  | 'module1.trend.noData'
  | 'module1.score.selectHint'
  | 'module1.score.noData'
  | 'module1.score.decomposition'
  // Module 6 — groups
  | 'module6.group.taxation'
  | 'module6.group.perCapita'
  | 'module6.group.performance'
  | 'module6.group.causal'
  // Module 7 — composite
  | 'module7.composite.description'
  // Module 9
  | 'module9.composition.title'
  // Module 10
  | 'module10.risk.title'
  | 'module10.governance.title'
  | 'module10.sentiment.title'
  | 'module10.composition.title'
  // Module 11 — sections
  | 'module11.accuracy'
  | 'module11.validationPeriod'
  | 'module11.variables'
  | 'module11.categories'
  | 'module11.horizon'
  | 'module11.horizonDesc'
  | 'module11.forecast.title'
  | 'module11.scenarios.title'
  | 'module11.scenarios.chart'
  | 'module11.drivers.title'
  | 'module11.drivers.description'
  | 'module11.validation.title'
  | 'module11.confidence.note'
  | 'module11.executive.title'
  | 'module11.executive.note'
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
    'navigation.module12': 'Capacidade Portuária',
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
    'common.noDataAvailable': 'Dados não disponíveis',
    'common.noDataForFilter': 'Dados não disponíveis para o filtro atual.',
    'common.filters': 'Filtros:',
    'common.clearFilters': 'Limpar filtros',
    'common.all': 'Todos',
    'common.searchSeries': 'Buscar na série',
    'common.indicator': 'Indicador',
    'common.year': 'Ano',
    'common.source': 'Fonte:',
    'common.period': 'Período:',
    'common.value': 'Valor:',
    'common.weight': 'Peso:',
    'common.scale': 'Escala',
    'common.composition': 'Composição:',
    'common.methodNote': 'Nota metodológica:',
    'common.hide': 'Ocultar',
    'common.show': 'Mostrar',
    'common.indicators': 'Indicadores',
    'common.current': 'Atual',
    'common.previous': 'Anterior',
    'common.active': 'Ativo',
    'common.exportModule': 'Exportar Módulo',
    'common.exportIndicator': 'Exportar Indicador',
    'common.generating': 'Gerando...',
    'common.selectInstallation': 'Selecione uma instalação no filtro acima.',
    // Module 1
    'module1.tab.descriptive': 'Indicadores Descritivos',
    'module1.tab.trend': 'Tendência Operacional',
    'module1.tab.score': 'Score de Eficiência',
    'module1.trend.selectHint': 'Selecione uma instalação no filtro acima para ver a análise de tendência.',
    'module1.trend.noData': 'Sem dados de tendência para esta instalação/período.',
    'module1.score.selectHint': 'Selecione uma instalação no filtro acima para ver o score de eficiência.',
    'module1.score.noData': 'Sem dados de eficiência para esta instalação/período.',
    'module1.score.decomposition': 'Decomposição por componente',
    // Module 6
    'module6.group.taxation': 'Arrecadação Municipal (FINBRA)',
    'module6.group.perCapita': 'Indicadores per Capita',
    'module6.group.performance': 'Eficiência Fiscal por Tonelada',
    'module6.group.causal': 'Associação Tonelagem × Receita',
    // Module 7
    'module7.composite.description': 'Indicadores integrados que combinam dados operacionais, econômicos, fiscais e ambientais. Cada índice inclui transparência total sobre os componentes utilizados.',
    // Module 9
    'module9.composition.title': 'Composição do Índice de Risco Ambiental',
    // Module 10
    'module10.risk.title': 'Risco Regulatório',
    'module10.governance.title': 'Governança Portuária',
    'module10.sentiment.title': 'Análise de Menções em Diário Oficial',
    'module10.composition.title': 'Composição do Índice de Risco Regulatório',
    // Module 11
    'module11.accuracy': 'Taxa de Erro do Modelo',
    'module11.validationPeriod': 'Quanto menor, melhor · Validação 12 meses',
    'module11.variables': 'Variáveis Consideradas',
    'module11.categories': '5 categorias de dados',
    'module11.horizon': 'Horizonte',
    'module11.horizonDesc': '60 meses com faixa de confiança de 80% e 95%',
    'module11.forecast.title': 'Projeção de Tonelagem — 5 Anos',
    'module11.scenarios.title': 'Cenários — 5 Anos',
    'module11.scenarios.chart': 'Comparativo de Cenários',
    'module11.drivers.title': 'Fatores que Influenciam a Previsão',
    'module11.drivers.description': 'Peso relativo de cada fator na projeção. Os fatores são agrupados em 5 categorias: Histórico, Macroeconomia, Operação, Safra e Clima.',
    'module11.validation.title': 'Validação do Modelo — Precisão por Período',
    'module11.confidence.note': 'Confiança: Alta (Ano 1, fatores observados), Média (Anos 2-3, cenário macroeconômico projetado), Baixa (Anos 4-5, tendência de longo prazo — faixa ampla, usar com cautela).',
    'module11.executive.title': 'Resumo Executivo',
    'module11.executive.note': 'Análise gerada automaticamente com base no histórico operacional do porto selecionado. Escrita para gestores e investidores.',
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
    'module12.title': 'Capacidade Portuária',
    'module12.subtitle': 'Análise de capacidade de cais (Eq. 1b), BOR/BUR e identificação de gargalos para investidores',
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
    'navigation.module12': 'Port Capacity',
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
    'common.noDataAvailable': 'Data not available',
    'common.noDataForFilter': 'No data available for the current filter.',
    'common.filters': 'Filters:',
    'common.clearFilters': 'Clear filters',
    'common.all': 'All',
    'common.searchSeries': 'Search series',
    'common.indicator': 'Indicator',
    'common.year': 'Year',
    'common.source': 'Source:',
    'common.period': 'Period:',
    'common.value': 'Value:',
    'common.weight': 'Weight:',
    'common.scale': 'Scale',
    'common.composition': 'Composition:',
    'common.methodNote': 'Methodology note:',
    'common.hide': 'Hide',
    'common.show': 'Show',
    'common.indicators': 'Indicators',
    'common.current': 'Current',
    'common.previous': 'Previous',
    'common.active': 'Active',
    'common.exportModule': 'Export Module',
    'common.exportIndicator': 'Export Indicator',
    'common.generating': 'Generating...',
    'common.selectInstallation': 'Select a facility in the filter above.',
    // Module 1
    'module1.tab.descriptive': 'Descriptive Indicators',
    'module1.tab.trend': 'Operational Trend',
    'module1.tab.score': 'Efficiency Score',
    'module1.trend.selectHint': 'Select a facility in the filter above to view the trend analysis.',
    'module1.trend.noData': 'No trend data for this facility/period.',
    'module1.score.selectHint': 'Select a facility in the filter above to view the efficiency score.',
    'module1.score.noData': 'No efficiency data for this facility/period.',
    'module1.score.decomposition': 'Component breakdown',
    // Module 6
    'module6.group.taxation': 'Municipal Revenue (FINBRA)',
    'module6.group.perCapita': 'Per Capita Indicators',
    'module6.group.performance': 'Fiscal Efficiency per Tonne',
    'module6.group.causal': 'Tonnage × Revenue Association',
    // Module 7
    'module7.composite.description': 'Integrated indicators combining operational, economic, fiscal, and environmental data. Each index includes full transparency on the components used.',
    // Module 9
    'module9.composition.title': 'Environmental Risk Index Composition',
    // Module 10
    'module10.risk.title': 'Regulatory Risk',
    'module10.governance.title': 'Port Governance',
    'module10.sentiment.title': 'Official Gazette Mentions Analysis',
    'module10.composition.title': 'Regulatory Risk Index Composition',
    // Module 11
    'module11.accuracy': 'Model Error Rate',
    'module11.validationPeriod': 'Lower is better · 12-month validation',
    'module11.variables': 'Variables Considered',
    'module11.categories': '5 data categories',
    'module11.horizon': 'Forecast Horizon',
    'module11.horizonDesc': '60 months with 80% and 95% confidence intervals',
    'module11.forecast.title': 'Tonnage Projection — 5 Years',
    'module11.scenarios.title': 'Scenarios — 5 Years',
    'module11.scenarios.chart': 'Scenario Comparison',
    'module11.drivers.title': 'Factors Influencing the Forecast',
    'module11.drivers.description': 'Relative weight of each factor in the projection. Factors are grouped into 5 categories: Historical, Macroeconomics, Operations, Crops, and Climate.',
    'module11.validation.title': 'Model Validation — Accuracy by Period',
    'module11.confidence.note': 'Confidence: High (Year 1, observed factors), Medium (Years 2-3, projected macro scenario), Low (Years 4-5, long-term trend — wide range, use with caution).',
    'module11.executive.title': 'Executive Summary',
    'module11.executive.note': 'Analysis generated automatically based on the selected port\'s operational history. Written for managers and investors.',
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
    'module12.title': 'Port Capacity',
    'module12.subtitle': 'Berth capacity analysis (Eq. 1b), BOR/BUR and bottleneck identification for investors',
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
