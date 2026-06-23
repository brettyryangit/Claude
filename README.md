# WhatsApp Accountability Bot — v1 (friends-only pilot)

A WhatsApp bot that acts as a personal accountability coach: it interviews you
about your goals, proactively checks in on a schedule it picks, logs your
self-reported yes/no replies, notices patterns over time, and keeps the tone
light and never shaming.

This repo is the v1 scaffold built to the project spec. It targets the founder +
a handful of friends in Australia, but the data model and access gating are
**global-ready** so opening up later is config, not a rewrite.

## Stack

| Concern | Choice | Why |
|---|---|---|
| Backend + DB | **Supabase** (Postgres + Edge Functions) | No server to manage; functions run on a schedule and on webhook. |
| Messaging | **Twilio WhatsApp** behind a `WhatsAppClient` interface | Cleanest dev sandbox + full control. Swappable — see below. |
| AI layer | **Anthropic Claude** (`claude-opus-4-8`, configurable) | Drives the interview, writes check-in copy, analyzes patterns. |
| Scheduling | **GitHub Actions cron** hitting function URLs | Zero infra; matches the spec's "simple external cron". |

> **BSP choice:** the spec left "Wati vs ManyChat vs Twilio" open. v1 ships
> **Twilio** because it's the fastest to a working programmable sandbox. All
> WhatsApp I/O goes through `supabase/functions/_shared/whatsapp.ts` — to switch
> providers, implement `WhatsAppClient` for the new BSP and change
> `getWhatsAppClient()`. Nothing else touches the BSP.

## Layout

```
supabase/
  migrations/0001_initial_schema.sql   # users, goals, checkins, patterns,
                                       # messages_log, allowed_numbers (+ RLS)
  functions/
    _shared/        # supabase, anthropic, whatsapp, allowlist, prompts,
                    # parse (yes/no), tz, repo, onboarding, types
    whatsapp-webhook/   # inbound messages → onboarding / check-in / chat
    send-checkins/      # cron: send check-ins, nudge, mark misses
    detect-patterns/    # cron: weekly day-of-week pattern detection
    expire-trials/      # cron: flip trial → expired after N days
  config.toml
.github/workflows/cron.yml             # schedules the three cron functions
docs/PRIVACY.md                        # v1 privacy notice
scripts/                               # allowlist, comping, data deletion
.env.example
```

## How it works

**Onboarding** (`onboarding.ts`) — On first contact a user is created in the
`onboarding` state. Each inbound message replays the conversation to Claude with
two tools, `save_goal` and `finish_onboarding`. Claude runs a natural interview
(one question at a time, confirms before saving), capturing `title`, `why`,
`obstacle`, `preferred_time`, `preferred_tone`, `cadence` per goal — capped at 3.

**Daily check-ins** (`send-checkins`) — Runs every ~15 min. For each active goal
of a non-expired user, once local time passes `preferred_time` it sends one
AI-written, varied check-in. Unanswered ones get 1–2 gentle nudges, then are
marked `missed` after 24h — never chased forever.

**Replies** (`whatsapp-webhook`) — An inbound reply is matched to the open
check-in and classified yes/no (fast keyword pass, Claude fallback for "kinda /
not yet"). Yes → streak + acknowledgement; no → light encouragement, and after a
couple of misses it may gently offer to adjust using the stated obstacle.

**Patterns** (`detect-patterns`) — Weekly. Computes day-of-week miss rates and,
for a strong unsurfaced pattern, sends one warm conversational observation
("noticed Mondays are tough — want to try evenings?").

**Monetization** (`expire-trials`) — 7-day trial → `expired`, check-ins pause, a
subscribe nudge is sent. Friends can be set to `comped` to never expire. Real
billing (Stripe Checkout) is intentionally **out of scope for v1** — stubbed.

## Setup

Prereqs: a Supabase project, a Twilio WhatsApp sandbox, an Anthropic API key,
and the [Supabase CLI](https://supabase.com/docs/guides/cli).

```bash
# 1. Link the project
supabase login
supabase link --project-ref <your-project-ref>

# 2. Apply the schema
supabase db push

# 3. Set function secrets (fill in .env first from .env.example)
cp .env.example .env
supabase secrets set --env-file .env

# 4. Deploy the functions
supabase functions deploy whatsapp-webhook
supabase functions deploy send-checkins
supabase functions deploy detect-patterns
supabase functions deploy expire-trials
```

**Wire up Twilio:** in the WhatsApp sandbox settings, set "When a message comes
in" to:
`https://<project-ref>.supabase.co/functions/v1/whatsapp-webhook` (POST).

**Schedule the jobs:** add repo secrets `FUNCTIONS_BASE_URL`
(`https://<project-ref>.supabase.co/functions/v1`) and `CRON_SECRET`, then enable
the `.github/workflows/cron.yml` workflow. (Or point cron-job.org / Supabase's
scheduler at the same URLs with the `x-cron-secret` header.)

**Allow yourself + friends:** run `scripts/admin.sql` (insert numbers into
`allowed_numbers`, optionally `comped`). Then message the Twilio sandbox number
from an allowlisted WhatsApp to start onboarding.

## Local development

```bash
supabase start
supabase functions serve --env-file .env
# Simulate an inbound Twilio webhook:
curl -X POST http://127.0.0.1:54321/functions/v1/whatsapp-webhook \
  -d 'From=whatsapp:+61400000000' -d 'Body=hey' -d 'MessageSid=SMtest'
```

## Privacy & data

See [docs/PRIVACY.md](docs/PRIVACY.md). Supabase encrypts at rest by default;
RLS is enabled with no public policies (functions use the service-role key);
message content is never sent to third-party analytics; data deletion is
available on request via `scripts/delete-user.sql`.

## Open questions (tracked, not blockers)

- **BSP commitment** — v1 uses Twilio; revisit once a working sandbox loop is
  validated. The interface makes switching cheap.
- **AI model / cost ceiling** — defaults to `claude-opus-4-8`; set
  `ANTHROPIC_MODEL` (e.g. `claude-haiku-4-5`) to trade quality for cost on
  high-volume check-in copy once usage is observed.
- **Web dashboard** — deferred. v1 setup happens entirely over WhatsApp; admin
  tasks use `scripts/*.sql`.

## Explicitly out of scope for v1

Photo/proof verification, social/shared accountability, honesty checking, native
app, multi-language, calendar/fitness integrations, real Stripe billing, and
more than 3 goals per user.
