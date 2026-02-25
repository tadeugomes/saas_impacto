import { create } from 'zustand';
import type { User } from '../types/auth';

const bypassAuth = import.meta.env.VITE_DISABLE_AUTH === 'true';

const testUser: User = {
  id: '00000000-0000-0000-0000-000000000001',
  email: 'teste_local@impacto.local',
  name: 'Usuário de Teste',
  nome: 'Usuário de Teste',
  tenant_id: '00000000-0000-0000-0000-000000000001',
  roles: ['admin'],
  ativo: true,
};

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
  setLoading: (loading: boolean) => void;
  checkAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false, // Changed from true to false
  setAuth: (user, token) =>
    set({
      user,
      token,
      isAuthenticated: true,
      isLoading: false,
    }),
  clearAuth: () =>
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    }),
  setLoading: (isLoading) => set({ isLoading }),
  checkAuth: () => {
    if (bypassAuth) {
      set({
        user: testUser,
        token: 'dev-token',
        isAuthenticated: true,
        isLoading: false,
      });
      return;
    }

    const token = localStorage.getItem('access_token');
    if (token) {
      set({
        isAuthenticated: true,
        isLoading: false,
        token,
      });
    } else {
      set({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        token: null,
      });
    }
  },
}));
