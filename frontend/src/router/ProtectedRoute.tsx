import { ReactNode, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import { useAuthStore } from '../store/authStore';

interface ProtectedRouteProps {
  children: ReactNode;
}

function LoadingFallback() {
  return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="text-lg text-primary font-semibold">
          Carregando SaaS Impacto Portuário...
        </div>
      </div>
    </div>
  );
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const skipAuth = import.meta.env.VITE_DISABLE_AUTH === 'true';
  const location = useLocation();
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();

  if (skipAuth) {
    return <>{children}</>;
  }

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      checkAuth();
    }
  }, [isLoading, isAuthenticated, checkAuth]);

  if (isLoading) {
    return <LoadingFallback />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <>{children}</>;
}
