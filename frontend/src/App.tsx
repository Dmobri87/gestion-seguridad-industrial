import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuthStore } from './stores/authStore';

const MainLayout          = React.lazy(() => import('./layouts/MainLayout'));
const LoginPage           = React.lazy(() => import('./pages/auth/LoginPage'));
const DashboardPage       = React.lazy(() => import('./pages/dashboard/DashboardPage'));
const PlanningListPage    = React.lazy(() => import('./pages/planning/PlanningListPage'));
const PlanningDetailPage  = React.lazy(() => import('./pages/planning/PlanningDetailPage'));
const ExecutionPage       = React.lazy(() => import('./pages/execution/ExecutionPage'));
const EmergenciesPage     = React.lazy(() => import('./pages/emergencies/EmergenciesPage'));
const EquipmentPage       = React.lazy(() => import('./pages/equipment/EquipmentPage'));
const CertificationsPage  = React.lazy(() => import('./pages/certifications/CertificationsPage'));
const ActivitiesPage      = React.lazy(() => import('./pages/activities/ActivitiesPage'));
const UsersPerformancePage = React.lazy(() => import('./pages/users/UsersPerformancePage'));
const AdminPage           = React.lazy(() => import('./pages/admin/AdminPage'));
const ProfilePage         = React.lazy(() => import('./pages/profile/ProfilePage'));
const ReportsPage         = React.lazy(() => import('./pages/reports/ReportsPage'));
const NotificationsPage   = React.lazy(() => import('./pages/notifications/NotificationsPage'));

const PageLoader = () => (
  <div style={{
    display: 'flex', justifyContent: 'center', alignItems: 'center',
    height: '100vh', background: '#f0f2f5',
  }}>
    <Spin size="large" tip="Cargando..." />
  </div>
);

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, token, logout } = useAuthStore((state) => ({
    isAuthenticated: state.isAuthenticated,
    token: state.token,
    logout: state.logout,
  }));
  const storedToken = localStorage.getItem('access_token');
  const isReallyAuthenticated = Boolean(isAuthenticated && token && storedToken && token === storedToken);

  React.useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'access_token' && !e.newValue) void logout();
      if (e.key === 'auth-storage' && !e.newValue) void logout();
    };
    const handlePopState = () => {
      if (!localStorage.getItem('access_token')) void logout();
    };
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('popstate', handlePopState);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('popstate', handlePopState);
    };
  }, [logout]);

  if (!isReallyAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard"          element={<DashboardPage />} />
            <Route path="catalogo"           element={<ActivitiesPage />} />
            <Route path="planificacion"      element={<PlanningListPage />} />
            <Route path="planificacion/:planId" element={<PlanningDetailPage />} />
            <Route path="planning" element={<Navigate to="/planificacion" replace />} />
            <Route path="planning/:planId" element={<PlanningDetailPage />} />
            <Route path="ejecucion"          element={<ExecutionPage />} />
            <Route path="emergencias"        element={<EmergenciesPage />} />
            <Route path="equipos"            element={<EquipmentPage />} />
            <Route path="certificaciones"    element={<CertificationsPage />} />
            <Route path="reportes"           element={<ReportsPage />} />
            <Route path="notificaciones"     element={<NotificationsPage />} />
            <Route path="desempeno"          element={<UsersPerformancePage />} />
            <Route path="administracion"     element={<AdminPage />} />
            <Route path="perfil"             element={<ProfilePage />} />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
