import * as React from "react"
import type {
  MembershipSummary,
  UserResponse,
} from "@/api/types"
import type { User as SupabaseUser } from "@supabase/supabase-js"

export type AuthMode = "real" | "demo" | "unauthenticated"

export interface AuthContextType {
  authMode: AuthMode
  isAuthenticated: boolean
  isDemoMode: boolean
  isLoading: boolean
  isSupabaseConfigured: boolean
  token: string | null

  // User Profile
  user: UserResponse | null
  supabaseUser: SupabaseUser | null
  userEmail: string | null
  userFullName: string | null

  // Multi-tenant Organization Scope
  memberships: MembershipSummary[]
  activeMembership: MembershipSummary | null
  activeOrganizationId: string | null
  activeRole: string

  // Authentication Operations
  signInWithPassword: (email: string, password: string) => Promise<void>
  signUpWithPassword: (email: string, password: string, fullName: string) => Promise<void>
  signOut: () => Promise<void>
  switchOrganization: (orgId: string) => void
  selectDemoPersona: (persona: string) => Promise<void>
  refreshProfile: () => Promise<void>

  // Diagnostic & Error States
  error: string | null
  clearError: () => void
}

export const AuthContext = React.createContext<AuthContextType | undefined>(undefined)
