import { NavLink } from "react-router-dom"
import { useDemoRole } from "@/context/useDemoRole"
import { type DemoRole } from "@/data/demoUsers"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  Search,
  CalendarCheck2,
  Award,
  Camera,
  ClipboardList,
  AlertTriangle,
  FolderKanban,
  CheckSquare,
  Clock,
  FileCheck2,
  Building,
  Users,
  History,
  Scale,
  Sliders,
  ChevronRight,
  ShieldAlert,
  Sparkles,
} from "lucide-react"

interface SidebarProps {
  onNavigate?: () => void
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const { currentRole, currentUser, setRole } = useDemoRole()

  const handleRoleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setRole(e.target.value as DemoRole)
  }

  return (
    <aside className="w-64 flex-shrink-0 bg-white border-r border-slate-200 flex flex-col justify-between h-full select-none">
      {/* Brand & Organization */}
      <div>
        <div className="p-5 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center font-bold text-white shadow-sm shadow-blue-600/20">
              S
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-slate-900 block leading-tight">
                ShareSpace
              </span>
              <span className="text-xs font-semibold text-blue-700 tracking-wide block">
                Apex Institute of Tech
              </span>
            </div>
          </div>
        </div>

        {/* Navigation Sections */}
        <div className="p-3 space-y-6 overflow-y-auto max-h-[calc(100vh-215px)] scrollbar-none">
          {/* Main Shared Navigation */}
          <div>
            <div className="px-3 mb-1.5 text-xs font-bold uppercase tracking-wider text-slate-400">
              Platform Core
            </div>
            <nav className="space-y-0.5">
              <NavLink
                to="/"
                end
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <LayoutDashboard className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>Overview</span>
                  </>
                )}
              </NavLink>

              <NavLink
                to="/resources"
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Search className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>Resource Discovery</span>
                  </>
                )}
              </NavLink>

              <NavLink
                to="/bookings"
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <CalendarCheck2 className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>My Bookings</span>
                  </>
                )}
              </NavLink>
            </nav>
          </div>

          {/* Student Workflows */}
          <div>
            <div className="px-3 mb-1.5 flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-400">
              <span>Student Lifecycle</span>
              {currentRole === "student" && (
                <span className="px-1.5 py-0.5 text-[10px] rounded bg-blue-100 text-blue-800 font-semibold">
                  Active
                </span>
              )}
            </div>
            <nav className="space-y-0.5">
              <NavLink
                to="/qualifications"
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Award className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>Qualifications & Permits</span>
                  </>
                )}
              </NavLink>

              <NavLink
                to="/handover"
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Camera className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>Check-in & Return</span>
                    <span className="ml-auto w-2 h-2 rounded-full bg-amber-500" />
                  </>
                )}
              </NavLink>

              <NavLink
                to="/condition-reports"
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <ClipboardList className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>Condition Reports</span>
                  </>
                )}
              </NavLink>

              <NavLink
                to="/incidents/report"
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <AlertTriangle className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>Report an Incident</span>
                  </>
                )}
              </NavLink>
            </nav>
          </div>

          {/* Manager Workflows */}
          <div>
            <div className="px-3 mb-1.5 flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-400">
              <span>Facility Manager</span>
              {currentRole === "manager" && (
                <span className="px-1.5 py-0.5 text-[10px] rounded bg-emerald-100 text-emerald-800 font-semibold">
                  Active
                </span>
              )}
            </div>
            <nav className="space-y-0.5">
              <NavLink
                to="/manage/resources"
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <FolderKanban className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>Managed Resources</span>
                  </>
                )}
              </NavLink>

              <NavLink
                to="/manage/approvals"
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <CheckSquare className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>Booking Approvals</span>
                    <span className="ml-auto px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
                      3
                    </span>
                  </>
                )}
              </NavLink>

              <NavLink
                to="/manage/availability"
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Clock className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>Availability Windows</span>
                  </>
                )}
              </NavLink>

              <NavLink
                to="/manage/handovers"
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <FileCheck2 className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>Handover Records</span>
                  </>
                )}
              </NavLink>

              <NavLink
                to="/manage/incidents"
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <ShieldAlert className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>Incident Reviews</span>
                  </>
                )}
              </NavLink>
            </nav>
          </div>

          {/* Administrator Workflows */}
          <div>
            <div className="px-3 mb-1.5 flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-400">
              <span>Administration</span>
              {currentRole === "admin" && (
                <span className="px-1.5 py-0.5 text-[10px] rounded bg-purple-100 text-purple-800 font-semibold">
                  Active
                </span>
              )}
            </div>
            <nav className="space-y-0.5">
              <NavLink
                to="/admin/organization"
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Building className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>Organization Setup</span>
                  </>
                )}
              </NavLink>

              <NavLink
                to="/admin/members"
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Users className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>Members & Roles</span>
                  </>
                )}
              </NavLink>

              <NavLink
                to="/admin/audit-logs"
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <History className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>Append-Only Audit Log</span>
                  </>
                )}
              </NavLink>

              <NavLink
                to="/admin/disputes"
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Scale className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>Dispute Arbitration</span>
                  </>
                )}
              </NavLink>

              <NavLink
                to="/admin/fair-use"
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-3 border-blue-600 rounded-l-none pl-2.5"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Sliders className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-500")} />
                    <span>Fair-Use Quotas</span>
                  </>
                )}
              </NavLink>
            </nav>
          </div>
        </div>
      </div>

      {/* Footer Role Switcher */}
      <div className="p-3 border-t border-slate-200 bg-slate-50">
        <div className="p-3 rounded-xl bg-white border border-slate-200 space-y-2 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-amber-500" />
              Demo Persona
            </span>
            <span className="text-[10px] text-blue-700 font-medium">Simulation</span>
          </div>

          <select
            value={currentRole}
            onChange={handleRoleChange}
            className="w-full bg-slate-50 border border-slate-300 text-xs rounded-lg px-2.5 py-1.5 text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600 cursor-pointer"
          >
            <option value="student">Student (Alex Chen)</option>
            <option value="manager">Manager (Dr. Sarah Miller)</option>
            <option value="admin">Administrator (Dean Vance)</option>
          </select>

          <div className="pt-1 flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-blue-100 border border-blue-200 flex items-center justify-center text-xs font-bold text-blue-800">
              {currentUser.avatarInitials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-slate-900 truncate">{currentUser.name}</p>
              <p className="text-[11px] text-slate-500 truncate">{currentUser.roleLabel}</p>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
          </div>
        </div>
      </div>
    </aside>
  )
}
