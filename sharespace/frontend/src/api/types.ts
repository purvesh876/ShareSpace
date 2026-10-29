export interface HealthResponse {
  status: "ok" | "degraded" | "error"
  app_name: string
  version: string
  environment: string
  timestamp: string
  database_configured: boolean
}

export interface ReadinessResponse {
  status: "ready" | "unavailable"
  database: "connected" | "not configured" | "unreachable"
  timestamp: string
  message?: string
}

export interface ApiErrorDetail {
  loc?: (string | number)[]
  msg: string
  type?: string
}

export interface ApiErrorResponse {
  error: {
    code: string
    message: string
    details?: ApiErrorDetail[] | Record<string, unknown>
  }
}

export interface UserResponse {
  id: string
  email: string
  full_name: string
  avatar_url?: string | null
  phone_number?: string | null
  is_active: boolean
  is_verified: boolean
  created_at: string
}

export interface MembershipSummary {
  membership_id: string
  organization_id: string
  organization_name: string
  organization_slug: string
  role: string
  department?: string | null
  is_active: boolean
}

export interface UserProfileResponse {
  user: UserResponse
  memberships: MembershipSummary[]
}

export interface DemoTokenResponse {
  access_token: string
  token_type: string
  user: UserResponse
  active_role: string
}

export interface OrganizationResponse {
  id: string
  name: string
  slug: string
  domain?: string | null
  is_active: boolean
  created_at: string
}

export interface OrganizationMemberResponse {
  membership_id: string
  user_id: string
  email: string
  full_name: string
  role: string
  department?: string | null
  is_active: boolean
  joined_at: string
}

export interface AuditEventResponse {
  id: string
  organization_id?: string | null
  user_id?: string | null
  user_email?: string | null
  actor_user_id?: string | null
  action: string
  entity_type?: string | null
  resource_type?: string | null
  entity_id?: string | null
  resource_id?: string | null
  payload_before?: Record<string, unknown> | null
  payload_after?: Record<string, unknown> | null
  metadata_json?: Record<string, unknown> | null
  ip_address?: string | null
  timestamp: string
}

export interface AssignMemberRequest {
  email: string
  role?: string
  department?: string
}

export interface ResourceResponse {
  id: string
  organization_id: string
  name: string
  slug: string
  category: string
  description?: string | null
  location?: string | null
  is_available: boolean
  requires_approval: boolean
  requires_permit: boolean
  requires_qualification: boolean
  hourly_rate_credits: number

  specifications_json?: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface ResourceCreateRequest {
  name: string
  category: string
  description?: string
  location?: string
  requires_approval?: boolean
  requires_permit?: boolean
  requires_qualification?: boolean
  hourly_rate_credits?: number
  specifications_json?: Record<string, unknown>
}

export interface ResourceUpdateRequest {
  name?: string
  category?: string
  description?: string
  location?: string
  is_available?: boolean
  requires_approval?: boolean
  requires_permit?: boolean
  requires_qualification?: boolean
  hourly_rate_credits?: number
  specifications_json?: Record<string, unknown>
}

export interface TimeSlot {
  start_time: string
  end_time: string
  status: string
}

export interface ResourceAvailabilityResponse {
  resource_id: string
  resource_name: string
  is_available: boolean
  requires_approval: boolean
  reserved_slots: TimeSlot[]
}

export interface BookingCreateRequest {
  resource_id: string
  start_time: string
  end_time: string
  purpose?: string
}

export interface BookingResponse {
  id: string
  organization_id: string
  resource_id: string
  resource_name?: string | null
  user_id: string
  user_email?: string | null
  user_full_name?: string | null
  start_time: string
  end_time: string
  status: "pending" | "approved" | "rejected" | "in_use" | "completed" | "cancelled" | string
  purpose?: string | null
  total_credits: number
  rejection_reason?: string | null
  checkin_time?: string | null
  checkout_time?: string | null
  created_at: string
  updated_at: string
}

export interface BookingDecisionRequest {
  action: "approve" | "reject"
  reason?: string
}

export interface BookingCancelRequest {
  reason?: string
}

export interface BookingCheckinRequest {
  checklist_completed: boolean
  condition_notes?: string
  photo_evidence_url?: string
}

export interface BookingReturnRequest {
  checklist_completed: boolean
  condition_notes?: string
  incident_reported?: boolean
  photo_evidence_url?: string
}

export interface QualificationResponse {
  id: string
  organization_id: string
  user_id: string
  user_email?: string | null
  user_full_name?: string | null
  resource_id?: string | null
  resource_name?: string | null
  qualification_code: string
  title: string
  certified_by?: string | null
  certified_at: string
  expires_at?: string | null
  status: "active" | "expired" | "suspended" | string
  created_at: string
  updated_at: string
}

export interface SafetyPermitResponse {
  id: string
  organization_id: string
  user_id: string
  user_email?: string | null
  user_full_name?: string | null
  permit_type: string
  issuer?: string | null
  issue_date: string
  expiry_date: string
  status: "active" | "expired" | "revoked" | "pending" | string
  document_url?: string | null
  created_at: string
  updated_at: string
}

export interface StorageStatusResponse {
  configured: boolean
  provider: string
  bucket_name?: string | null
}

export interface EvidenceUploadResponse {
  storage_path: string
  signed_url: string
  filename: string
  content_type: string
  size_bytes: number
  handover_type: string
  uploaded_at: string
}

export interface SignedUrlResponse {
  storage_path: string
  signed_url: string
  expires_in: number
}



