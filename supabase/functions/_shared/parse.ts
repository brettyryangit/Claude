// Natural-language yes/no classification for check-in replies.
//
// Users reply informally: "yeah", "nah", "not yet", "done ✅", "missed it
// today", "kinda". A fast keyword pass handles the obvious cases; anything
// ambiguous falls back to Claude. Returns null when it genuinely can't tell
// (the caller then treats it as a normal conversational message, not a y/n).

import { generateText } from "./anthropic.ts";

export type YesNo = "yes" | "no" | null;

const YES = [
  "yes", "yeah", "yep", "yup", "ya", "yarp", "yes!", "did it", "done",
  "completed", "finished", "got it done", "✅", "👍", "sure did", "indeed",
  "affirmative", "all done", "smashed it",
];
const NO = [
  "no", "nope", "nah", "naw", "not yet", "didn't", "didnt", "did not",
  "missed", "missed it", "skip", "skipped", "couldn't", "couldnt", "failed",
  "no time", "not today", "negative", "❌",
];

function keywordPass(raw: string): YesNo {
  const t = raw.trim().toLowerCase();
  if (!t) return null;
  // Whole-message exact match first (most reliable).
  if (YES.includes(t)) return "yes";
  if (NO.includes(t)) return "no";
  // "not"/"didn't" style negations take priority over a stray "yes".
  if (NO.some((k) => t.includes(k))) return "no";
  if (YES.some((k) => t.includes(k))) return "yes";
  return null;
}

export async function classifyYesNo(raw: string): Promise<YesNo> {
  const quick = keywordPass(raw);
  if (quick !== null) return quick;

  // Ambiguous — ask the model. Keep it cheap and deterministic.
  const out = await generateText(
    "You classify a person's reply to 'did you do your task today?' Respond with " +
      "exactly one word: YES, NO, or UNCLEAR. Nothing else.",
    `Reply: "${raw}"`,
    { maxTokens: 8 },
  );
  const v = out.trim().toLowerCase();
  if (v.startsWith("yes")) return "yes";
  if (v.startsWith("no")) return "no";
  return null;
}
