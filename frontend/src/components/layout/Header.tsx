// import { useNavigate } from 'react-router-dom';
import { LogOut, User, Menu } from 'lucide-react';
  import { useAuth } from '../../hooks/useAuth';
import { Locale } from '../../i18n/translations';
import { useI18n } from '../../i18n/I18nContext';

interface HeaderProps {
  onMenuToggle?: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  // const navigate = useNavigate();
  const { user, logout, isLoading } = useAuth();
  const { locale, setLocale, t } = useI18n();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <header className="bg-primary text-white shadow-md">
      <div className="flex items-center justify-between px-6 py-3">
        <div className="flex items-center gap-4">
          {onMenuToggle && (
            <button
              onClick={onMenuToggle}
              className="p-2 hover:bg-primary-dark rounded-lg transition-colors lg:hidden"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}
          <h1 className="text-xl font-bold">{t('app.title')}</h1>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 text-sm">
            <User className="w-4 h-4" />
            <span>{user?.name || t('app.userFallback')}</span>
          </div>
          <select
            value={locale}
            onChange={(event) => setLocale(event.target.value as Locale)}
            className="rounded-md border border-white/30 bg-white/10 px-2 py-1 text-sm text-white"
            aria-label="Idioma"
            title="Idioma / Language"
          >
            <option value="pt-BR">Português</option>
            <option value="en-US">English</option>
          </select>
          <button
            onClick={handleLogout}
            disabled={isLoading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-primary-dark transition-colors disabled:opacity-50"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">{t('app.logout')}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
