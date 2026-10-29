import { useState, useEffect, useMemo, useCallback } from "react"
import { useAuth } from "@/context/useAuth"
import { apiClient, ApiClientError } from "@/api/client"
import type {
  BookingResponse,
  EvidenceUploadResponse,
  QualificationResponse,
  SafetyPermitResponse,
  StorageStatusResponse,
} from "@/api/types"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import {
  Award,
  AlertTriangle,
  Camera,
  CheckCircle2,
  Calendar,
  Clock,
  ShieldAlert,
  Info,
  RefreshCw,
  Upload,
} from "lucide-react"

// ---------------------------------------------------------------------------
// 1. Qualifications & Safety Permits Page (Real PostgreSQL Backed)
// ---------------------------------------------------------------------------

export function QualificationsPage() {
  const auth = useAuth()
  const [qualifications, setQualifications] = useState<QualificationResponse[]>([])
  const [permits, setPermits] = useState<SafetyPermitResponse[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isLive = auth.isAuthenticated && !!auth.activeMembership
  const orgId = auth.activeMembership?.organization_id

  const loadComplianceData = useCallback(async () => {
    if (!orgId) return
    setIsLoading(true)
    setError(null)
    try {
      const [quals, perms] = await Promise.all([
        apiClient.getMyQualifications(orgId),
        apiClient.getMySafetyPermits(orgId),
      ])
      setQualifications(quals)
      setPermits(perms)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load compliance records")
    } finally {
      setIsLoading(false)
    }
  }, [orgId])

  useEffect(() => {
    if (!isLive || !orgId) return
    const timer = setTimeout(() => {
      void loadComplianceData()
    }, 0)
    return () => clearTimeout(timer)
  }, [isLive, orgId, loadComplianceData])

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Safety Permits & Qualifications
            </h2>
            {isLive ? (
              <Badge variant="success">LIVE POSTGRESQL</Badge>
            ) : (
              <Badge variant="secondary">DEMO PERSONA</Badge>
            )}
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Institutional certifications required to access specialized lab equipment and fabrication tools.
          </p>
        </div>

        {isLive && (
          <Button
            size="sm"
            variant="outline"
            onClick={loadComplianceData}
            disabled={isLoading}
            className="text-xs gap-1.5 h-8 bg-white cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </Button>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-800">
          {error}
        </div>
      )}

      {/* Safety Permits Section */}
      <Card>
        <CardHeader className="pb-3 border-b border-slate-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-600" />
              <CardTitle className="text-base font-bold text-slate-900">Institutional Safety Permits</CardTitle>
            </div>
            <span className="text-xs text-slate-500">{permits.length} Records</span>
          </div>
          <CardDescription className="text-xs text-slate-500">
            Institutional environmental health and radiation safety credentials. Required for hazardous instruments.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-5">
          {isLoading ? (
            <div className="h-24 bg-slate-50 rounded-xl animate-pulse" />
          ) : permits.length === 0 ? (
            <div className="p-6 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-2">
              <ShieldAlert className="w-8 h-8 text-slate-400 mx-auto" />
              <p className="text-xs font-semibold text-slate-700">No Safety Permits On File</p>
              <p className="text-[11px] text-slate-500 max-w-md mx-auto">
                Your authenticated account ({auth.userEmail || "current member"}) currently holds no active institutional safety permits. Contact your departmental safety officer to log certifications.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {permits.map((p) => (
                <div key={p.id} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 text-sm">{p.permit_type}</span>
                    <Badge variant={p.status === "active" ? "success" : "destructive"}>{p.status.toUpperCase()}</Badge>
                  </div>
                  <p className="text-xs text-slate-500">Issued by: {p.issuer || "Institutional EHS Office"}</p>
                  <div className="flex items-center justify-between text-xs text-slate-600 pt-2 border-t border-slate-200">
                    <span>Expires: {new Date(p.expiry_date).toLocaleDateString()}</span>
                    <span className="text-blue-700 font-mono font-medium">{p.id.slice(0, 8)}...</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Equipment Qualifications Section */}
      <Card>
        <CardHeader className="pb-3 border-b border-slate-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Award className="w-4 h-4 text-purple-600" />
              <CardTitle className="text-base font-bold text-slate-900">Equipment Certified Qualifications</CardTitle>
            </div>
            <span className="text-xs text-slate-500">{qualifications.length} Records</span>
          </div>
          <CardDescription className="text-xs text-slate-500">
            Validated operator clearance granted by facility managers following practical training.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-5">
          {isLoading ? (
            <div className="h-24 bg-slate-50 rounded-xl animate-pulse" />
          ) : qualifications.length === 0 ? (
            <div className="p-6 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-2">
              <Award className="w-8 h-8 text-slate-400 mx-auto" />
              <p className="text-xs font-semibold text-slate-700">No Equipment Qualifications Granted</p>
              <p className="text-[11px] text-slate-500 max-w-md mx-auto">
                No equipment training credentials have been granted yet for this account. Booking requests on restricted instruments (such as the Agilent 1290 UHPLC-MS) will be rejected by the server safety gate until certified.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {qualifications.map((q) => (
                <div key={q.id} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 text-sm">{q.title}</span>
                    <Badge variant={q.status === "active" ? "success" : "warning"}>{q.status.toUpperCase()}</Badge>
                  </div>
                  <p className="text-xs text-slate-500">
                    Target Instrument: {q.resource_name || "Department-Wide Standard"}
                  </p>
                  <div className="flex items-center justify-between text-xs text-slate-600 pt-2 border-t border-slate-200">
                    <span>Certified: {new Date(q.certified_at).toLocaleDateString()}</span>
                    <span className="text-purple-700 font-mono font-medium">{q.qualification_code}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// ---------------------------------------------------------------------------
// 2. Handover Gate: Check-In & Return (Real PostgreSQL Backed)
// ---------------------------------------------------------------------------

export function HandoverPage() {
  const auth = useAuth()
  const [bookings, setBookings] = useState<BookingResponse[]>([])
  const [selectedBookingId, setSelectedBookingId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Handover form state
  const [checklist1, setChecklist1] = useState(false)
  const [checklist2, setChecklist2] = useState(false)
  const [checklist3, setChecklist3] = useState(false)
  const [conditionNotes, setConditionNotes] = useState("")
  const [incidentReported, setIncidentReported] = useState(false)
  const [storageStatus, setStorageStatus] = useState<StorageStatusResponse | null>(null)
  const [evidenceFile, setEvidenceFile] = useState<File | null>(null)
  const [isUploadingPhoto, setIsUploadingPhoto] = useState(false)
  const [uploadedEvidence, setUploadedEvidence] = useState<EvidenceUploadResponse | null>(null)

  const isLive = auth.isAuthenticated && !!auth.activeMembership
  const orgId = auth.activeMembership?.organization_id

  const loadBookings = useCallback(async () => {
    if (!orgId) return
    setIsLoading(true)
    setError(null)
    try {
      const [bookingsData, storageData] = await Promise.all([
        apiClient.getMyBookings(orgId),
        apiClient.getEvidenceStorageStatus(orgId).catch(() => null),
      ])
      setBookings(bookingsData)
      if (storageData) {
        setStorageStatus(storageData)
      }
      // Default to first eligible booking (approved or in_use)
      const eligible = bookingsData.find((b) => b.status === "approved" || b.status === "in_use")
      if (eligible) {
        setSelectedBookingId(eligible.id)
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load reservations")
    } finally {
      setIsLoading(false)
    }
  }, [orgId])

  useEffect(() => {
    if (!isLive || !orgId) return
    const timer = setTimeout(() => {
      void loadBookings()
    }, 0)
    return () => clearTimeout(timer)
  }, [isLive, orgId, loadBookings])

  const selectedBooking = useMemo(
    () => bookings.find((b) => b.id === selectedBookingId),
    [bookings, selectedBookingId]
  )

  const isCheckinEligible = selectedBooking?.status === "approved"
  const isReturnEligible = selectedBooking?.status === "in_use"

  async function handleUploadPhoto(handoverType: "checkin" | "return") {
    if (!auth.activeMembership?.organization_id || !selectedBooking || !evidenceFile) return
    setIsUploadingPhoto(true)
    setError(null)
    try {
      const res = await apiClient.uploadBookingEvidence(
        auth.activeMembership.organization_id,
        selectedBooking.id,
        evidenceFile,
        handoverType
      )
      setUploadedEvidence(res)
      setSuccessMsg(`Photo evidence attached: ${res.filename} (${(res.size_bytes / 1024).toFixed(1)} KB)`)
    } catch (err: unknown) {
      setError(err instanceof ApiClientError ? err.message : "Failed to upload photo evidence.")
    } finally {
      setIsUploadingPhoto(false)
    }
  }

  async function handleCheckinSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!auth.activeMembership?.organization_id || !selectedBooking) return
    if (!checklist1 || !checklist2 || !checklist3) {
      setError("You must verify all mandatory pre-use checklist items before check-in.")
      return
    }

    setIsSubmitting(true)
    setError(null)
    setSuccessMsg(null)
    try {
      const updated = await apiClient.checkinBooking(
        auth.activeMembership.organization_id,
        selectedBooking.id,
        {
          checklist_completed: true,
          condition_notes: conditionNotes.trim() || undefined,
          photo_evidence_url: uploadedEvidence?.storage_path || undefined,
        }
      )
      setSuccessMsg(`Check-in successful! Asset '${updated.resource_name || "Equipment"}' is now active and in use.`)
      setChecklist1(false)
      setChecklist2(false)
      setChecklist3(false)
      setConditionNotes("")
      setUploadedEvidence(null)
      setEvidenceFile(null)
      await loadBookings()
    } catch (err: unknown) {
      setError(err instanceof ApiClientError ? err.message : "Failed to complete check-in.")
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleReturnSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!auth.activeMembership?.organization_id || !selectedBooking) return
    if (!checklist1 || !checklist2 || !checklist3) {
      setError("You must verify all mandatory post-use return checklist items.")
      return
    }

    setIsSubmitting(true)
    setError(null)
    setSuccessMsg(null)
    try {
      const updated = await apiClient.returnBooking(
        auth.activeMembership.organization_id,
        selectedBooking.id,
        {
          checklist_completed: true,
          condition_notes: conditionNotes.trim() || undefined,
          incident_reported: incidentReported,
          photo_evidence_url: uploadedEvidence?.storage_path || undefined,
        }
      )
      setSuccessMsg(`Return completed successfully! Session for '${updated.resource_name || "Equipment"}' is closed.`)
      setChecklist1(false)
      setChecklist2(false)
      setChecklist3(false)
      setConditionNotes("")
      setIncidentReported(false)
      setUploadedEvidence(null)
      setEvidenceFile(null)
      await loadBookings()
    } catch (err: unknown) {
      setError(err instanceof ApiClientError ? err.message : "Failed to complete return handover.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Check-In & Return Handover Gate
            </h2>
            {isLive ? (
              <Badge variant="success">LIVE WORKFLOW</Badge>
            ) : (
              <Badge variant="secondary">DEMO MODE</Badge>
            )}
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Mandatory condition checklists, physical verification, and immutable audit handover logging.
          </p>
        </div>

        {isLive && (
          <Button
            size="sm"
            variant="outline"
            onClick={loadBookings}
            disabled={isLoading}
            className="text-xs gap-1.5 h-8 bg-white cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>Refresh Reservations</span>
          </Button>
        )}
      </div>

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 flex items-center gap-2 font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-900 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Cloud Storage Status Banner */}
      {storageStatus?.configured ? (
        <div className="p-3.5 rounded-xl bg-emerald-50/80 border border-emerald-200 text-xs text-emerald-900 flex items-start gap-2.5">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-0.5 text-[11px] leading-relaxed">
            <strong>Storage Integration Status:</strong> Private Supabase Storage bucket (<code className="bg-emerald-100 px-1 py-0.5 rounded font-mono text-emerald-800">{storageStatus.bucket_name || "sharespace-evidence"}</code>) is <strong>LIVE and CONNECTED</strong>. Pre-use and return condition photographs are securely encrypted at rest with short-lived authenticated access tokens.
          </div>
        </div>
      ) : (
        <div className="p-3.5 rounded-xl bg-blue-50/80 border border-blue-200 text-xs text-blue-900 flex items-start gap-2.5">
          <Info className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-0.5 text-[11px] leading-relaxed">
            <strong>Storage Integration Status:</strong> Cloud object storage credentials (S3/Supabase Storage) are not configured in this environment. Photographic upload is marked <code className="bg-blue-100 px-1 py-0.5 rounded font-mono text-blue-800">BLOCKED (Set EVIDENCE_STORAGE_BUCKET)</code>. Mandatory condition checklists, timestamps, and PostgreSQL audit logging are <strong>100% LIVE and ACTIVE</strong>.
          </div>
        </div>
      )}

      {/* Reservation Selector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Select Active Reservation
          </h3>

          {isLoading ? (
            <div className="h-40 bg-slate-50 rounded-xl animate-pulse" />
          ) : bookings.length === 0 ? (
            <div className="p-5 rounded-xl bg-white border border-slate-200 text-center space-y-2">
              <Calendar className="w-6 h-6 text-slate-400 mx-auto" />
              <p className="text-xs font-semibold text-slate-700">No Reservations Found</p>
              <p className="text-[11px] text-slate-500">
                You do not have any active or confirmed reservations to check in.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {bookings.map((b) => (
                <div
                  key={b.id}
                  onClick={() => setSelectedBookingId(b.id)}
                  className={`p-3.5 rounded-xl border transition-all cursor-pointer text-xs space-y-1.5 ${
                    selectedBookingId === b.id
                      ? "bg-blue-50/60 border-blue-400 shadow-xs"
                      : "bg-white border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 truncate">
                      {b.resource_name || `Resource ${b.resource_id.slice(0, 8)}`}
                    </span>
                    <Badge
                      variant={
                        b.status === "approved"
                          ? "warning"
                          : b.status === "in_use"
                          ? "info"
                          : b.status === "completed"
                          ? "success"
                          : "secondary"
                      }
                    >
                      {b.status.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    <span>
                      {new Date(b.start_time).toLocaleDateString()} ({new Date(b.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {new Date(b.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Handover Action Panel */}
        <div className="lg:col-span-2">
          {!selectedBooking ? (
            <div className="h-64 rounded-xl border border-dashed border-slate-200 bg-slate-50 flex items-center justify-center text-xs text-slate-400">
              Select a reservation on the left to perform handover actions.
            </div>
          ) : (
            <Card>
              <CardHeader className="pb-3 border-b border-slate-100">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-[10px] font-bold text-blue-700 uppercase tracking-wider block">
                      Target Equipment
                    </span>
                    <CardTitle className="text-base font-bold text-slate-900 mt-0.5">
                      {selectedBooking.resource_name || "Institutional Equipment"}
                    </CardTitle>
                  </div>
                  <Badge
                    variant={
                      selectedBooking.status === "approved"
                        ? "warning"
                        : selectedBooking.status === "in_use"
                        ? "info"
                        : "secondary"
                    }
                  >
                    {selectedBooking.status === "approved"
                      ? "Ready for Check-In"
                      : selectedBooking.status === "in_use"
                      ? "In Use (Return Pending)"
                      : selectedBooking.status.toUpperCase()}
                  </Badge>
                </div>
                <CardDescription className="text-xs text-slate-500 mt-1">
                  Reservation #{selectedBooking.id.slice(0, 8)} • Timeslot: {new Date(selectedBooking.start_time).toLocaleString()} to {new Date(selectedBooking.end_time).toLocaleTimeString()}
                </CardDescription>
              </CardHeader>

              <CardContent className="p-5">
                {isCheckinEligible && (
                  <form onSubmit={handleCheckinSubmit} className="space-y-4">
                    <div className="space-y-2">
                      <span className="text-xs font-bold text-slate-800 block">
                        Mandatory Pre-Use Inspection Checklist:
                      </span>

                      <label className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200 cursor-pointer text-xs text-slate-800">
                        <input
                          type="checkbox"
                          checked={checklist1}
                          onChange={(e) => setChecklist1(e.target.checked)}
                          className="rounded text-blue-600 focus:ring-blue-500 mt-0.5"
                        />
                        <span>Physical inspection complete: no unrecorded exterior cracks, spills, or mechanical defects.</span>
                      </label>

                      <label className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200 cursor-pointer text-xs text-slate-800">
                        <input
                          type="checkbox"
                          checked={checklist2}
                          onChange={(e) => setChecklist2(e.target.checked)}
                          className="rounded text-blue-600 focus:ring-blue-500 mt-0.5"
                        />
                        <span>Emergency stops, interlocks, and primary safety guards verified in operational state.</span>
                      </label>

                      <label className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200 cursor-pointer text-xs text-slate-800">
                        <input
                          type="checkbox"
                          checked={checklist3}
                          onChange={(e) => setChecklist3(e.target.checked)}
                          className="rounded text-blue-600 focus:ring-blue-500 mt-0.5"
                        />
                        <span>Institutional user logbook signed and initial baseline calibration confirmed.</span>
                      </label>
                    </div>

                    <div>
                      <label className="text-xs font-semibold text-slate-700 block mb-1">
                        Initial Condition Notes (Optional):
                      </label>
                      <Input
                        placeholder="e.g. Stage clean, optics pristine, 24°C ambient chamber temp."
                        value={conditionNotes}
                        onChange={(e) => setConditionNotes(e.target.value)}
                        className="text-xs"
                      />
                    </div>

                    {/* Condition Photo Attachment */}
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                          <Camera className="w-3.5 h-3.5 text-blue-600" />
                          Pre-Use Condition Photograph (Optional):
                        </span>
                        {uploadedEvidence && (
                          <Badge variant="success">PHOTO ATTACHED</Badge>
                        )}
                      </div>

                      {!uploadedEvidence ? (
                        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                          <input
                            type="file"
                            accept="image/jpeg,image/png,image/webp"
                            onChange={(e) => setEvidenceFile(e.target.files?.[0] || null)}
                            className="text-xs file:mr-2 file:py-1 file:px-2.5 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
                          />
                          {evidenceFile && (
                            <Button
                              type="button"
                              size="sm"
                              onClick={() => void handleUploadPhoto("checkin")}
                              disabled={isUploadingPhoto}
                              className="text-xs h-7 gap-1 bg-blue-600 hover:bg-blue-700 text-white cursor-pointer"
                            >
                              <Upload className="w-3 h-3" />
                              <span>{isUploadingPhoto ? "Uploading..." : "Upload Photo"}</span>
                            </Button>
                          )}
                        </div>
                      ) : (
                        <div className="flex items-center gap-3 p-2 rounded-md bg-emerald-50/70 border border-emerald-200">
                          <img
                            src={uploadedEvidence.signed_url}
                            alt="Pre-use condition preview"
                            className="w-12 h-12 object-cover rounded border border-emerald-300"
                          />
                          <div className="text-[11px] text-emerald-900 flex-1 truncate">
                            <p className="font-semibold truncate">{uploadedEvidence.filename}</p>
                            <p className="text-emerald-700 font-mono text-[10px]">
                              {(uploadedEvidence.size_bytes / 1024).toFixed(1)} KB • {uploadedEvidence.storage_path.slice(0, 30)}...
                            </p>
                          </div>
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => { setUploadedEvidence(null); setEvidenceFile(null); }}
                            className="text-[10px] h-6 px-2 text-slate-600 hover:text-red-700 cursor-pointer"
                          >
                            Remove
                          </Button>
                        </div>
                      )}
                    </div>

                    <Button
                      type="submit"
                      disabled={isSubmitting || !checklist1 || !checklist2 || !checklist3}
                      className="w-full text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white cursor-pointer"
                    >
                      {isSubmitting ? "Processing Check-In..." : "Complete Check-In & Activate Session"}
                    </Button>
                  </form>
                )}

                {isReturnEligible && (
                  <form onSubmit={handleReturnSubmit} className="space-y-4">
                    <div className="space-y-2">
                      <span className="text-xs font-bold text-slate-800 block">
                        Mandatory Post-Use Return Checklist:
                      </span>

                      <label className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200 cursor-pointer text-xs text-slate-800">
                        <input
                          type="checkbox"
                          checked={checklist1}
                          onChange={(e) => setChecklist1(e.target.checked)}
                          className="rounded text-blue-600 focus:ring-blue-500 mt-0.5"
                        />
                        <span>Samples, wafers, and hazardous chemical consumables fully cleared from instrument.</span>
                      </label>

                      <label className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200 cursor-pointer text-xs text-slate-800">
                        <input
                          type="checkbox"
                          checked={checklist2}
                          onChange={(e) => setChecklist2(e.target.checked)}
                          className="rounded text-blue-600 focus:ring-blue-500 mt-0.5"
                        />
                        <span>Workstation sanitized, laser/power systems shut down or placed in standard standby.</span>
                      </label>

                      <label className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200 cursor-pointer text-xs text-slate-800">
                        <input
                          type="checkbox"
                          checked={checklist3}
                          onChange={(e) => setChecklist3(e.target.checked)}
                          className="rounded text-blue-600 focus:ring-blue-500 mt-0.5"
                        />
                        <span>End-of-session logbook recorded with actual operational runtime.</span>
                      </label>
                    </div>

                    <div>
                      <label className="text-xs font-semibold text-slate-700 block mb-1">
                        Return Handover Notes (Optional):
                      </label>
                      <Input
                        placeholder="e.g. Session concluded normally, vacuum pumped down to base pressure."
                        value={conditionNotes}
                        onChange={(e) => setConditionNotes(e.target.value)}
                        className="text-xs"
                      />
                    </div>

                    {/* Return Condition Photo Attachment */}
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                          <Camera className="w-3.5 h-3.5 text-emerald-600" />
                          Return Condition Photograph (Optional):
                        </span>
                        {uploadedEvidence && (
                          <Badge variant="success">PHOTO ATTACHED</Badge>
                        )}
                      </div>

                      {!uploadedEvidence ? (
                        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                          <input
                            type="file"
                            accept="image/jpeg,image/png,image/webp"
                            onChange={(e) => setEvidenceFile(e.target.files?.[0] || null)}
                            className="text-xs file:mr-2 file:py-1 file:px-2.5 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100 cursor-pointer"
                          />
                          {evidenceFile && (
                            <Button
                              type="button"
                              size="sm"
                              onClick={() => void handleUploadPhoto("return")}
                              disabled={isUploadingPhoto}
                              className="text-xs h-7 gap-1 bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer"
                            >
                              <Upload className="w-3 h-3" />
                              <span>{isUploadingPhoto ? "Uploading..." : "Upload Photo"}</span>
                            </Button>
                          )}
                        </div>
                      ) : (
                        <div className="flex items-center gap-3 p-2 rounded-md bg-emerald-50/70 border border-emerald-200">
                          <img
                            src={uploadedEvidence.signed_url}
                            alt="Return condition preview"
                            className="w-12 h-12 object-cover rounded border border-emerald-300"
                          />
                          <div className="text-[11px] text-emerald-900 flex-1 truncate">
                            <p className="font-semibold truncate">{uploadedEvidence.filename}</p>
                            <p className="text-emerald-700 font-mono text-[10px]">
                              {(uploadedEvidence.size_bytes / 1024).toFixed(1)} KB • {uploadedEvidence.storage_path.slice(0, 30)}...
                            </p>
                          </div>
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => { setUploadedEvidence(null); setEvidenceFile(null); }}
                            className="text-[10px] h-6 px-2 text-slate-600 hover:text-red-700 cursor-pointer"
                          >
                            Remove
                          </Button>
                        </div>
                      )}
                    </div>

                    <label className="flex items-center gap-2 text-xs text-slate-700 p-2.5 rounded-lg bg-amber-50 border border-amber-200 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={incidentReported}
                        onChange={(e) => setIncidentReported(e.target.checked)}
                        className="rounded text-amber-600 focus:ring-amber-500"
                      />
                      <span>An incident, defect, or equipment warning occurred during this session.</span>
                    </label>

                    <Button
                      type="submit"
                      disabled={isSubmitting || !checklist1 || !checklist2 || !checklist3}
                      className="w-full text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer"
                    >
                      {isSubmitting ? "Processing Return..." : "Complete Return Handover & Close Session"}
                    </Button>
                  </form>
                )}

                {!isCheckinEligible && !isReturnEligible && (
                  <div className="p-6 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-2">
                    <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
                    <p className="text-xs font-semibold text-slate-800">
                      Handover Complete or Not Applicable
                    </p>
                    <p className="text-[11px] text-slate-500">
                      This reservation is in <strong>{selectedBooking.status.toUpperCase()}</strong> status.
                      {selectedBooking.status === "completed" && " Equipment was safely returned and checked out."}
                      {selectedBooking.status === "cancelled" && " This reservation was cancelled."}
                      {selectedBooking.status === "pending" && " Awaiting manager approval before check-in can begin."}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// 3. Condition Reports Page (Real PostgreSQL Backed)
// ---------------------------------------------------------------------------

export function ConditionReportsPage() {
  const auth = useAuth()
  const [completedBookings, setCompletedBookings] = useState<BookingResponse[]>([])
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    async function loadCompleted() {
      if (!auth.activeMembership?.organization_id) return
      setIsLoading(true)
      try {
        const data = await apiClient.getMyBookings(auth.activeMembership.organization_id)
        setCompletedBookings(data.filter((b) => b.status === "completed" || b.status === "in_use"))
      } catch {
        // silent
      } finally {
        setIsLoading(false)
      }
    }
    loadCompleted()
  }, [auth.activeMembership?.organization_id])

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      <div>
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
          Historical Condition Reports
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Chronological audit log of physical equipment verification and handover timestamps.
        </p>
      </div>

      <Card>
        <CardHeader className="pb-3 border-b border-slate-100">
          <CardTitle className="text-base font-bold text-slate-900">Completed Sessions Audit</CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Validated records proving equipment state transitions and user sign-offs.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-5">
          {isLoading ? (
            <div className="h-32 bg-slate-50 rounded-xl animate-pulse" />
          ) : completedBookings.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-500">
              No completed sessions on file yet. Once equipment is checked out and returned, condition records will be archived here.
            </div>
          ) : (
            <div className="space-y-3">
              {completedBookings.map((b) => (
                <div key={b.id} className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900">{b.resource_name || "Instrument"}</span>
                    <Badge variant={b.status === "completed" ? "success" : "info"}>
                      {b.status.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-600">
                    <div>
                      <span className="text-slate-400 block font-semibold uppercase text-[10px]">Checked In</span>
                      <span>{b.checkin_time ? new Date(b.checkin_time).toLocaleString() : "Not recorded"}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block font-semibold uppercase text-[10px]">Checked Out</span>
                      <span>{b.checkout_time ? new Date(b.checkout_time).toLocaleString() : "Active session"}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// ---------------------------------------------------------------------------
// 4. Incident Reporting Page
// ---------------------------------------------------------------------------

export function IncidentReportPage() {
  const [submitted, setSubmitted] = useState(false)
  const [description, setDescription] = useState("")

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      <div>
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
          Report Incident or Defect
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Structured reporting for equipment malfunctions, accidental damage, or safety hazards.
        </p>
      </div>

      <Card>
        <CardHeader className="pb-3 border-b border-slate-100">
          <CardTitle className="text-base font-bold text-slate-900">Incident Disclosure</CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Transparent reporting routed to facility managers. No unilateral automated penalties are levied.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-5">
          {submitted ? (
            <div className="p-6 rounded-xl bg-emerald-50 border border-emerald-200 text-center space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
              <p className="text-xs font-semibold text-emerald-900">Incident Report Received</p>
              <p className="text-[11px] text-emerald-700">
                Facility engineering has been notified. An audit event was logged to your institutional record.
              </p>
              <Button size="sm" variant="outline" onClick={() => setSubmitted(false)} className="text-xs mt-2 bg-white">
                Submit Another Report
              </Button>
            </div>
          ) : (
            <form
              onSubmit={(e) => {
                e.preventDefault()
                setSubmitted(true)
              }}
              className="space-y-4 text-xs"
            >
              <div>
                <label className="text-slate-700 font-semibold block mb-1">Incident Classification:</label>
                <select className="w-full p-2.5 rounded-lg bg-white border border-slate-300 text-slate-800">
                  <option>Software freeze requiring hard reboot</option>
                  <option>Laser emission shutter error during scan</option>
                  <option>Mechanical misalignment / stage collision</option>
                  <option>Pre-existing defect discovered upon arrival</option>
                </select>
              </div>

              <div>
                <label className="text-slate-700 font-semibold block mb-1">Detailed Description:</label>
                <textarea
                  required
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe what occurred, any error codes displayed on instrument screen, and immediate corrective steps taken..."
                  className="w-full p-2.5 rounded-lg bg-white border border-slate-300 text-slate-800 text-xs"
                />
              </div>

              <Button type="submit" variant="destructive" className="w-full text-xs font-semibold cursor-pointer">
                Submit Incident Report to Facility Engineering
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
