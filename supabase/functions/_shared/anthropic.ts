// Claude API wrapper for the AI/personalization layer.
//
// Used for:
//   (a) the onboarding interview conversation (tool-driven; see onboarding.ts)
//   (b) generating check-in message variations
//   (c) periodic pattern analysis on a user's history
//
// Model is configurable via ANTHROPIC_MODEL so the founder can tune the
// per-message cost ceiling once real usage is observed (open question in the
// spec). Default is the most capable current model.

// Pin to the installed version after first deploy for reproducibility (e.g.
// "npm:@anthropic-ai/sdk@<version>"). Unpinned resolves to latest at deploy time.
import Anthropic from "npm:@anthropic-ai/sdk";

export const MODEL = Deno.env.get("ANTHROPIC_MODEL") ?? "claude-opus-4-8";

let cached: Anthropic | null = null;

export function getAnthropic(): Anthropic {
  if (cached) return cached;
  const apiKey = Deno.env.get("ANTHROPIC_API_KEY");
  if (!apiKey) throw new Error("ANTHROPIC_API_KEY must be set.");
  cached = new Anthropic({ apiKey });
  return cached;
}

/**
 * One-shot text generation. Adaptive thinking is left off for these short,
 * latency-sensitive calls (check-in copy, yes/no classification); turn it on
 * for the heavier reasoning calls (see analyzePatterns).
 */
export async function generateText(
  system: string,
  user: string,
  opts: { maxTokens?: number; adaptiveThinking?: boolean } = {},
): Promise<string> {
  const client = getAnthropic();
  const res = await client.messages.create({
    model: MODEL,
    max_tokens: opts.maxTokens ?? 1024,
    ...(opts.adaptiveThinking
      ? { thinking: { type: "adaptive" as const } }
      : {}),
    system,
    messages: [{ role: "user", content: user }],
  });
  return res.content
    .filter((b): b is Anthropic.TextBlock => b.type === "text")
    .map((b) => b.text)
    .join("\n")
    .trim();
}

export { Anthropic };
