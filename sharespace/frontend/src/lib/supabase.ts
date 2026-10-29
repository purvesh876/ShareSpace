import { createClient, type SupabaseClient } from "@supabase/supabase-js"

/**
 * Frontend Supabase Auth Client
 *
 * Exposes ONLY the public project URL and publishable/anon key.
 * Never expose the database password, JWT secret, or service_role key to browser bundles!
 */

const rawSupabaseUrl = (
  typeof import.meta !== "undefined" && import.meta.env?.VITE_SUPABASE_URL
    ? import.meta.env.VITE_SUPABASE_URL
    : ""
).trim()

const rawSupabaseAnonKey = (
  typeof import.meta !== "undefined" && import.meta.env?.VITE_SUPABASE_ANON_KEY
    ? import.meta.env.VITE_SUPABASE_ANON_KEY
    : ""
).trim()

export const isSupabaseConfigured: boolean = Boolean(
  rawSupabaseUrl &&
    rawSupabaseAnonKey &&
    !rawSupabaseUrl.includes("[YOUR-PROJECT-REF]") &&
    !rawSupabaseAnonKey.includes("replace-with-your") &&
    !rawSupabaseAnonKey.includes("your-supabase-publishable")
)

export const supabase: SupabaseClient | null = isSupabaseConfigured
  ? createClient(rawSupabaseUrl, rawSupabaseAnonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    })
  : null
