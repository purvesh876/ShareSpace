import { useEffect, useState, useMemo } from "react"
import { useParams, Link, useNavigate } from "react-router-dom"
import { useAuth } from "@/context/useAuth"
import { apiClient, ApiClientError } from "@/api/client"
import type { ResourceResponse } from "@/api/types"
import { DEMO_RESOURCES } from "@/data/demoData"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import {
  ArrowLeft,
  Calendar,
  MapPin,
  Clock,
  Camera,
  CheckCircle2,
  FileCheck2,
  Sliders,
  AlertCircle,
  Sparkles,
  ShieldAlert,
} from "lucide-react"
import { AuthModal } from "@/components/common/AuthModal"

function getTomorrowDateString(): string {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().split("T")[0]
}

function getTodayDateString(): string {
  return new Date().toISOString().split("T")[0]
}

export function ResourceDetail() {
  const { id } = useParams<{ id: string }>()
  const auth = useAuth()
  const navigate = useNavigate()

  const [liveResource, setLiveResource] = useState<ResourceResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false)

  // Booking Form State
  const [bookingDate, setBookingDate] = useState(getTomorrowDateString)
  const minDate = useMemo(() => getTodayDateString(), [])
  const [startTime, setStartTime] = useState("10:00")
  const [endTime, setEndTime] = useState("12:00")
  const [purpose, setPurpose] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [bookingSuccess, setBookingSuccess] = useState<string | null>(null)
  const [bookingError, setBookingError] = useState<string | null>(null)
  const [eligibilityRejection, setEligibilityRejection] = useState<{
    detail: string
    isQualification: boolean
    isPermit: boolean
  } | null>(null)

  const isLiveOrg = auth.isAuthenticated && !!auth.activeMembership

  useEffect(() => {
    async function loadResource() {
      if (!id) return

      if (auth.activeMembership?.organization_id) {
        setIsLoading(true)
        setError(null)
        try {
          const data = await apiClient.getResource(auth.activeMembership.organization_id, id)
          setLiveResource(data)
        } catch (err: unknown) {
          if (err instanceof ApiClientError && err.status === 404) {
            setLiveResource(null)
            if (!auth.isDemoMode) {
              setError("Resource was not found in your active institutional catalog.")
            }
          } else {
            setError(err instanceof Error ? err.message : "Failed to load resource")
          }
        } finally {
          setIsLoading(false)
        }
        return
      }

      // In demo mode without live org
      if (auth.isDemoMode) {
        const found = DEMO_RESOURCES.find((r) => r.id === id)
        if (!found) {
          setError("Demo resource not found.")
        }
      }
    }
    void loadResource()
  }, [id, auth.activeMembership?.organization_id, auth.isDemoMode])

  // Only use demo fallback if in explicit demo mode
  const demoFallback = auth.isDemoMode ? (DEMO_RESOURCES.find((r) => r.id === id) || DEMO_RESOURCES[0]) : null

  const resourceName = liveResource ? liveResource.name : demoFallback?.name || "Institutional Asset"
  const resourceCategory = liveResource ? liveResource.category : demoFallback?.category || "Equipment"
  const resourceLocation = liveResource ? liveResource.location : demoFallback ? `${demoFallback.location}, ${demoFallback.building}` : "Facility Campus"
  const resourceDesc = liveResource ? liveResource.description : demoFallback?.description || ""
  const isAvailable = liveResource ? liveResource.is_available : demoFallback ? demoFallback.status === "AVAILABLE" : true
  const requiresApproval = liveResource ? liveResource.requires_approval : demoFallback?.requiresApproval || false
  const requiresPermit = liveResource ? Boolean(liveResource.requires_permit) : false
  const requiresQualification = liveResource ? Boolean(liveResource.requires_qualification) : false
  const hourlyRateCredits = liveResource ? liveResource.hourly_rate_credits : demoFallback ? 25 : 0

  // Calculate reservation duration and total credits
  const calculateCost = () => {
    const [startH, startM] = startTime.split(":").map(Number)
    const [endH, endM] = endTime.split(":").map(Number)
    const startMins = startH * 60 + startM
    const endMins = endH * 60 + endM
    const diffHours = Math.max(0, (endMins - startMins) / 60)
    return {
      hours: diffHours,
      totalCredits: Math.round(diffHours * hourlyRateCredits),
    }
  }

  const { hours, totalCredits } = calculateCost()

  const handleBookingSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!auth.activeMembership?.organization_id || !id) {
      setBookingError("Please sign in to an active institutional organization to book equipment.")
      return
    }

    if (hours <= 0) {
      setBookingError("End time must be strictly after start time.")
      return
    }

    setIsSubmitting(true)
    setBookingError(null)
    setBookingSuccess(null)
    setEligibilityRejection(null)

    const startIso = new Date(`${bookingDate}T${startTime}:00Z`).toISOString()
    const endIso = new Date(`${bookingDate}T${endTime}:00Z`).toISOString()

    try {
      const booking = await apiClient.createBooking(auth.activeMembership.organization_id, {
        resource_id: id,
        start_time: startIso,
        end_time: endIso,
        purpose: purpose.trim() || undefined,
      })

      const statusMsg =
        booking.status === "approved"
          ? "Reservation Confirmed! Slot successfully locked."
          : "Reservation Submitted for Review (Pending Facility Manager Approval)."

      setBookingSuccess(statusMsg)
    } catch (err: unknown) {
      if (err instanceof ApiClientError && err.status === 409) {
        setBookingError("Scheduling Conflict: This resource is already reserved during that time window. Please select another slot.")
      } else if (err instanceof ApiClientError && err.status === 403) {
        const msg = err.message || "Access denied: Missing safety or qualification prerequisite."
        const isQual = msg.toLowerCase().includes("qualification") || msg.toLowerCase().includes("training")
        const isPerm = msg.toLowerCase().includes("permit") || msg.toLowerCase().includes("safety")
        if (isQual || isPerm) {
          setEligibilityRejection({
            detail: msg,
            isQualification: isQual,
            isPermit: isPerm,
          })
        }
        setBookingError(msg)
      } else if (err instanceof ApiClientError) {
        setBookingError(err.message || "Failed to reserve resource.")
      } else {
        setBookingError("An unexpected error occurred while booking.")
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Back button */}
      <div>
        <Link to="/resources">
          <Button variant="ghost" size="sm" className="gap-2 text-xs text-slate-600 hover:text-slate-900 cursor-pointer">
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Discovery Catalog</span>
          </Button>
        </Link>
      </div>

      {isLoading && (
        <div className="h-40 bg-slate-100 rounded-2xl animate-pulse border border-slate-200" />
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-800">
          {error}
        </div>
      )}

      {/* Main Asset Header Card */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Badge variant="info">
              {resourceCategory.replace(/_/g, " ").toUpperCase()}
            </Badge>
            <Badge variant={isAvailable ? "success" : "destructive"}>
              {isAvailable ? "AVAILABLE" : "MAINTENANCE"}
            </Badge>
            {requiresApproval && (
              <Badge variant="warning">Requires Manager Approval</Badge>
            )}
            {requiresPermit && (
              <Badge variant="destructive">Safety Permit Required</Badge>
            )}
            {requiresQualification && (
              <Badge variant="warning">Certified Qualification Required</Badge>
            )}
            {liveResource ? (
              <Badge variant="success">LIVE ASSET</Badge>
            ) : auth.isDemoMode ? (
              <Badge variant="secondary">DEMO RECORD</Badge>
            ) : null}
          </div>
          <span className="font-mono text-xs text-slate-500 font-medium">Asset ID: {id?.slice(0, 8)}...</span>
        </div>

        <div>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            {resourceName}
          </h2>
          <p className="text-sm text-slate-600 leading-relaxed max-w-3xl mt-2">
            {resourceDesc}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-3 border-t border-slate-100 text-xs">
          <div className="flex items-center gap-2 text-slate-700">
            <MapPin className="w-4 h-4 text-blue-600" />
            <div>
              <span className="block text-slate-400 text-[10px] font-semibold uppercase">Campus Location</span>
              <span className="font-semibold">{resourceLocation}</span>
            </div>
          </div>

          <div className="flex items-center gap-2 text-slate-700">
            <Sliders className="w-4 h-4 text-amber-600" />
            <div>
              <span className="block text-slate-400 text-[10px] font-semibold uppercase">Usage Rate</span>
              <span className="font-semibold">{hourlyRateCredits} credits / hr</span>
            </div>
          </div>

          <div className="flex items-center gap-2 text-slate-700">
            <Clock className="w-4 h-4 text-emerald-600" />
            <div>
              <span className="block text-slate-400 text-[10px] font-semibold uppercase">Reservation Type</span>
              <span className="font-semibold">{requiresApproval ? "Approval Review" : "Instant Lock"}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Two Column Layout: Specs & Real Booking Form */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Handover Rules & Eligibility */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Camera className="w-5 h-5 text-blue-600" />
                Institutional Handover & Operational Guidelines
              </CardTitle>
              <CardDescription>
                To maintain research instrument integrity, this asset enforces check-in and return verification protocols.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <span className="text-xs font-bold text-blue-900 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-blue-600" /> Check-in Verification
                  </span>
                  <ul className="text-xs text-slate-700 space-y-1.5 list-disc list-inside">
                    <li>Arrival condition inspection of stages and optics</li>
                    <li>Power-on checklist and cleanroom attire verification</li>
                    <li>Calibration benchmark log recorded</li>
                  </ul>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <span className="text-xs font-bold text-emerald-900 flex items-center gap-1.5">
                    <FileCheck2 className="w-4 h-4 text-emerald-600" /> Return Verification
                  </span>
                  <ul className="text-xs text-slate-700 space-y-1.5 list-disc list-inside">
                    <li>Post-run clean-down and specimen removal</li>
                    <li>Laser shutter and vacuum stage interlock check</li>
                    <li>Incident or irregularity logging</li>
                  </ul>
                </div>
              </div>

              {liveResource?.specifications_json && Object.keys(liveResource.specifications_json).length > 0 && (
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
                  <span className="font-bold text-slate-900 block">Instrument Technical Specifications:</span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-700">
                    {Object.entries(liveResource.specifications_json).map(([k, v]) => (
                      <div key={k} className="flex justify-between border-b border-slate-200/60 pb-1">
                        <span className="font-medium text-slate-500 capitalize">{k.replace(/_/g, " ")}:</span>
                        <span className="font-semibold text-slate-900">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Col: Real Interactive Booking Form */}
        <div>
          <Card className="shadow-xs border-slate-200">
            <CardHeader>
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-blue-600" />
                Reserve Asset
              </CardTitle>
              <CardDescription>
                Transactional row locking prevents double-booking conflicts.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {bookingSuccess && (
                <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 space-y-2 animate-in fade-in">
                  <div className="flex items-center gap-1.5 font-semibold">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>{bookingSuccess}</span>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => navigate("/bookings")}
                    className="w-full text-xs bg-white text-emerald-800 border-emerald-300 hover:bg-emerald-100/50"
                  >
                    View in My Reservations
                  </Button>
                </div>
              )}

              {eligibilityRejection ? (
                <div className="p-4 rounded-xl bg-amber-50 border-2 border-amber-400 text-xs text-amber-950 space-y-2.5 animate-in fade-in shadow-xs">
                  <div className="flex items-start gap-2.5">
                    <ShieldAlert className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      <h4 className="font-bold text-amber-900 text-xs sm:text-sm">
                        {eligibilityRejection.isQualification
                          ? "Equipment Qualification Prerequisite Enforced"
                          : "Institutional Safety Permit Required"}
                      </h4>
                      <p className="text-amber-800 text-[11px] leading-relaxed">
                        {eligibilityRejection.detail}
                      </p>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-amber-200/80 text-[11px] space-y-1.5 text-slate-700">
                    <span className="font-semibold block text-slate-900">Why was this reservation rejected?</span>
                    <p className="text-slate-600 leading-snug">
                      Your institutional account is verified and active, but institutional safety policy strictly requires documented
                      {eligibilityRejection.isQualification ? " certified equipment qualification" : ""}
                      {eligibilityRejection.isQualification && eligibilityRejection.isPermit ? " and" : ""}
                      {eligibilityRejection.isPermit ? " an active safety permit" : ""} before operating this high-hazard instrument.
                    </p>
                    <div className="pt-2 flex flex-wrap items-center gap-2">
                      <Link to="/resources">
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs bg-white text-slate-800 border-amber-300 hover:bg-amber-100/50 cursor-pointer"
                        >
                          Explore Open Equipment (e.g. DGX H100)
                        </Button>
                      </Link>
                      <span className="text-[10px] text-slate-500">
                        Contact your facility manager to record training credentials.
                      </span>
                    </div>
                  </div>
                </div>
              ) : bookingError ? (
                <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-xs text-red-900 flex items-start gap-2 animate-in fade-in">
                  <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
                  <span>{bookingError}</span>
                </div>
              ) : null}

              {(requiresPermit || requiresQualification) && (
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-[11px] text-amber-900 flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                  <span>
                    <strong>Eligibility Prerequisite:</strong> This high-hazard asset requires an active institutional safety permit
                    {requiresQualification ? " and certified training qualification" : ""}. Unqualified booking requests will be rejected by server authorization.
                  </span>
                </div>
              )}

              <form onSubmit={handleBookingSubmit} className="space-y-3.5 text-xs">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Reservation Date *</label>
                  <Input
                    type="date"
                    required
                    min={minDate}
                    value={bookingDate}
                    onChange={(e) => setBookingDate(e.target.value)}
                  />
                </div>

                <div className="grid grid-cols-2 gap-2.5">
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">Start Time (UTC) *</label>
                    <select
                      value={startTime}
                      onChange={(e) => setStartTime(e.target.value)}
                      className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800"
                    >
                      {Array.from({ length: 14 }, (_, i) => i + 8).map((hour) => {
                        const val = `${hour.toString().padStart(2, "0")}:00`
                        return <option key={val} value={val}>{val}</option>
                      })}
                    </select>
                  </div>
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">End Time (UTC) *</label>
                    <select
                      value={endTime}
                      onChange={(e) => setEndTime(e.target.value)}
                      className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800"
                    >
                      {Array.from({ length: 14 }, (_, i) => i + 9).map((hour) => {
                        const val = `${hour.toString().padStart(2, "0")}:00`
                        return <option key={val} value={val}>{val}</option>
                      })}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Research Purpose / Project Tag</label>
                  <Input
                    placeholder="e.g. Nanowire conductivity characterization"
                    value={purpose}
                    onChange={(e) => setPurpose(e.target.value)}
                  />
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span>Duration:</span>
                    <span className="text-slate-900 font-semibold">{hours} hours</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Estimated Cost:</span>
                    <span className="text-blue-700 font-bold">{totalCredits} credits</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Concurrency Guard:</span>
                    <span className="text-emerald-700 font-semibold">PostgreSQL FOR UPDATE</span>
                  </div>
                </div>

                {/* Reservation Action Button with 4 Distinct Session-Aware States */}
                {!auth.isAuthenticated && (
                  <Button
                    type="button"
                    onClick={() => setIsAuthModalOpen(true)}
                    className="w-full text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white cursor-pointer"
                  >
                    Sign In to Reserve
                  </Button>
                )}

                {auth.isAuthenticated && !auth.activeMembership && (
                  <div className="space-y-2">
                    <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 space-y-1">
                      <div className="flex items-center gap-1.5 font-semibold text-amber-800">
                        <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                        <span>Institutional Membership Required</span>
                      </div>
                      <p className="text-[11px] text-amber-700 leading-snug">
                        Your account ({auth.userEmail || "authenticated"}) is signed in, but has no active institutional membership. An administrator or department manager must grant access to your institution before you can reserve equipment.
                      </p>
                    </div>
                    <Button
                      type="button"
                      disabled
                      className="w-full text-xs font-semibold bg-slate-100 border border-slate-300 text-slate-500 cursor-not-allowed"
                    >
                      Institutional Membership Required
                    </Button>
                  </div>
                )}

                {isLiveOrg && (
                  <>
                    {(requiresPermit || requiresQualification) && (
                      <div className="p-2.5 rounded-lg bg-blue-50 border border-blue-200 text-xs text-blue-900 flex items-start gap-2">
                        <ShieldAlert className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                        <div className="text-[11px] leading-snug">
                          <strong className="block font-semibold">Safety Prerequisites Required</strong>
                          {requiresPermit && requiresQualification
                            ? "This instrument enforces both an active institutional safety permit and certified training qualification."
                            : requiresPermit
                            ? "This instrument enforces an active institutional safety permit valid through reservation time."
                            : "This instrument enforces certified training qualification before access is granted."}
                        </div>
                      </div>
                    )}

                    <Button
                      type="submit"
                      disabled={isSubmitting || !isAvailable}
                      className="w-full text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white cursor-pointer"
                    >
                      {isSubmitting ? (
                        "Locking Reservation..."
                      ) : !isAvailable ? (
                        "Asset Offline (Maintenance)"
                      ) : (
                        <span className="flex items-center justify-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>
                            {requiresApproval ? "Submit Reservation for Approval" : "Confirm Instant Reservation"}
                          </span>
                        </span>
                      )}
                    </Button>
                  </>
                )}

                <p className="text-[11px] text-center text-slate-500">
                  {requiresApproval
                    ? "Requires facility manager review. You will receive notification upon approval."
                    : "Direct instant confirmation. Timeslot will be immediately locked."}
                </p>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
      />
    </div>
  )
}
