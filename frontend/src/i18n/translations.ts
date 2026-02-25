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
  | 'navigation.module7';

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
