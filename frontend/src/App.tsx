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
import POSPage from "./pages/POSPage"
import MarketingPage from "./pages/MarketingPage"
import SchedulingPage from "./pages/SchedulingPage"
import PayrollPage from "./pages/PayrollPage"
import AuditPage from "./pages/AuditPage"
import MemberDetailPage from "./pages/MemberDetailPage"
import KioskPage from "./pages/KioskPage"
import ShiftsPage from "./pages/ShiftsPage"

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
        <Route path="pos" element={<POSPage />} />
        <Route path="marketing" element={<MarketingPage />} />
        <Route path="scheduling" element={<SchedulingPage />} />
        <Route path="payroll" element={<PayrollPage />} />
        <Route path="audit" element={<AuditPage />} />
        <Route path="members/:id" element={<MemberDetailPage />} />
        <Route path="kiosk" element={<KioskPage />} />
        <Route path="shifts" element={<ShiftsPage />} />
      </Route>
    </Routes>
  )
}
