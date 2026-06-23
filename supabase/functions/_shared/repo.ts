// Common data-access helpers shared across functions.

import { getAdminClient } from "./supabase.ts";
import type { Checkin, Goal, MessageLog, User } from "./types.ts";

const MAX_GOALS = 3; // v1 cap (spec section 5.1)

export async function findUserByNumber(
  whatsappNumber: string,
): Promise<User | null> {
  const db = getAdminClient();
  const { data } = await db
    .from("users")
    .select("*")
    .eq("whatsapp_number", whatsappNumber)
    .maybeSingle();
  return (data as User) ?? null;
}

/** First contact creates the user in the 'onboarding' state and starts the trial. */
export async function getOrCreateUser(whatsappNumber: string): Promise<User> {
  const existing = await findUserByNumber(whatsappNumber);
  if (existing) return existing;

  const db = getAdminClient();
  const defaultTz = Deno.env.get("DEFAULT_TIMEZONE") ?? "Australia/Perth";
  const { data, error } = await db
    .from("users")
    .insert({
      whatsapp_number: whatsappNumber,
      timezone: defaultTz,
      onboarding_state: "onboarding",
      subscription_status: "trial",
      trial_started_at: new Date().toISOString(),
    })
    .select("*")
    .single();
  if (error) throw error;
  return data as User;
}

export async function logMessage(args: {
  userId: string | null;
  direction: "inbound" | "outbound";
  body: string;
  checkinId?: string | null;
  providerId?: string | null;
}): Promise<void> {
  const db = getAdminClient();
  const { error } = await db.from("messages_log").insert({
    user_id: args.userId,
    direction: args.direction,
    body: args.body,
    checkin_id: args.checkinId ?? null,
    provider_id: args.providerId ?? null,
  });
  if (error) console.error("logMessage failed", error);
}

/** Recent conversation turns for feeding back into the AI layer (oldest first). */
export async function getRecentHistory(
  userId: string,
  limit = 30,
): Promise<MessageLog[]> {
  const db = getAdminClient();
  const { data } = await db
    .from("messages_log")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(limit);
  return ((data as MessageLog[]) ?? []).reverse();
}

export async function getActiveGoals(userId: string): Promise<Goal[]> {
  const db = getAdminClient();
  const { data } = await db
    .from("goals")
    .select("*")
    .eq("user_id", userId)
    .eq("status", "active")
    .order("created_at", { ascending: true });
  return (data as Goal[]) ?? [];
}

export async function countActiveGoals(userId: string): Promise<number> {
  const db = getAdminClient();
  const { count } = await db
    .from("goals")
    .select("id", { count: "exact", head: true })
    .eq("user_id", userId)
    .eq("status", "active");
  return count ?? 0;
}

export { MAX_GOALS };

export async function createGoal(
  userId: string,
  g: {
    title: string;
    why: string;
    obstacle: string;
    preferred_time: string; // "HH:MM"
    preferred_tone: "soft" | "direct";
    cadence: "daily" | "weekly";
  },
): Promise<Goal> {
  const db = getAdminClient();
  const { data, error } = await db
    .from("goals")
    .insert({ user_id: userId, ...g })
    .select("*")
    .single();
  if (error) throw error;
  return data as Goal;
}

export async function setOnboardingState(
  userId: string,
  state: "onboarding" | "active",
): Promise<void> {
  const db = getAdminClient();
  await db.from("users").update({ onboarding_state: state }).eq("id", userId);
}

/**
 * Most recent check-in for a goal that was sent but not yet answered. Used to
 * match an inbound reply to the check-in it answers.
 */
export async function findOpenCheckin(goalId: string): Promise<Checkin | null> {
  const db = getAdminClient();
  const { data } = await db
    .from("checkins")
    .select("*")
    .eq("goal_id", goalId)
    .is("responded_at", null)
    .not("sent_at", "is", null)
    .order("sent_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  return (data as Checkin) ?? null;
}

/** The single most recent open check-in across all of a user's active goals. */
export async function findOpenCheckinForUser(
  userId: string,
): Promise<{ checkin: Checkin; goal: Goal } | null> {
  const goals = await getActiveGoals(userId);
  let best: { checkin: Checkin; goal: Goal } | null = null;
  for (const goal of goals) {
    const c = await findOpenCheckin(goal.id);
    if (c && (!best || c.sent_at! > best.checkin.sent_at!)) {
      best = { checkin: c, goal };
    }
  }
  return best;
}

export async function recordCheckinResponse(
  checkinId: string,
  response: "yes" | "no" | "missed",
): Promise<void> {
  const db = getAdminClient();
  await db
    .from("checkins")
    .update({ response, responded_at: new Date().toISOString() })
    .eq("id", checkinId);
}

/**
 * Current streak for a goal = consecutive most-recent answered check-ins with
 * response 'yes'. A 'no' or 'missed' breaks it; unanswered (null) check-ins are
 * ignored.
 */
export async function computeStreak(goalId: string): Promise<number> {
  const db = getAdminClient();
  const { data } = await db
    .from("checkins")
    .select("response, responded_at")
    .eq("goal_id", goalId)
    .not("response", "is", null)
    .order("scheduled_for", { ascending: false })
    .limit(60);
  let streak = 0;
  for (const row of (data as { response: string }[]) ?? []) {
    if (row.response === "yes") streak++;
    else break;
  }
  return streak;
}

/** Count of the most recent consecutive non-'yes' check-ins (for obstacle nudges). */
export async function recentMisses(goalId: string): Promise<number> {
  const db = getAdminClient();
  const { data } = await db
    .from("checkins")
    .select("response")
    .eq("goal_id", goalId)
    .not("response", "is", null)
    .order("scheduled_for", { ascending: false })
    .limit(10);
  let misses = 0;
  for (const row of (data as { response: string }[]) ?? []) {
    if (row.response === "yes") break;
    misses++;
  }
  return misses;
}
