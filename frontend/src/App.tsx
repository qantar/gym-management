import { Routes, Route, Navigate } from "react-router-dom"
import { useAuthStore } from "./stores/auth"
import LoginPage from "./pages/LoginPage"
import AppShell from "./components/layout/AppShell"
import DashboardPage from "./pages/DashboardPage"
import MembersPage from "./pages/MembersPage"
import BillingPage from "./pages/BillingPage"
import CRMPage from "./pages/CRMPage"
import AttendancePage from "./pages/AttendancePage"
import InventoryPage from "./pages/InventoryPage"
import StaffPage from "./pages/StaffPage"
import ReportsPage from "./pages/ReportsPage"
import BranchesPage from "./pages/BranchesPage"
import SettingsPage from "./pages/SettingsPage"

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<PrivateRoute><AppShell /></PrivateRoute>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="members" element={<MembersPage />} />
        <Route path="billing" element={<BillingPage />} />
        <Route path="crm" element={<CRMPage />} />
        <Route path="attendance" element={<AttendancePage />} />
        <Route path="inventory" element={<InventoryPage />} />
        <Route path="staff" element={<StaffPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="branches" element={<BranchesPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}
