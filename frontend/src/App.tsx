import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuthStore } from './store/authStore';
import { useThemeStore } from './store/themeStore';
import MainLayout from './components/layout/MainLayout';
import ProtectedRoute from './components/shared/ProtectedRoute';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import EmpresasList from './pages/empresas/EmpresasList';
import F29Dashboard from './pages/tributario/F29Dashboard';
import DJDashboard from './pages/tributario/DJDashboard';
import SituacionTributaria from './pages/tributario/SituacionTributaria';
import IADashboard from './pages/ia/IADashboard';

export default function App() {
  const { loadFromStorage } = useAuthStore();
  const { theme } = useThemeStore();

  useEffect(() => {
    loadFromStorage();
    document.documentElement.setAttribute('data-theme', theme);
  }, [loadFromStorage, theme]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Dashboard />} />
          <Route path="/empresas" element={<EmpresasList />} />
          <Route path="/f29" element={<F29Dashboard />} />
          <Route path="/dj" element={<DJDashboard />} />
          <Route path="/situacion-tributaria" element={<SituacionTributaria />} />
          <Route path="/ia" element={<IADashboard />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
