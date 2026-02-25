import {
  createContext,
  PropsWithChildren,
  ReactNode,
  useContext,
  useMemo,
  useState,
} from 'react';
import {
  DEFAULT_LOCALE,
  getInitialLocale,
  Locale,
  TranslationKey,
  normalizeLocale,
  persistLocale,
  t as translate,
} from './translations';

type I18nContextValue = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: TranslationKey) => string;
};

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: PropsWithChildren): ReactNode {
  const [locale, setLocaleState] = useState<Locale>(getInitialLocale());

  const value = useMemo<I18nContextValue>(
    () => ({
      locale,
      setLocale: (nextLocale: Locale) => {
        const normalized = normalizeLocale(nextLocale);
        setLocaleState(normalized);
        persistLocale(normalized);
      },
      t: (key) => translate(locale, key),
    }),
    [locale],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const context = useContext(I18nContext);
  if (!context) {
    return {
      locale: DEFAULT_LOCALE,
      setLocale: () => {},
      t: (key) => translate(DEFAULT_LOCALE, key),
    };
  }
  return context;
}
