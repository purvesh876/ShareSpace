import { useState, useEffect } from "react"
import { useLocation } from "react-router-dom"
import { useDemoRole } from "@/context/useDemoRole"
import { useAuth } from "@/context/useAuth"
import { DEMO_USERS, type DemoRole } from "@/data/demoUsers"
import { apiClient } from "@/api/client"
import type { HealthResponse, ReadinessResponse } from "@/api/types"
import {
  Menu,
  Bell,
  Activity,
  ChevronDown,
  CheckCircle2,
  XCircle,
  Database,
  Building2,
  AlertTriangle,
  LogIn,
  LogOut,
  Sparkles,
} from "lucide-react"
import { Dialog } from "@/components/ui/Dialog"
import { AuthModal } from "@/components/common/AuthModal"

interface HeaderProps {
  onToggleMobileMenu: () => void
}

export function Header({ onToggleMobileMenu }: HeaderProps) {
  const location = useLocation()
  const { currentRole, currentUser, setRole } = useDemoRole()
  const auth = useAuth()

  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null)
  const [isHealthDialogOpen, setIsHealthDialogOpen] = useState(false)
  const [isNotifDialogOpen, setIsNotifDialogOpen] = useState(false)
  const [isRoleDropdownOpen, setIsRoleDropdownOpen] = useState(false)
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false)

  // Derive breadcrumb / title from path
  const getPageTitle = (path: string) => {
    switch (path) {
      case "/":
        return "Dashboard Overview"
      case "/resources":
        return "Institutional Resource Discovery"
      case "/bookings":
        return "My Reservations & Timelines"
      case "/qualifications":
        return "Safety Permits & Qualifications"
      case "/handover":
        return "Check-in & Return Handover Gate"
      case "/condition-reports":
        return "Historical Condition Reports"
      case "/incidents/report":
        return "Report Incident or Equipment Defect"
      case "/manage/resources":
        return "Facility Asset Management"
      case "/manage/approvals":
        return "Booking Approval Queue"
      case "/manage/availability":
        return "Blackout Windows & Maintenance"
      case "/manage/handovers":
        return "Handover Evidence Verification"
      case "/manage/incidents":
        return "Incident Review & Resolution"
      case "/admin/organization":
        return "Tenant Organization Settings"
      case "/admin/members":
        return "Community Members & Role Delegation"
      case "/admin/audit-logs":
        return "Append-Only Audit Trail"
      case "/admin/disputes":
        return "Dispute Arbitration Board"
      case "/admin/fair-use":
        return "Fair-Use Quotas & Cooldown Rules"
      default:
        return "ShareSpace Portal"
    }
  }

  const [isProbing, setIsProbing] = useState(false)

  useEffect(() => {
    let isMounted = true
    let activeController: AbortController | null = null
    let isRequestInProgress = false

    const fetchDiagnostics = async () => {
      // Guard against overlapping concurrent requests
      if (isRequestInProgress) return
      isRequestInProgress = true

      activeController = new AbortController()

      try {
        const diag = await apiClient.getDiagnosticStatus(activeController.signal)
        if (!isMounted) return
        setHealth(diag.health)
        setReadiness(diag.readiness)
      } catch (err: unknown) {
        if (!isMounted) return
        const error = err as Error
        if (error.name !== "AbortError") {
          console.warn("Diagnostics error:", error)
          setHealth(null)
          setReadiness({
            status: "unavailable",
            database: "unreachable",
            timestamp: new Date().toISOString(),
            message: "Cannot contact backend service.",
          })
        }
      } finally {
        isRequestInProgress = false
      }
    }

    void fetchDiagnostics()

    // 30-second polling interval with cleanup
    const timer = setInterval(() => {
      void fetchDiagnostics()
    }, 30000)

    return () => {
      isMounted = false
      clearInterval(timer)
      if (activeController) {
        activeController.abort()
      }
    }
  }, [])

  const handleManualReadinessProbe = async () => {
    setIsProbing(true)
    try {
      const liveReadiness = await apiClient.getReadiness()
      setReadiness(liveReadiness)
    } catch (err) {
      console.warn("Manual readiness probe failed:", err)
    } finally {
      setIsProbing(false)
    }
  }

  return (
    <header className="h-16 border-b border-slate-200 bg-white px-4 sm:px-6 lg:px-8 flex items-center justify-between sticky top-0 z-30 select-none shadow-xs">
      {/* Left side: Mobile Toggle & Page Title */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobileMenu}
          className="lg:hidden p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors cursor-pointer"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
            <span className="flex items-center gap-1 text-slate-600">
              <Building2 className="w-3.5 h-3.5 text-blue-600" />
              {auth.activeMembership?.organization_name || "Apex Institute of Tech"}
            </span>
            <span>/</span>
            <span className="text-slate-700 capitalize font-medium">{currentRole} Portal</span>
          </div>
          <h1 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">
            {getPageTitle(location.pathname)}
          </h1>
        </div>
      </div>

      {/* Right side: Session status, Backend Indicators, Notifications, Role Switcher */}
      <div className="flex items-center gap-2.5 sm:gap-3.5">
        {/* Session Status Pill */}
        {auth.authMode === "real" ? (
          <div className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-900 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span className="truncate max-w-[200px]">Supabase: {auth.userEmail}</span>
          </div>
        ) : auth.authMode === "demo" ? (
          <div className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-900 border border-amber-200">
            <Sparkles className="w-3.5 h-3.5 text-amber-600" />
            <span>Demo Simulation (Local Dev)</span>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setIsAuthModalOpen(true)}
            className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-600 text-white hover:bg-blue-700 transition-colors cursor-pointer"
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>Sign In / Connect</span>
          </button>
        )}

        {/* Honest Backend Diagnostic Status */}
        <button
          onClick={() => setIsHealthDialogOpen(true)}
          className="flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-slate-50 border border-slate-200 hover:bg-slate-100 transition-colors cursor-pointer"
          title="Click to view detailed backend & database readiness"
        >
          {/* API Health Indicator */}
          <span className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                health?.status === "ok" ? "bg-emerald-500" : "bg-red-500"
              }`}
            />
            <span className="text-slate-700 font-medium hidden sm:inline">
              {health?.status === "ok" ? "API healthy" : "API offline"}
            </span>
          </span>

          <span className="text-slate-300">|</span>

          {/* Database Readiness Indicator */}
          <span className="text-slate-600 text-[11px] hidden sm:inline">
            {readiness?.status === "ready"
              ? "DB ready"
              : readiness?.database === "not configured"
              ? "DB setup pending"
              : "DB unreachable"}
          </span>
        </button>

        {/* Notification Bell Placeholder */}
        <button
          onClick={() => setIsNotifDialogOpen(true)}
          className="relative p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors cursor-pointer"
          aria-label="View notifications"
        >
          <Bell className="w-4 h-4" />
          {currentUser.pendingActionCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-blue-600 ring-2 ring-white" />
          )}
        </button>

        {/* Persona & Session Management Dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsRoleDropdownOpen((prev) => !prev)}
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-slate-50 border border-slate-200 hover:bg-slate-100 hover:border-slate-300 transition-all text-xs cursor-pointer shadow-xs"
          >
            <div
              className={`w-6 h-6 rounded-md flex items-center justify-center font-bold text-xs ${
                auth.authMode === "real"
                  ? "bg-emerald-100 border border-emerald-200 text-emerald-800"
                  : "bg-blue-100 border border-blue-200 text-blue-800"
              }`}
            >
              {currentUser.avatarInitials}
            </div>
            <div className="text-left hidden sm:block">
              <span className="text-slate-900 font-semibold block leading-tight">{currentUser.name}</span>
              <span className="text-[11px] text-slate-500 block leading-tight">
                {auth.authMode === "real"
                  ? `${auth.activeRole.toUpperCase()} (Supabase)`
                  : currentUser.roleLabel}
              </span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-500 ml-1" />
          </button>

          {isRoleDropdownOpen && (
            <div
              className="absolute right-0 mt-2 w-72 rounded-xl border border-slate-200 bg-white p-2 shadow-lg z-50 animate-in fade-in zoom-in-95"
              onClick={() => setIsRoleDropdownOpen(false)}
            >
              <div className="px-2.5 py-2 border-b border-slate-100 mb-1">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                    Session Mode
                  </span>
                  <span
                    className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                      auth.authMode === "real"
                        ? "bg-emerald-100 text-emerald-800"
                        : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {auth.authMode === "real" ? "Verified Auth" : "Dev Simulation"}
                  </span>
                </div>
                <p className="text-xs font-semibold text-slate-900 mt-1 truncate">
                  {auth.userEmail || currentUser.email}
                </p>
              </div>

              {/* Multi-tenant memberships switcher */}
              {auth.memberships.length > 1 && (
                <div className="p-2 border-b border-slate-100">
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
                    Active Organization
                  </p>
                  <div className="space-y-1">
                    {auth.memberships.map((m) => (
                      <button
                        key={m.membership_id}
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          auth.switchOrganization(m.organization_id)
                        }}
                        className={`w-full text-left px-2 py-1.5 rounded-md text-xs flex items-center justify-between cursor-pointer ${
                          auth.activeOrganizationId === m.organization_id
                            ? "bg-blue-50 text-blue-800 font-semibold"
                            : "text-slate-600 hover:bg-slate-50"
                        }`}
                      >
                        <span className="truncate">{m.organization_name}</span>
                        <span className="text-[10px] capitalize text-slate-400">{m.role}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Demo Persona Switching (Available in Dev mode) */}
              {auth.isDemoMode && (
                <div className="py-1">
                  <p className="px-2.5 text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
                    Switch Persona (Dev Simulation)
                  </p>
                  {(["student", "manager", "admin"] as DemoRole[]).map((role) => {
                    const user = DEMO_USERS[role]
                    const isSelected = currentRole === role
                    return (
                      <button
                        key={role}
                        onClick={() => setRole(role)}
                        className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-left text-xs transition-colors cursor-pointer ${
                          isSelected
                            ? "bg-blue-50 text-blue-800 font-semibold border border-blue-200"
                            : "text-slate-700 hover:bg-slate-100"
                        }`}
                      >
                        <div className="w-5 h-5 rounded-md bg-slate-100 border border-slate-200 flex items-center justify-center font-bold text-[10px] text-slate-700">
                          {user.avatarInitials}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-slate-900 font-medium">{user.name}</p>
                          <p className="truncate text-[10px] text-slate-500">{user.roleLabel}</p>
                        </div>
                        {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />}
                      </button>
                    )
                  })}
                </div>
              )}

              {/* Action Buttons: Sign In or Sign Out */}
              <div className="pt-1 mt-1 border-t border-slate-100">
                {auth.authMode === "real" ? (
                  <button
                    type="button"
                    onClick={() => void auth.signOut()}
                    className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-left text-xs text-red-700 hover:bg-red-50 transition-colors cursor-pointer font-medium"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Sign Out of Supabase</span>
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => setIsAuthModalOpen(true)}
                    className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-left text-xs text-blue-700 hover:bg-blue-50 transition-colors cursor-pointer font-medium"
                  >
                    <LogIn className="w-3.5 h-3.5" />
                    <span>Connect Real Supabase Account</span>
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Backend Diagnostics Modal */}
      <Dialog
        isOpen={isHealthDialogOpen}
        onClose={() => setIsHealthDialogOpen(false)}
        title="FastAPI Service & Database Readiness"
        description={`Base URL: ${apiClient.getBaseUrl()}`}
      >
        <div className="space-y-4 text-sm">
          {/* API Health Card */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-900 flex items-center gap-2 text-xs">
                <Activity className="w-4 h-4 text-blue-600" />
                API Service (/api/v1/health)
              </span>
              {health?.status === "ok" ? (
                <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5" /> API healthy
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs font-bold text-red-700 bg-red-50 px-2.5 py-0.5 rounded-full border border-red-200">
                  <XCircle className="w-3.5 h-3.5" /> API offline
                </span>
              )}
            </div>
            <p className="text-xs text-slate-600 font-mono">
              {health ? `${health.app_name} v${health.version} (${health.environment})` : "Cannot reach backend on port 8000"}
            </p>
          </div>

          {/* Database Readiness Card */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-900 flex items-center gap-2 text-xs">
                <Database className="w-4 h-4 text-slate-600" />
                PostgreSQL Readiness (/api/v1/ready)
              </span>
              {readiness?.status === "ready" ? (
                <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Connected
                </span>
              ) : readiness?.database === "not configured" ? (
                <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-800 bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" /> DB setup pending
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs font-semibold text-red-800 bg-red-50 px-2.5 py-0.5 rounded-full border border-red-200">
                  <XCircle className="w-3.5 h-3.5 text-red-600" /> DB unreachable
                </span>
              )}
            </div>
            <p className="text-xs text-slate-600">
              {readiness?.database === "not configured"
                ? "DATABASE_URL is not set. The backend is intentionally running detached; database setup and Alembic migrations are planned for Step 5."
                : readiness?.database === "unreachable"
                ? (readiness.message || "Configured database instance could not be reached.")
                : "PostgreSQL connection active and operational."}
            </p>

            <div className="pt-2 border-t border-slate-200 flex items-center justify-between">
              <span className="text-[11px] text-slate-500 font-mono">
                {readiness?.timestamp ? `Checked: ${new Date(readiness.timestamp).toLocaleTimeString()}` : "Not checked"}
              </span>
              <button
                type="button"
                onClick={handleManualReadinessProbe}
                disabled={isProbing}
                className="px-2.5 py-1 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-50 cursor-pointer transition-colors shadow-2xs"
              >
                {isProbing ? "Probing /api/v1/ready..." : "Probe /ready Endpoint Now"}
              </button>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-blue-50 border border-blue-200 text-xs text-blue-900 leading-relaxed">
            <strong>Architecture Notice:</strong> The system intentionally runs without database connectivity during foundational steps. The API service reports health independently, and never claims full operational readiness before Step 5.
          </div>
        </div>
      </Dialog>

      {/* Notifications Modal Placeholder */}
      <Dialog
        isOpen={isNotifDialogOpen}
        onClose={() => setIsNotifDialogOpen(false)}
        title="Institutional Notification Center"
        description="Feature Roadmap: Step 11"
      >
        <div className="space-y-4 text-sm">
          <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-2">
            <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 mx-auto">
              <Bell className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-bold text-slate-900">Automated Notifications Engine</h4>
            <p className="text-xs text-slate-500 leading-relaxed max-w-sm mx-auto">
              In Step 11, ShareSpace will dispatch automated email, SMS, and in-app alerts for pending booking approvals, upcoming handover windows, overdue equipment reminders, and reported damage incidents.
            </p>
          </div>

          <div className="text-xs text-slate-500 border-t border-slate-200 pt-3 flex items-center justify-between">
            <span>Status: Foundation Placeholder</span>
            <span className="font-semibold text-blue-700">Scheduled for Step 11</span>
          </div>
        </div>
      </Dialog>

      {/* Supabase Authentication & Demo Persona Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
      />
    </header>
  )
}

