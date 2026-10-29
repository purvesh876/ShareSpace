import * as React from "react"
import { DEMO_USERS, type DemoRole, type DemoUser } from "@/data/demoUsers"
import { DemoRoleContext } from "./demoRoleContextDef"
import { useAuth } from "./useAuth"

const DEMO_ROLE_STORAGE_KEY = "sharespace_demo_role"

function normalizeRole(roleString: string): DemoRole {
  const lower = roleString.toLowerCase()
  if (lower === "admin" || lower === "auditor") return "admin"
  if (lower === "lab_manager" || lower === "manager" || lower === "technician") return "manager"
  return "student"
}

export function DemoRoleProvider({ children }: { children: React.ReactNode }) {
  const auth = useAuth()

  const [demoRole, setDemoRole] = React.useState<DemoRole>(() => {
    try {
      const saved = localStorage.getItem(DEMO_ROLE_STORAGE_KEY) as DemoRole
      if (saved && (saved === "student" || saved === "manager" || saved === "admin")) {
        return saved
      }
    } catch {
      // Fallback
    }
    return "student"
  })

  const setRole = (role: DemoRole) => {
    if (auth.isDemoMode) {
      setDemoRole(role)
      try {
        localStorage.setItem(DEMO_ROLE_STORAGE_KEY, role)
      } catch {
        // Ignore
      }
      void auth.selectDemoPersona(role)
    } else {
      console.warn("Cannot change role locally in real Supabase session. Role is bound to institutional membership.")
    }
  }

  // Derive currentRole & currentUser from real auth or demo state
  let currentRole: DemoRole = demoRole
  let currentUser: DemoUser = DEMO_USERS[demoRole]

  if (auth.authMode === "real") {
    currentRole = normalizeRole(auth.activeRole)
    const initials =
      (auth.userFullName || "User")
        .split(" ")
        .filter(Boolean)
        .map((s) => s[0])
        .join("")
        .toUpperCase()
        .slice(0, 2) || "U"

    currentUser = {
      id: auth.user?.id || auth.supabaseUser?.id || "real-user",
      name: auth.userFullName || "Institutional Member",
      email: auth.userEmail || "",
      role: currentRole,
      roleLabel: auth.activeMembership
        ? `${auth.activeMembership.role.replace("_", " ").toUpperCase()}`
        : "Unassigned Member",
      title: auth.activeMembership?.role || "Campus Member",
      department: auth.activeMembership?.department || "Institutional Resource Member",
      avatarInitials: initials,
      organization: auth.activeMembership?.organization_name || "Apex Institute of Technology",
      qualifications: [],
      pendingActionCount: 0,
    }
  } else if (auth.authMode === "demo") {
    currentUser = DEMO_USERS[demoRole] || DEMO_USERS.student
  } else {
    currentUser = {
      id: "unauthenticated",
      name: "Guest Visitor",
      email: "",
      role: "student",
      roleLabel: "Guest",
      title: "Visitor",
      department: "Public Discovery",
      avatarInitials: "G",
      organization: "ShareSpace Network",
      qualifications: [],
      pendingActionCount: 0,
    }
  }

  return (
    <DemoRoleContext.Provider
      value={{
        currentRole,
        currentUser,
        setRole,
        isDemoMode: auth.isDemoMode,
      }}
    >
      {children}
    </DemoRoleContext.Provider>
  )
}

