import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import SearchPage from './pages/SearchPage'
import CompanyPage from './pages/CompanyPage'
import ScoreResultPage from './pages/ScoreResultPage'
import ComparePage from './pages/ComparePage'
import ReportsPage from './pages/ReportsPage'
import AdminPage from './pages/AdminPage'
import ValidationLabPage from './pages/ValidationLabPage'
import AISearchPage from './pages/AISearchPage'
import DataHealthPage from './pages/DataHealthPage'
import LabelingLabPage from './pages/LabelingLabPage'
import ProtectedRoute from './components/ProtectedRoute'
import AppShell from './components/layout/AppShell'

function Protected({ children }) {
  return (
    <ProtectedRoute>
      <AppShell>{children}</AppShell>
    </ProtectedRoute>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<Protected><DashboardPage /></Protected>} />
      <Route path="/companies" element={<Protected><SearchPage /></Protected>} />
      <Route path="/search" element={<Navigate to="/companies" replace />} />
      <Route path="/ai-search" element={<Protected><AISearchPage /></Protected>} />
      <Route path="/companies/:id" element={<Protected><CompanyPage /></Protected>} />
      <Route path="/score-runs/:id" element={<Protected><ScoreResultPage /></Protected>} />
      <Route path="/compare" element={<Protected><ComparePage /></Protected>} />
      <Route path="/reports" element={<Protected><ReportsPage /></Protected>} />
      <Route path="/admin" element={<Protected><AdminPage /></Protected>} />
      <Route path="/validation" element={<Protected><ValidationLabPage /></Protected>} />
      <Route path="/data-health" element={<Protected><DataHealthPage /></Protected>} />
      <Route path="/labeling" element={<Protected><LabelingLabPage /></Protected>} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
