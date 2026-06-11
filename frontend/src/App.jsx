import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import AuthCallbackPage from './pages/AuthCallbackPage'
import DashboardPage from './pages/DashboardPage'
import SearchPage from './pages/SearchPage'
import CompanyPage from './pages/CompanyPage'
import ScoreResultPage from './pages/ScoreResultPage'
import ComparePage from './pages/ComparePage'
import AdminPage from './pages/AdminPage'
import ValidationLabPage from './pages/ValidationLabPage'
import DataHealthPage from './pages/DataHealthPage'
import LabelingLabPage from './pages/LabelingLabPage'
import ForecastingPage from './pages/ForecastingPage'
import ForecastingDetailPage from './pages/ForecastingDetailPage'
import ResearchPage from './pages/ResearchPage'
import ResearchAgentPage from './pages/ResearchAgentPage'
import DataQualityPage from './pages/DataQualityPage'
import ExperimentsPage from './pages/ExperimentsPage'
import BenchmarkPage from './pages/BenchmarkPage'
import CompaniesResearchPage from './pages/CompaniesResearchPage'
import CompanyResearchDetailPage from './pages/CompanyResearchDetailPage'
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
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/callback" element={<AuthCallbackPage />} />
      <Route path="/dashboard" element={<Protected><DashboardPage /></Protected>} />
      <Route path="/companies" element={<Protected><SearchPage /></Protected>} />
      <Route path="/search" element={<Navigate to="/companies" replace />} />
      <Route path="/ai-search" element={<Navigate to="/research-agent" replace />} />
      <Route path="/companies/:id" element={<Protected><CompanyPage /></Protected>} />
      <Route path="/score-runs/:id" element={<Protected><ScoreResultPage /></Protected>} />
      <Route path="/compare" element={<Protected><ComparePage /></Protected>} />
      <Route path="/reports" element={<Navigate to="/dashboard" replace />} />
      <Route path="/admin" element={<Protected><AdminPage /></Protected>} />
      <Route path="/validation" element={<Protected><ValidationLabPage /></Protected>} />
      <Route path="/data-health" element={<Protected><DataHealthPage /></Protected>} />
      <Route path="/labeling" element={<Protected><LabelingLabPage /></Protected>} />
      <Route path="/forecasting" element={<Protected><ForecastingPage /></Protected>} />
      <Route path="/forecasting/detail" element={<Protected><ForecastingDetailPage /></Protected>} />
      <Route path="/research" element={<Protected><ResearchPage /></Protected>} />
      <Route path="/research-agent" element={<Protected><ResearchAgentPage /></Protected>} />
      <Route path="/data-quality" element={<Protected><DataQualityPage /></Protected>} />
      <Route path="/experiments" element={<Protected><ExperimentsPage /></Protected>} />
      <Route path="/benchmark" element={<Protected><BenchmarkPage /></Protected>} />
      <Route path="/research/companies" element={<Protected><CompaniesResearchPage /></Protected>} />
      <Route path="/research/companies/:ticker" element={<Protected><CompanyResearchDetailPage /></Protected>} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
