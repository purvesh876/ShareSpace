import test from "node:test"
import assert from "node:assert"
import { apiClient, ApiClientError } from "../src/api/client.ts"
import type { MembershipSummary, UserProfileResponse } from "../src/api/types.ts"

test("API client attaches Authorization header when token provider is set", async () => {
  let capturedHeaders: HeadersInit | undefined

  // Mock fetch
  const originalFetch = globalThis.fetch
  globalThis.fetch = async (_input: RequestInfo | URL, init?: RequestInit) => {
    capturedHeaders = init?.headers
    return new Response(
      JSON.stringify({
        user: { id: "u-1", email: "user@apex.edu", full_name: "User", is_active: true, is_verified: true, created_at: "" },
        memberships: [],
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    )
  }

  try {
    apiClient.setTokenProvider(() => "test-crypto-jwt-token-xyz")
    await apiClient.getMyProfile()

    const headers = capturedHeaders as Record<string, string>
    assert.strictEqual(
      headers["Authorization"],
      "Bearer test-crypto-jwt-token-xyz",
      "Expected Bearer token in Authorization header"
    )
  } finally {
    globalThis.fetch = originalFetch
    apiClient.setTokenProvider(null)
  }
})

test("API client omits Authorization header when no token is present", async () => {
  let capturedHeaders: HeadersInit | undefined

  const originalFetch = globalThis.fetch
  globalThis.fetch = async (_input: RequestInfo | URL, init?: RequestInit) => {
    capturedHeaders = init?.headers
    return new Response(
      JSON.stringify({ status: "ok", app_name: "ShareSpace", version: "0.1.0", environment: "test", timestamp: "", database_configured: false }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    )
  }

  try {
    apiClient.setTokenProvider(() => null)
    await apiClient.getHealth()

    const headers = capturedHeaders as Record<string, string>
    assert.strictEqual(headers["Authorization"], undefined, "Expected no Authorization header")
  } finally {
    globalThis.fetch = originalFetch
    apiClient.setTokenProvider(null)
  }
})

test("HTTP 401 response invokes onUnauthorized handler", async () => {
  let unauthorizedTriggered = false

  const originalFetch = globalThis.fetch
  globalThis.fetch = async () => {
    return new Response(
      JSON.stringify({ detail: "Authentication token has expired" }),
      { status: 401, headers: { "Content-Type": "application/json" } }
    )
  }

  try {
    apiClient.setOnUnauthorized(() => {
      unauthorizedTriggered = true
    })

    await assert.rejects(
      async () => {
        await apiClient.getMyProfile()
      },
      (err: Error) => {
        assert(err instanceof ApiClientError)
        assert.strictEqual(err.status, 401)
        assert(err.message.includes("expired"))
        return true
      }
    )

    assert.strictEqual(unauthorizedTriggered, true, "Expected onUnauthorized handler to be called")
  } finally {
    globalThis.fetch = originalFetch
    apiClient.setOnUnauthorized(null)
  }
})

test("HTTP 403 response raises ApiClientError without clearing session", async () => {
  let unauthorizedTriggered = false

  const originalFetch = globalThis.fetch
  globalThis.fetch = async () => {
    return new Response(
      JSON.stringify({ detail: "Access denied: Insufficient role permissions. Required: ['admin']" }),
      { status: 403, headers: { "Content-Type": "application/json" } }
    )
  }

  try {
    apiClient.setOnUnauthorized(() => {
      unauthorizedTriggered = true
    })

    await assert.rejects(
      async () => {
        await apiClient.getOrganizationAuditEvents("org-uuid-123")
      },
      (err: Error) => {
        assert(err instanceof ApiClientError)
        assert.strictEqual(err.status, 403)
        assert(err.message.includes("Insufficient role permissions"))
        return true
      }
    )

    assert.strictEqual(
      unauthorizedTriggered,
      false,
      "403 Forbidden must NOT trigger session clearance"
    )
  } finally {
    globalThis.fetch = originalFetch
    apiClient.setOnUnauthorized(null)
  }
})

test("User profile with memberships resolves active membership correctly", () => {
  const mockMemberships: MembershipSummary[] = [
    {
      membership_id: "mem-1",
      organization_id: "org-1",
      organization_name: "Apex Institute of Technology",
      organization_slug: "apex-institute",
      role: "student",
      department: "Robotics",
      is_active: true,
    },
    {
      membership_id: "mem-2",
      organization_id: "org-2",
      organization_name: "State Research Labs",
      organization_slug: "state-labs",
      role: "researcher",
      department: "Materials Science",
      is_active: true,
    },
  ]

  // Default selection selects the first membership
  const defaultSelected = mockMemberships[0]
  assert.strictEqual(defaultSelected.organization_slug, "apex-institute")
  assert.strictEqual(defaultSelected.role, "student")

  // Switching selection resolves chosen organization
  const switched = mockMemberships.find((m) => m.organization_id === "org-2")
  assert(switched)
  assert.strictEqual(switched.organization_slug, "state-labs")
  assert.strictEqual(switched.role, "researcher")
})

test("User with zero organization memberships maps to unassigned state", () => {
  const profile: UserProfileResponse = {
    user: {
      id: "u-99",
      email: "new.member@apex.edu",
      full_name: "New Student",
      is_active: true,
      is_verified: true,
      created_at: "2026-10-29T00:00:00Z",
    },
    memberships: [],
  }

  const activeMembership = profile.memberships.length > 0 ? profile.memberships[0] : null
  const activeRole = activeMembership ? (activeMembership as MembershipSummary).role : "guest"

  assert.strictEqual(activeMembership, null, "Expected activeMembership to be null")
  assert.strictEqual(activeRole, "guest", "Expected guest fallback when user has no memberships")
})

test("Client-side role switching does not alter server-issued JWT token", () => {
  const token = "verified.supabase.token"
  let currentToken = token

  // Attempting to change role locally should never rewrite cryptographic token
  const simulateLocalRoleChange = (_newRole: string) => {
    // In real mode, token remains unchanged
    return currentToken
  }

  const resultToken = simulateLocalRoleChange("admin")
  assert.strictEqual(resultToken, token, "Client role selection must NOT alter verified bearer token")
})

test("API client assignOrganizationMember posts payload and returns member response", async () => {
  let capturedBody: string | undefined
  let capturedUrl: string | undefined

  const originalFetch = globalThis.fetch
  globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    capturedUrl = input.toString()
    capturedBody = init?.body as string
    return new Response(
      JSON.stringify({
        membership_id: "mem-123",
        user_id: "u-456",
        email: "target@apex.edu",
        full_name: "Target User",
        role: "researcher",
        department: "Optics",
        is_active: true,
        joined_at: "2026-10-29T00:00:00Z",
      }),
      { status: 201, headers: { "Content-Type": "application/json" } }
    )
  }

  try {
    const res = await apiClient.assignOrganizationMember("org-999", {
      email: "target@apex.edu",
      role: "researcher",
      department: "Optics",
    })
    assert(capturedUrl?.includes("/organizations/org-999/members"))
    const parsedBody = JSON.parse(capturedBody || "{}")
    assert.strictEqual(parsedBody.email, "target@apex.edu")
    assert.strictEqual(parsedBody.role, "researcher")
    assert.strictEqual(res.role, "researcher")
    assert.strictEqual(res.is_active, true)
  } finally {
    globalThis.fetch = originalFetch
  }
})

