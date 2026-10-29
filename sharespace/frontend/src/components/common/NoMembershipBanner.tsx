import { useAuth } from "@/context/useAuth"
import { AlertCircle, RefreshCw, LogOut } from "lucide-react"
import { useState } from "react"

export function NoMembershipBanner() {
  const auth = useAuth()
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Only display when user is authenticated but holds zero active memberships
  if (!auth.isAuthenticated || auth.isLoading || auth.memberships.length > 0) {
    return null
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      await auth.refreshProfile()
    } finally {
      setIsRefreshing(false)
    }
  }

  return (
    <div className="bg-amber-50 border-b border-amber-200 px-4 py-3 text-xs text-amber-900">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-bold text-amber-900">
              No Active Institutional Membership Found
            </p>
            <p className="text-[11px] text-amber-800 mt-0.5">
              You are signed in as <span className="font-semibold">{auth.userEmail}</span>, but an institutional administrator has not assigned you an active role in any organization.
              Contact your department administrator to request membership.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-center">
          <button
            type="button"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="px-2.5 py-1 bg-white border border-amber-300 rounded-md font-medium text-amber-900 hover:bg-amber-100/60 transition-colors flex items-center gap-1.5 cursor-pointer shadow-2xs"
          >
            <RefreshCw className={`w-3 h-3 ${isRefreshing ? "animate-spin" : ""}`} />
            <span>Check Membership</span>
          </button>
          <button
            type="button"
            onClick={() => void auth.signOut()}
            className="px-2.5 py-1 bg-white border border-slate-300 rounded-md font-medium text-slate-700 hover:bg-slate-50 transition-colors flex items-center gap-1.5 cursor-pointer shadow-2xs"
          >
            <LogOut className="w-3 h-3" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </div>
  )
}
