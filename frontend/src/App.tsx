import { Component, ReactNode, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import type { ErrorInfo } from 'react';

import { ProtectedRoute } from './router/ProtectedRoute';
import { APP_ROUTES } from './router/routes';
import type { AppRoute } from './router/routes';

// Error Boundary para capturar erros
class ErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean; error: Error | null }
> {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary capturou:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '40px', fontFamily: 'Arial, sans-serif', backgroundColor: '#fee' }}>
          <h1 style={{ color: '#c00' }}>Erro na Aplicação</h1>
          <pre style={{ backgroundColor: '#fff', padding: '20px', borderRadius: '5px' }}>
            {String(this.state.error)}
          </pre>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '10px 20px',
              background: '#0c4a6e',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
            }}
          >
            Recarregar
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

function LoadingFallback() {
  return (
    <div className="flex h-screen items-center justify-center">
      <div>Carregando SaaS Impacto Portuário...</div>
    </div>
  );
}

function wrapRouteElements(routes: AppRoute[]) {
  return routes.map((route) => {
    const shouldProtect = route.requiresAuth ?? false;
    const routeElement = shouldProtect ? <ProtectedRoute>{route.element}</ProtectedRoute> : route.element;

    return (
      <Route
        key={route.path || 'route'}
        path={route.path ?? ''}
        element={routeElement}
      >
        {route.children ? wrapRouteElements(route.children) : null}
      </Route>
    );
  });
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            {wrapRouteElements(APP_ROUTES)}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
