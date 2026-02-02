import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import MainLayout from './layouts/MainLayout';
import LoginPage from './pages/auth/LoginPage';
import DashboardPage from './pages/dashboard/DashboardPage';
import PlanningListPage from './pages/planning/PlanningListPage';
import PlanningDetailPage from './pages/planning/PlanningDetailPage';
import ExecutionPage from './pages/execution/ExecutionPage';
import EmergenciesPage from './pages/emergencies/EmergenciesPage';
import EquipmentPage from './pages/equipment/EquipmentPage';
import CertificationsPage from './pages/certifications/CertificationsPage';
import ActivitiesPage from './pages/activities/ActivitiesPage';
import UsersPerformancePage from './pages/users/UsersPerformancePage';
import AdminPage from './pages/admin/AdminPage';
import ProfilePage from './pages/profile/ProfilePage';

// Componente para rutas protegidas
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Ruta pública */}
        <Route path="/login" element={<LoginPage />} />

        {/* Rutas protegidas */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="planning" element={<PlanningListPage />} />
          <Route path="planning/:planId" element={<PlanningDetailPage />} />
          <Route path="execution" element={<ExecutionPage />} />
          <Route path="emergencies" element={<EmergenciesPage />} />
          <Route path="equipment" element={<EquipmentPage />} />
          <Route path="certifications" element={<CertificationsPage />} />
          <Route path="activities" element={<ActivitiesPage />} />
          <Route path="users/performance" element={<UsersPerformancePage />} />
          <Route path="admin" element={<AdminPage />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>

        {/* Ruta por defecto */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
