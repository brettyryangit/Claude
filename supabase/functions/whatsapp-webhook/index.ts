// Inbound WhatsApp webhook.
//
// Entry point for everything a user sends. Routes by user state:
//   * not on allowlist        -> polite "not available yet", stop
//   * subscription expired     -> subscribe prompt, stop (check-ins are paused)
//   * onboarding               -> AI interview (onboarding.ts)
//   * active + open check-in   -> parse yes/no, log it, acknowledge
//   * active, no open check-in -> light conversational reply
//
// Configure this URL as the inbound webhook in your BSP (Twilio sandbox →
// "When a message comes in").

import { getWhatsAppClient } from "../_shared/whatsapp.ts";
import { isAllowed } from "../_shared/allowlist.ts";
import {
  computeStreak,
  findOpenCheckinForUser,
  getOrCreateUser,
  getRecentHistory,
  logMessage,
  recentMisses,
  recordCheckinResponse,
} from "../_shared/repo.ts";
import { runOnboardingTurn } from "../_shared/onboarding.ts";
import { classifyYesNo } from "../_shared/parse.ts";
import { ackPrompt, BOT_VOICE } from "../_shared/prompts.ts";
import { Anthropic, generateText, getAnthropic, MODEL } from "../_shared/anthropic.ts";
import type { User } from "../_shared/types.ts";

Deno.serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  const wa = getWhatsAppClient();

  let inbound;
  try {
    inbound = await wa.parseInbound(req);
  } catch (err) {
    console.error("failed to parse inbound", err);
    return new Response("bad request", { status: 400 });
  }

  if (!inbound.from || !inbound.body) {
    return ok(); // delivery receipts / empty bodies — nothing to do
  }

  try {
    // Access gate (v1 friends-only pilot).
    if (!(await isAllowed(inbound.from))) {
      await wa.send(
        inbound.from,
        "Hey! This accountability bot is in a small private pilot right now and " +
          "your number isn't on the list yet. Hang tight 🙂",
      );
      return ok();
    }

    const user = await getOrCreateUser(inbound.from);
    await logMessage({
      userId: user.id,
      direction: "inbound",
      body: inbound.body,
      providerId: inbound.providerId,
    });

    // Trial/subscription gate. Check-ins are paused once expired; we only nudge
    // toward subscribing. (Real billing is out of scope for v1 — see PRIVACY/README.)
    if (user.subscription_status === "expired") {
      await reply(
        user,
        "Your free trial has wrapped up! To keep your check-ins going it's about " +
          "$5/week. Want me to send the link? (Reply 'yes' and I'll sort it.)",
      );
      return ok();
    }

    let replies: string[];
    if (user.onboarding_state === "onboarding") {
      const result = await runOnboardingTurn(user);
      replies = result.replies;
    } else {
      replies = await handleActiveMessage(user, inbound.body);
    }

    for (const r of replies) {
      if (r.trim()) await reply(user, r.trim());
    }
    return ok();
  } catch (err) {
    console.error("webhook error", err);
    // Still return 200 so the BSP doesn't retry-storm; we've logged it.
    return ok();
  }
});

async function handleActiveMessage(
  user: User,
  body: string,
): Promise<string[]> {
  const open = await findOpenCheckinForUser(user.id);

  if (open) {
    const verdict = await classifyYesNo(body);
    if (verdict !== null) {
      await recordCheckinResponse(open.checkin.id, verdict);
      const streak = await computeStreak(open.goal.id);
      const misses = await recentMisses(open.goal.id);
      const ack = await generateText(
        BOT_VOICE,
        ackPrompt({
          did_it: verdict === "yes",
          goal_title: open.goal.title,
          why: open.goal.why,
          streak,
          tone: open.goal.preferred_tone,
          recent_misses: misses,
          obstacle: open.goal.obstacle,
        }),
        { maxTokens: 256 },
      );
      return [ack];
    }
    // Couldn't tell if it's yes/no — fall through to a normal conversational reply.
  }

  return [await conversationalReply(user)];
}

/** Light, on-voice reply using recent history when there's no pending check-in. */
async function conversationalReply(user: User): Promise<string> {
  const client = getAnthropic();
  const history = await getRecentHistory(user.id, 20);
  const messages: Anthropic.MessageParam[] = history.map((m) => ({
    role: m.direction === "inbound" ? "user" : "assistant",
    content: m.body,
  }));
  if (messages.length === 0 || messages[0].role !== "user") {
    messages.unshift({ role: "user", content: "(hello)" });
  }
  const res = await client.messages.create({
    model: MODEL,
    max_tokens: 256,
    system: `${BOT_VOICE}

The user is set up and active. Reply briefly and helpfully to their latest
message. If they seem to want to change a goal or timing, acknowledge and tell
them you'll note it (a human can adjust it for now in this pilot).`,
    messages,
  });
  return res.content
    .filter((b): b is Anthropic.TextBlock => b.type === "text")
    .map((b) => b.text)
    .join("\n")
    .trim() || "👍";
}

async function reply(user: User, body: string): Promise<void> {
  const wa = getWhatsAppClient();
  const providerId = await wa.send(user.whatsapp_number, body);
  await logMessage({
    userId: user.id,
    direction: "outbound",
    body,
    providerId,
  });
}

function ok(): Response {
  // Empty 200 — Twilio accepts this (no TwiML reply needed; we send via REST).
  return new Response("", { status: 200 });
}
