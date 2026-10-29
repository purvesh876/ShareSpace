import * as React from "react"
import { useAuth } from "@/context/useAuth"
import { Dialog } from "@/components/ui/Dialog"
import { LogIn, UserPlus, Sparkles, AlertCircle, CheckCircle2 } from "lucide-react"

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
}

export function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const auth = useAuth()
  const [tab, setTab] = React.useState<"signin" | "signup" | "demo">("signin")
  const [email, setEmail] = React.useState("")
  const [password, setPassword] = React.useState("")
  const [fullName, setFullName] = React.useState("")
  const [localError, setLocalError] = React.useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const [successMessage, setSuccessMessage] = React.useState<string | null>(null)

  const handleClose = React.useCallback(() => {
    setLocalError(null)
    setSuccessMessage(null)
    auth.clearError()
    onClose()
  }, [auth, onClose])

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError(null)
    setIsSubmitting(true)
    try {
      await auth.signInWithPassword(email, password)
      setSuccessMessage("Authenticated successfully!")
      setTimeout(() => {
        handleClose()
      }, 700)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to sign in"
      setLocalError(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError(null)
    setIsSubmitting(true)
    try {
      await auth.signUpWithPassword(email, password, fullName)
      setSuccessMessage("Account created! Please check your email for confirmation if required.")
      setTimeout(() => {
        handleClose()
      }, 1500)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to register"
      setLocalError(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSelectDemo = async (persona: string) => {
    setLocalError(null)
    setIsSubmitting(true)
    try {
      await auth.selectDemoPersona(persona)
      setSuccessMessage(`Switched to demo persona: ${persona}`)
      setTimeout(() => {
        handleClose()
      }, 600)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to select persona"
      setLocalError(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog
      isOpen={isOpen}
      onClose={handleClose}
      title="Institutional Authentication & Access"
      description="Connect to your institution's verified Supabase account or development persona."
    >
      <div className="space-y-4 text-sm">
        {/* Mode Tabs */}
        <div className="flex border-b border-slate-200">
          <button
            type="button"
            onClick={() => {
              setTab("signin")
              setLocalError(null)
            }}
            className={`flex-1 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
              tab === "signin"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setTab("signup")
              setLocalError(null)
            }}
            className={`flex-1 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
              tab === "signup"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            Create Account
          </button>
          {(import.meta.env.DEV || import.meta.env.VITE_ENABLE_DEMO_PERSONAS === "true") && (
            <button
              type="button"
              onClick={() => {
                setTab("demo")
                setLocalError(null)
              }}
              className={`flex-1 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center justify-center gap-1 ${
                tab === "demo"
                  ? "border-amber-600 text-amber-700"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <Sparkles className="w-3 h-3 text-amber-500" />
              Dev Personas
            </button>
          )}
        </div>

        {/* Supabase unconfigured warning if in signin/signup */}
        {!auth.isSupabaseConfigured && tab !== "demo" && (
          <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 space-y-1">
            <div className="flex items-center gap-1.5 font-bold">
              <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
              Supabase Auth Client Unconfigured
            </div>
            <p className="text-[11px] text-amber-800 leading-relaxed">
              Frontend environment variables <code className="bg-amber-100 px-1 py-0.5 rounded">VITE_SUPABASE_URL</code> and{" "}
              <code className="bg-amber-100 px-1 py-0.5 rounded">VITE_SUPABASE_ANON_KEY</code> have not been set in{" "}
              <code className="bg-amber-100 px-1 py-0.5 rounded">frontend/.env</code>. You can test immediately using local Dev Personas.
            </p>
          </div>
        )}

        {/* Error notification */}
        {(localError || auth.error) && (
          <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-800 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
            <span>{localError || auth.error}</span>
          </div>
        )}

        {/* Success message */}
        {successMessage && (
          <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Sign In Form */}
        {tab === "signin" && (
          <form onSubmit={handleSignIn} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Institutional Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="researcher@apex.edu"
                className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-600"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-600"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !auth.isSupabaseConfigured}
              className="w-full py-2 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-semibold transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-xs"
            >
              <LogIn className="w-3.5 h-3.5" />
              {isSubmitting ? "Authenticating..." : "Sign In to ShareSpace"}
            </button>
          </form>
        )}

        {/* Sign Up Form */}
        {tab === "signup" && (
          <form onSubmit={handleSignUp} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Full Name
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Dr. Jordan Hayes"
                className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-600"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Institutional Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="jordan.hayes@apex.edu"
                className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-600"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Password
              </label>
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 6 characters"
                className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-600"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !auth.isSupabaseConfigured}
              className="w-full py-2 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-semibold transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-xs"
            >
              <UserPlus className="w-3.5 h-3.5" />
              {isSubmitting ? "Registering..." : "Create Verified Account"}
            </button>
          </form>
        )}

        {/* Dev Personas Tab */}
        {tab === "demo" && (
          <div className="space-y-2.5">
            <p className="text-xs text-slate-500">
              Select an institutional persona. Generates cryptographic test JWT verified by backend.
            </p>
            <div className="grid grid-cols-2 gap-2">
              {[
                { persona: "student", label: "Student", desc: "Maya Lin (Robotics)" },
                { persona: "manager", label: "Lab Manager", desc: "Dr. Aris Vance (Optics)" },
                { persona: "admin", label: "Dean / Admin", desc: "Dean Sarah Connor (Eng)" },
                { persona: "researcher", label: "Researcher", desc: "Dr. Jordan Hayes (Physics)" },
                { persona: "technician", label: "Technician", desc: "Alex Mercer (FabLab)" },
                { persona: "auditor", label: "Compliance Auditor", desc: "Elena Rostova (Compliance)" },
              ].map(({ persona, label, desc }) => (
                <button
                  key={persona}
                  type="button"
                  onClick={() => handleSelectDemo(persona)}
                  disabled={isSubmitting}
                  className="p-2.5 text-left rounded-lg border border-slate-200 hover:border-blue-400 hover:bg-blue-50/50 transition-colors cursor-pointer group"
                >
                  <p className="font-semibold text-xs text-slate-900 group-hover:text-blue-700">
                    {label}
                  </p>
                  <p className="text-[11px] text-slate-500 truncate">{desc}</p>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </Dialog>
  )
}
