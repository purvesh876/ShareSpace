import type {
  AssignMemberRequest,
  AuditEventResponse,
  BookingCancelRequest,
  BookingCheckinRequest,
  BookingCreateRequest,
  BookingDecisionRequest,
  BookingResponse,
  BookingReturnRequest,
  DemoTokenResponse,
  HealthResponse,
  OrganizationMemberResponse,
  OrganizationResponse,
  QualificationResponse,
  ReadinessResponse,
  ResourceAvailabilityResponse,
  ResourceCreateRequest,
  ResourceResponse,
  ResourceUpdateRequest,
  SafetyPermitResponse,
  SignedUrlResponse,
  StorageStatusResponse,
  EvidenceUploadResponse,
  UserProfileResponse,
} from "./types"



// The API base URL is resolved dynamically from Vite environment variables.
// In production or custom environments, specify VITE_API_BASE_URL.
const API_BASE_URL: string =
  typeof import.meta !== "undefined" && import.meta.env?.VITE_API_BASE_URL
    ? import.meta.env.VITE_API_BASE_URL.replace(/\/$/, "")
    : "http://localhost:8000/api/v1"

export class ApiClientError extends Error {
  status: number
  code?: string
  details?: unknown

  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message)
    this.name = "ApiClientError"
    this.status = status
    this.code = code
    this.details = details
  }
}

let tokenProvider: (() => string | null | Promise<string | null>) | null = null
let onUnauthorizedHandler: (() => void) | null = null

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`

  const headers: Record<string, string> = {
    "Accept": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  }

  // Only default to JSON Content-Type if not sending FormData
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json"
  }

  // Attach verified Bearer token if not explicitly supplied
  if (!headers["Authorization"] && tokenProvider) {
    const token = await tokenProvider()
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })

    const contentType = response.headers.get("content-type")
    const isJson = contentType && contentType.includes("application/json")
    const data = isJson ? await response.json() : null

    if (!response.ok) {
      // Trigger session clearance on 401 Unauthorized
      if (response.status === 401 && onUnauthorizedHandler) {
        onUnauthorizedHandler()
      }
      const errorMessage = data?.error?.message || data?.detail || `HTTP Error ${response.status}`
      const errorCode = data?.error?.code || `HTTP_${response.status}`
      throw new ApiClientError(errorMessage, response.status, errorCode, data?.error?.details || data)
    }

    return data as T
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error
    }
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error
    }
    // Handle network failures (e.g. backend server is not running)
    const err = error as Error
    throw new ApiClientError(
      err.message || "Network request failed. Is the FastAPI backend running?",
      0,
      "NETWORK_ERROR"
    )
  }
}

export const apiClient = {
  getBaseUrl(): string {
    return API_BASE_URL
  },

  async getHealth(signal?: AbortSignal): Promise<HealthResponse> {
    return request<HealthResponse>("/health", { signal })
  },

  /**
   * Evaluates readiness of backend dependencies (PostgreSQL).
   *
   * Returns HTTP 200 when PostgreSQL is connected, and HTTP 503 when
   * DATABASE_URL is unconfigured (detached mode) or unreachable.
   */
  async getReadiness(signal?: AbortSignal): Promise<ReadinessResponse> {
    const url = `${API_BASE_URL}/ready`

    try {
      const response = await fetch(url, {
        headers: {
          Accept: "application/json",
        },
        signal,
      })

      const contentType = response.headers.get("content-type")
      const isJson = contentType && contentType.includes("application/json")
      const data = isJson ? await response.json() : null

      // HTTP 200: Fully operational and connected
      if (response.status === 200 && data) {
        return {
          status: "ready",
          database: "connected",
          timestamp: data.timestamp || new Date().toISOString(),
          message: data.message || "PostgreSQL connection active.",
        }
      }

      // HTTP 503: Expected state when database is not configured or temporarily unreachable
      if (response.status === 503) {
        const isNotConfigured = !data || data.database === "not configured"
        const dbStatus = isNotConfigured ? "not configured" : "unreachable"

        return {
          status: "unavailable",
          database: dbStatus,
          timestamp: data?.timestamp || new Date().toISOString(),
          message:
            data?.message ||
            (isNotConfigured
              ? "DATABASE_URL is not set."
              : "Database connection unreachable."),
        }
      }

      // Unexpected HTTP error status (e.g. 404, 500, 502) - keep observable
      if (!response.ok) {
        const message = data?.detail || data?.error?.message || `HTTP ${response.status} from readiness endpoint`
        throw new ApiClientError(message, response.status, `HTTP_${response.status}`, data)
      }

      return data as ReadinessResponse
    } catch (error) {
      if (error instanceof ApiClientError) {
        throw error
      }
      if (error instanceof DOMException && error.name === "AbortError") {
        throw error
      }

      // Genuine network connectivity problem (server offline, DNS fail, CORS, etc.)
      const err = error as Error
      return {
        status: "unavailable",
        database: "unreachable",
        timestamp: new Date().toISOString(),
        message: `Network connectivity failure: ${err.message || "Failed to contact backend API."}`,
      }
    }
  },

  /**
   * Diagnostic resolver:
   * First calls /health (HTTP 200).
   * - If health check indicates database is NOT configured (database_configured: false),
   *   we know with certainty the DB setup is pending (detached mode).
   *   We do NOT call /ready, eliminating repeated HTTP 503 console errors.
   * - If health check indicates database IS configured (database_configured: true),
   *   we call /ready to verify actual live connectivity to PostgreSQL (ready vs unreachable).
   * - If /health fails with network error, API is offline.
   */
  async getDiagnosticStatus(signal?: AbortSignal): Promise<{
    health: HealthResponse | null
    readiness: ReadinessResponse
  }> {
    const health = await this.getHealth(signal)

    if (!health.database_configured) {
      return {
        health,
        readiness: {
          status: "unavailable",
          database: "not configured",
          timestamp: health.timestamp,
          message: "DATABASE_URL is not set. The backend is running in detached development mode.",
        },
      }
    }

    // Database is configured: query live readiness to verify actual connection
    const readiness = await this.getReadiness(signal)
    return {
      health,
      readiness,
    }
  },

  setTokenProvider(provider: (() => string | null | Promise<string | null>) | null) {
    tokenProvider = provider
  },

  setOnUnauthorized(handler: (() => void) | null) {
    onUnauthorizedHandler = handler
  },

  async getMyProfile(options?: { token?: string; signal?: AbortSignal }): Promise<UserProfileResponse> {
    const headers: Record<string, string> = {}
    if (options?.token) {
      headers["Authorization"] = `Bearer ${options.token}`
    }
    return request<UserProfileResponse>("/auth/me", {
      signal: options?.signal,
      headers,
    })
  },

  async getDemoToken(persona: string): Promise<DemoTokenResponse> {
    return request<DemoTokenResponse>("/auth/demo-token", {
      method: "POST",
      body: JSON.stringify({ persona }),
    })
  },

  async getOrganizations(signal?: AbortSignal): Promise<OrganizationResponse[]> {
    return request<OrganizationResponse[]>("/organizations", { signal })
  },

  async getOrganization(
    id: string,
    signal?: AbortSignal
  ): Promise<{ organization: OrganizationResponse; user_role: string; membership_id: string }> {
    return request(`/organizations/${id}`, { signal })
  },

  async getOrganizationMembers(
    id: string,
    signal?: AbortSignal
  ): Promise<OrganizationMemberResponse[]> {
    return request<OrganizationMemberResponse[]>(`/organizations/${id}/members`, { signal })
  },

  async getOrganizationAuditEvents(
    id: string,
    signal?: AbortSignal
  ): Promise<AuditEventResponse[]> {
    return request<AuditEventResponse[]>(`/organizations/${id}/audit-events`, { signal })
  },

  async assignOrganizationMember(
    organizationId: string,
    data: AssignMemberRequest,
    signal?: AbortSignal
  ): Promise<OrganizationMemberResponse> {
    return request<OrganizationMemberResponse>(`/organizations/${organizationId}/members`, {
      method: "POST",
      body: JSON.stringify(data),
      signal,
    })
  },

  async getResources(
    organizationId: string,
    params?: { category?: string; available_only?: boolean; search?: string },
    signal?: AbortSignal
  ): Promise<ResourceResponse[]> {
    const query = new URLSearchParams()
    if (params?.category && params.category !== "ALL") {
      query.set("category", params.category)
    }
    if (params?.available_only) {
      query.set("available_only", "true")
    }
    if (params?.search) {
      query.set("search", params.search)
    }
    const qStr = query.toString() ? `?${query.toString()}` : ""
    return request<ResourceResponse[]>(`/organizations/${organizationId}/resources${qStr}`, { signal })
  },

  async getResource(
    organizationId: string,
    resourceId: string,
    signal?: AbortSignal
  ): Promise<ResourceResponse> {
    return request<ResourceResponse>(`/organizations/${organizationId}/resources/${resourceId}`, { signal })
  },

  async createResource(
    organizationId: string,
    data: ResourceCreateRequest,
    signal?: AbortSignal
  ): Promise<ResourceResponse> {
    return request<ResourceResponse>(`/organizations/${organizationId}/resources`, {
      method: "POST",
      body: JSON.stringify(data),
      signal,
    })
  },

  async updateResource(
    organizationId: string,
    resourceId: string,
    data: ResourceUpdateRequest,
    signal?: AbortSignal
  ): Promise<ResourceResponse> {
    return request<ResourceResponse>(`/organizations/${organizationId}/resources/${resourceId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      signal,
    })
  },

  async getResourceAvailability(
    organizationId: string,
    resourceId: string,
    params?: { start_time?: string; end_time?: string },
    signal?: AbortSignal
  ): Promise<ResourceAvailabilityResponse> {
    const query = new URLSearchParams()
    if (params?.start_time) query.set("start_time", params.start_time)
    if (params?.end_time) query.set("end_time", params.end_time)
    const qStr = query.toString() ? `?${query.toString()}` : ""
    return request<ResourceAvailabilityResponse>(
      `/organizations/${organizationId}/resources/${resourceId}/availability${qStr}`,
      { signal }
    )
  },

  async createBooking(
    organizationId: string,
    data: BookingCreateRequest,
    signal?: AbortSignal
  ): Promise<BookingResponse> {
    return request<BookingResponse>(`/organizations/${organizationId}/bookings`, {
      method: "POST",
      body: JSON.stringify(data),
      signal,
    })
  },

  async getMyBookings(
    organizationId: string,
    signal?: AbortSignal
  ): Promise<BookingResponse[]> {
    return request<BookingResponse[]>(`/organizations/${organizationId}/bookings/my`, { signal })
  },

  async getOrganizationBookings(
    organizationId: string,
    params?: { status?: string; resource_id?: string },
    signal?: AbortSignal
  ): Promise<BookingResponse[]> {
    const query = new URLSearchParams()
    if (params?.status && params.status !== "ALL") query.set("status", params.status)
    if (params?.resource_id) query.set("resource_id", params.resource_id)
    const qStr = query.toString() ? `?${query.toString()}` : ""
    return request<BookingResponse[]>(`/organizations/${organizationId}/bookings${qStr}`, { signal })
  },

  async cancelBooking(
    organizationId: string,
    bookingId: string,
    data?: BookingCancelRequest,
    signal?: AbortSignal
  ): Promise<BookingResponse> {
    return request<BookingResponse>(`/organizations/${organizationId}/bookings/${bookingId}/cancel`, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
      signal,
    })
  },

  async reviewBookingDecision(
    organizationId: string,
    bookingId: string,
    data: BookingDecisionRequest,
    signal?: AbortSignal
  ): Promise<BookingResponse> {
    return request<BookingResponse>(`/organizations/${organizationId}/bookings/${bookingId}/decision`, {
      method: "POST",
      body: JSON.stringify(data),
      signal,
    })
  },

  async checkinBooking(
    organizationId: string,
    bookingId: string,
    data: BookingCheckinRequest,
    signal?: AbortSignal
  ): Promise<BookingResponse> {
    return request<BookingResponse>(`/organizations/${organizationId}/bookings/${bookingId}/checkin`, {
      method: "POST",
      body: JSON.stringify(data),
      signal,
    })
  },

  async returnBooking(
    organizationId: string,
    bookingId: string,
    data: BookingReturnRequest,
    signal?: AbortSignal
  ): Promise<BookingResponse> {
    return request<BookingResponse>(`/organizations/${organizationId}/bookings/${bookingId}/return`, {
      method: "POST",
      body: JSON.stringify(data),
      signal,
    })
  },

  async getMyQualifications(
    organizationId: string,
    signal?: AbortSignal
  ): Promise<QualificationResponse[]> {
    return request<QualificationResponse[]>(`/organizations/${organizationId}/qualifications/my`, { signal })
  },

  async getMySafetyPermits(
    organizationId: string,
    signal?: AbortSignal
  ): Promise<SafetyPermitResponse[]> {
    return request<SafetyPermitResponse[]>(`/organizations/${organizationId}/safety-permits/my`, { signal })
  },

  async getOrganizationQualifications(
    organizationId: string,
    signal?: AbortSignal
  ): Promise<QualificationResponse[]> {
    return request<QualificationResponse[]>(`/organizations/${organizationId}/qualifications`, { signal })
  },

  async getOrganizationSafetyPermits(
    organizationId: string,
    signal?: AbortSignal
  ): Promise<SafetyPermitResponse[]> {
    return request<SafetyPermitResponse[]>(`/organizations/${organizationId}/safety-permits`, { signal })
  },

  async getEvidenceStorageStatus(
    organizationId: string,
    signal?: AbortSignal
  ): Promise<StorageStatusResponse> {
    return request<StorageStatusResponse>(`/organizations/${organizationId}/evidence/status`, { signal })
  },

  async uploadBookingEvidence(
    organizationId: string,
    bookingId: string,
    file: File,
    handoverType: "checkin" | "return" = "checkin",
    signal?: AbortSignal
  ): Promise<EvidenceUploadResponse> {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("handover_type", handoverType)

    return request<EvidenceUploadResponse>(
      `/organizations/${organizationId}/bookings/${bookingId}/evidence/upload`,
      {
        method: "POST",
        body: formData,
        signal,
      }
    )
  },

  async getEvidenceSignedUrl(
    organizationId: string,
    bookingId: string,
    storagePath: string,
    expiresIn = 3600,
    signal?: AbortSignal
  ): Promise<SignedUrlResponse> {
    const params = new URLSearchParams({
      storage_path: storagePath,
      expires_in: expiresIn.toString(),
    })
    return request<SignedUrlResponse>(
      `/organizations/${organizationId}/bookings/${bookingId}/evidence/signed-url?${params.toString()}`,
      { signal }
    )
  },
}





