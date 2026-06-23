// Trial expiry (run daily via cron).
//
// Flips users from 'trial' to 'expired' once their free trial window has passed,
// and sends one clear message offering to subscribe. Check-ins then pause (the
// send-checkins job only serves trial/active/comped users).
//
// v1 pilot note: friends can be set to 'comped' (manually, e.g. via the SQL in
// scripts/) so they're never expired. Real billing is out of scope for v1.

import { getAdminClient } from "../_shared/supabase.ts";
import { getWhatsAppClient } from "../_shared/whatsapp.ts";
import { logMessage } from "../_shared/repo.ts";
import type { User } from "../_shared/types.ts";

const TRIAL_DAYS = Number(Deno.env.get("TRIAL_DAYS") ?? "7");

Deno.serve(async (req) => {
  const guard = checkSecret(req);
  if (guard) return guard;

  const db = getAdminClient();
  const cutoff = new Date(Date.now() - TRIAL_DAYS * 24 * 3600 * 1000)
    .toISOString();

  const { data: expiring, error } = await db
    .from("users")
    .select("*")
    .eq("subscription_status", "trial")
    .not("trial_started_at", "is", null)
    .lt("trial_started_at", cutoff);
  if (error) return json({ error: "load failed" }, 500);

  const wa = getWhatsAppClient();
  let expired = 0;

  for (const user of (expiring ?? []) as User[]) {
    try {
      await db
        .from("users")
        .update({ subscription_status: "expired" })
        .eq("id", user.id);

      const body =
        "Your free trial just wrapped up — hope the check-ins helped! To keep them " +
        "going it's about $5/week. Want the link? Reply 'yes' and I'll sort it out.";
      const providerId = await wa.send(user.whatsapp_number, body);
      await logMessage({
        userId: user.id,
        direction: "outbound",
        body,
        providerId,
      });
      expired++;
    } catch (err) {
      console.error(`expire failed for user ${user.id}`, err);
    }
  }

  return json({ expired });
});

function checkSecret(req: Request): Response | null {
  const expected = Deno.env.get("CRON_SECRET");
  if (!expected) return null;
  const got = req.headers.get("x-cron-secret") ??
    new URL(req.url).searchParams.get("secret");
  if (got !== expected) return json({ error: "unauthorized" }, 401);
  return null;
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}
