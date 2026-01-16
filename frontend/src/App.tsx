import { Component, Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// Error Boundary para capturar erros
class ErrorBoundary extends Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
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
            style={{ padding: '10px 20px', background: '#0c4a6e', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' }}
          >
            Recarregar
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Lazy loading dos componentes
const LoginView = lazy(() => import('./views/Login/LoginView').then(m => ({ default: m.LoginView })));
const DashboardHome = lazy(() => import('./views/Dashboard/DashboardHome').then(m => ({ default: m.DashboardHome })));
const Module1View = lazy(() => import('./views/Dashboard/ModuleViews/Module1View').then(m => ({ default: m.Module1View })));
const Module2View = lazy(() => import('./views/Dashboard/ModuleViews/Module2View').then(m => ({ default: m.Module2View })));
const Module3View = lazy(() => import('./views/Dashboard/ModuleViews/Module3View').then(m => ({ default: m.Module3View })));
const Module4View = lazy(() => import('./views/Dashboard/ModuleViews/Module4View').then(m => ({ default: m.Module4View })));
const Module5View = lazy(() => import('./views/Dashboard/ModuleViews/Module5View').then(m => ({ default: m.Module5View })));
const Module6View = lazy(() => import('./views/Dashboard/ModuleViews/Module6View').then(m => ({ default: m.Module6View })));
const Module7View = lazy(() => import('./views/Dashboard/ModuleViews/Module7View').then(m => ({ default: m.Module7View })));

// Layout principal - import estático pois é usado sempre
import { MainLayout } from './components/layout/MainLayout';

// Loading fallback
function LoadingFallback() {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      fontFamily: 'Arial, sans-serif',
      fontSize: '18px',
      color: '#0c4a6e'
    }}>
      <div>Carregando SaaS Impacto Portuário...</div>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            <Route path="/login" element={<LoginView />} />
            <Route path="/" element={<MainLayout />}>
              <Route index element={<DashboardHome />} />
              <Route path="dashboard/module1" element={<Module1View />} />
              <Route path="dashboard/module2" element={<Module2View />} />
              <Route path="dashboard/module3" element={<Module3View />} />
              <Route path="dashboard/module4" element={<Module4View />} />
              <Route path="dashboard/module5" element={<Module5View />} />
              <Route path="dashboard/module6" element={<Module6View />} />
              <Route path="dashboard/module7" element={<Module7View />} />
            </Route>
            {/* Redirect /dashboard to / */}
            <Route path="/dashboard" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
