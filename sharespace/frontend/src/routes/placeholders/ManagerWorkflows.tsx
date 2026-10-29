import { ModulePlaceholder } from "@/components/common/ModulePlaceholder"
import { FolderKanban, CheckSquare, Clock, FileCheck2, ShieldAlert, Check, X } from "lucide-react"
import { Badge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"
import { DEMO_RESOURCES } from "@/data/demoData"

export function ManageResourcesPage() {
  return (
    <ModulePlaceholder
      title="Managed Facility Assets"
      subtitle="Configure laboratory instruments, specify prerequisite qualifications, and manage operating conditions."
      stepNumber={7}
      lifecycleStage="Asset Administration"
      icon={<FolderKanban className="w-6 h-6" />}
      description="Facility managers define equipment specifications, operating hours, hourly maintenance fees, safety prerequisite tags, and whether bookings require manual approval."
      expectedFeatures={[
        "CRUD endpoints for equipment and spaces scoped by organization ID",
        "Configurable approval gates (Instant vs. Manager Review Required)",
        "Equipment retirement and maintenance state toggles",
        "Serial number and calibration logbook tracking",
      ]}
      previewContent={
        <div className="space-y-3">
          {DEMO_RESOURCES.slice(0, 3).map((res) => (
            <div
              key={res.id}
              className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between gap-3 text-xs"
            >
              <div>
                <span className="font-bold text-slate-900 text-sm block">{res.name}</span>
                <span className="text-slate-500">{res.location} • Tag: {res.modelNumber}</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={res.status === "AVAILABLE" ? "success" : "destructive"}>
                  {res.status}
                </Badge>
                <Button size="sm" variant="outline" className="h-8 text-xs bg-white" disabled>
                  Edit Policy
                </Button>
              </div>
            </div>
          ))}
        </div>
      }
    />
  )
}

import { useEffect, useState, useCallback } from "react"
import { useAuth } from "@/context/useAuth"
import { apiClient } from "@/api/client"
import type { BookingResponse } from "@/api/types"

export function ManageApprovalsPage() {
  const auth = useAuth()
  const [pendingBookings, setPendingBookings] = useState<BookingResponse[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [actioningId, setActioningId] = useState<string | null>(null)

  const isManagerOrAdmin =
    auth.activeMembership?.role === "admin" ||
    auth.activeMembership?.role === "lab_manager"

  const fetchPending = useCallback(async () => {
    if (!auth.activeMembership?.organization_id || !isManagerOrAdmin) return
    setIsLoading(true)
    try {
      const data = await apiClient.getOrganizationBookings(auth.activeMembership.organization_id, {
        status: "pending",
      })
      setPendingBookings(data)
    } catch {
      // Ignore in background
    } finally {
      setIsLoading(false)
    }
  }, [auth.activeMembership, isManagerOrAdmin])

  useEffect(() => {
    if (!isManagerOrAdmin) return
    const timer = setTimeout(() => {
      void fetchPending()
    }, 0)
    return () => clearTimeout(timer)
  }, [isManagerOrAdmin, fetchPending])

  const handleDecision = async (bookingId: string, action: "approve" | "reject") => {
    if (!auth.activeMembership?.organization_id) return
    const reason = action === "reject" ? prompt("Enter rejection reason (optional):") || undefined : undefined
    setActioningId(bookingId)
    try {
      await apiClient.reviewBookingDecision(auth.activeMembership.organization_id, bookingId, {
        action,
        reason,
      })
      await fetchPending()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to record decision")
    } finally {
      setActioningId(null)
    }
  }

  return (
    <ModulePlaceholder
      title="Booking Approvals Queue"
      subtitle="Review pending student reservation requests, verify research purpose, and prevent scheduling conflicts."
      stepNumber={5}
      lifecycleStage="Booking Concurrency & Approval"
      icon={<CheckSquare className="w-6 h-6" />}
      description="When a resource requires approval, requests enter this queue. Upon manager approval, transactional locking prevents double-bookings."
      expectedFeatures={[
        "Single-click Approve / Reject with optional explanation on rejection",
        "Real-time conflicting request detection before approval commit",
        "Transactional row lock (SELECT FOR UPDATE) on resource prevents race conditions",
        "Audit trail logged for all approval and rejection decisions",
      ]}
      previewContent={
        <div className="space-y-3">
          {isManagerOrAdmin && pendingBookings.length > 0 ? (
            pendingBookings.map((b) => (
              <div key={b.id} className="p-5 rounded-xl bg-white border border-slate-200 space-y-3 text-xs shadow-xs">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-bold text-slate-900 text-sm">{b.resource_name || "Institutional Asset"}</span>
                    <p className="text-slate-500">
                      Requested by {b.user_full_name || b.user_email || "Campus Member"}
                    </p>
                  </div>
                  <Badge variant="warning">Awaiting Approval</Badge>
                </div>

                <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-700">
                  <span className="text-slate-400 block text-[10px] font-semibold uppercase">Stated Research Purpose:</span>
                  <span className="text-slate-800 font-medium">"{b.purpose || "Research project testing"}"</span>
                </div>

                <div className="flex items-center justify-between text-slate-600 pt-1">
                  <span className="font-medium text-slate-700">
                    Slot: {new Date(b.start_time).toLocaleDateString()} {new Date(b.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {new Date(b.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ({b.total_credits} credits)
                  </span>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDecision(b.id, "reject")}
                      disabled={actioningId === b.id}
                      className="h-8 text-xs gap-1 cursor-pointer"
                    >
                      <X className="w-3.5 h-3.5" /> Reject
                    </Button>
                    <Button
                      size="sm"
                      variant="default"
                      onClick={() => handleDecision(b.id, "approve")}
                      disabled={actioningId === b.id}
                      className="h-8 text-xs gap-1 bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer"
                    >
                      <Check className="w-3.5 h-3.5" /> Approve Reservation
                    </Button>
                  </div>
                </div>
              </div>
            ))
          ) : isManagerOrAdmin && pendingBookings.length === 0 && !isLoading ? (
            <div className="p-6 text-center rounded-xl bg-white border border-slate-200 text-slate-600 text-xs">
              <Check className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
              <span className="font-bold text-slate-900 block text-sm">All Caught Up!</span>
              <span>Zero pending booking requests currently awaiting manager decision.</span>
            </div>
          ) : (
            <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-900 text-sm">Titan Krios G4 Cryo-TEM</span>
                  <p className="text-slate-500">Requested by Maya Lin (Robotics Engineering)</p>
                </div>
                <Badge variant="warning">Sample Demo Request</Badge>
              </div>

              <div className="p-3.5 rounded-lg bg-white border border-slate-200 text-slate-700">
                <span className="text-slate-400 block text-[10px] font-semibold uppercase">Stated Research Purpose:</span>
                <span className="text-slate-800">"Single-particle cryo-EM analysis of recombinant protein complexes."</span>
              </div>

              <div className="flex items-center justify-between text-slate-600 pt-1">
                <span className="font-medium">Time: Tomorrow, 10:00 - 13:00 (3 hrs)</span>
                <span className="text-slate-400 text-[11px] italic">Sign in as Lab Manager to approve live requests</span>
              </div>
            </div>
          )}
        </div>
      }
    />
  )
}


export function ManageAvailabilityPage() {
  return (
    <ModulePlaceholder
      title="Availability Windows & Maintenance Blackouts"
      subtitle="Schedule equipment calibration, service downtime, and institutional operating hours."
      stepNumber={8}
      lifecycleStage="Schedule Availability"
      icon={<Clock className="w-6 h-6" />}
      description="Block off recurring maintenance windows, public holidays, or emergency repairs. The booking engine automatically prevents reservation submissions during maintenance periods."
      expectedFeatures={[
        "Recurring operational schedules (e.g. Mon-Fri 08:00 - 20:00)",
        "One-time maintenance blackout intervals with automatic user notice",
        "Automatic cancellation and waitlist rescheduling on emergency downtime",
        "Facility utilization analytics",
      ]}
      previewContent={
        <div className="space-y-3 text-xs">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
            <div>
              <span className="font-bold text-slate-900 block">Bi-Weekly Laser Optics Alignment</span>
              <span className="text-slate-500">Leica Confocal SP8 • Every 2nd Tuesday 08:00 - 11:00</span>
            </div>
            <Badge variant="info">Active Rule</Badge>
          </div>
        </div>
      }
    />
  )
}

export function ManageHandoversPage() {
  return (
    <ModulePlaceholder
      title="Handover Records & Verification"
      subtitle="Inspect incoming return photographs, cleanliness checklists, and signed custody logs."
      stepNumber={10}
      lifecycleStage="Handover Oversight"
      icon={<FileCheck2 className="w-6 h-6" />}
      description="Facility managers can review physical handover evidence before closing completed transactions, ensuring that equipment is returned in good working condition."
      expectedFeatures={[
        "Manager override for physical check-in and returns",
        "Direct signed URL photo inspection modal",
        "Flagging damage or missing accessories directly into incident review",
        "Custody sign-off history per user and equipment",
      ]}
      previewContent={
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-900">Latest Return: Agilent FTIR Spectrometer</span>
            <Badge variant="success">Handover Verified</Badge>
          </div>
          <p className="text-slate-600">Completed by Alex Chen. Check-in and return photos verified with clean ATR crystal.</p>
        </div>
      }
    />
  )
}

export function ManageIncidentsPage() {
  return (
    <ModulePlaceholder
      title="Incident & Damage Reviews"
      subtitle="Human review board for equipment failures, user negligence disputes, and repair scheduling."
      stepNumber={11}
      lifecycleStage="Incident Arbitration"
      icon={<ShieldAlert className="w-6 h-6" />}
      description="All consequential damage, safety, and penalty decisions require authorized human review. Automated algorithms never levy penalties without manager adjudication."
      expectedFeatures={[
        "Structured incident triage queue with severity ratings",
        "Side-by-side evidence inspection of check-in and return photos",
        "Manager resolution findings form (No Fault / User Warning / Restitution)",
        "Formal appeal pathways for students",
      ]}
      previewContent={
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-900">Incident #INC-2026-004 — Tormach CNC Mill</span>
            <Badge variant="destructive">Under Review</Badge>
          </div>
          <p className="text-slate-700">Tool holder collision reported during aluminum roughing cycle.</p>
          <div className="pt-2 flex items-center justify-between text-slate-500 border-t border-slate-200">
            <span>Reported by: Workshop Tech</span>
            <Button size="sm" variant="secondary" className="h-8 text-xs bg-white" disabled>
              Open Resolution Hearing (Step 11)
            </Button>
          </div>
        </div>
      }
    />
  )
}
