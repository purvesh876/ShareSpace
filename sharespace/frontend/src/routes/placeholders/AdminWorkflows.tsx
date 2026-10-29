import { useState, useEffect } from "react"
import { useAuth } from "@/context/useAuth"
import { apiClient } from "@/api/client"
import type { AuditEventResponse } from "@/api/types"
import { ModulePlaceholder } from "@/components/common/ModulePlaceholder"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card"
import { Building, Users, History, Scale, Sliders } from "lucide-react"
import { Badge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"

export function AdminOrganizationPage() {
  return (
    <ModulePlaceholder
      title="Tenant Organization Settings"
      subtitle="Multi-tenant isolation, institutional domain configuration, and campus policies."
      stepNumber={6}
      lifecycleStage="Multi-Tenant Isolation"
      icon={<Building className="w-6 h-6" />}
      description="ShareSpace enforces strict tenant isolation. All tables reference org_id and queries filter by tenant context, preventing colleges or departments from accessing cross-institutional data."
      expectedFeatures={[
        "Organization metadata and slug management",
        "Configurable tenant operating guidelines and contact officers",
        "Row-Level Security (RLS) enforcement at PostgreSQL layer",
        "Institutional domain white-listing for automated membership onboarding",
      ]}
      previewContent={
        <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-3 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-900 text-sm">Apex Institute of Technology</span>
            <Badge variant="success">Tenant Isolated</Badge>
          </div>
          <div className="grid grid-cols-2 gap-3 text-slate-700">
            <div>
              <span className="text-slate-400 block text-[10px] font-semibold uppercase">Tenant UUID:</span>
              <span className="font-mono text-xs text-slate-900 font-medium">org_a1b2c3d4-e5f6-7890</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] font-semibold uppercase">Active Members:</span>
              <span className="font-semibold text-slate-900">1,240 Registered</span>
            </div>
          </div>
        </div>
      }
    />
  )
}

export function AdminMembersPage() {
  return (
    <ModulePlaceholder
      title="Membership & Role Administration"
      subtitle="Manage institutional access, grant facility manager permissions, and assign safety qualifications."
      stepNumber={6}
      lifecycleStage="Role-Based Access Control"
      icon={<Users className="w-6 h-6" />}
      description="Role management is strictly enforced by FastAPI and PostgreSQL. Frontend role switching is only a preview mechanism; actual API privileges require verified database records."
      expectedFeatures={[
        "Role assignment (Student / Researcher, Facility Manager, System Administrator)",
        "Safety permit qualification grant and revocation",
        "User suspension for persistent fair-use or incident violations",
        "Tenant-scoped user directory and activity logs",
      ]}
      previewContent={
        <div className="space-y-2 text-xs">
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
            <div>
              <span className="text-slate-900 font-bold block">Dr. Sarah Miller</span>
              <span className="text-slate-500">Microscopy & Fabrication Suites</span>
            </div>
            <Badge variant="default">Manager Role</Badge>
          </div>
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
            <div>
              <span className="text-slate-900 font-bold block">Alex Chen</span>
              <span className="text-slate-500">Dept. of Biomedical Engineering</span>
            </div>
            <Badge variant="secondary">Student Role</Badge>
          </div>
        </div>
      }
    />
  )
}

export function AdminAuditLogsPage() {
  const auth = useAuth()
  const [events, setEvents] = useState<AuditEventResponse[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isLive = auth.isAuthenticated && !!auth.activeMembership

  useEffect(() => {
    async function loadAudit() {
      if (!auth.activeMembership?.organization_id) return
      setIsLoading(true)
      setError(null)
      try {
        const data = await apiClient.getOrganizationAuditEvents(auth.activeMembership.organization_id)
        setEvents(data)
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load audit events")
      } finally {
        setIsLoading(false)
      }
    }
    if (isLive) {
      loadAudit()
    }
  }, [isLive, auth.activeMembership?.organization_id])

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Append-Only Institutional Audit Trail
            </h2>
            {isLive ? (
              <Badge variant="success">LIVE AUDIT LOG</Badge>
            ) : (
              <Badge variant="secondary">DEMO MODE</Badge>
            )}
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Immutable historical records of every booking change, access override, and state transition.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-800">
          {error}
        </div>
      )}

      <Card>
        <CardHeader className="pb-3 border-b border-slate-100">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-bold text-slate-900">Recorded Compliance Events</CardTitle>
            <span className="text-xs text-slate-500">{events.length} Events</span>
          </div>
          <CardDescription className="text-xs text-slate-500">
            Audit records are append-only. Rows cannot be updated or deleted by normal users or API callers.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-5">
          {isLoading ? (
            <div className="h-40 bg-slate-50 rounded-xl animate-pulse" />
          ) : events.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-500 space-y-1">
              <History className="w-8 h-8 text-slate-400 mx-auto" />
              <p className="font-semibold text-slate-700">No Audit Events Logged Yet</p>
              <p className="text-[11px] text-slate-400">
                Any future booking creations, cancellations, check-ins, or manager approvals will be permanently archived here.
              </p>
            </div>
          ) : (
            <div className="space-y-2.5 font-mono text-xs">
              {events.map((ev) => (
                <div key={ev.id} className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-800 space-y-1">
                  <div className="flex items-center justify-between text-slate-500 text-[11px]">
                    <span className="text-blue-700 font-bold">[{ev.action}]</span>
                    <span>{new Date(ev.timestamp).toUTCString()}</span>
                  </div>
                  <div className="text-[11px] text-slate-700 flex flex-wrap gap-2">
                    <span>Actor: {ev.user_email || ev.user_id?.slice(0, 8) || "System"}</span>
                    <span>•</span>
                    <span>Entity: {ev.entity_type} ({ev.entity_id ? ev.entity_id.slice(0, 8) : "N/A"})</span>
                  </div>
                  {ev.payload_after && (
                    <div className="text-[10px] bg-white p-2 rounded border border-slate-200 text-slate-600 truncate">
                      Payload: {JSON.stringify(ev.payload_after)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export function AdminDisputesPage() {
  return (
    <ModulePlaceholder
      title="Dispute Arbitration & Penalty Reviews"
      subtitle="Final human adjudication for disputed equipment damage, overdue penalties, and appeals."
      stepNumber={11}
      lifecycleStage="Governance & Arbitration"
      icon={<Scale className="w-6 h-6" />}
      description="In compliance with safety and legal standards, automated systems never levy consequential monetary penalties or permanent academic bans. All disputes are reviewed by campus administrators."
      expectedFeatures={[
        "Side-by-side photographic evidence comparison",
        "Formal written findings and restitution determination",
        "Two-stage appeal workflows for students",
        "Suspension management with defined probationary restoration dates",
      ]}
      previewContent={
        <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-3 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-900 text-sm">Dispute #DISP-2026-001 — CNC Spindle Collision</span>
            <Badge variant="warning">Arbitration Hearing Pending</Badge>
          </div>
          <p className="text-slate-700">
            Student claims pre-existing collet runout contributed to tool failure; workshop manager requests replacement cost.
          </p>
          <div className="pt-2 flex items-center justify-between text-slate-500 border-t border-slate-200">
            <span>Evidence: 4 Handover Photos Attached</span>
            <Button size="sm" variant="outline" className="h-8 text-xs bg-white" disabled>
              Open Formal Hearing (Step 11)
            </Button>
          </div>
        </div>
      }
    />
  )
}

export function AdminFairUsePage() {
  return (
    <ModulePlaceholder
      title="Fair-Use Quotas & Anti-Monopolization Policy"
      subtitle="Configure transparent limits to prevent high-demand equipment from being hoarded."
      stepNumber={9}
      lifecycleStage="Fair Allocation Engine"
      icon={<Sliders className="w-6 h-6" />}
      description="Configure weekly maximum reservation hours per student, mandatory cooldown intervals between high-demand bookings, and automated waitlist reallocation."
      expectedFeatures={[
        "Weekly quota enforcement per equipment category (e.g. max 12 hrs/week)",
        "Mandatory 24-hour cooldown after peak usage periods",
        "Anti-hoarding limits on concurrent active reservations (max 2 per student)",
        "Automated waitlist notification with 2-hour exclusive claim window upon cancellation",
      ]}
      previewContent={
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-slate-500">Undergraduate Weekly Max:</span>
            <p className="font-bold text-slate-900 text-sm">16 Hours / Week</p>
            <span className="text-xs text-emerald-700 font-medium">Reset Every Monday 00:00 UTC</span>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-slate-500">Peak Resource Cooldown:</span>
            <p className="font-bold text-slate-900 text-sm">18 Hours Mandatory</p>
            <span className="text-xs text-amber-700 font-medium">Applies to Electron Microscopes & 3D Printers</span>
          </div>
        </div>
      }
    />
  )
}
