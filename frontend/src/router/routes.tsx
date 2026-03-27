import { Navigate } from 'react-router-dom';
import { ReactElement } from 'react';
import { lazy } from 'react';

import { MainLayout } from '../components/layout/MainLayout';

const LoginView = lazy(() =>
  import('../views/Login/LoginView').then((m) => ({ default: m.LoginView }))
);
const Module1View = lazy(() =>
  import('../views/Dashboard/ModuleViews/Module1View').then((m) => ({ default: m.Module1View }))
);
const Module2View = lazy(() =>
  import('../views/Dashboard/ModuleViews/Module2View').then((m) => ({ default: m.Module2View }))
);
const Module3View = lazy(() =>
  import('../views/Dashboard/ModuleViews/Module3View').then((m) => ({ default: m.Module3View }))
);
const Module4View = lazy(() =>
  import('../views/Dashboard/ModuleViews/Module4View').then((m) => ({ default: m.Module4View }))
);
const Module5View = lazy(() =>
  import('../views/Dashboard/ModuleViews/Module5View').then((m) => ({ default: m.Module5View }))
);
const Module6View = lazy(() =>
  import('../views/Dashboard/ModuleViews/Module6View').then((m) => ({ default: m.Module6View }))
);
const Module7View = lazy(() =>
  import('../views/Dashboard/ModuleViews/Module7View').then((m) => ({ default: m.Module7View }))
);
const Module8View = lazy(() =>
  import('../views/Dashboard/ModuleViews/Module8View').then((m) => ({ default: m.Module8View }))
);
const Module9View = lazy(() =>
  import('../views/Dashboard/ModuleViews/Module9View').then((m) => ({ default: m.Module9View }))
);
const RegisterView = lazy(() =>
  import('../views/Login/RegisterView').then((m) => ({ default: m.RegisterView }))
);
const AdminDashboard = lazy(() =>
  import('../views/Admin/AdminDashboard').then((m) => ({ default: m.AdminDashboard }))
);

export type AppRoute = {
  path?: string;
  index?: true;
  element: ReactElement;
  requiresAuth?: boolean;
  children?: AppRoute[];
};

export const APP_ROUTES: AppRoute[] = [
  {
    path: '/login',
    element: <LoginView />,
    requiresAuth: false,
  },
  {
    path: '/register',
    element: <RegisterView />,
    requiresAuth: false,
  },
  {
    path: '/',
    element: <MainLayout />,
    requiresAuth: true,
    children: [
      { index: true, element: <Navigate to="/dashboard/module3" replace /> },
      { path: 'dashboard', element: <Navigate to="/dashboard/module3" replace /> },
      { path: 'dashboard/module1', element: <Module1View /> },
      { path: 'dashboard/module2', element: <Module2View /> },
      { path: 'dashboard/module3', element: <Module3View /> },
      { path: 'dashboard/module4', element: <Module4View /> },
      { path: 'dashboard/module5', element: <Module5View /> },
      { path: 'dashboard/module6', element: <Module6View /> },
      { path: 'dashboard/module7', element: <Module7View /> },
      { path: 'dashboard/module8', element: <Module8View /> },
      { path: 'dashboard/module9', element: <Module9View /> },
      { path: 'admin', element: <AdminDashboard /> },
    ],
  },
];
