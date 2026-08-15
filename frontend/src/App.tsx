import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { api } from './services/api';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import HistoryPage from './pages/HistoryPage';
import PredictPage from './pages/PredictPage';
import BatchPage from './pages/BatchPage';
import InvestigationsPage from './pages/InvestigationsPage';
import ModelsPage from './pages/ModelsPage';
import MonitoringPage from './pages/MonitoringPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!api.isAuthenticated()) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="predict" element={<PredictPage />} />
          <Route path="batch" element={<BatchPage />} />
          <Route path="investigations" element={<InvestigationsPage />} />
          <Route path="models" element={<ModelsPage />} />
          <Route path="monitoring" element={<MonitoringPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
