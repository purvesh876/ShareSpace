import * as React from "react"
import type { DemoRole, DemoUser } from "@/data/demoUsers"

export interface DemoRoleContextType {
  currentRole: DemoRole
  currentUser: DemoUser
  setRole: (role: DemoRole) => void
  isDemoMode: boolean
}

export const DemoRoleContext = React.createContext<DemoRoleContextType | undefined>(undefined)
