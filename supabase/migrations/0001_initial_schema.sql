-- WhatsApp Accountability Bot — initial schema (v1: friends-only pilot)
--
-- Design notes (from the build spec):
--   * timezone is per-user from day one (global-readiness, costs nothing now).
--   * checkins.response stays null until answered; the send-checkins job marks
--     stale unanswered check-ins as a miss after a cutoff window — never chased
--     forever.
--   * messages_log stores raw inbound/outbound WhatsApp messages for debugging
--     and for feeding conversation history back into the AI layer.
--   * allowed_numbers gates access to the founder + friends. Opening up later is
--     a data change (insert rows / flip a flag), not a code change.
--
-- Supabase encrypts data at rest by default (AES-256). No app-level changes
-- needed to satisfy the v1 privacy bar; see docs/PRIVACY.md.

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- Access allowlist (v1 = Australia / friends only)
-- ---------------------------------------------------------------------------
create table if not exists allowed_numbers (
  id            uuid primary key default gen_random_uuid(),
  whatsapp_number text unique not null,   -- E.164, e.g. +61412345678
  note          text,                     -- "founder", "alex (friend)", etc.
  enabled       boolean not null default true,
  created_at    timestamptz not null default now()
);

comment on table allowed_numbers is
  'Invite allowlist. To open the product up later, relax the check in the '
  'webhook (or insert rows) — no code rewrite required.';

-- ---------------------------------------------------------------------------
-- Users
-- ---------------------------------------------------------------------------
create table if not exists users (
  id                  uuid primary key default gen_random_uuid(),
  whatsapp_number     text unique not null,
  display_name        text,
  timezone            text not null default 'Australia/Perth',
  -- onboarding | active : drives which conversation flow inbound messages hit.
  onboarding_state    text not null default 'onboarding'
                        check (onboarding_state in ('onboarding', 'active')),
  trial_started_at    timestamptz,
  -- trial | active | expired | cancelled | comped
  -- 'comped' = friends pilot access granted manually, never billed.
  subscription_status text not null default 'trial'
                        check (subscription_status in
                          ('trial', 'active', 'expired', 'cancelled', 'comped')),
  created_at          timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Goals (cap of 3 per user enforced in app logic, see _shared/goals.ts)
-- ---------------------------------------------------------------------------
create table if not exists goals (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references users(id) on delete cascade,
  title          text not null,            -- e.g. "Go to the gym"
  why            text,                     -- stated motivation, used in nudge copy
  obstacle       text,                     -- what typically gets in the way
  preferred_time time,                     -- local time they're most likely to do it
  preferred_tone text not null default 'soft'
                   check (preferred_tone in ('soft', 'direct')),
  -- cadence: how often we check in. v1 supports daily + weekly.
  cadence        text not null default 'daily'
                   check (cadence in ('daily', 'weekly')),
  status         text not null default 'active'
                   check (status in ('active', 'paused', 'archived')),
  created_at     timestamptz not null default now()
);

create index if not exists goals_user_id_idx on goals(user_id);
create index if not exists goals_active_idx on goals(status) where status = 'active';

-- ---------------------------------------------------------------------------
-- Check-ins
-- ---------------------------------------------------------------------------
create table if not exists checkins (
  id            uuid primary key default gen_random_uuid(),
  goal_id       uuid not null references goals(id) on delete cascade,
  scheduled_for timestamptz not null,
  sent_at       timestamptz,
  responded_at  timestamptz,
  response      text check (response in ('yes', 'no', 'missed')),
  -- how many nudges we've sent for this check-in (cap enforced in send-checkins).
  nudge_count   smallint not null default 0,
  created_at    timestamptz not null default now()
);

create index if not exists checkins_goal_id_idx on checkins(goal_id);
-- Fast lookup of the most recent open (sent, unanswered) check-in for a goal —
-- used when matching an inbound reply to the check-in it answers.
create index if not exists checkins_open_idx
  on checkins(goal_id, sent_at)
  where responded_at is null and sent_at is not null;
create index if not exists checkins_scheduled_idx
  on checkins(scheduled_for) where sent_at is null;

-- ---------------------------------------------------------------------------
-- Patterns (computed/cached insights, refreshed by the weekly job)
-- ---------------------------------------------------------------------------
create table if not exists patterns (
  id           uuid primary key default gen_random_uuid(),
  goal_id      uuid not null references goals(id) on delete cascade,
  insight      text not null,   -- e.g. "Misses check-ins on Mondays 4/5 times"
  -- whether this insight has already been surfaced to the user conversationally,
  -- so we don't repeat the same observation every week.
  surfaced_at  timestamptz,
  computed_at  timestamptz not null default now()
);

create index if not exists patterns_goal_id_idx on patterns(goal_id);

-- ---------------------------------------------------------------------------
-- Raw message log (debugging + AI conversation history)
-- ---------------------------------------------------------------------------
create table if not exists messages_log (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references users(id) on delete cascade,
  -- direction: inbound (user -> bot) or outbound (bot -> user)
  direction   text not null check (direction in ('inbound', 'outbound')),
  body        text not null,
  -- optional link to the check-in this message relates to (a sent prompt, or a reply)
  checkin_id  uuid references checkins(id) on delete set null,
  -- BSP message id (Twilio SID etc.) for delivery debugging
  provider_id text,
  created_at  timestamptz not null default now()
);

create index if not exists messages_log_user_id_idx on messages_log(user_id, created_at desc);

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------
-- All access is via Edge Functions using the service-role key (which bypasses
-- RLS). We still enable RLS with no permissive policies so that if the anon /
-- authenticated keys are ever exposed (e.g. a future web dashboard), these
-- tables are not readable by default. Add scoped policies when the dashboard
-- lands.
alter table allowed_numbers enable row level security;
alter table users           enable row level security;
alter table goals           enable row level security;
alter table checkins        enable row level security;
alter table patterns        enable row level security;
alter table messages_log    enable row level security;
