import { useEffect, useState, useCallback } from "react"
import { Link } from "react-router-dom"
import { useAuth } from "@/context/useAuth"
import { apiClient } from "@/api/client"
import type { BookingResponse } from "@/api/types"
import { DEMO_BOOKINGS } from "@/data/demoData"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"
import { Calendar, CheckCircle2, Clock, RefreshCw, XCircle, AlertCircle, ArrowRight } from "lucide-react"

export function Bookings() {
  const auth = useAuth()
  const [filter, setFilter] = useState<"ALL" | "ACTIVE" | "COMPLETED">("ALL")
  const [liveBookings, setLiveBookings] = useState<BookingResponse[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cancellingId, setCancellingId] = useState<string | null>(null)

  const isLiveMode = auth.isAuthenticated && !!auth.activeMembership

  const fetchMyBookings = useCallback(async () => {
    if (!auth.activeMembership?.organization_id) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await apiClient.getMyBookings(auth.activeMembership.organization_id)
      setLiveBookings(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load bookings")
    } finally {
      setIsLoading(false)
    }
  }, [auth.activeMembership])

  useEffect(() => {
    if (!isLiveMode) return
    const timer = setTimeout(() => {
      void fetchMyBookings()
    }, 0)
    return () => clearTimeout(timer)
  }, [isLiveMode, fetchMyBookings])

  const handleCancel = async (bookingId: string) => {
    if (!auth.activeMembership?.organization_id) return
    if (!window.confirm("Are you sure you want to cancel this reservation?")) return

    setCancellingId(bookingId)
    try {
      await apiClient.cancelBooking(auth.activeMembership.organization_id, bookingId, {
        reason: "Cancelled by user",
      })
      await fetchMyBookings()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to cancel booking")
    } finally {
      setCancellingId(null)
    }
  }

  // Filter live or demo bookings
  const displayedLive = liveBookings.filter((b) => {
    if (filter === "ACTIVE") return b.status === "approved" || b.status === "pending"
    if (filter === "COMPLETED") return b.status === "completed" || b.status === "cancelled" || b.status === "rejected"
    return true
  })

  const filteredDemo = DEMO_BOOKINGS.filter((b) => {
    if (filter === "ACTIVE") return b.status === "APPROVED" || b.status === "REQUESTED"
    if (filter === "COMPLETED") return b.status === "COMPLETED"
    return true
  })

  const formatDateTime = (iso: string) => {
    try {
      const d = new Date(iso)
      return d.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZoneName: "short",
      })
    } catch {
      return iso
    }
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-white border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center gap-2.5">
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              My Reservations & Timelines
            </h2>
            {isLiveMode ? (
              <Badge variant="success">LIVE POSTGRESQL RESERVATIONS</Badge>
            ) : (
              <Badge variant="secondary">SIMULATED DEMO MODE</Badge>
            )}
          </div>
          <p className="text-sm text-slate-500 mt-1">
            {isLiveMode
              ? `Manage your active bookings and pending approvals in ${auth.activeMembership?.organization_name}.`
              : "Track confirmed bookings, pending manager approvals, and upcoming check-in/return handovers."}
          </p>
        </div>

        {isLiveMode && (
          <Button
            variant="outline"
            size="sm"
            onClick={fetchMyBookings}
            disabled={isLoading}
            className="gap-1.5 text-xs bg-white cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </Button>
        )}
      </div>

      {/* Demo Warning Banner */}
      {!isLiveMode && auth.isDemoMode && (
        <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
            <span>
              <strong>Demo Records:</strong> The bookings shown below are demonstration mock items. Sign in to your institutional organization to view your live reservations.
            </span>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-800 flex items-center justify-between">
          <span>Failed to load bookings: {error}</span>
          <Button size="sm" variant="outline" onClick={fetchMyBookings} className="h-7 text-xs bg-white">
            Retry
          </Button>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setFilter("ALL")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium cursor-pointer transition-colors ${
            filter === "ALL"
              ? "bg-blue-600 text-white font-semibold shadow-xs"
              : "bg-white text-slate-700 border border-slate-300 hover:bg-slate-50"
          }`}
        >
          All Reservations ({isLiveMode ? liveBookings.length : DEMO_BOOKINGS.length})
        </button>
        <button
          onClick={() => setFilter("ACTIVE")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium cursor-pointer transition-colors ${
            filter === "ACTIVE"
              ? "bg-blue-600 text-white font-semibold shadow-xs"
              : "bg-white text-slate-700 border border-slate-300 hover:bg-slate-50"
          }`}
        >
          Active / Pending
        </button>
        <button
          onClick={() => setFilter("COMPLETED")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium cursor-pointer transition-colors ${
            filter === "COMPLETED"
              ? "bg-blue-600 text-white font-semibold shadow-xs"
              : "bg-white text-slate-700 border border-slate-300 hover:bg-slate-50"
          }`}
        >
          Past / Cancelled
        </button>
      </div>

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="space-y-4">
          {[1, 2].map((n) => (
            <div key={n} className="h-32 rounded-2xl bg-slate-100 animate-pulse border border-slate-200" />
          ))}
        </div>
      )}

      {/* Live Bookings List */}
      {isLiveMode && !isLoading && (
        <div className="space-y-4">
          {displayedLive.length === 0 ? (
            <div className="p-12 text-center rounded-2xl bg-white border border-slate-200 space-y-3">
              <Calendar className="w-12 h-12 text-slate-300 mx-auto" />
              <h3 className="text-base font-bold text-slate-900">No Reservations Found</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                You do not have any active or past reservations matching this filter.
              </p>
              <Link to="/resources">
                <Button size="sm" className="text-xs bg-blue-600 hover:bg-blue-700 text-white gap-1.5 cursor-pointer">
                  <span>Browse Equipment Catalog</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </Link>
            </div>
          ) : (
            displayedLive.map((booking) => {
              const isApproved = booking.status === "approved"
              const isPending = booking.status === "pending"
              const isCancelled = booking.status === "cancelled"
              const isCancellable = isApproved || isPending

              return (
                <Card key={booking.id} className="border-slate-200 shadow-xs">
                  <CardHeader className="p-5 pb-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge
                          variant={
                            isApproved
                              ? "success"
                              : isPending
                              ? "warning"
                              : isCancelled
                              ? "secondary"
                              : "destructive"
                          }
                        >
                          {booking.status.toUpperCase()}
                        </Badge>
                        <span className="font-mono text-xs text-slate-400 font-medium">
                          ID: {booking.id.slice(0, 8)}...
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>
                          {formatDateTime(booking.start_time)} → {formatDateTime(booking.end_time)}
                        </span>
                      </div>
                    </div>

                    <CardTitle className="text-base text-slate-900 font-bold mt-2">
                      {booking.resource_name || "Institutional Asset"}
                    </CardTitle>
                    <CardDescription className="text-xs text-slate-500 mt-0.5">
                      {booking.purpose ? `Purpose: ${booking.purpose}` : "Research Reservation"}
                    </CardDescription>
                  </CardHeader>

                  <CardContent className="p-5 pt-0">
                    <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                      <div className="space-y-1">
                        <span className="font-bold text-slate-900 block">Reservation Details:</span>
                        <span className="text-slate-600">
                          Total Usage Fee: <strong>{booking.total_credits} credits</strong> • Status:{" "}
                          <span className="capitalize">{booking.status}</span>
                        </span>
                        {booking.rejection_reason && (
                          <span className="text-red-700 block mt-1">Note: {booking.rejection_reason}</span>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        {isCancellable && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleCancel(booking.id)}
                            disabled={cancellingId === booking.id}
                            className="text-xs text-red-600 hover:bg-red-50 cursor-pointer gap-1"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            <span>{cancellingId === booking.id ? "Cancelling..." : "Cancel Reservation"}</span>
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })
          )}
        </div>
      )}

      {/* Demo Bookings Fallback (strictly in explicit demo mode) */}
      {!isLiveMode && auth.isDemoMode && (
        <div className="space-y-4">
          {filteredDemo.map((booking) => (
            <Card key={booking.id} className="border-slate-200 shadow-xs opacity-95">
              <CardHeader className="p-5 pb-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant={booking.status === "APPROVED" ? "success" : booking.status === "REQUESTED" ? "warning" : "secondary"}>
                      {booking.status}
                    </Badge>
                    <span className="font-mono text-xs text-slate-400 font-medium">{booking.id}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>{booking.date}, {booking.startTime} - {booking.endTime}</span>
                  </div>
                </div>
                <CardTitle className="text-base text-slate-900 font-bold mt-1.5">{booking.resourceName}</CardTitle>
                <CardDescription className="text-xs text-slate-500 mt-0.5">{booking.purpose}</CardDescription>
              </CardHeader>

              <CardContent className="p-5 pt-0">
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                  <div className="space-y-1">
                    <span className="font-bold text-slate-900 block">Handover Verification Gate:</span>
                    <span className="text-emerald-700 font-medium flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Both check-in and return condition verified.
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Unauthenticated / No Membership State */}
      {!isLiveMode && !auth.isDemoMode && (
        <div className="p-12 text-center rounded-2xl bg-white border border-slate-200 space-y-3">
          <Calendar className="w-12 h-12 text-slate-300 mx-auto" />
          <h3 className="text-base font-bold text-slate-900">
            {auth.isAuthenticated ? "Active Institutional Membership Required" : "Sign In to View Your Reservations"}
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {auth.isAuthenticated
              ? "Your account does not currently belong to an active institutional workspace. Please contact your institution administrator to enroll your account."
              : "Sign in with your institutional credentials to inspect and manage your live equipment reservations."}
          </p>
        </div>
      )}
    </div>
  )
}
