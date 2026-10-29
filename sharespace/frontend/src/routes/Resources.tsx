import { useEffect, useState, useTransition, useCallback } from "react"
import { Link } from "react-router-dom"
import { useAuth } from "@/context/useAuth"
import { apiClient } from "@/api/client"
import type { ResourceResponse } from "@/api/types"
import { DEMO_RESOURCES, DEMO_CATEGORIES } from "@/data/demoData"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import {
  Search,
  MapPin,
  ShieldAlert,
  ArrowRight,
  Filter,
  Plus,
  RefreshCw,
  Cpu,
  Wrench,
  FlaskConical,
  Building2,
  Box,
} from "lucide-react"

export function Resources() {
  const auth = useAuth()
  const [search, setSearch] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("ALL")
  const [approvalFilter, setApprovalFilter] = useState<"ALL" | "INSTANT" | "APPROVAL">("ALL")

  // Live API state
  const [liveResources, setLiveResources] = useState<ResourceResponse[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [, startTransition] = useTransition()

  // New Resource Modal state (for managers/admins)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [newResName, setNewResName] = useState("")
  const [newResCategory, setNewResCategory] = useState("lab_instrument")
  const [newResLocation, setNewResLocation] = useState("")
  const [newResRate, setNewResRate] = useState(25)
  const [newResApproval, setNewResApproval] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const isLiveMode = auth.isAuthenticated && !!auth.activeMembership
  const isManagerOrAdmin =
    auth.activeMembership?.role === "admin" ||
    auth.activeMembership?.role === "lab_manager"

  const fetchLiveResources = useCallback(async () => {
    if (!auth.activeMembership?.organization_id) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await apiClient.getResources(auth.activeMembership.organization_id, {
        category: selectedCategory !== "ALL" ? selectedCategory : undefined,
        search: search.trim() || undefined,
      })
      startTransition(() => {
        setLiveResources(data)
      })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load resources"
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }, [auth.activeMembership, selectedCategory, search])

  useEffect(() => {
    if (!isLiveMode) return
    const timer = setTimeout(() => {
      void fetchLiveResources()
    }, 0)
    return () => clearTimeout(timer)
  }, [isLiveMode, fetchLiveResources])

  const handleCreateResource = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!auth.activeMembership?.organization_id) return
    setIsSubmitting(true)
    setCreateError(null)
    try {
      await apiClient.createResource(auth.activeMembership.organization_id, {
        name: newResName.trim(),
        category: newResCategory,
        location: newResLocation.trim() || undefined,
        hourly_rate_credits: Number(newResRate),
        requires_approval: newResApproval,
      })
      setIsModalOpen(false)
      setNewResName("")
      setNewResLocation("")
      await fetchLiveResources()
    } catch (err: unknown) {
      setCreateError(err instanceof Error ? err.message : "Failed to register resource")
    } finally {
      setIsSubmitting(false)
    }
  }

  // Filter live resources or demo resources
  const displayedLive = liveResources.filter((res) => {
    const matchesApproval =
      approvalFilter === "ALL" ||
      (approvalFilter === "INSTANT" && !res.requires_approval) ||
      (approvalFilter === "APPROVAL" && res.requires_approval)
    return matchesApproval
  })

  const filteredDemo = DEMO_RESOURCES.filter((res) => {
    const matchesSearch =
      res.name.toLowerCase().includes(search.toLowerCase()) ||
      res.modelNumber.toLowerCase().includes(search.toLowerCase()) ||
      res.location.toLowerCase().includes(search.toLowerCase())

    const matchesCat = selectedCategory === "ALL" || res.category === selectedCategory
    const matchesApproval =
      approvalFilter === "ALL" ||
      (approvalFilter === "INSTANT" && !res.requiresApproval) ||
      (approvalFilter === "APPROVAL" && res.requiresApproval)

    return matchesSearch && matchesCat && matchesApproval
  })

  const getCategoryIcon = (cat: string) => {
    switch (cat.toLowerCase()) {
      case "lab_instrument":
      case "lab":
        return <FlaskConical className="w-3.5 h-3.5 text-blue-600" />
      case "workshop_tool":
      case "workshop":
        return <Wrench className="w-3.5 h-3.5 text-amber-600" />
      case "computing_cluster":
      case "computing":
        return <Cpu className="w-3.5 h-3.5 text-purple-600" />
      case "testing_facility":
      case "space":
        return <Building2 className="w-3.5 h-3.5 text-emerald-600" />
      default:
        return <Box className="w-3.5 h-3.5 text-slate-500" />
    }
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-white border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center gap-2.5">
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Institutional Resource Discovery
            </h2>
            {isLiveMode ? (
              <Badge variant="success">LIVE INSTITUTIONAL DATABASE</Badge>
            ) : auth.isDemoMode ? (
              <Badge variant="secondary">SIMULATED DEMO MODE</Badge>
            ) : (
              <Badge variant="outline">DISCOVERY CATALOG</Badge>
            )}
          </div>
          <p className="text-sm text-slate-500 mt-1">
            {isLiveMode
              ? `Connected to ${auth.activeMembership?.organization_name}. Real-time equipment discovery and conflict-free booking.`
              : auth.isDemoMode
              ? "Search laboratories, fabrication tools, seminar rooms, and specialized AV kits across demo campus departments."
              : "Explore institutional research facilities, fabrication tools, and scientific equipment."}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isLiveMode && (
            <Button
              variant="outline"
              size="sm"
              onClick={fetchLiveResources}
              disabled={isLoading}
              className="gap-1.5 text-xs bg-white cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </Button>
          )}

          {isManagerOrAdmin && (
            <Button
              variant="default"
              size="sm"
              onClick={() => setIsModalOpen(true)}
              className="gap-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Add Facility Asset</span>
            </Button>
          )}
        </div>
      </div>

      {/* Demo Warning Banner if in Demo Mode */}
      {!isLiveMode && auth.isDemoMode && (
        <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-600 flex-shrink-0" />
            <span>
              <strong>Demo Persona Active:</strong> The cards below reflect simulated demonstration records. Sign in with real institutional credentials to interact with real PostgreSQL assets.
            </span>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-800 flex items-center justify-between">
          <span>Failed to load resources: {error}</span>
          <Button size="sm" variant="outline" onClick={fetchLiveResources} className="h-7 text-xs bg-white">
            Retry
          </Button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-3 shadow-xs">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="flex-1">
            <Input
              type="text"
              placeholder="Search by instrument name, location, or specifications..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && isLiveMode && fetchLiveResources()}
              icon={<Search className="w-4 h-4 text-slate-400" />}
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-500" />
            <select
              value={approvalFilter}
              onChange={(e) => setApprovalFilter(e.target.value as "ALL" | "INSTANT" | "APPROVAL")}
              className="bg-white border border-slate-300 text-xs rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-600 cursor-pointer"
            >
              <option value="ALL">All Reservation Types</option>
              <option value="INSTANT">Direct Instant Booking</option>
              <option value="APPROVAL">Requires Manager Approval</option>
            </select>
          </div>
        </div>

        {/* Categories */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          {isLiveMode ? (
            <>
              {["ALL", "lab_instrument", "workshop_tool", "computing_cluster", "testing_facility"].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
                    selectedCategory === cat
                      ? "bg-blue-600 text-white font-semibold shadow-xs"
                      : "bg-white border border-slate-300 text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  {cat === "ALL"
                    ? "All Categories"
                    : cat.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                </button>
              ))}
            </>
          ) : (
            DEMO_CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
                  selectedCategory === cat.id
                    ? "bg-blue-600 text-white font-semibold shadow-xs"
                    : "bg-white border border-slate-300 text-slate-700 hover:bg-slate-50"
                }`}
              >
                {cat.name} ({cat.resourceCount})
              </button>
            ))
          )}
        </div>
      </div>

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-64 rounded-2xl bg-slate-100 animate-pulse border border-slate-200" />
          ))}
        </div>
      )}

      {/* Live Resources Catalog Grid */}
      {isLiveMode && !isLoading && (
        <>
          {displayedLive.length === 0 ? (
            <div className="p-12 text-center rounded-2xl bg-white border border-slate-200 space-y-3">
              <Box className="w-12 h-12 text-slate-300 mx-auto" />
              <h3 className="text-base font-bold text-slate-900">No Institutional Assets Found</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                No equipment matching your filters is currently listed in this organization.
              </p>
              {isManagerOrAdmin && (
                <Button size="sm" onClick={() => setIsModalOpen(true)} className="text-xs bg-blue-600 text-white">
                  Add First Asset
                </Button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {displayedLive.map((res) => (
                <Card key={res.id} className="hover:border-slate-300 flex flex-col justify-between transition-colors shadow-2xs">
                  <CardHeader className="p-5">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-1.5">
                        {getCategoryIcon(res.category)}
                        <Badge variant="info">
                          {res.category.replace(/_/g, " ").toUpperCase()}
                        </Badge>
                      </div>
                      <Badge variant={res.is_available ? "success" : "destructive"}>
                        {res.is_available ? "AVAILABLE" : "MAINTENANCE"}
                      </Badge>
                    </div>

                    <CardTitle className="text-base font-bold text-slate-900 leading-snug line-clamp-2" title={res.name}>
                      {res.name}
                    </CardTitle>
                    <CardDescription className="text-xs text-slate-500 mt-1 line-clamp-2">
                      {res.description || "High-precision institutional equipment available for academic research and testing."}
                    </CardDescription>
                  </CardHeader>

                  <CardContent className="p-5 pt-0 space-y-3">
                    <div className="text-xs space-y-1.5 bg-slate-50 p-3 rounded-xl border border-slate-200">
                      <div className="flex items-center gap-1.5 text-slate-700">
                        <MapPin className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                        <span className="truncate">{res.location || "Campus Facility"}</span>
                      </div>
                      <div className="flex items-center justify-between text-slate-500">
                        <span>Approval Gate:</span>
                        <span className="text-slate-800 font-medium">
                          {res.requires_approval ? "Manager Review Required" : "Instant Direct Booking"}
                        </span>
                      </div>
                      {Boolean(res.requires_permit) && (
                        <div className="flex items-center justify-between text-amber-700">
                          <span>Safety Permit:</span>
                          <span className="font-semibold">Required</span>
                        </div>
                      )}
                      {Boolean(res.requires_qualification) && (
                        <div className="flex items-center justify-between text-purple-700">
                          <span>Certification:</span>
                          <span className="font-semibold">Required</span>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                      <span className="text-xs font-semibold text-slate-700">
                        {res.hourly_rate_credits > 0 ? `${res.hourly_rate_credits} credits / hr` : "Free Tier / Subsidized"}
                      </span>
                      <Link to={`/resources/${res.id}`}>
                        <Button size="sm" variant="default" className="text-xs gap-1 h-8 bg-blue-600 hover:bg-blue-700 text-white cursor-pointer">
                          <span>Reserve Asset</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Button>
                      </Link>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {/* Simulated Demo Resources Grid (strictly in Demo Mode) */}
      {!isLiveMode && auth.isDemoMode && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {filteredDemo.map((res) => (
            <Card key={res.id} className="hover:border-slate-300 flex flex-col justify-between transition-colors opacity-95">
              <CardHeader className="p-4 sm:p-5">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <Badge variant={res.category === "LAB" ? "info" : res.category === "WORKSHOP" ? "warning" : "default"}>
                    {res.categoryLabel}
                  </Badge>
                  <Badge variant={res.status === "AVAILABLE" ? "success" : "secondary"}>
                    {res.status}
                  </Badge>
                </div>

                <CardTitle className="text-sm sm:text-base font-bold text-slate-900 leading-snug line-clamp-2" title={res.name}>
                  {res.name}
                </CardTitle>
                <CardDescription className="text-xs text-slate-500 mt-1 line-clamp-2">
                  {res.description}
                </CardDescription>
              </CardHeader>

              <CardContent className="p-4 sm:p-5 pt-0 space-y-3">
                <div className="text-xs space-y-1.5 bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                  <div className="flex items-center gap-1.5 text-slate-700">
                    <MapPin className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                    <span className="truncate">{res.location}, {res.building}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-500">
                    <span>Manager:</span>
                    <span className="text-slate-800 font-medium truncate ml-1">{res.leadManager}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                  <span className="text-xs font-semibold text-slate-700">{res.hourlyRate}</span>
                  <Link to={`/resources/${res.id}`}>
                    <Button size="sm" variant="default" className="text-xs gap-1 h-8">
                      <span>Reserve Asset</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Unauthenticated / No Active Membership State */}
      {!isLiveMode && !auth.isDemoMode && (
        <div className="p-12 text-center rounded-2xl bg-white border border-slate-200 space-y-3">
          <Building2 className="w-12 h-12 text-slate-300 mx-auto" />
          <h3 className="text-base font-bold text-slate-900">
            {auth.isAuthenticated
              ? "Institutional Membership Required"
              : "Sign In to Access Real-Time Asset Discovery"}
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {auth.isAuthenticated
              ? "Your account does not currently belong to an active institutional workspace. Please contact your institution administrator to enroll your account."
              : "Sign in with your institutional credentials to discover equipment, verify real-time availability, and schedule conflict-free reservations."}
          </p>
        </div>
      )}

      {/* Manager Add Asset Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4 animate-in zoom-in-95">
            <h3 className="text-lg font-bold text-slate-900">Register Institutional Facility Asset</h3>
            <p className="text-xs text-slate-500">
              Add new laboratory equipment or workshop machinery to {auth.activeMembership?.organization_name}.
            </p>

            {createError && (
              <div className="p-3 rounded-lg bg-red-50 text-red-800 text-xs border border-red-200">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateResource} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Equipment Name *</label>
                <Input
                  required
                  placeholder="e.g. Oxford Instruments Cryostat"
                  value={newResName}
                  onChange={(e) => setNewResName(e.target.value)}
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Category *</label>
                <select
                  value={newResCategory}
                  onChange={(e) => setNewResCategory(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800"
                >
                  <option value="lab_instrument">Laboratory Instrument</option>
                  <option value="workshop_tool">Workshop Tool</option>
                  <option value="computing_cluster">Computing Cluster</option>
                  <option value="testing_facility">Testing Facility / Cleanroom</option>
                  <option value="general_space">General Space</option>
                </select>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Location / Room Number</label>
                <Input
                  placeholder="e.g. Science Quad, Room 402"
                  value={newResLocation}
                  onChange={(e) => setNewResLocation(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Hourly Credits</label>
                  <Input
                    type="number"
                    min="0"
                    value={newResRate}
                    onChange={(e) => setNewResRate(Number(e.target.value))}
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Approval Gate</label>
                  <select
                    value={newResApproval ? "yes" : "no"}
                    onChange={(e) => setNewResApproval(e.target.value === "yes")}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800"
                  >
                    <option value="yes">Manager Approval Required</option>
                    <option value="no">Instant Booking</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setIsModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="default"
                  disabled={isSubmitting}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {isSubmitting ? "Creating..." : "Save Asset"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
