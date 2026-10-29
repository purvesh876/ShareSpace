import { useState, useEffect, useCallback } from "react"
import { apiClient } from "@/api/client"
import type { HealthResponse, ReadinessResponse } from "@/api/types"
import { Activity, Database, CheckCircle2, AlertCircle, ShieldCheck, Cpu, Building2, Camera } from "lucide-react"

const CURRENT_YEAR = new Date().getFullYear()

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const checkBackendStatus = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const diag = await apiClient.getDiagnosticStatus()
      setHealth(diag.health)
      setReadiness(diag.readiness)
    } catch (err) {
      const e = err as Error
      setError(e.message || "Failed to contact backend API.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let ignore = false
    const runCheck = async () => {
      try {
        const diag = await apiClient.getDiagnosticStatus()
        if (ignore) return
        setHealth(diag.health)
        setReadiness(diag.readiness)
      } catch {
        // Ignored on initial mount
      }
    }
    void runCheck()
    return () => {
      ignore = true
    }
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation */}
      <header className="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
              S
            </div>
            <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              ShareSpace
            </span>
          </div>

          <div className="flex items-center space-x-3">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Step 2 Foundation Active
            </span>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 flex-1 flex flex-col justify-center">
        <div className="text-center max-w-3xl mx-auto space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            Institutional Resource Sharing Platform
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
            Unlock Underused{" "}
            <span className="bg-gradient-to-r from-indigo-400 via-sky-300 to-emerald-400 bg-clip-text text-transparent">
              Equipment & Spaces
            </span>
          </h1>

          <p className="text-lg text-slate-400 leading-relaxed">
            A reliable, multi-tenant sharing platform for colleges, research laboratories, and campus communities.
            Built with strict booking integrity, mandatory photo verification, and transparent fair-use policies.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <button
              onClick={() => void checkBackendStatus()}
              disabled={loading}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-medium text-sm transition-all shadow-lg shadow-indigo-600/30 disabled:opacity-50 cursor-pointer"
            >
              <Activity className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              {loading ? "Checking Status..." : "Ping Backend Health & Ready"}
            </button>
          </div>
        </div>

        {/* Live Diagnostics Card */}
        <div className="mt-16 max-w-2xl mx-auto w-full bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-indigo-400" />
              <h2 className="text-base font-semibold text-white">System Diagnostics (Live)</h2>
            </div>
            <span className="text-xs text-slate-400 font-mono">
              Target: {apiClient.getBaseUrl()}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Health Status */}
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">FastAPI API Service</span>
                {health?.status === "ok" ? (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Healthy
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-400">
                    <AlertCircle className="w-3.5 h-3.5" /> Waiting for Server
                  </span>
                )}
              </div>
              <p className="text-xs font-mono text-slate-300">
                {health ? `${health.app_name} v${health.version} (${health.environment})` : "Start backend on :8000"}
              </p>
            </div>

            {/* Readiness Status */}
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">PostgreSQL Database</span>
                {readiness?.status === "ready" ? (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Connected
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-slate-400">
                    <Database className="w-3.5 h-3.5" /> Not Configured
                  </span>
                )}
              </div>
              <p className="text-xs font-mono text-slate-300">
                {readiness?.database ? `DB Status: ${readiness.database}` : "Awaiting DB setup in Step 5"}
              </p>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-300">
              {error}
            </div>
          )}
        </div>

        {/* Feature Highlights Grid */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-900/40 border border-slate-800/60 rounded-2xl p-6 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Building2 className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white">Laboratories & Spaces</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Centrally list microscopes, 3D printers, seminar halls, and high-performance computing clusters with verified availability.
            </p>
          </div>

          <div className="bg-slate-900/40 border border-slate-800/60 rounded-2xl p-6 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white">Concurrency & Integrity</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              PostgreSQL exclusion constraints (`btree_gist`) physically prevent overlapping reservations at the storage layer.
            </p>
          </div>

          <div className="bg-slate-900/40 border border-slate-800/60 rounded-2xl p-6 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Camera className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white">Mandatory Handover Photos</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Check-in and return state transitions enforce written checklists and private photographic evidence.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        ShareSpace © {CURRENT_YEAR} — Step 2 Foundations Initialized. Ready for Step 3 Design System.
      </footer>
    </div>
  )
}
