// import { useNavigate } from 'react-router-dom';
import { LogOut, User, Menu } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

interface HeaderProps {
  onMenuToggle?: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  // const navigate = useNavigate();
  const { user, logout, isLoading } = useAuth();

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
          <h1 className="text-xl font-bold">SaaS Impacto Portuário</h1>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 text-sm">
            <User className="w-4 h-4" />
            <span>{user?.name || 'Usuário'}</span>
          </div>
          <button
            onClick={handleLogout}
            disabled={isLoading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-primary-dark transition-colors disabled:opacity-50"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">Sair</span>
          </button>
        </div>
      </div>
    </header>
  );
}
