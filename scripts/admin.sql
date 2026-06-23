-- Admin snippets for the v1 pilot. Run in the Supabase SQL editor.
-- Numbers are E.164 (e.g. +61412345678) — match exactly what WhatsApp sends.

-- 1. Add someone to the access allowlist (founder + friends).
insert into allowed_numbers (whatsapp_number, note)
values ('+61400000000', 'founder')
on conflict (whatsapp_number) do update set enabled = true;

-- 2. Comp a friend so they're never expired (free pilot access).
update users
set subscription_status = 'comped'
where whatsapp_number = '+61400000000';

-- 3. Remove/disable allowlist access for a number.
update allowed_numbers set enabled = false
where whatsapp_number = '+61400000000';

-- 4. Inspect a user's setup and recent activity.
select u.id, u.display_name, u.timezone, u.onboarding_state,
       u.subscription_status, u.trial_started_at
from users u
where u.whatsapp_number = '+61400000000';

select g.title, g.preferred_time, g.cadence, g.preferred_tone, g.status
from goals g
join users u on u.id = g.user_id
where u.whatsapp_number = '+61400000000';
