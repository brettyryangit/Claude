// Pattern detection (run weekly via cron).
//
// For each active goal it scans the check-in history and surfaces simple, real
// patterns (day-of-week miss rates) into the `patterns` table. When a strong,
// not-yet-surfaced pattern exists, it proactively sends ONE conversational
// observation to the user — phrased warmly, never as a clinical report.

import { getAdminClient } from "../_shared/supabase.ts";
import { getWhatsAppClient } from "../_shared/whatsapp.ts";
import { generateText } from "../_shared/anthropic.ts";
import { BOT_VOICE } from "../_shared/prompts.ts";
import { logMessage } from "../_shared/repo.ts";
import { localParts } from "../_shared/tz.ts";
import type { Checkin, Goal, User } from "../_shared/types.ts";

const DOW = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const MIN_SAMPLES = 3; // need at least this many of a weekday before calling it a pattern
const MISS_RATE_THRESHOLD = 0.6; // 60%+ miss rate on a weekday is noteworthy

Deno.serve(async (req) => {
  const guard = checkSecret(req);
  if (guard) return guard;

  const db = getAdminClient();
  const { data: goals, error } = await db
    .from("goals")
    .select("*, users!inner(*)")
    .eq("status", "active")
    .in("users.subscription_status", ["trial", "active", "comped"]);
  if (error) return json({ error: "load failed" }, 500);

  let insights = 0, surfaced = 0;

  for (const row of (goals ?? []) as (Goal & { users: User })[]) {
    const goal = row;
    const user = row.users;
    try {
      const insight = await computeDowPattern(goal, user);
      if (!insight) continue;
      insights++;

      // Store the insight (and surface at most one per user per run).
      const inserted = await storeInsight(goal.id, insight);
      if (inserted && surfaced === 0) {
        await surface(goal, user, insight);
        surfaced++;
      }
    } catch (err) {
      console.error(`pattern detect failed for goal ${goal.id}`, err);
    }
  }

  return json({ insights, surfaced });
});

/** Returns a human-readable insight string if a strong weekday pattern exists. */
async function computeDowPattern(
  goal: Goal,
  user: User,
): Promise<string | null> {
  const db = getAdminClient();
  const { data } = await db
    .from("checkins")
    .select("scheduled_for, response")
    .eq("goal_id", goal.id)
    .in("response", ["yes", "no", "missed"])
    .order("scheduled_for", { ascending: false })
    .limit(120);

  const rows = (data as Pick<Checkin, "scheduled_for" | "response">[]) ?? [];
  if (rows.length < MIN_SAMPLES) return null;

  // Tally per local weekday.
  const totals = new Array(7).fill(0);
  const misses = new Array(7).fill(0);
  for (const r of rows) {
    const wd = localParts(new Date(r.scheduled_for), user.timezone).weekday;
    totals[wd]++;
    if (r.response !== "yes") misses[wd]++;
  }

  let worst = -1, worstRate = 0;
  for (let i = 0; i < 7; i++) {
    if (totals[i] < MIN_SAMPLES) continue;
    const rate = misses[i] / totals[i];
    if (rate >= MISS_RATE_THRESHOLD && rate > worstRate) {
      worst = i;
      worstRate = rate;
    }
  }
  if (worst < 0) return null;

  return `Misses "${goal.title}" on ${DOW[worst]}s ${misses[worst]}/${totals[worst]} times.`;
}

/** Insert the insight unless an identical one was computed in the last 6 days. */
async function storeInsight(goalId: string, insight: string): Promise<boolean> {
  const db = getAdminClient();
  const sixDaysAgo = new Date(Date.now() - 6 * 24 * 3600 * 1000).toISOString();
  const { data: existing } = await db
    .from("patterns")
    .select("id")
    .eq("goal_id", goalId)
    .eq("insight", insight)
    .gte("computed_at", sixDaysAgo)
    .maybeSingle();
  if (existing) return false;

  await db.from("patterns").insert({ goal_id: goalId, insight });
  return true;
}

/** Send a warm, conversational version of the insight and mark it surfaced. */
async function surface(goal: Goal, user: User, insight: string): Promise<void> {
  const body = await generateText(
    BOT_VOICE,
    `You noticed this pattern in the user's check-ins: "${insight}". Mention it ` +
      `conversationally (not as a report) and gently ask if something about that ` +
      `day makes it harder, or if they'd like to adjust the plan. One short message.`,
    { maxTokens: 200, adaptiveThinking: false },
  );
  const wa = getWhatsAppClient();
  const providerId = await wa.send(user.whatsapp_number, body);
  await logMessage({
    userId: user.id,
    direction: "outbound",
    body,
    providerId,
  });

  const db = getAdminClient();
  await db
    .from("patterns")
    .update({ surfaced_at: new Date().toISOString() })
    .eq("goal_id", goal.id)
    .eq("insight", insight);
}

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
