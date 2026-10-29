import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { AuthProvider } from "./context/AuthContext"
import { DemoRoleProvider } from "./context/DemoRoleContext"
import { AppLayout } from "./components/layout/AppLayout"
import { Dashboard } from "./routes/Dashboard"
import { Resources } from "./routes/Resources"
import { ResourceDetail } from "./routes/ResourceDetail"
import { Bookings } from "./routes/Bookings"

// Student workflow placeholders
import {
  QualificationsPage,
  HandoverPage,
  ConditionReportsPage,
  IncidentReportPage,
} from "./routes/placeholders/StudentWorkflows"

// Manager workflow placeholders
import {
  ManageResourcesPage,
  ManageApprovalsPage,
  ManageAvailabilityPage,
  ManageHandoversPage,
  ManageIncidentsPage,
} from "./routes/placeholders/ManagerWorkflows"

// Admin workflow placeholders
import {
  AdminOrganizationPage,
  AdminMembersPage,
  AdminAuditLogsPage,
  AdminDisputesPage,
  AdminFairUsePage,
} from "./routes/placeholders/AdminWorkflows"

export default function App() {
  return (
    <AuthProvider>
      <DemoRoleProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<AppLayout />}>
              {/* Core Platform Shared Routes */}
              <Route index element={<Dashboard />} />
              <Route path="resources" element={<Resources />} />
              <Route path="resources/:id" element={<ResourceDetail />} />
              <Route path="bookings" element={<Bookings />} />

              {/* Student Lifecycle Routes */}
              <Route path="qualifications" element={<QualificationsPage />} />
              <Route path="handover" element={<HandoverPage />} />
              <Route path="condition-reports" element={<ConditionReportsPage />} />
              <Route path="incidents/report" element={<IncidentReportPage />} />

              {/* Facility Manager Lifecycle Routes */}
              <Route path="manage/resources" element={<ManageResourcesPage />} />
              <Route path="manage/approvals" element={<ManageApprovalsPage />} />
              <Route path="manage/availability" element={<ManageAvailabilityPage />} />
              <Route path="manage/handovers" element={<ManageHandoversPage />} />
              <Route path="manage/incidents" element={<ManageIncidentsPage />} />

              {/* Administrator Governance Routes */}
              <Route path="admin/organization" element={<AdminOrganizationPage />} />
              <Route path="admin/members" element={<AdminMembersPage />} />
              <Route path="admin/audit-logs" element={<AdminAuditLogsPage />} />
              <Route path="admin/disputes" element={<AdminDisputesPage />} />
              <Route path="admin/fair-use" element={<AdminFairUsePage />} />

              {/* Catch-all redirect */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </DemoRoleProvider>
    </AuthProvider>
  )
}

