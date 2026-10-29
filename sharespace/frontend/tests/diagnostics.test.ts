import test from "node:test"
import assert from "node:assert"
import type { HealthResponse, ReadinessResponse } from "../src/api/types"

/**
 * Pure diagnostic resolution logic matching apiClient.getDiagnosticStatus
 */
async function resolveDiagnosticStatus(
  fetchHealth: () => Promise<HealthResponse>,
  fetchReadiness: () => Promise<ReadinessResponse>
) {
  const health = await fetchHealth()

  if (!health.database_configured) {
    return {
      health,
      readiness: {
        status: "unavailable" as const,
        database: "not configured" as const,
        timestamp: health.timestamp,
        message: "DATABASE_URL is not set. The backend is running in detached development mode.",
      },
    }
  }

  const readiness = await fetchReadiness()
  return {
    health,
    readiness,
  }
}

function getHeaderBadgeLabels(health: HealthResponse | null, readiness: ReadinessResponse | null) {
  const apiLabel = health?.status === "ok" ? "API healthy" : "API offline"
  const dbLabel =
    readiness?.status === "ready"
      ? "DB ready"
      : readiness?.database === "not configured"
      ? "DB setup pending"
      : "DB unreachable"

  return { apiLabel, dbLabel }
}

test("Healthy API with no database configured does NOT call /ready and reports DB setup pending", async () => {
  let readinessCallCount = 0

  const mockHealth: HealthResponse = {
    status: "ok",
    app_name: "ShareSpace API",
    version: "0.1.0",
    environment: "development",
    timestamp: "2026-10-29T00:00:00Z",
    database_configured: false,
  }

  const result = await resolveDiagnosticStatus(
    async () => mockHealth,
    async () => {
      readinessCallCount++
      return {
        status: "unavailable",
        database: "not configured",
        timestamp: "2026-10-29T00:00:00Z",
      }
    }
  )

  // Critical assertion: /ready MUST NOT be called when database_configured is false!
  assert.strictEqual(readinessCallCount, 0, "Expected /ready NOT to be called when database is unconfigured")
  assert.strictEqual(result.health?.status, "ok")
  assert.strictEqual(result.readiness.status, "unavailable")
  assert.strictEqual(result.readiness.database, "not configured")

  const badges = getHeaderBadgeLabels(result.health, result.readiness)
  assert.strictEqual(badges.apiLabel, "API healthy")
  assert.strictEqual(badges.dbLabel, "DB setup pending")
})

test("Healthy API with configured database calls /ready and reports DB ready when connected", async () => {
  let readinessCallCount = 0

  const mockHealth: HealthResponse = {
    status: "ok",
    app_name: "ShareSpace API",
    version: "0.1.0",
    environment: "development",
    timestamp: "2026-10-29T00:00:00Z",
    database_configured: true,
  }

  const result = await resolveDiagnosticStatus(
    async () => mockHealth,
    async () => {
      readinessCallCount++
      return {
        status: "ready",
        database: "connected",
        timestamp: "2026-10-29T00:00:00Z",
        message: "PostgreSQL connection active.",
      }
    }
  )

  assert.strictEqual(readinessCallCount, 1, "Expected /ready to be called when database is configured")
  assert.strictEqual(result.health?.status, "ok")
  assert.strictEqual(result.readiness.status, "ready")
  assert.strictEqual(result.readiness.database, "connected")

  const badges = getHeaderBadgeLabels(result.health, result.readiness)
  assert.strictEqual(badges.apiLabel, "API healthy")
  assert.strictEqual(badges.dbLabel, "DB ready")
})

test("Healthy API with configured database calls /ready and reports DB unreachable when database fails", async () => {
  let readinessCallCount = 0

  const mockHealth: HealthResponse = {
    status: "ok",
    app_name: "ShareSpace API",
    version: "0.1.0",
    environment: "development",
    timestamp: "2026-10-29T00:00:00Z",
    database_configured: true,
  }

  const result = await resolveDiagnosticStatus(
    async () => mockHealth,
    async () => {
      readinessCallCount++
      return {
        status: "unavailable",
        database: "unreachable",
        timestamp: "2026-10-29T00:00:00Z",
        message: "Failed to connect to configured PostgreSQL instance.",
      }
    }
  )

  assert.strictEqual(readinessCallCount, 1)
  assert.strictEqual(result.readiness.status, "unavailable")
  assert.strictEqual(result.readiness.database, "unreachable")

  const badges = getHeaderBadgeLabels(result.health, result.readiness)
  assert.strictEqual(badges.apiLabel, "API healthy")
  assert.strictEqual(badges.dbLabel, "DB unreachable")
})

test("Offline API correctly maps to API offline badge", () => {
  const badges = getHeaderBadgeLabels(null, null)
  assert.strictEqual(badges.apiLabel, "API offline")
  assert.strictEqual(badges.dbLabel, "DB unreachable")
})
