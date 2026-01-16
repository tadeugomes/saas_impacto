import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { authService } from '../api/auth';
import type { LoginRequest, RegisterRequest } from '../types/auth';

export function useAuth() {
  const navigate = useNavigate();
  const { user, isAuthenticated, isLoading, setAuth, clearAuth, setLoading } = useAuthStore();

  const login = useCallback(async (credentials: LoginRequest) => {
    try {
      setLoading(true);
      const data = await authService.login(credentials);
      // Buscar dados do usuário
      const userData = await authService.getCurrentUser();
      setAuth(userData, data.access_token);
      navigate('/');
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  }, [navigate, setAuth, setLoading]);

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearAuth();
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      navigate('/login');
    }
  }, [navigate, clearAuth]);

  const register = useCallback(async (data: RegisterRequest) => {
    try {
      setLoading(true);
      await authService.register(data);
      // Após registro, fazer login automaticamente
      await login({ email: data.email, password: data.password });
    } catch (error) {
      setLoading(false);
      throw error;
    }
  }, [login, setLoading]);

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    register,
  };
}
