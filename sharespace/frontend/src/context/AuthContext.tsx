import * as React from "react"
import { supabase, isSupabaseConfigured } from "@/lib/supabase"
import { apiClient } from "@/api/client"
import type {
  MembershipSummary,
  UserProfileResponse,
  UserResponse,
} from "@/api/types"
import type { Session, User as SupabaseUser } from "@supabase/supabase-js"
import { AuthContext, type AuthMode } from "./authContextDef"

const ACTIVE_ORG_STORAGE_KEY = "sharespace_active_org_id"
const DEMO_PERSONA_STORAGE_KEY = "sharespace_demo_persona"
const EXPLICIT_DEMO_STORAGE_KEY = "sharespace_explicit_demo_mode"

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [authMode, setAuthMode] = React.useState<AuthMode>("unauthenticated")
  const [token, setToken] = React.useState<string | null>(null)
  const tokenRef = React.useRef<string | null>(null)
  const [supabaseUser, setSupabaseUser] = React.useState<SupabaseUser | null>(null)
  const [user, setUser] = React.useState<UserResponse | null>(null)
  const [memberships, setMemberships] = React.useState<MembershipSummary[]>([])
  const [activeMembership, setActiveMembership] = React.useState<MembershipSummary | null>(null)
  const [isLoading, setIsLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  // Configure API client token provider
  React.useEffect(() => {
    apiClient.setTokenProvider(() => tokenRef.current)
    apiClient.setOnUnauthorized(() => {
      // Clear session when backend returns 401
      tokenRef.current = null
      setToken(null)
      setUser(null)
      setMemberships([])
      setActiveMembership(null)
      setAuthMode("unauthenticated")
    })
  }, [])

  // Resolve active organization membership
  const selectMembership = React.useCallback(
    (allMemberships: MembershipSummary[], preferredOrgId?: string | null) => {
      if (!allMemberships || allMemberships.length === 0) {
        setActiveMembership(null)
        return
      }

      if (preferredOrgId) {
        const found = allMemberships.find((m) => m.organization_id === preferredOrgId)
        if (found) {
          setActiveMembership(found)
          try {
            localStorage.setItem(ACTIVE_ORG_STORAGE_KEY, found.organization_id)
          } catch {
            // Ignore storage errors
          }
          return
        }
      }

      // Default to first membership
      const defaultMem = allMemberships[0]
      setActiveMembership(defaultMem)
      try {
        localStorage.setItem(ACTIVE_ORG_STORAGE_KEY, defaultMem.organization_id)
      } catch {
        // Ignore storage errors
      }
    },
    []
  )

  // Fetch verified profile and institutional memberships from backend
  const fetchBackendProfile = React.useCallback(
    async (accessToken?: string): Promise<UserProfileResponse | null> => {
      try {
        const effectiveToken = accessToken || tokenRef.current || undefined
        const profile = await apiClient.getMyProfile({ token: effectiveToken })
        setUser(profile.user)
        setMemberships(profile.memberships)

        const savedOrg = localStorage.getItem(ACTIVE_ORG_STORAGE_KEY)
        selectMembership(profile.memberships, savedOrg)
        return profile
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Failed to load profile"
        console.warn("Backend profile resolution error:", message)
        setError(message)
        return null
      }
    },
    [selectMembership]
  )

  // Initialize session lifecycle on mount
  React.useEffect(() => {
    let isMounted = true

    async function initSession() {
      setIsLoading(true)
      setError(null)

      // 1. Check for real Supabase session if configured
      if (isSupabaseConfigured && supabase) {
        try {
          const {
            data: { session },
          } = await supabase.auth.getSession()

          if (session?.access_token && isMounted) {
            tokenRef.current = session.access_token
            setToken(session.access_token)
            setSupabaseUser(session.user)
            setAuthMode("real")
            // Ensure demo keys are cleared when real session is restored
            try {
              localStorage.removeItem(EXPLICIT_DEMO_STORAGE_KEY)
              localStorage.removeItem(DEMO_PERSONA_STORAGE_KEY)
            } catch {
              // Ignore
            }
            await fetchBackendProfile(session.access_token)
            setIsLoading(false)
            return
          }
        } catch (err) {
          console.warn("Error restoring Supabase session:", err)
        }
      }

      // 2. ONLY activate demo mode if explicitly chosen previously by user
      const isDemoAllowed =
        import.meta.env.DEV || import.meta.env.VITE_ENABLE_DEMO_PERSONAS === "true"
      const isExplicitDemo =
        localStorage.getItem(EXPLICIT_DEMO_STORAGE_KEY) === "true"

      if (isDemoAllowed && isExplicitDemo) {
        const savedPersona = localStorage.getItem(DEMO_PERSONA_STORAGE_KEY)
        if (savedPersona) {
          try {
            const demoRes = await apiClient.getDemoToken(savedPersona)
            if (isMounted) {
              tokenRef.current = demoRes.access_token
              setToken(demoRes.access_token)
              setAuthMode("demo")
              await fetchBackendProfile(demoRes.access_token)
              setIsLoading(false)
              return
            }
          } catch (err) {
            console.warn("Explicit demo token initialization error:", err)
          }
        }
      }

      // 3. Default to unauthenticated state (never silently fallback to demo personas)
      if (isMounted) {
        setAuthMode("unauthenticated")
        setIsLoading(false)
      }
    }

    void initSession()

    // 4. Listen to Supabase auth state changes
    if (isSupabaseConfigured && supabase) {
      const {
        data: { subscription },
      } = supabase.auth.onAuthStateChange(async (event, session: Session | null) => {
        if (!isMounted) return

        if (session?.access_token) {
          tokenRef.current = session.access_token
          setToken(session.access_token)
          setSupabaseUser(session.user)
          setAuthMode("real")
          setError(null)
          try {
            localStorage.removeItem(EXPLICIT_DEMO_STORAGE_KEY)
            localStorage.removeItem(DEMO_PERSONA_STORAGE_KEY)
          } catch {
            // Ignore
          }
          await fetchBackendProfile(session.access_token)
        } else if (event === "SIGNED_OUT") {
          tokenRef.current = null
          setToken(null)
          setSupabaseUser(null)
          setUser(null)
          setMemberships([])
          setActiveMembership(null)
          setAuthMode("unauthenticated")
          try {
            localStorage.removeItem(ACTIVE_ORG_STORAGE_KEY)
            localStorage.removeItem(EXPLICIT_DEMO_STORAGE_KEY)
            localStorage.removeItem(DEMO_PERSONA_STORAGE_KEY)
          } catch {
            // Ignore
          }
        }
      })

      return () => {
        isMounted = false
        subscription.unsubscribe()
      }
    }

    return () => {
      isMounted = false
    }
  }, [fetchBackendProfile])

  // Sign In with Supabase
  const signInWithPassword = async (email: string, password: string) => {
    if (!isSupabaseConfigured || !supabase) {
      throw new Error(
        "Supabase is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY."
      )
    }
    setError(null)
    const { data, error: authError } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    if (authError) {
      setError(authError.message)
      throw authError
    }
    if (data.session) {
      tokenRef.current = data.session.access_token
      setToken(data.session.access_token)
      setSupabaseUser(data.session.user)
      setAuthMode("real")
      await fetchBackendProfile(data.session.access_token)
    }
  }

  // Sign Up with Supabase
  const signUpWithPassword = async (email: string, password: string, fullName: string) => {
    if (!isSupabaseConfigured || !supabase) {
      throw new Error("Supabase is not configured.")
    }
    setError(null)
    const { data, error: authError } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
        },
      },
    })
    if (authError) {
      setError(authError.message)
      throw authError
    }
    if (data.session) {
      tokenRef.current = data.session.access_token
      setToken(data.session.access_token)
      setSupabaseUser(data.session.user)
      setAuthMode("real")
      try {
        localStorage.removeItem(EXPLICIT_DEMO_STORAGE_KEY)
        localStorage.removeItem(DEMO_PERSONA_STORAGE_KEY)
      } catch {
        // Ignore
      }
      await fetchBackendProfile(data.session.access_token)
    }
  }

  // Sign Out
  const signOut = async () => {
    if (isSupabaseConfigured && supabase) {
      try {
        await supabase.auth.signOut()
      } catch (err) {
        console.warn("Supabase signOut error:", err)
      }
    }
    tokenRef.current = null
    setToken(null)
    setSupabaseUser(null)
    setUser(null)
    setMemberships([])
    setActiveMembership(null)
    setAuthMode("unauthenticated")
    try {
      localStorage.removeItem(ACTIVE_ORG_STORAGE_KEY)
      localStorage.removeItem(DEMO_PERSONA_STORAGE_KEY)
      localStorage.removeItem(EXPLICIT_DEMO_STORAGE_KEY)
      localStorage.removeItem("sharespace_demo_role")
    } catch {
      // Ignore
    }
  }

  // Switch Active Organization
  const switchOrganization = (orgId: string) => {
    selectMembership(memberships, orgId)
  }

  // Select Demo Persona (Dev Only)
  const selectDemoPersona = async (persona: string) => {
    const isDemoAllowed =
      import.meta.env.DEV || import.meta.env.VITE_ENABLE_DEMO_PERSONAS === "true"
    if (!isDemoAllowed) {
      throw new Error("Demo persona generation is disabled in production environments.")
    }
    setError(null)
    setIsLoading(true)
    try {
      const demoRes = await apiClient.getDemoToken(persona)
      tokenRef.current = demoRes.access_token
      setToken(demoRes.access_token)
      setAuthMode("demo")
      try {
        localStorage.setItem(EXPLICIT_DEMO_STORAGE_KEY, "true")
        localStorage.setItem(DEMO_PERSONA_STORAGE_KEY, persona)
      } catch {
        // Ignore
      }
      await fetchBackendProfile(demoRes.access_token)
    } finally {
      setIsLoading(false)
    }
  }

  const refreshProfile = async () => {
    const currentToken = tokenRef.current || token
    if (currentToken) {
      await fetchBackendProfile(currentToken)
    }
  }

  const clearError = () => setError(null)

  const activeRole = activeMembership?.role || "guest"
  const activeOrganizationId = activeMembership?.organization_id || null
  const userEmail = user?.email || supabaseUser?.email || null
  const userFullName = user?.full_name || supabaseUser?.user_metadata?.full_name || userEmail || "User"

  return (
    <AuthContext.Provider
      value={{
        authMode,
        isAuthenticated: authMode !== "unauthenticated" && Boolean(token),
        isDemoMode: authMode === "demo",
        isLoading,
        isSupabaseConfigured,
        token,
        user,
        supabaseUser,
        userEmail,
        userFullName,
        memberships,
        activeMembership,
        activeOrganizationId,
        activeRole,
        signInWithPassword,
        signUpWithPassword,
        signOut,
        switchOrganization,
        selectDemoPersona,
        refreshProfile,
        error,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
