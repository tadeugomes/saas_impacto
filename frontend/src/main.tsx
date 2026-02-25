import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';
import { I18nProvider } from './i18n/I18nContext';

if ('serviceWorker' in navigator) {
  if (import.meta.env.DEV) {
    navigator.serviceWorker
      .getRegistrations()
      .then((registrations) => {
        registrations.forEach((registration) => void registration.unregister());
      })
      .catch(() => {});
  } else {
    navigator.serviceWorker
      .getRegistration('/sw.js')
      .then((registration) => {
        if (registration) {
          registration.unregister().catch(() => {});
        }
      })
      .catch(() => {});
  }

  window.addEventListener('load', () => {
    if (!import.meta.env.DEV) {
      navigator.serviceWorker
        .register('/sw.js')
        .catch(() => {
          console.warn('Falha ao registrar Service Worker');
        });
    }
  });
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <I18nProvider>
      <App />
    </I18nProvider>
  </StrictMode>
);
