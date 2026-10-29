import { useState } from "react"
import { Link } from "react-router-dom"
import { useAuth } from "@/context/useAuth"
import { useDemoRole } from "@/context/useDemoRole"
import { DEMO_CATEGORIES, DEMO_RESOURCES, DEMO_BOOKINGS } from "@/data/demoData"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import {
  Search,
  Calendar,
  Clock,
  ArrowRight,
  ShieldCheck,
  Camera,
  CheckCircle2,
  AlertTriangle,
  Building2,
  Microscope,
  Hammer,
  Video,
  UserCheck,
} from "lucide-react"

export function Dashboard() {
  const auth = useAuth()
  const { currentRole, currentUser } = useDemoRole()
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("ALL")

  // Filter resources based on search and category
  const filteredResources = DEMO_RESOURCES.filter((res) => {
    const matchesSearch =
      res.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      res.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
      res.modelNumber.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesCategory = selectedCategory === "ALL" || res.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const getCategoryIcon = (id: string) => {
    switch (id) {
      case "LAB":
        return <Microscope className="w-4 h-4 text-blue-600" />
      case "WORKSHOP":
        return <Hammer className="w-4 h-4 text-amber-600" />
      case "ROOM":
        return <Building2 className="w-4 h-4 text-emerald-600" />
      case "AV":
        return <Video className="w-4 h-4 text-purple-600" />
      default:
        return <Microscope className="w-4 h-4 text-blue-600" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Welcome Panel - Full width, clean institutional layout */}
      <div className="w-full rounded-2xl bg-white border border-slate-200 p-5 sm:p-6 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
          <div className="space-y-2.5 max-w-3xl">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-800 border border-blue-200">
              <UserCheck className="w-3.5 h-3.5 text-blue-600" />
              <span>Active Demonstration Persona: {currentUser.roleLabel}</span>
            </div>

            <h2 className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-900 tracking-tight">
              Welcome, {currentUser.name}
            </h2>

            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
              {currentRole === "student" &&
                "Reserve specialized laboratory instruments, fabrication equipment, and seminar spaces. Mandatory photo check-ins are required upon arrival."}
              {currentRole === "manager" &&
                "Manage facility assets, review incoming reservation requests, and verify equipment return checklists and condition photographs."}
              {currentRole === "admin" &&
                "Oversee institutional resource allocation, monitor tenant isolation, enforce fair-use quotas, and review dispute escalations."}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 sm:gap-3 flex-shrink-0">
            <Link to="/resources">
              <Button size="sm" className="gap-2">
                <Search className="w-4 h-4" />
                Browse All Equipment
              </Button>
            </Link>
            {currentRole === "student" && (
              <Link to="/handover">
                <Button variant="outline" size="sm" className="gap-2">
                  <Camera className="w-4 h-4 text-blue-600" />
                  Upcoming Check-in Gate
                </Button>
              </Link>
            )}
            {currentRole === "manager" && (
              <Link to="/manage/approvals">
                <Button variant="outline" size="sm" className="gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  Review 3 Pending Bookings
                </Button>
              </Link>
            )}
            {currentRole === "admin" && (
              <Link to="/admin/audit-logs">
                <Button variant="outline" size="sm" className="gap-2">
                  <span>View Audit Trail</span>
                </Button>
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Role-Specific Action Reminder */}
      {currentRole === "student" && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-sm">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber-100 border border-amber-200 flex items-center justify-center text-amber-700 flex-shrink-0">
              <Camera className="w-5 h-5" />
            </div>
            <div>
              <p className="font-bold text-amber-900 text-sm">
                Mandatory Check-In Window Starts in 1h 45m
              </p>
              <p className="text-xs text-amber-800">
                Leica SP8 Confocal Laser Microscope (Room 312). You must upload an initial condition photograph before equipment activation.
              </p>
            </div>
          </div>
          <Link to="/handover">
            <Button size="sm" variant="outline" className="border-amber-300 text-amber-900 hover:bg-amber-100 text-xs whitespace-nowrap bg-white">
              Open Check-in Gate
            </Button>
          </Link>
        </div>
      )}

      {currentRole === "manager" && (
        <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-sm">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-100 border border-blue-200 flex items-center justify-center text-blue-700 flex-shrink-0">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <p className="font-bold text-blue-950 text-sm">
                3 Resource Reservations Awaiting Manager Approval
              </p>
              <p className="text-xs text-blue-800">
                Form 3B+ 3D Printer and FTIR Spectrometer requests require safety eligibility sign-off.
              </p>
            </div>
          </div>
          <Link to="/manage/approvals">
            <Button size="sm" variant="default" className="text-xs whitespace-nowrap">
              Review Requests
            </Button>
          </Link>
        </div>
      )}

      {currentRole === "admin" && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-sm">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-red-100 border border-red-200 flex items-center justify-center text-red-700 flex-shrink-0">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <p className="font-bold text-red-950 text-sm">
                1 Incident Damage Dispute Escalated to Administration
              </p>
              <p className="text-xs text-red-800">
                CNC Milling Center tool collision report requires human administrative review under Fair-Use Article 4.
              </p>
            </div>
          </div>
          <Link to="/admin/disputes">
            <Button size="sm" variant="destructive" className="text-xs whitespace-nowrap">
              Inspect Dispute Record
            </Button>
          </Link>
        </div>
      )}

      {/* Institutional Metrics Grid (Responsive 1/2/4 columns, aligned height) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-col justify-between space-y-2">
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500 font-medium">Weekly Quota</span>
              {auth.isDemoMode && (
                <span className="text-[10px] uppercase font-bold text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">Demo Data</span>
              )}
            </div>
            <p className="text-2xl font-bold text-slate-900">
              {currentRole === "student" ? "14.5 / 20 hrs" : "Unlimited"}
            </p>
          </div>
          <span className="text-xs text-emerald-700 flex items-center gap-1 font-medium pt-1 border-t border-slate-100">
            <ShieldCheck className="w-3.5 h-3.5" /> Anti-hoarding limit active
          </span>
        </div>

        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-col justify-between space-y-2">
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500 font-medium">Active Bookings</span>
              {auth.isDemoMode && (
                <span className="text-[10px] uppercase font-bold text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">Demo Data</span>
              )}
            </div>
            <p className="text-2xl font-bold text-slate-900">
              {currentRole === "student" ? "2 Upcoming" : "18 Across Suites"}
            </p>
          </div>
          <span className="text-xs text-slate-500 flex items-center gap-1 pt-1 border-t border-slate-100">
            <Clock className="w-3.5 h-3.5 text-slate-400" /> Range exclusion locked
          </span>
        </div>

        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-col justify-between space-y-2">
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500 font-medium">Safety Permits</span>
              {auth.isDemoMode && (
                <span className="text-[10px] uppercase font-bold text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">Demo Data</span>
              )}
            </div>
            <p className="text-2xl font-bold text-slate-900">
              {currentUser.qualifications.length} Verified
            </p>
          </div>
          <span className="text-xs text-blue-700 font-medium flex items-center gap-1 pt-1 border-t border-slate-100">
            <UserCheck className="w-3.5 h-3.5 text-blue-600" /> Laser & Biosafety L2
          </span>
        </div>

        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-col justify-between space-y-2">
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500 font-medium">Evidence Audit</span>
              {auth.isDemoMode && (
                <span className="text-[10px] uppercase font-bold text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">Demo Data</span>
              )}
            </div>
            <p className="text-2xl font-bold text-emerald-700">100% Compliant</p>
          </div>
          <span className="text-xs text-slate-500 flex items-center gap-1 pt-1 border-t border-slate-100">
            <Camera className="w-3.5 h-3.5 text-slate-400" /> Photo handovers verified
          </span>
        </div>
      </div>

      {/* Resource Discovery Section */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-lg font-bold text-slate-900 tracking-tight">Institutional Resource Catalog</h3>
            <p className="text-xs text-slate-500">
              High-value shared facilities with enforced reservation integrity.
            </p>
          </div>
          <Link to="/resources" className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1">
            <span>Explore all campus assets</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Search Bar & Category Filter Chips - Responsive layout */}
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
          <div className="w-full lg:max-w-md">
            <Input
              type="text"
              placeholder="Search equipment, models, rooms..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              icon={<Search className="w-4 h-4 text-slate-400" />}
            />
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none max-w-full">
            {DEMO_CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
                  selectedCategory === cat.id
                    ? "bg-blue-600 text-white font-semibold shadow-xs"
                    : "bg-white border border-slate-300 text-slate-700 hover:bg-slate-50"
                }`}
              >
                {getCategoryIcon(cat.id)}
                <span>{cat.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Resources Responsive Grid: 1 col (mobile), 2 cols (tablet), 3 cols (desktop), 4 cols (wide desktop) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {filteredResources.slice(0, 8).map((res) => (
            <Card key={res.id} className="hover:border-slate-300 flex flex-col justify-between transition-colors">
              <CardHeader className="p-4 sm:p-5">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <Badge variant={res.category === "LAB" ? "info" : res.category === "WORKSHOP" ? "warning" : "default"}>
                    {res.categoryLabel}
                  </Badge>
                  <Badge variant={res.status === "AVAILABLE" ? "success" : res.status === "RESERVED" ? "secondary" : "destructive"}>
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
                <div className="text-xs space-y-1.5 bg-slate-50 p-2.5 sm:p-3 rounded-lg border border-slate-200">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Location:</span>
                    <span className="font-medium text-slate-800 truncate ml-1">{res.location}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Model Tag:</span>
                    <span className="font-mono text-slate-700 truncate ml-1">{res.modelNumber}</span>
                  </div>
                  {res.requiredQualification && (
                    <div className="flex items-center justify-between text-amber-800">
                      <span className="flex-shrink-0">Permit:</span>
                      <span className="font-semibold truncate ml-1">{res.requiredQualification}</span>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                  <span className="text-xs font-semibold text-slate-700">{res.hourlyRate}</span>
                  <Link to={`/resources/${res.id}`}>
                    <Button size="sm" variant="default" className="text-xs gap-1 h-8">
                      <span>Details & Reserve</span>
                      <ArrowRight className="w-3 h-3" />
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Recent Reservations Table Preview - Full width with controlled horizontal scroll */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between p-4 sm:p-6 pb-3">
          <div>
            <CardTitle className="text-base sm:text-lg">Recent & Upcoming Institutional Reservations</CardTitle>
            <CardDescription className="text-xs sm:text-sm">
              Temporal scheduling managed under atomic range exclusion constraints.
            </CardDescription>
          </div>
          <Link to="/bookings">
            <Button variant="ghost" size="sm" className="text-xs gap-1 text-slate-600 hover:text-slate-900">
              <span>View All</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent className="p-4 sm:p-6 pt-0">
          <div className="overflow-x-auto rounded-lg border border-slate-200">
            <table className="w-full min-w-[680px] text-xs text-left text-slate-700">
              <thead className="bg-slate-50 border-b border-slate-200 text-[11px] uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="py-3 px-4 font-semibold">Booking ID</th>
                  <th className="py-3 px-4 font-semibold">Resource</th>
                  <th className="py-3 px-4 font-semibold">Reserved By</th>
                  <th className="py-3 px-4 font-semibold">Window</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Handover Evidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {DEMO_BOOKINGS.map((bk) => (
                  <tr key={bk.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 font-mono text-slate-600 font-medium">{bk.id}</td>
                    <td className="py-3 px-4 font-semibold text-slate-900">{bk.resourceName}</td>
                    <td className="py-3 px-4 text-slate-700">{bk.userName}</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 text-slate-600">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        {bk.date}, {bk.startTime} - {bk.endTime}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <Badge
                        variant={
                          bk.status === "APPROVED"
                            ? "success"
                            : bk.status === "REQUESTED"
                            ? "warning"
                            : bk.status === "COMPLETED"
                            ? "secondary"
                            : "destructive"
                        }
                      >
                        {bk.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-4">
                      {bk.hasCheckinPhotos && bk.hasReturnPhotos ? (
                        <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Both Photos Verified
                        </span>
                      ) : bk.status === "APPROVED" ? (
                        <span className="inline-flex items-center gap-1 text-amber-800 font-medium">
                          <Clock className="w-3.5 h-3.5 text-amber-600" /> Check-in Photo Required
                        </span>
                      ) : (
                        <span className="text-slate-400">Pending Gate</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
