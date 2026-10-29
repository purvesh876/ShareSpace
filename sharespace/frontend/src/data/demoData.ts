export interface DemoCategory {
  id: string
  name: string
  description: string
  icon: string
  resourceCount: number
}

export interface DemoResource {
  id: string
  name: string
  category: "LAB" | "WORKSHOP" | "ROOM" | "AV"
  categoryLabel: string
  modelNumber: string
  location: string
  building: string
  status: "AVAILABLE" | "RESERVED" | "MAINTENANCE"
  requiresApproval: boolean
  requiredQualification?: string
  hourlyRate: string
  leadManager: string
  description: string
}

export interface DemoBooking {
  id: string
  resourceId: string
  resourceName: string
  category: "LAB" | "WORKSHOP" | "ROOM" | "AV"
  userName: string
  userRole: string
  startTime: string
  endTime: string
  date: string
  status: "REQUESTED" | "APPROVED" | "CHECKED_IN" | "COMPLETED" | "DISPUTED"
  purpose: string
  hasCheckinPhotos: boolean
  hasReturnPhotos: boolean
}

export const DEMO_CATEGORIES: DemoCategory[] = [
  {
    id: "ALL",
    name: "All Resources",
    description: "Browse all available institutional equipment and spaces",
    icon: "LayoutGrid",
    resourceCount: 24,
  },
  {
    id: "LAB",
    name: "Laboratory & Testing",
    description: "Spectrometers, microscopes, centrifuges, and thermal analyzers",
    icon: "Microscope",
    resourceCount: 9,
  },
  {
    id: "WORKSHOP",
    name: "Workshops & Fab Lab",
    description: "3D printers, CNC mills, laser cutters, and electronics benches",
    icon: "Hammer",
    resourceCount: 7,
  },
  {
    id: "ROOM",
    name: "Rooms & Seminar Spaces",
    description: "Meeting rooms, collaborative suites, and lecture halls",
    icon: "Building2",
    resourceCount: 5,
  },
  {
    id: "AV",
    name: "Cameras & Media Kits",
    description: "Cinema cameras, wireless microphones, and lighting kits",
    icon: "Camera",
    resourceCount: 3,
  },
]

export const DEMO_RESOURCES: DemoResource[] = [
  {
    id: "res-001",
    name: "Leica TCS SP8 Confocal Laser Microscope",
    category: "LAB",
    categoryLabel: "Laboratory & Testing",
    modelNumber: "SP8-LASER-04",
    location: "Room 312, Bioengineering Wing",
    building: "Discovery Science Complex",
    status: "AVAILABLE",
    requiresApproval: true,
    requiredQualification: "Laser Safety Level 1",
    hourlyRate: "Institutional Grant / $0",
    leadManager: "Dr. Sarah Miller",
    description: "High-resolution spectral confocal microscope with tandem scanner and resonant scanning for live cell imaging.",
  },
  {
    id: "res-002",
    name: "Formlabs Form 3B+ SLA Resin 3D Printer",
    category: "WORKSHOP",
    categoryLabel: "Workshops & Fab Lab",
    modelNumber: "FL-FORM3B-01",
    location: "Makerspace Bay 2, Ground Floor",
    building: "Innovation Hub",
    status: "AVAILABLE",
    requiresApproval: false,
    requiredQualification: "General FabLab Induction",
    hourlyRate: "Material Cost Recovery",
    leadManager: "Alex Thorne",
    description: "Industrial desktop stereolithography printer optimized for biocompatible resins and high-precision prototyping.",
  },
  {
    id: "res-003",
    name: "Agilent Cary 630 FTIR Spectrometer",
    category: "LAB",
    categoryLabel: "Laboratory & Testing",
    modelNumber: "AGI-CARY-630",
    location: "Materials Suite Room 208",
    building: "Chemical Sciences Building",
    status: "AVAILABLE",
    requiresApproval: true,
    requiredQualification: "Spectrometry Safety Orientation",
    hourlyRate: "Free for Department Members",
    leadManager: "Dr. Emily Zhang",
    description: "Compact, robust FTIR spectrometer equipped with diamond ATR sampling for rapid quantitative polymer analysis.",
  },
  {
    id: "res-004",
    name: "Executive Seminar Hall 204 & Hybrid AV",
    category: "ROOM",
    categoryLabel: "Rooms & Seminar Spaces",
    modelNumber: "ROOM-204-CONF",
    location: "Level 2, North Wing",
    building: "Academic Conference Center",
    status: "AVAILABLE",
    requiresApproval: true,
    hourlyRate: "Facility Allocated",
    leadManager: "Campus Facilities Desk",
    description: "60-seat tiered presentation space featuring dual 85-inch 4K displays, PTZ cameras, and integrated Shure ceiling microphone arrays.",
  },
  {
    id: "res-005",
    name: "Sony FX6 Full-Frame Cinema Camera Kit",
    category: "AV",
    categoryLabel: "Cameras & Media Kits",
    modelNumber: "SNY-FX6-KIT-A",
    location: "Media Equipment Desk, Room 102",
    building: "Fine Arts & Media Building",
    status: "RESERVED",
    requiresApproval: false,
    requiredQualification: "Media Equipment Checkout Permit",
    hourlyRate: "Student Project Free Allowance",
    leadManager: "Marcus Vance",
    description: "4K full-frame cinema camera with 24-70mm GM lens, dual wireless lavalier microphones, and Pelican transport case.",
  },
  {
    id: "res-006",
    name: "Tormach PCNC 1100 4-Axis CNC Milling Center",
    category: "WORKSHOP",
    categoryLabel: "Workshops & Fab Lab",
    modelNumber: "TRM-1100-CNC",
    location: "Fabrication Machine Shop Bay C",
    building: "Mechanical Engineering Labs",
    status: "MAINTENANCE",
    requiresApproval: true,
    requiredQualification: "Heavy Machining & CAM Certified",
    hourlyRate: "$15/hr Machine Time",
    leadManager: "Dr. Sarah Miller",
    description: "Precision CNC vertical milling machine with automatic tool changer for aluminum, steel, and engineering plastics.",
  },
]

export const DEMO_BOOKINGS: DemoBooking[] = [
  {
    id: "bk-2026-089",
    resourceId: "res-001",
    resourceName: "Leica TCS SP8 Confocal Laser Microscope",
    category: "LAB",
    userName: "Alex Chen",
    userRole: "Student / Researcher",
    date: "Today",
    startTime: "14:00",
    endTime: "16:00",
    status: "APPROVED",
    purpose: "Cellular fluorescence kinetics assay for senior thesis project.",
    hasCheckinPhotos: false,
    hasReturnPhotos: false,
  },
  {
    id: "bk-2026-087",
    resourceId: "res-002",
    resourceName: "Formlabs Form 3B+ SLA Resin 3D Printer",
    category: "WORKSHOP",
    userName: "Alex Chen",
    userRole: "Student / Researcher",
    date: "Tomorrow",
    startTime: "10:00",
    endTime: "13:30",
    status: "REQUESTED",
    purpose: "Microfluidic chip casing prototype print.",
    hasCheckinPhotos: false,
    hasReturnPhotos: false,
  },
  {
    id: "bk-2026-072",
    resourceId: "res-003",
    resourceName: "Agilent Cary 630 FTIR Spectrometer",
    category: "LAB",
    userName: "Alex Chen",
    userRole: "Student / Researcher",
    date: "Yesterday",
    startTime: "09:30",
    endTime: "11:00",
    status: "COMPLETED",
    purpose: "Polymer matrix degradation testing.",
    hasCheckinPhotos: true,
    hasReturnPhotos: true,
  },
]
