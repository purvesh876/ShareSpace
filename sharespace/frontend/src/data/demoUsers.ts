export type DemoRole = "student" | "manager" | "admin"

export interface DemoUser {
  id: string
  name: string
  email?: string
  role: DemoRole
  roleLabel: string
  title: string
  department: string
  organization: string
  avatarInitials: string
  qualifications: string[]
  pendingActionCount: number
}

export const DEMO_USERS: Record<DemoRole, DemoUser> = {
  student: {
    id: "demo-user-student-01",
    name: "Alex Chen",
    role: "student",
    roleLabel: "Student / Researcher",
    title: "Undergraduate Researcher",
    department: "Dept. of Biomedical Engineering",
    organization: "Apex Institute of Technology",
    avatarInitials: "AC",
    qualifications: ["LASER_SAFETY_LEVEL_1", "BIOSAFETY_LEVEL_2"],
    pendingActionCount: 1, // Mandatory Check-in pending
  },
  manager: {
    id: "demo-user-manager-02",
    name: "Dr. Sarah Miller",
    role: "manager",
    roleLabel: "Resource Owner / Manager",
    title: "Lead Facility Manager",
    department: "Microscopy & Fabrication Suites",
    organization: "Apex Institute of Technology",
    avatarInitials: "SM",
    qualifications: ["FACILITY_DIRECTOR", "EQUIPMENT_AUDITOR"],
    pendingActionCount: 3, // 3 approvals pending
  },
  admin: {
    id: "demo-user-admin-03",
    name: "Dean Marcus Vance",
    role: "admin",
    roleLabel: "System Administrator",
    title: "Director of Research Facilities",
    department: "Campus Operational Infrastructure",
    organization: "Apex Institute of Technology",
    avatarInitials: "MV",
    qualifications: ["CAMPUS_SUPERADMIN", "TENANT_CONTROLLER"],
    pendingActionCount: 1, // 1 dispute review
  },
}
