import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { authService } from '../api/auth';
import type { LoginRequest, RegisterRequest, OnboardingCompanyRequest } from '../types/auth';

export function useAuth() {
  const bypassAuth = import.meta.env.VITE_DISABLE_AUTH === 'true';
  const navigate = useNavigate();
  const { user, isAuthenticated, isLoading, setAuth, clearAuth, setLoading } = useAuthStore();

  const login = useCallback(async (credentials: LoginRequest) => {
    setLoading(true);
    try {
      const data = await authService.login(credentials);
      const userData = await authService.getCurrentUser();
      setAuth(userData, data.access_token);
      navigate('/');
    } finally {
      setLoading(false);
    }
  }, [navigate, setAuth, setLoading]);

  const logout = useCallback(async () => {
    if (bypassAuth) {
      clearAuth();
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      navigate('/');
      return;
    }

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

  const registerCompany = useCallback(
    async (data: OnboardingCompanyRequest) => {
      setLoading(true);
      try {
        const registerResponse = await authService.registerCompany(data);
        localStorage.setItem('access_token', registerResponse.access_token);
        localStorage.setItem('refresh_token', registerResponse.refresh_token);

        const user = await authService.getCurrentUser();
        setAuth(user, registerResponse.access_token);
        navigate('/');
      } finally {
        setLoading(false);
      }
    },
    [navigate, setAuth, setLoading],
  );

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    register,
    registerCompany,
  };
}
