import test from "node:test"
import assert from "node:assert"
import { apiClient, ApiClientError } from "../src/api/client.ts"
import type { ResourceResponse, BookingResponse } from "../src/api/types.ts"

test("apiClient.getResources formats query parameters and parses resource list", async () => {
  let capturedUrl = ""
  const originalFetch = globalThis.fetch

  globalThis.fetch = async (input: RequestInfo | URL) => {
    capturedUrl = input.toString()
    const mockResources: ResourceResponse[] = [
      {
        id: "res-1",
        organization_id: "org-apex",
        name: "Titan Krios Cryo-TEM",
        slug: "titan-krios-cryo-tem",
        category: "lab_instrument",
        status: "available",
        hourly_rate_credits: 50,
        requires_approval: true,
        created_at: "2026-10-29T12:00:00Z",
        updated_at: "2026-10-29T12:00:00Z",
      },
    ]
    return new Response(JSON.stringify(mockResources), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })
  }

  try {
    apiClient.setTokenProvider(() => "mock-jwt")
    const result = await apiClient.getResources("org-apex", {
      category: "lab_instrument",
      search: "krios",
    })

    assert.ok(capturedUrl.includes("/api/v1/organizations/org-apex/resources"))
    assert.ok(capturedUrl.includes("category=lab_instrument"))
    assert.ok(capturedUrl.includes("search=krios"))
    assert.strictEqual(result.length, 1)
    assert.strictEqual(result[0].name, "Titan Krios Cryo-TEM")
  } finally {
    globalThis.fetch = originalFetch
    apiClient.setTokenProvider(null)
  }
})

test("apiClient.createBooking successfully posts reservation payload", async () => {
  let capturedBody = ""
  let capturedMethod = ""
  const originalFetch = globalThis.fetch

  globalThis.fetch = async (_input: RequestInfo | URL, init?: RequestInit) => {
    capturedMethod = init?.method ?? "GET"
    capturedBody = typeof init?.body === "string" ? init.body : ""
    const mockBooking: BookingResponse = {
      id: "book-1",
      organization_id: "org-apex",
      resource_id: "res-1",
      user_id: "user-1",
      start_time: "2026-10-30T10:00:00Z",
      end_time: "2026-10-30T12:00:00Z",
      status: "approved",
      purpose: "Single-particle cryo-EM analysis",
      total_credits: 100,
      created_at: "2026-10-29T12:00:00Z",
      updated_at: "2026-10-29T12:00:00Z",
    }
    return new Response(JSON.stringify(mockBooking), {
      status: 201,
      headers: { "Content-Type": "application/json" },
    })
  }

  try {
    apiClient.setTokenProvider(() => "mock-jwt")
    const res = await apiClient.createBooking("org-apex", {
      resource_id: "res-1",
      start_time: "2026-10-30T10:00:00Z",
      end_time: "2026-10-30T12:00:00Z",
      purpose: "Single-particle cryo-EM analysis",
    })

    assert.strictEqual(capturedMethod, "POST")
    const parsedBody = JSON.parse(capturedBody)
    assert.strictEqual(parsedBody.resource_id, "res-1")
    assert.strictEqual(parsedBody.purpose, "Single-particle cryo-EM analysis")
    assert.strictEqual(res.id, "book-1")
    assert.strictEqual(res.status, "approved")
  } finally {
    globalThis.fetch = originalFetch
    apiClient.setTokenProvider(null)
  }
})

test("apiClient.createBooking handles HTTP 409 conflict on overlapping reservation", async () => {
  const originalFetch = globalThis.fetch

  globalThis.fetch = async () => {
    return new Response(
      JSON.stringify({
        detail: "Resource is already reserved or pending approval for the selected time window.",
      }),
      { status: 409, headers: { "Content-Type": "application/json" } }
    )
  }

  try {
    apiClient.setTokenProvider(() => "mock-jwt")
    await assert.rejects(
      async () => {
        await apiClient.createBooking("org-apex", {
          resource_id: "res-1",
          start_time: "2026-10-30T10:00:00Z",
          end_time: "2026-10-30T12:00:00Z",
        })
      },
      (err: unknown) => {
        assert.ok(err instanceof ApiClientError)
        assert.strictEqual(err.status, 409)
        assert.ok(err.message.includes("already reserved"))
        return true
      }
    )
  } finally {
    globalThis.fetch = originalFetch
    apiClient.setTokenProvider(null)
  }
})

test("apiClient.cancelBooking sends POST request with cancellation reason", async () => {
  let capturedUrl = ""
  let capturedBody = ""
  const originalFetch = globalThis.fetch

  globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    capturedUrl = input.toString()
    capturedBody = typeof init?.body === "string" ? init.body : ""
    const mockCancelled: BookingResponse = {
      id: "book-1",
      organization_id: "org-apex",
      resource_id: "res-1",
      user_id: "user-1",
      start_time: "2026-10-30T10:00:00Z",
      end_time: "2026-10-30T12:00:00Z",
      status: "cancelled",
      cancellation_reason: "User schedule conflict",
      created_at: "2026-10-29T12:00:00Z",
      updated_at: "2026-10-29T12:05:00Z",
    }
    return new Response(JSON.stringify(mockCancelled), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })
  }

  try {
    apiClient.setTokenProvider(() => "mock-jwt")
    const res = await apiClient.cancelBooking("org-apex", "book-1", {
      reason: "User schedule conflict",
    })

    assert.ok(capturedUrl.includes("/api/v1/organizations/org-apex/bookings/book-1/cancel"))
    const body = JSON.parse(capturedBody)
    assert.strictEqual(body.reason, "User schedule conflict")
    assert.strictEqual(res.status, "cancelled")
  } finally {
    globalThis.fetch = originalFetch
    apiClient.setTokenProvider(null)
  }
})

test("apiClient.reviewBookingDecision sends manager approval decision", async () => {
  let capturedUrl = ""
  let capturedBody = ""
  const originalFetch = globalThis.fetch

  globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    capturedUrl = input.toString()
    capturedBody = typeof init?.body === "string" ? init.body : ""
    const mockApproved: BookingResponse = {
      id: "book-2",
      organization_id: "org-apex",
      resource_id: "res-1",
      user_id: "user-student",
      start_time: "2026-10-30T14:00:00Z",
      end_time: "2026-10-30T16:00:00Z",
      status: "approved",
      reviewed_by_id: "user-manager",
      created_at: "2026-10-29T12:00:00Z",
      updated_at: "2026-10-29T12:10:00Z",
    }
    return new Response(JSON.stringify(mockApproved), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })
  }

  try {
    apiClient.setTokenProvider(() => "mock-jwt")
    const res = await apiClient.reviewBookingDecision("org-apex", "book-2", {
      action: "approve",
    })

    assert.ok(capturedUrl.includes("/api/v1/organizations/org-apex/bookings/book-2/decision"))
    const body = JSON.parse(capturedBody)
    assert.strictEqual(body.action, "approve")
    assert.strictEqual(res.status, "approved")
  } finally {
    globalThis.fetch = originalFetch
    apiClient.setTokenProvider(null)
  }
})

test("apiClient.createBooking handles HTTP 403 when safety permit is missing", async () => {
  const originalFetch = globalThis.fetch

  globalThis.fetch = async () => {
    return new Response(
      JSON.stringify({
        detail: "Safety permit required: You must hold an active institutional safety permit.",
      }),
      { status: 403, headers: { "Content-Type": "application/json" } }
    )
  }

  try {
    apiClient.setTokenProvider(() => "mock-jwt")
    await assert.rejects(
      async () => {
        await apiClient.createBooking("org-apex", {
          resource_id: "res-hazardous-1",
          start_time: "2026-10-30T10:00:00Z",
          end_time: "2026-10-30T12:00:00Z",
        })
      },
      (err: unknown) => {
        assert.ok(err instanceof ApiClientError)
        assert.strictEqual(err.status, 403)
        assert.ok(err.message.includes("Safety permit required"))
        return true
      }
    )
  } finally {
    globalThis.fetch = originalFetch
    apiClient.setTokenProvider(null)
  }
})

test("apiClient.createBooking handles HTTP 403 when equipment qualification is missing", async () => {
  const originalFetch = globalThis.fetch

  globalThis.fetch = async () => {
    return new Response(
      JSON.stringify({
        detail: "Equipment qualification required: You must hold an active certified training qualification.",
      }),
      { status: 403, headers: { "Content-Type": "application/json" } }
    )
  }

  try {
    apiClient.setTokenProvider(() => "mock-jwt")
    await assert.rejects(
      async () => {
        await apiClient.createBooking("org-apex", {
          resource_id: "res-cnc-1",
          start_time: "2026-10-30T10:00:00Z",
          end_time: "2026-10-30T12:00:00Z",
        })
      },
      (err: unknown) => {
        assert.ok(err instanceof ApiClientError)
        assert.strictEqual(err.status, 403)
        assert.ok(err.message.includes("Equipment qualification required"))
        return true
      }
    )
  } finally {
    globalThis.fetch = originalFetch
    apiClient.setTokenProvider(null)
  }
})

test("apiClient.checkinBooking sends check-in handover payload and transitions booking", async () => {
  let capturedUrl = ""
  let capturedBody = ""
  const originalFetch = globalThis.fetch

  globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    capturedUrl = input.toString()
    capturedBody = typeof init?.body === "string" ? init.body : ""
    const mockRes: BookingResponse = {
      id: "booking-checkin-1",
      organization_id: "org-apex",
      resource_id: "res-1",
      user_id: "user-1",
      start_time: "2026-10-30T10:00:00Z",
      end_time: "2026-10-30T12:00:00Z",
      status: "in_use",
      checkin_time: "2026-10-30T09:55:00Z",
      total_credits: 40,
      created_at: "2026-10-29T12:00:00Z",
      updated_at: "2026-10-30T09:55:00Z",
    }
    return new Response(JSON.stringify(mockRes), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })
  }

  try {
    apiClient.setTokenProvider(() => "mock-jwt")
    const res = await apiClient.checkinBooking("org-apex", "booking-checkin-1", {
      checklist_completed: true,
      condition_notes: "Clean and ready",
    })

    assert.ok(capturedUrl.includes("/bookings/booking-checkin-1/checkin"))
    const parsed = JSON.parse(capturedBody)
    assert.strictEqual(parsed.checklist_completed, true)
    assert.strictEqual(parsed.condition_notes, "Clean and ready")
    assert.strictEqual(res.status, "in_use")
  } finally {
    globalThis.fetch = originalFetch
    apiClient.setTokenProvider(null)
  }
})

test("apiClient.returnBooking sends return handover payload and closes session", async () => {
  let capturedUrl = ""
  let capturedBody = ""
  const originalFetch = globalThis.fetch

  globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    capturedUrl = input.toString()
    capturedBody = typeof init?.body === "string" ? init.body : ""
    const mockRes: BookingResponse = {
      id: "booking-return-1",
      organization_id: "org-apex",
      resource_id: "res-1",
      user_id: "user-1",
      start_time: "2026-10-30T10:00:00Z",
      end_time: "2026-10-30T12:00:00Z",
      status: "completed",
      checkin_time: "2026-10-30T09:55:00Z",
      checkout_time: "2026-10-30T11:58:00Z",
      total_credits: 40,
      created_at: "2026-10-29T12:00:00Z",
      updated_at: "2026-10-30T11:58:00Z",
    }
    return new Response(JSON.stringify(mockRes), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })
  }

  try {
    apiClient.setTokenProvider(() => "mock-jwt")
    const res = await apiClient.returnBooking("org-apex", "booking-return-1", {
      checklist_completed: true,
      condition_notes: "Session concluded without issues",
      incident_reported: false,
    })

    assert.ok(capturedUrl.includes("/bookings/booking-return-1/return"))
    const parsed = JSON.parse(capturedBody)
    assert.strictEqual(parsed.checklist_completed, true)
    assert.strictEqual(parsed.incident_reported, false)
    assert.strictEqual(res.status, "completed")
    assert.ok(res.checkout_time)
  } finally {
    globalThis.fetch = originalFetch
    apiClient.setTokenProvider(null)
  }
})

test("apiClient.getEvidenceStorageStatus retrieves configuration status", async () => {
  let capturedUrl = ""
  const originalFetch = globalThis.fetch

  globalThis.fetch = async (input: RequestInfo | URL) => {
    capturedUrl = input.toString()
    return new Response(
      JSON.stringify({
        configured: true,
        provider: "supabase",
        bucket_name: "sharespace-evidence",
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    )
  }

  try {
    apiClient.setTokenProvider(() => "mock-jwt")
    const res = await apiClient.getEvidenceStorageStatus("org-apex")
    assert.ok(capturedUrl.includes("/organizations/org-apex/evidence/status"))
    assert.strictEqual(res.configured, true)
    assert.strictEqual(res.provider, "supabase")
    assert.strictEqual(res.bucket_name, "sharespace-evidence")
  } finally {
    globalThis.fetch = originalFetch
    apiClient.setTokenProvider(null)
  }
})

test("apiClient.uploadBookingEvidence sends multipart form data with authorization", async () => {
  let capturedUrl = ""
  let capturedHeaders: HeadersInit | undefined
  let capturedBody: unknown
  const originalFetch = globalThis.fetch

  globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    capturedUrl = input.toString()
    capturedHeaders = init?.headers
    capturedBody = init?.body
    return new Response(
      JSON.stringify({
        storage_path: "org-apex/booking-1/checkin_abc.jpg",
        signed_url: "https://supabase.co/storage/v1/object/sign/sharespace-evidence/pic.jpg?token=abc",
        filename: "condition.jpg",
        content_type: "image/jpeg",
        size_bytes: 1024,
        handover_type: "checkin",
        uploaded_at: "2026-10-29T12:00:00Z",
      }),
      { status: 201, headers: { "Content-Type": "application/json" } }
    )
  }

  try {
    apiClient.setTokenProvider(() => "mock-jwt")
    const fakeFile = new File(["dummy image content"], "condition.jpg", { type: "image/jpeg" })
    const res = await apiClient.uploadBookingEvidence("org-apex", "booking-1", fakeFile, "checkin")

    assert.ok(capturedUrl.includes("/organizations/org-apex/bookings/booking-1/evidence/upload"))
    assert.ok(capturedBody instanceof FormData)
    // Authorization header must be set
    const h = capturedHeaders as Record<string, string>
    assert.strictEqual(h["Authorization"], "Bearer mock-jwt")
    assert.strictEqual(res.filename, "condition.jpg")
    assert.strictEqual(res.handover_type, "checkin")
    assert.ok(res.signed_url.includes("https://"))
  } finally {
    globalThis.fetch = originalFetch
    apiClient.setTokenProvider(null)
  }
})
