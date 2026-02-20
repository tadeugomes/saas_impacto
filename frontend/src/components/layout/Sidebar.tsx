import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '../../utils/cn';
import {
  LayoutDashboard,
  Anchor,
  Package,
  Users,
  Globe,
  TrendingUp,
  Building,
  LineChart,
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const navItems = [
  {
    path: '/dashboard',
    icon: LayoutDashboard,
    label: 'Dashboard',
    description: 'Visão geral',
  },
  {
    path: '/dashboard/module1',
    icon: Anchor,
    label: 'Módulo 1',
    description: 'Operações de Navios (12)',
    moduleColor: 'module1',
  },
  {
    path: '/dashboard/module2',
    icon: Package,
    label: 'Módulo 2',
    description: 'Operações de Carga (13)',
    moduleColor: 'module2',
  },
  {
    path: '/dashboard/module3',
    icon: Users,
    label: 'Módulo 3',
    description: 'Recursos Humanos (12)',
    moduleColor: 'module3',
  },
  {
    path: '/dashboard/module4',
    icon: Globe,
    label: 'Módulo 4',
    description: 'Comércio Exterior (10)',
    moduleColor: 'module4',
  },
  {
    path: '/dashboard/module5',
    icon: TrendingUp,
    label: 'Módulo 5',
    description: 'Impacto Econômico (21)',
    moduleColor: 'module5',
  },
  {
    path: '/dashboard/module6',
    icon: Building,
    label: 'Módulo 6',
    description: 'Finanças Públicas (6)',
    moduleColor: 'module6',
  },
  {
    path: '/dashboard/module7',
    icon: LineChart,
    label: 'Módulo 7',
    description: 'Índices Sintéticos (7)',
    moduleColor: 'module7',
  },
];

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation();

  return (
    <>
      {/* Overlay mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed lg:sticky top-0 left-0 z-50 h-screen bg-white border-r border-gray-200 transition-transform duration-300 lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full w-64">
          {/* Logo section */}
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                <Anchor className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="font-bold text-gray-900">Impacto Portuário</h2>
                <p className="text-xs text-gray-500">Sistema de Análise</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4">
            <ul className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;

                return (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      onClick={onClose}
                      className={cn(
                        'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                        isActive
                          ? 'bg-primary text-white shadow-sm'
                          : 'text-gray-700 hover:bg-gray-100'
                      )}
                    >
                      <Icon className="w-5 h-5" />
                      <div className="flex-1">
                        <div className="font-medium">{item.label}</div>
                        <div className={cn(
                          'text-xs',
                          isActive ? 'text-white/70' : 'text-gray-500'
                        )}>
                          {item.description}
                        </div>
                      </div>
                      {item.moduleColor && isActive && (
                        <div className={cn(
                          'w-2 h-2 rounded-full',
                          {
                            'bg-module1': item.moduleColor === 'module1',
                            'bg-module2': item.moduleColor === 'module2',
                            'bg-module3': item.moduleColor === 'module3',
                            'bg-module4': item.moduleColor === 'module4',
                            'bg-module5': item.moduleColor === 'module5',
                            'bg-module6': item.moduleColor === 'module6',
                            'bg-module7': item.moduleColor === 'module7',
                          }
                        )} />
                      )}
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              v{import.meta.env.VITE_APP_VERSION || '0.1.0'}
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}
