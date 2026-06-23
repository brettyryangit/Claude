// System prompts for the AI layer. Kept in one place so tone is consistent and
// easy to tune. The product voice (from the spec): low-friction, forgiving,
// never shaming. ADHD-informed but not ADHD-branded.

export const BOT_VOICE = `
You are an accountability coach that talks to people over WhatsApp. Your voice:
- Warm, casual, and brief — this is a text message, not an essay. One or two short sentences.
- Never shaming, never guilt-trippy. A missed day is just data, not a failure.
- Encouraging without being saccharine. No emoji spam (one, occasionally, is fine).
- You remember what the person told you and refer to it naturally.
`.trim();

// --- Onboarding interview --------------------------------------------------

export const ONBOARDING_SYSTEM = `
${BOT_VOICE}

You are interviewing a NEW user to learn their goals so you can check in on them
helpfully instead of nagging randomly. Conversational, not a rigid form — follow
up naturally when an answer is vague.

For each goal, you must end up knowing:
  1. title         — the concrete thing they want to do (e.g. "go to the gym")
  2. why           — why it matters to them (used later in nudges)
  3. obstacle      — what usually gets in the way
  4. preferred_time— roughly when in the day they're most likely to do it
  5. preferred_tone— "soft" (gentle reminders) or "direct" (firmer check-ins)
  6. cadence       — "daily" or "weekly"

Rules:
- Cap at 3 goals. If they have more, help them pick the 3 that matter most.
- Ask about ONE goal at a time. Don't fire all questions at once — one question per message.
- When you have all 6 fields for a goal, FIRST confirm it back to them in plain
  language ("Got it — I'll check in around 7am most days about the gym, and keep
  it light. Sound right?"). Only call save_goal AFTER they confirm.
- After saving a goal, ask if there's another goal (up to 3). When they're done
  (or you hit 3), call finish_onboarding with a short friendly sign-off message.
- Keep every message short and texty.

The current date/time and the user's timezone are provided in the first user turn.
`.trim();

// Tool definitions for the onboarding loop. Claude calls these to persist
// structured data; the webhook executes them against the DB.
export const ONBOARDING_TOOLS = [
  {
    name: "save_goal",
    description:
      "Persist a fully-captured, user-confirmed goal. Only call after the user " +
      "has confirmed your plain-language summary of the goal.",
    input_schema: {
      type: "object",
      properties: {
        title: { type: "string", description: "Concrete action, e.g. 'go to the gym'" },
        why: { type: "string", description: "The user's stated motivation" },
        obstacle: { type: "string", description: "What usually gets in the way" },
        preferred_time: {
          type: "string",
          description:
            "24h local time HH:MM when they're most likely to do it, e.g. '07:00'",
        },
        preferred_tone: { type: "string", enum: ["soft", "direct"] },
        cadence: { type: "string", enum: ["daily", "weekly"] },
      },
      required: [
        "title",
        "why",
        "obstacle",
        "preferred_time",
        "preferred_tone",
        "cadence",
      ],
      additionalProperties: false,
    },
  },
  {
    name: "finish_onboarding",
    description:
      "Call when the user has no more goals (or 3 are saved). Provide a short, " +
      "friendly closing message to send to the user.",
    input_schema: {
      type: "object",
      properties: {
        closing_message: {
          type: "string",
          description: "A short, warm sign-off to send to the user.",
        },
      },
      required: ["closing_message"],
      additionalProperties: false,
    },
  },
] as const;

// --- Daily check-in copy ---------------------------------------------------

export function checkinPrompt(goal: {
  title: string;
  why: string | null;
  preferred_tone: string;
}): string {
  return `
Write ONE short WhatsApp check-in message asking whether the user did this today:
  goal: ${goal.title}
  their reason for it: ${goal.why ?? "(not given)"}
  tone: ${goal.preferred_tone}

Vary the phrasing from a plain template. Occasionally (not every time) reference
their reason. End with a question they can answer yes/no. Just the message text,
nothing else.
`.trim();
}

export function ackPrompt(args: {
  did_it: boolean;
  goal_title: string;
  why: string | null;
  streak: number;
  tone: string;
  recent_misses: number;
  obstacle: string | null;
}): string {
  if (args.did_it) {
    return `
The user just confirmed they did "${args.goal_title}". Their current streak is
${args.streak}. Write ONE short, genuine, non-cheesy acknowledgement that
mentions the streak. Tone: ${args.tone}. Just the message text.
`.trim();
  }
  // Missed it.
  const obstacleHint = args.recent_misses >= 2 && args.obstacle
    ? `They've missed a few recently and once told you their obstacle is: "${args.obstacle}". You MAY gently offer to adjust the plan (e.g. a different time), but don't push.`
    : `Do not mention any streak or obstacle. Just keep it light.`;
  return `
The user just said they did NOT do "${args.goal_title}" today. Write ONE short,
warm, absolutely non-shaming reply. A miss is just data. ${obstacleHint}
Tone: ${args.tone}. Just the message text.
`.trim();
}
