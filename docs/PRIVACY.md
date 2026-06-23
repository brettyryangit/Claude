# Privacy Policy (v1 pilot)

_Last updated: 2026-06-23_

This is a lightweight privacy notice for the friends-only pilot of the WhatsApp
accountability bot. It is intentionally plain; it is not enterprise/HIPAA-grade.

## What we collect

- Your WhatsApp number and display name.
- The goals you tell us about (title, your motivation, what gets in your way,
  preferred timing and tone).
- Your check-in responses (yes / no / no-reply) and timestamps.
- The content of messages exchanged with the bot, kept to run and debug the
  service and to give the AI helpful context.
- A timezone, so check-ins land at sensible local times.

## How it's used

- To send you personalized check-ins and notice patterns over time.
- To improve your experience (e.g. adjusting timing if mornings aren't working).

We do **not** sell or share your data with third parties for advertising.

## Who processes it

- **Supabase** (database/hosting) — data is encrypted at rest by default.
- **Twilio** (WhatsApp message delivery).
- **Anthropic** (the AI that writes check-ins and reads your history to respond).

We do not send your message content to third-party analytics tools.

## Your choices

- **Delete my data:** ask and we'll remove your account and all associated data.
  In v1 this is done manually by an admin (see `scripts/delete-user.sql`); it is
  always possible on request.
- **Stop messages:** tell the bot to stop, or ask to be removed from the pilot.

## Contact

brettyryan@gmail.com
