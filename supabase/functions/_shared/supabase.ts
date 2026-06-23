// Supabase admin client (service-role key) for use inside Edge Functions.
//
// The service-role key bypasses RLS — only ever use it server-side. Never ship
// it to a browser/dashboard. Supabase injects SUPABASE_URL and
// SUPABASE_SERVICE_ROLE_KEY into the function runtime automatically.

import { createClient, type SupabaseClient } from "npm:@supabase/supabase-js@2";

let cached: SupabaseClient | null = null;

export function getAdminClient(): SupabaseClient {
  if (cached) return cached;

  const url = Deno.env.get("SUPABASE_URL");
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !serviceKey) {
    throw new Error(
      "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in the function environment.",
    );
  }

  cached = createClient(url, serviceKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
  return cached;
}
