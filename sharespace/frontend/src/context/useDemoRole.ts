import * as React from "react"
import { DemoRoleContext } from "./demoRoleContextDef"

export function useDemoRole() {
  const context = React.useContext(DemoRoleContext)
  if (!context) {
    throw new Error("useDemoRole must be used within a DemoRoleProvider")
  }
  return context
}
