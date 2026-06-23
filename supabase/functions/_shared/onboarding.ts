// AI-driven onboarding interview.
//
// On each inbound message while a user is in the 'onboarding' state, we replay
// the recent conversation to Claude with the save_goal / finish_onboarding
// tools. Claude drives the interview, and when it has a confirmed goal it calls
// save_goal (which we persist). Returns the text reply(ies) to send back.

import { Anthropic, getAnthropic, MODEL } from "./anthropic.ts";
import {
  countActiveGoals,
  createGoal,
  getRecentHistory,
  MAX_GOALS,
  setOnboardingState,
} from "./repo.ts";
import { ONBOARDING_SYSTEM, ONBOARDING_TOOLS } from "./prompts.ts";
import type { User } from "./types.ts";

export interface OnboardingResult {
  replies: string[]; // messages to send back to the user, in order
  finished: boolean; // true once finish_onboarding fired
}

export async function runOnboardingTurn(user: User): Promise<OnboardingResult> {
  const client = getAnthropic();
  const history = await getRecentHistory(user.id, 40);
  const savedCount = await countActiveGoals(user.id);

  const now = new Date().toLocaleString("en-AU", { timeZone: user.timezone });
  const system = `${ONBOARDING_SYSTEM}

Context: the user's timezone is ${user.timezone}; local time is ${now}. They have
${savedCount}/${MAX_GOALS} goals saved so far.`;

  // Build the message list from logged text turns.
  const messages: Anthropic.MessageParam[] = history.map((m) => ({
    role: m.direction === "inbound" ? "user" : "assistant",
    content: m.body,
  }));
  // The conversation must start with a user turn.
  if (messages.length === 0 || messages[0].role !== "user") {
    messages.unshift({ role: "user", content: "(the user just messaged for the first time)" });
  }

  const replies: string[] = [];
  let finished = false;

  // Tool-use loop, bounded so a misbehaving model can't spin forever.
  for (let i = 0; i < 6; i++) {
    const res = await client.messages.create({
      model: MODEL,
      max_tokens: 1024,
      system,
      tools: ONBOARDING_TOOLS as unknown as Anthropic.Tool[],
      messages,
    });

    for (const block of res.content) {
      if (block.type === "text" && block.text.trim()) {
        replies.push(block.text.trim());
      }
    }

    if (res.stop_reason !== "tool_use") break;

    // Execute each tool call and gather results to feed back.
    messages.push({ role: "assistant", content: res.content });
    const toolResults: Anthropic.ToolResultBlockParam[] = [];

    for (const block of res.content) {
      if (block.type !== "tool_use") continue;
      try {
        if (block.name === "save_goal") {
          const result = await handleSaveGoal(user, block.input);
          toolResults.push({
            type: "tool_result",
            tool_use_id: block.id,
            content: result,
          });
        } else if (block.name === "finish_onboarding") {
          const input = block.input as { closing_message?: string };
          if (input.closing_message) replies.push(input.closing_message.trim());
          await setOnboardingState(user.id, "active");
          finished = true;
          toolResults.push({
            type: "tool_result",
            tool_use_id: block.id,
            content: "Onboarding marked complete.",
          });
        } else {
          toolResults.push({
            type: "tool_result",
            tool_use_id: block.id,
            content: `Unknown tool: ${block.name}`,
            is_error: true,
          });
        }
      } catch (err) {
        toolResults.push({
          type: "tool_result",
          tool_use_id: block.id,
          content: `Error: ${err instanceof Error ? err.message : String(err)}`,
          is_error: true,
        });
      }
    }

    if (finished) break;
    messages.push({ role: "user", content: toolResults });
  }

  return { replies, finished };
}

async function handleSaveGoal(user: User, input: unknown): Promise<string> {
  const count = await countActiveGoals(user.id);
  if (count >= MAX_GOALS) {
    return `The user already has ${MAX_GOALS} goals (the v1 cap). Do not save more; ` +
      `move to finishing onboarding.`;
  }
  const g = input as {
    title: string;
    why: string;
    obstacle: string;
    preferred_time: string;
    preferred_tone: "soft" | "direct";
    cadence: "daily" | "weekly";
  };
  const time = normalizeTime(g.preferred_time);
  await createGoal(user.id, { ...g, preferred_time: time });
  return `Saved "${g.title}" (${count + 1}/${MAX_GOALS}). If they have another goal, ask about it; otherwise finish.`;
}

/** Coerce "7am", "7:00", "07:00" → "HH:MM" for the time column. */
function normalizeTime(raw: string): string {
  const t = raw.trim().toLowerCase();
  const m = t.match(/^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$/);
  if (!m) return "09:00"; // safe default
  let h = parseInt(m[1], 10);
  const min = m[2] ? parseInt(m[2], 10) : 0;
  if (m[3] === "pm" && h < 12) h += 12;
  if (m[3] === "am" && h === 12) h = 0;
  return `${String(h).padStart(2, "0")}:${String(min).padStart(2, "0")}`;
}
