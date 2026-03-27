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
  | 'module5.diagnostics.parallelTrends';

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
    // Module 3 — multiplier panel
    'module3.multiplier.causalBeta': 'Estimativa causal aproximada (beta)',
    'module3.multiplier.causalActive': 'Estimativa causal ativa',
    'module3.multiplier.literaryProxy': 'Proxy literário · não causal',
    'module3.multiplier.coefficient': 'Coeficiente',
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
    'module3.shock.disclaimer': 'Δ Total estimado de empregos (diretos + indiretos + induzidos) para cada cenário de variação de tonelagem. Base: multiplicadores de literatura (UNCTAD/MInfra). Hipótese linear — não constitui previsão causal.',
    // Module 3 — causal link
    'module3.causal.linkDescription': 'Para verificar se o impacto no emprego é causal (e não apenas correlação), execute uma análise econométrica no Módulo 5 com o indicador de vínculos.',
    'module3.causal.linkButton': 'Analisar impacto causal no emprego →',
    // Module 5 — matching
    'module5.matching.suggest': 'Sugerir automaticamente',
    'module5.matching.searching': 'Buscando...',
    // Module 5 — report download
    'module5.report.generating': 'Gerando...',
    'module5.report.button': 'Relatório',
    // Module 5 — diagnostics
    'module5.diagnostics.title': 'Diagnósticos da Estimativa',
    'module5.diagnostics.observations': 'Observações',
    'module5.diagnostics.parallelTrends': 'Parallel trends (p)',
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
    // Module 3 — multiplier panel
    'module3.multiplier.causalBeta': 'Approximate causal estimate (beta)',
    'module3.multiplier.causalActive': 'Active causal estimate',
    'module3.multiplier.literaryProxy': 'Literary proxy · non-causal',
    'module3.multiplier.coefficient': 'Coefficient',
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
    'module3.shock.disclaimer': 'Δ Estimated total jobs (direct + indirect + induced) for each tonnage variation scenario. Base: literature multipliers (UNCTAD/MInfra). Linear hypothesis — does not constitute a causal forecast.',
    // Module 3 — causal link
    'module3.causal.linkDescription': 'To verify whether the employment impact is causal (not just correlation), run an econometric analysis in Module 5 using the employment indicator.',
    'module3.causal.linkButton': 'Analyze causal employment impact →',
    // Module 5 — matching
    'module5.matching.suggest': 'Auto-suggest',
    'module5.matching.searching': 'Searching...',
    // Module 5 — report download
    'module5.report.generating': 'Generating...',
    'module5.report.button': 'Report',
    // Module 5 — diagnostics
    'module5.diagnostics.title': 'Estimation Diagnostics',
    'module5.diagnostics.observations': 'Observations',
    'module5.diagnostics.parallelTrends': 'Parallel trends (p)',
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
