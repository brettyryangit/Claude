// Scheduled check-in sender. Run this on a cron (e.g. every 15 minutes) via the
// Supabase cron scheduler, an external cron service, or GitHub Actions hitting
// this function's URL. Protect it with a shared secret (CRON_SECRET).
//
// Each run, for every active goal of a non-expired user it:
//   1. SENDS the day's/week's check-in once local time passes preferred_time.
//   2. NUDGES open (unanswered) check-ins, at most CHECKIN_MAX_NUDGES per day,
//      spaced NUDGE_GAP_HOURS apart.
//   3. Marks check-ins MISSED once unanswered past MISS_CUTOFF_HOURS — never
//      chased forever (spec: response=null after cutoff is a miss).

import { getAdminClient } from "../_shared/supabase.ts";
import { getWhatsAppClient } from "../_shared/whatsapp.ts";
import { generateText } from "../_shared/anthropic.ts";
import { BOT_VOICE, checkinPrompt } from "../_shared/prompts.ts";
import { logMessage } from "../_shared/repo.ts";
import {
  localDateKey,
  localMinutes,
  localWeekKey,
  timeToMinutes,
} from "../_shared/tz.ts";
import type { Goal, User } from "../_shared/types.ts";

const MAX_NUDGES = Number(Deno.env.get("CHECKIN_MAX_NUDGES") ?? "2");
const NUDGE_GAP_HOURS = Number(Deno.env.get("NUDGE_GAP_HOURS") ?? "4");
const MISS_CUTOFF_HOURS = Number(Deno.env.get("MISS_CUTOFF_HOURS") ?? "24");

Deno.serve(async (req) => {
  const guard = checkSecret(req);
  if (guard) return guard;

  const db = getAdminClient();
  const now = new Date();

  // Active goals belonging to users who should still receive check-ins.
  const { data: goals, error } = await db
    .from("goals")
    .select("*, users!inner(*)")
    .eq("status", "active")
    .in("users.subscription_status", ["trial", "active", "comped"])
    .eq("users.onboarding_state", "active");

  if (error) {
    console.error("failed to load goals", error);
    return json({ error: "load failed" }, 500);
  }

  let sent = 0, nudged = 0, missed = 0;

  for (const row of (goals ?? []) as (Goal & { users: User })[]) {
    const user = row.users;
    const goal = row;
    try {
      missed += await sweepMisses(goal, now);
      const didSend = await maybeSendInitial(goal, user, now);
      if (didSend) {
        sent++;
      } else {
        nudged += await maybeNudge(goal, user, now);
      }
    } catch (err) {
      console.error(`goal ${goal.id} failed`, err);
    }
  }

  return json({ sent, nudged, missed });
});

/** Send the initial check-in for this period if it's due and not yet created. */
async function maybeSendInitial(
  goal: Goal,
  user: User,
  now: Date,
): Promise<boolean> {
  if (!goal.preferred_time) return false;
  if (localMinutes(now, user.timezone) < timeToMinutes(goal.preferred_time)) {
    return false; // not yet their preferred time today
  }

  const db = getAdminClient();
  const periodKey = goal.cadence === "weekly"
    ? localWeekKey(now, user.timezone)
    : localDateKey(now, user.timezone);

  // Look back far enough to cover a week; compare by local period key.
  const sinceMs = goal.cadence === "weekly"
    ? 8 * 24 * 3600 * 1000
    : 36 * 3600 * 1000;
  const { data: recent } = await db
    .from("checkins")
    .select("scheduled_for")
    .eq("goal_id", goal.id)
    .gte("scheduled_for", new Date(now.getTime() - sinceMs).toISOString());

  const alreadyThisPeriod = (recent ?? []).some((c) => {
    const d = new Date(c.scheduled_for as string);
    const key = goal.cadence === "weekly"
      ? localWeekKey(d, user.timezone)
      : localDateKey(d, user.timezone);
    return key === periodKey;
  });
  if (alreadyThisPeriod) return false;

  const body = await generateText(BOT_VOICE, checkinPrompt(goal), {
    maxTokens: 200,
  });

  const { data: checkin, error } = await db
    .from("checkins")
    .insert({
      goal_id: goal.id,
      scheduled_for: now.toISOString(),
      sent_at: now.toISOString(),
      nudge_count: 0,
    })
    .select("id")
    .single();
  if (error) throw error;

  await send(user, body, checkin.id);
  return true;
}

/** Send a gentle nudge for an open check-in, within the daily/spacing caps. */
async function maybeNudge(goal: Goal, user: User, now: Date): Promise<number> {
  const db = getAdminClient();
  const { data: open } = await db
    .from("checkins")
    .select("*")
    .eq("goal_id", goal.id)
    .is("responded_at", null)
    .not("sent_at", "is", null)
    .order("sent_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (!open) return 0;

  const sentAt = new Date(open.sent_at as string);
  // Only nudge same-local-day check-ins; older ones get swept to 'missed'.
  if (localDateKey(sentAt, user.timezone) !== localDateKey(now, user.timezone)) {
    return 0;
  }
  if ((open.nudge_count as number) >= MAX_NUDGES) return 0;

  const hoursSince = (now.getTime() - sentAt.getTime()) / 3600000;
  if (hoursSince < NUDGE_GAP_HOURS * ((open.nudge_count as number) + 1)) return 0;

  const body = await generateText(
    BOT_VOICE,
    `Write ONE very short, gentle nudge re-asking whether they did "${goal.title}" ` +
      `today. They haven't replied yet. No guilt at all. Just the message text.`,
    { maxTokens: 120 },
  );
  await send(user, body, open.id as string);
  await db
    .from("checkins")
    .update({ nudge_count: (open.nudge_count as number) + 1 })
    .eq("id", open.id);
  return 1;
}

/** Mark long-unanswered check-ins as missed. */
async function sweepMisses(goal: Goal, now: Date): Promise<number> {
  const db = getAdminClient();
  const cutoff = new Date(now.getTime() - MISS_CUTOFF_HOURS * 3600000)
    .toISOString();
  const { data } = await db
    .from("checkins")
    .update({ response: "missed", responded_at: now.toISOString() })
    .eq("goal_id", goal.id)
    .is("responded_at", null)
    .not("sent_at", "is", null)
    .lt("sent_at", cutoff)
    .select("id");
  return (data ?? []).length;
}

async function send(user: User, body: string, checkinId: string): Promise<void> {
  const wa = getWhatsAppClient();
  const providerId = await wa.send(user.whatsapp_number, body);
  await logMessage({
    userId: user.id,
    direction: "outbound",
    body,
    checkinId,
    providerId,
  });
}

// --- helpers ---------------------------------------------------------------

function checkSecret(req: Request): Response | null {
  const expected = Deno.env.get("CRON_SECRET");
  if (!expected) return null; // not configured (e.g. local dev)
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
