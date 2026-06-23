// Access gating for the v1 friends-only pilot.
//
// To open the product up later, this is the ONE place to change: either flip
// ALLOWLIST_ENABLED=false (env), or keep the allowlist and just insert more
// rows into allowed_numbers. No other code touches access control.

import { getAdminClient } from "./supabase.ts";

export async function isAllowed(whatsappNumber: string): Promise<boolean> {
  // Global kill-switch for the allowlist (set ALLOWLIST_ENABLED=false to open up).
  if ((Deno.env.get("ALLOWLIST_ENABLED") ?? "true").toLowerCase() === "false") {
    return true;
  }

  const db = getAdminClient();
  const { data, error } = await db
    .from("allowed_numbers")
    .select("id")
    .eq("whatsapp_number", whatsappNumber)
    .eq("enabled", true)
    .maybeSingle();

  if (error) {
    console.error("allowlist lookup failed", error);
    return false; // fail closed
  }
  return data !== null;
}
